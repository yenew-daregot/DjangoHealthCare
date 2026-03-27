import json
import jwt
from django.conf import settings
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, ChatParticipant
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Authenticate user
        user = await self.get_user_from_token()
        if not user:
            await self.close()
            return
        
        self.user = user
        
        # Check if user has access to the chat room
        has_access = await self.check_chat_room_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update participant online status
        await self.update_participant_status(True)
        
        # Send join message
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': user.id,
                'username': user.username
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update participant offline status
        if hasattr(self, 'user'):
            await self.update_participant_status(False)
            
            # Send leave message
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'typing':
            await self.handle_typing(text_data_json)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(text_data_json)

    async def handle_chat_message(self, data):
        message_content = data['message']
        message_type = data.get('message_type', 'text')
        
        # Save message to database
        message = await self.save_message(message_content, message_type)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'message_type': message.message_type,
                    'timestamp': message.timestamp.isoformat(),
                    'is_read': message.is_read
                }
            }
        )

    async def handle_typing(self, data):
        is_typing = data['typing']
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        message_id = data['message_id']
        
        # Mark message as read
        await self.mark_message_as_read(message_id)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'user_id': self.user.id,
                'username': self.user.username
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'typing': event['typing']
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username']
        }))

    @database_sync_to_async
    def get_user_from_token(self):
        """Authenticate user from JWT token"""
        try:
            token = self.scope['query_string'].decode().split('token=')[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            return User.objects.get(id=user_id)
        except (KeyError, IndexError, jwt.InvalidTokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def check_chat_room_access(self):
        """Check if user has access to the chat room"""
        return ChatParticipant.objects.filter(
            chat_room_id=self.room_id,
            user=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, content, message_type):
        """Save message to database"""
        chat_room = ChatRoom.objects.get(id=self.room_id)
        
        message = Message.objects.create(
            chat_room=chat_room,
            sender=self.user,
            message_type=message_type,
            content=content
        )
        
        # Update chat room last activity
        chat_room.last_activity = message.timestamp
        chat_room.save()
        
        return message

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(id=message_id)
            if not message.is_read and message.sender != self.user:
                message.mark_as_read()
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def update_participant_status(self, is_online):
        """Update participant online status"""
        try:
            participant = ChatParticipant.objects.get(
                chat_room_id=self.room_id,
                user=self.user
            )
            participant.is_online = is_online
            participant.save()
        except ChatParticipant.DoesNotExist:
            pass