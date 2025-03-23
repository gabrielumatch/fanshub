import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fanshub.settings')

import json
import logging
import traceback
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

User = get_user_model()

# Store online users in memory
online_users = {}
offline_tasks = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            logger.debug(f"Attempting to connect to chat room: {self.scope['url_route']['kwargs']['chat_id']}")
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.room_group_name = f'chat_{self.chat_id}'
            self.user_id = self.scope['user'].id
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Add user to online users set
            if self.chat_id not in online_users:
                online_users[self.chat_id] = set()
            online_users[self.chat_id].add(self.user_id)
            
            # Cancel any existing offline task for this user
            if self.user_id in offline_tasks:
                offline_tasks[self.user_id].cancel()
                del offline_tasks[self.user_id]
            
            # Notify others that user is online
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user_id,
                    'status': 'online'
                }
            )
            
            await self.accept()
            logger.debug(f"Successfully connected to chat room: {self.chat_id}")
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def disconnect(self, close_code):
        try:
            logger.debug(f"Disconnecting from chat room: {self.chat_id}")
            
            # Create a task to mark user as offline after 10 seconds
            async def mark_offline():
                await asyncio.sleep(10)  # 10 second cooldown
                if self.chat_id in online_users and self.user_id in online_users[self.chat_id]:
                    online_users[self.chat_id].discard(self.user_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'user_status',
                            'user_id': self.user_id,
                            'status': 'offline'
                        }
                    )
            
            # Store the task
            offline_tasks[self.user_id] = asyncio.create_task(mark_offline())
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.debug(f"Successfully disconnected from chat room: {self.chat_id}")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def receive(self, text_data):
        try:
            logger.debug(f"Received message: {text_data}")
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                message = text_data_json.get('message', '')
                await self.save_message(message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user_id': self.user_id,
                        'username': self.scope['user'].username
                    }
                )
            elif message_type == 'typing':
                is_typing = text_data_json.get('is_typing', False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_status',
                        'user_id': self.user_id,
                        'username': self.scope['user'].username,
                        'is_typing': is_typing
                    }
                )
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def chat_message(self, event):
        try:
            logger.debug(f"Sending chat message: {event}")
            message = event['message']
            user_id = event['user_id']
            username = event['username']
            
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message': message,
                'user_id': user_id,
                'username': username
            }))
        except Exception as e:
            logger.error(f"Error in chat_message: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def user_status(self, event):
        try:
            logger.debug(f"Sending user status: {event}")
            user_id = event['user_id']
            status = event['status']
            
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': user_id,
                'status': status
            }))
        except Exception as e:
            logger.error(f"Error in user_status: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def typing_status(self, event):
        try:
            logger.debug(f"Sending typing status: {event}")
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
            logger.error(f"Error in typing_status: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @database_sync_to_async
    def save_message(self, message):
        try:
            logger.debug(f"Saving message to database: {message}")
            chat = Chat.objects.get(id=self.chat_id)
            Message.objects.create(
                chat=chat,
                sender=self.scope['user'],
                content=message
            )
            logger.debug("Message saved successfully")
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            logger.error(traceback.format_exc())
            raise 