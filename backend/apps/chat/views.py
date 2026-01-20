"""
Views для chat приложения
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from apps.accounts.models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_rooms_list(request):
    """Список чатов пользователя"""
    rooms = ChatRoom.objects.filter(participants=request.user).order_by('-updated_at')
    serializer = ChatRoomSerializer(rooms, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_room_detail(request, pk):
    """Детали комнаты чата"""
    try:
        room = ChatRoom.objects.filter(participants=request.user).get(pk=pk)
        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data)
    except ChatRoom.DoesNotExist:
        return Response(
            {'error': 'Комната чата не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def messages_list(request, pk):
    """Список сообщений в комнате"""
    try:
        room = ChatRoom.objects.filter(participants=request.user).get(pk=pk)
        messages = Message.objects.filter(room=room).order_by('created_at')
        
        # Помечаем сообщения как прочитанные
        Message.objects.filter(room=room, is_read=False).exclude(sender=request.user).update(is_read=True)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    except ChatRoom.DoesNotExist:
        return Response(
            {'error': 'Комната чата не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_chat_room(request, user_id):
    """Создание комнаты чата с пользователем (личный чат)"""
    try:
        other_user = User.objects.get(pk=user_id)
        
        if other_user == request.user:
            return Response(
                {'error': 'Нельзя создать чат с самим собой'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, существует ли уже комната (личный чат без привязки к заявке)
        existing_room = ChatRoom.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).filter(
            request__isnull=True  # Личный чат, не связанный с заявкой
        ).distinct().first()
        
        if existing_room:
            serializer = ChatRoomSerializer(existing_room, context={'request': request})
            return Response(serializer.data)
        
        # Создаём новую комнату
        room = ChatRoom.objects.create()
        room.participants.add(request.user, other_user)
        
        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_request_chat_room(request, request_id):
    """Создание группового чата для активности"""
    try:
        from apps.activities.models import Request, Participation
        
        req = Request.objects.get(pk=request_id)
        
        # Проверяем, участвует ли пользователь в этой активности
        participation = Participation.objects.filter(
            request=req,
            user=request.user,
            status='approved'
        ).first()
        
        if not participation and req.creator != request.user:
            return Response(
                {'error': 'Вы не участвуете в этой активности'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Проверяем, существует ли уже комната для этой заявки
        existing_room = ChatRoom.objects.filter(request=req).first()
        
        if existing_room:
            # Проверяем, есть ли пользователь в участниках
            if existing_room.participants.filter(id=request.user.id).exists():
                serializer = ChatRoomSerializer(existing_room, context={'request': request})
                return Response(serializer.data)
            else:
                # Добавляем пользователя в существующую комнату
                existing_room.participants.add(request.user)
                serializer = ChatRoomSerializer(existing_room, context={'request': request})
                return Response(serializer.data)
        
        # Создаём новую групповую комнату
        # Добавляем создателя и всех одобренных участников
        room = ChatRoom.objects.create(request=req)
        room.participants.add(req.creator)
        
        # Добавляем всех одобренных участников
        approved_participants = Participation.objects.filter(
            request=req,
            status='approved'
        ).values_list('user', flat=True)
        
        for participant_id in approved_participants:
            room.participants.add(participant_id)
        
        serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, pk):
    """Отправка сообщения в комнату чата (HTTP endpoint)"""
    try:
        room = ChatRoom.objects.filter(participants=request.user).get(pk=pk)
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response(
                {'error': 'Сообщение не может быть пустым'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаём сообщение
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=content
        )
        
        # Обновляем время последнего обновления комнаты
        room.save()
        
        # Создаём уведомления для всех участников комнаты, кроме отправителя
        from apps.notifications.models import Notification
        for participant in room.participants.exclude(id=request.user.id):
            # Обрезаем текст сообщения для уведомления (макс 100 символов)
            message_preview = content[:100] + ('...' if len(content) > 100 else '')
            Notification.objects.create(
                user=participant,
                notification_type='new_message',
                title=f'Новое сообщение от {request.user.username}',
                message=f'{message_preview}',
                related_user=request.user
            )
        
        # Отправляем сообщение через WebSocket (если подключены клиенты)
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'sender': {
                                'id': request.user.id,
                                'username': request.user.username
                            },
                            'content': message.content,
                            'created_at': message.created_at.isoformat()
                        }
                    }
                )
        except Exception as e:
            # Если WebSocket не работает, просто продолжаем
            print(f'WebSocket error (non-critical): {e}')
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except ChatRoom.DoesNotExist:
        return Response(
            {'error': 'Комната чата не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
