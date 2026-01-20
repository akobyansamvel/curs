"""
WebSocket consumer для чата
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatRoom, Message
from apps.accounts.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Проверяем авторизацию
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Проверяем доступ к комнате
        room = await self.get_room()
        if not room:
            await self.close()
            return
        
        # Проверяем, является ли пользователь участником комнаты
        is_participant = await self.is_participant(room)
        if not is_participant:
            await self.close()
            return
        
        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'message':
            content = data.get('content', '')
            if content:
                # Сохраняем сообщение в БД
                message = await self.save_message(content)
                
                # Отправляем сообщение в группу
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message['id'],
                            'sender': message['sender'],
                            'content': message['content'],
                            'created_at': message['created_at'],
                        }
                    }
                )
        elif message_type == 'typing':
            # Отправляем сигнал "печатает..."
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user': self.scope['user'].username,
                }
            )
    
    async def chat_message(self, event):
        """Отправка сообщения клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Отправка индикатора печатания"""
        if event['user'] != self.scope['user'].username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user']
            }))
    
    @database_sync_to_async
    def get_room(self):
        """Получение комнаты чата"""
        try:
            return ChatRoom.objects.get(id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def is_participant(self, room):
        """Проверка, является ли пользователь участником комнаты"""
        return room.participants.filter(id=self.scope['user'].id).exists()
    
    @database_sync_to_async
    def save_message(self, content):
        """Сохранение сообщения в БД"""
        from apps.notifications.models import Notification
        
        room = ChatRoom.objects.get(id=self.room_id)
        sender = self.scope['user']
        
        message = Message.objects.create(
            room=room,
            sender=sender,
            content=content
        )
        
        # Создаём уведомления для всех участников комнаты, кроме отправителя
        for participant in room.participants.exclude(id=sender.id):
            # Обрезаем текст сообщения для уведомления (макс 100 символов)
            message_preview = content[:100] + ('...' if len(content) > 100 else '')
            Notification.objects.create(
                user=participant,
                notification_type='new_message',
                title=f'Новое сообщение от {sender.username}',
                message=f'{message_preview}',
                related_user=sender
            )
        
        return {
            'id': message.id,
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
            },
            'content': message.content,
            'created_at': message.created_at.isoformat(),
        }
