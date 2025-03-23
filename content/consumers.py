import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fanshub.settings')

import json
import logging
import traceback
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

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Get chat_id from URL route
            self.chat_id = self.scope['url_route']['kwargs']['chat_id']
            self.room_group_name = f'chat_{self.chat_id}'
            
            logger.info(f"Attempting to connect to chat {self.chat_id}")
            logger.debug(f"Connection scope: {self.scope}")
            
            # Verify chat exists and user has permission
            chat = await self.get_chat()
            if not chat:
                logger.error(f"Chat {self.chat_id} not found")
                await self.close()
                return
                
            user = self.scope.get('user')
            if not user or not user.is_authenticated:
                logger.error(f"Unauthenticated user tried to connect to chat {self.chat_id}")
                await self.close()
                return
                
            if user.id not in [chat.creator_id, chat.subscriber_id]:
                logger.error(f"User {user.id} not authorized for chat {self.chat_id}")
                await self.close()
                return

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"Added to group {self.room_group_name}")

            await self.accept()
            logger.info(f"Connection accepted for chat {self.chat_id}")
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            logger.error(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        try:
            logger.info(f"Disconnecting from chat {self.chat_id} with code {close_code}")
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"Disconnected from group {self.room_group_name}")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")
            logger.error(traceback.format_exc())

    async def receive(self, text_data):
        try:
            logger.info(f"Received message in chat {self.chat_id}")
            logger.debug(f"Raw message data: {text_data}")
            
            # Parse message data
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            user_id = text_data_json['user_id']
            
            # Verify user has permission
            chat = await self.get_chat()
            if not chat or user_id not in [chat.creator_id, chat.subscriber_id]:
                logger.error(f"User {user_id} not authorized to send messages in chat {self.chat_id}")
                return
            
            logger.info(f"Processing message from user {user_id} in chat {self.chat_id}")
            logger.debug(f"Message content: {message}")

            # Save message to database
            try:
                saved_message = await self.save_message(user_id, message)
                logger.info(f"Message {saved_message.id} saved to database for chat {self.chat_id}")
            except Exception as e:
                logger.error(f"Failed to save message to database: {str(e)}")
                logger.error(traceback.format_exc())
                return

            # Send message to room group
            try:
                username = await self.get_username(user_id)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'user_id': user_id,
                        'username': username,
                        'message_id': saved_message.id
                    }
                )
                logger.info(f"Message sent to group {self.room_group_name}")
            except Exception as e:
                logger.error(f"Failed to send message to group: {str(e)}")
                logger.error(traceback.format_exc())
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message JSON: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing required field in message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing message: {str(e)}")
            logger.error(traceback.format_exc())

    async def chat_message(self, event):
        try:
            logger.info(f"Broadcasting message {event.get('message_id')} in chat {self.chat_id}")
            logger.debug(f"Event data: {event}")
            
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': event['message'],
                'user_id': event['user_id'],
                'username': event['username'],
                'message_id': event.get('message_id')
            }))
            logger.info(f"Message broadcast complete in chat {self.chat_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast message: {str(e)}")
            logger.error(traceback.format_exc())

    @database_sync_to_async
    def get_chat(self):
        try:
            return Chat.objects.get(id=self.chat_id)
        except Chat.DoesNotExist:
            logger.error(f"Chat {self.chat_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting chat: {str(e)}")
            return None

    @database_sync_to_async
    def save_message(self, user_id, message):
        try:
            user = User.objects.get(id=user_id)
            chat = Chat.objects.get(id=self.chat_id)
            
            logger.debug(f"Found user {user.username} and chat {chat.id}")
            
            message_obj = Message.objects.create(
                chat=chat,
                sender=user,
                content=message
            )
            logger.info(f"Created message {message_obj.id} in chat {chat.id}")
            return message_obj
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            raise
        except Chat.DoesNotExist:
            logger.error(f"Chat {self.chat_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise

    @database_sync_to_async
    def get_username(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            logger.debug(f"Found username {user.username} for user {user_id}")
            return user.username
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error getting username: {str(e)}")
            raise 