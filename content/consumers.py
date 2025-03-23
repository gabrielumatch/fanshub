import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fanshub.settings')

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from accounts.models import User
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Store online users in memory
online_users = {}
offline_tasks = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.room_group_name = f'chat_{self.chat_id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Add user to online users set
            if self.chat_id not in online_users:
                online_users[self.chat_id] = set()
            online_users[self.chat_id].add(self.scope['user'].id)
            
            # Cancel any existing offline task for this user
            if self.scope['user'].id in offline_tasks:
                offline_tasks[self.scope['user'].id].cancel()
                del offline_tasks[self.scope['user'].id]
            
            # Notify others that user is online
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.scope['user'].id,
                    'status': 'online'
                }
            )
            
            await self.accept()
            
            # Mark user as online
            await self.mark_online()
        except Exception as e:
            raise

    async def disconnect(self, close_code):
        try:
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Start offline cooldown
            asyncio.create_task(self.mark_offline())
        except Exception as e:
            raise

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data:
                # Handle text messages
                data = json.loads(text_data)
                message_type = data.get('type')
                
                if message_type == 'message':
                    # Handle text message
                    message = data.get('message', '')
                    if message:
                        new_message = await self.save_message(message)
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': new_message.content,
                                'user_id': self.scope['user'].id,
                                'username': self.scope['user'].username,
                                'timestamp': new_message.created_at.isoformat()
                            }
                        )
                
                elif message_type == 'media_message':
                    # Handle media message
                    try:
                        # Decode base64 data
                        import base64
                        file_data = base64.b64decode(data['data'])
                        
                        # Get file extension from content type
                        content_type = data.get('content_type', '')
                        
                        if content_type.startswith('image/'):
                            file_extension = '.jpg'  # Default to jpg for images
                        elif content_type.startswith('video/'):
                            file_extension = '.mp4'  # Default to mp4 for videos
                        else:
                            file_extension = self.get_file_extension(file_data[:4])
                        
                        if not file_extension:
                            return
                        
                        # Create a unique filename
                        filename = f'chat_{self.chat_id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}{file_extension}'
                        
                        # Save the file
                        file_path = await self.save_media_file(file_data, filename)
                        
                        # Determine media type
                        media_type = 'image' if file_extension in ['.jpg', '.jpeg', '.png', '.gif'] else 'video'
                        
                        # Save message with media
                        new_message = await self.save_message('', media_url=file_path, media_type=media_type)
                        
                        # Send media message to group
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': '',
                                'media_url': file_path,
                                'media_type': media_type,
                                'user_id': self.scope['user'].id,
                                'username': self.scope['user'].username,
                                'timestamp': new_message.created_at.isoformat()
                            }
                        )
                    except Exception as e:
                        pass
                
                elif message_type == 'typing':
                    # Handle typing status
                    is_typing = data.get('is_typing', False)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'typing_status',
                            'user_id': self.scope['user'].id,
                            'username': self.scope['user'].username,
                            'is_typing': is_typing
                        }
                    )
            
            elif bytes_data:
                pass
            
        except json.JSONDecodeError:
            pass
        except Exception as e:
            raise

    def get_file_extension(self, header_bytes):
        # Check for image signatures
        if header_bytes.startswith(b'\xFF\xD8\xFF'):  # JPEG
            return '.jpg'
        elif header_bytes.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return '.png'
        elif header_bytes.startswith(b'GIF87a') or header_bytes.startswith(b'GIF89a'):  # GIF
            return '.gif'
        # Check for video signatures
        elif header_bytes.startswith(b'\x00\x00\x00') or header_bytes.startswith(b'ftyp'):  # MP4
            return '.mp4'
        return None
    
    @database_sync_to_async
    def save_media_file(self, file_data, filename):
        try:
            # Create the chat_media directory if it doesn't exist
            media_dir = 'chat_media'
            if not default_storage.exists(media_dir):
                default_storage.makedirs(media_dir)
            
            # Save the file using Django's storage
            file_path = os.path.join(media_dir, filename)
            path = default_storage.save(file_path, ContentFile(file_data))
            return path
        except Exception as e:
            raise

    async def chat_message(self, event):
        try:
            message = event.get('message', '')
            user_id = event['user_id']
            media_url = event.get('media_url')
            media_type = event.get('media_type')
            timestamp = event.get('timestamp')
            
            # Ensure the URL is absolute
            if media_url and not media_url.startswith(('http://', 'https://')):
                # Get the request scheme (http or https)
                scheme = 'https' if self.scope.get('scheme') == 'https' else 'http'
                # Get the host from headers
                host = None
                for header_name, header_value in self.scope.get('headers', []):
                    if header_name == b'host':
                        host = header_value.decode('utf-8')
                        break
                if not host:
                    host = f"{self.scope['server'][0]}:{self.scope['server'][1]}"
                # Convert the file path to a URL
                media_url = f"{scheme}://{host}/media/{media_url}"
            
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message': message,
                'user_id': user_id,
                'media_url': media_url,
                'media_type': media_type,
                'timestamp': timestamp
            }))
        except Exception as e:
            raise

    async def user_status(self, event):
        try:
            user_id = event['user_id']
            status = event['status']
            
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': user_id,
                'status': status
            }))
        except Exception as e:
            raise

    async def typing_status(self, event):
        try:
            user_id = event['user_id']
            username = event['username']
            is_typing = event['is_typing']
            
            await self.send(text_data=json.dumps({
                'type': 'typing_status',
                'user_id': user_id,
                'username': username,
                'is_typing': is_typing
            }))
        except Exception as e:
            raise

    @database_sync_to_async
    def save_message(self, message, media_url=None, media_type=None):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return Message.objects.create(
                chat=chat,
                sender=self.scope['user'],
                content=message,
                media=media_url,
                media_type=media_type
            )
        except Exception as e:
            raise

    @database_sync_to_async
    def mark_online(self):
        user = self.scope['user']
        user.is_online = True
        user.last_seen = timezone.now()
        user.save()

    async def mark_offline(self):
        await asyncio.sleep(10)  # 10 second cooldown
        await self.mark_offline_db()

    @database_sync_to_async
    def mark_offline_db(self):
        user = self.scope['user']
        user.is_online = False
        user.last_seen = timezone.now()
        user.save() 