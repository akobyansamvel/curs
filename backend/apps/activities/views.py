"""
Views для activities приложения
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, Count, Avg, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from .models import Category, Activity, Request, Participation, Favorite, Review
from .serializers import (CategorySerializer, ActivitySerializer, RequestSerializer,
                         ParticipationSerializer, FavoriteSerializer, ReviewSerializer)
from .search import search_requests as search_requests_func
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os
from django.conf import settings
from decimal import Decimal


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """Список категорий"""
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def activity_list(request):
    """Список активностей"""
    activities = Activity.objects.filter(is_active=True)
    
    category_id = request.query_params.get('category_id')
    if category_id:
        activities = activities.filter(category_id=category_id)
    
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def request_list(request):
    """Список заявок с фильтрами"""
    # Получаем текущую дату и время
    now = timezone.now()
    today = now.date()
    current_time = now.time()
    
    # Сначала помечаем прошедшие активности как completed
    # Находим все активные заявки, которые уже прошли (но не "набрана")
    past_requests = Request.objects.filter(
        Q(status='active') & (Q(date__lt=today) | Q(date=today, time__lt=current_time))
    )
    
    # Помечаем их как завершённые
    past_requests.update(status='completed')
    
    # Также помечаем прошедшие заявки со статусом "набрана" как завершённые
    past_filled_requests = Request.objects.filter(
        Q(status='filled') & (Q(date__lt=today) | Q(date=today, time__lt=current_time))
    )
    past_filled_requests.update(status='completed')
    
    # Проверяем, является ли пользователь модератором
    is_mod = request.user.is_authenticated and (request.user.is_moderator or request.user.is_staff)
    
    # Фильтры (применяем ДО фильтрации по статусу, чтобы creator_id работал для всех заявок)
    category_id = request.query_params.get('category_id')
    activity_id = request.query_params.get('activity_id')
    request_type = request.query_params.get('request_type')
    level = request.query_params.get('level')
    format_type = request.query_params.get('format')
    creator_id = request.query_params.get('creator_id')
    
    # Начинаем с базового queryset
    requests = Request.objects.all()
    
    # Применяем фильтры
    if category_id:
        requests = requests.filter(activity__category_id=category_id)
    if activity_id:
        requests = requests.filter(activity_id=activity_id)
    if request_type:
        requests = requests.filter(request_type=request_type)
    if level:
        requests = requests.filter(level=level)
    if format_type:
        requests = requests.filter(format=format_type)
    if creator_id:
        # Если запрашиваются заявки конкретного пользователя, показываем все его заявки
        requests = requests.filter(creator_id=creator_id)
    else:
        # Если не указан creator_id, применяем стандартную фильтрацию
        if is_mod:
            # Модераторы видят все заявки
            status_filter = request.query_params.get('status')
            if status_filter:
                requests = requests.filter(status=status_filter)
        else:
            # Фильтруем только активные заявки, которые ещё не прошли
            # Заявки со статусом "filled" (набрана) не показываются на главной странице
            # (участники видят их в своем профиле)
            if request.user.is_authenticated:
                # Проверяем, является ли пользователь участником каких-либо заявок
                user_participation_ids = Participation.objects.filter(
                    user=request.user,
                    status='approved'
                ).values_list('request_id', flat=True)
                
                # Показываем только активные заявки, которые ещё не прошли
                # ИЛИ заявки, в которых пользователь участвует (даже если они "filled")
                requests = requests.filter(
                    (
                        Q(status='active') & 
                        Q(visibility='public') & 
                        (Q(date__gt=today) | Q(date=today, time__gte=current_time))
                    ) | 
                    Q(id__in=user_participation_ids)
                )
            else:
                # Для неавторизованных показываем только активные заявки
                requests = requests.filter(
                    Q(status='active') & 
                    Q(visibility='public') & 
                    (Q(date__gt=today) | Q(date=today, time__gte=current_time))
                )
    
    # Если пользователь авторизован, добавляем рекомендации на основе интересов
    if request.user.is_authenticated:
        from apps.accounts.models import Interest
        user_interests = list(Interest.objects.filter(user=request.user).values_list('activity_id', flat=True))
        if user_interests:
            # Приоритизируем заявки по интересам пользователя
            requests = requests.annotate(
                interest_priority=Case(
                    When(activity_id__in=user_interests, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ).order_by('-interest_priority', '-created_at')
        else:
            requests = requests.order_by('-created_at')
    else:
        requests = requests.order_by('-created_at')
    
    # Быстрые теги
    quick_tag = request.query_params.get('quick_tag')
    if quick_tag == 'today':
        today = timezone.now().date()
        requests = requests.filter(date=today)
    elif quick_tag == 'weekend':
        today = timezone.now().date()
        # Находим ближайшие выходные
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = today + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        requests = requests.filter(date__in=[saturday, sunday])
    elif quick_tag == 'nearby':
        # Фильтр по геолокации (можно добавить позже)
        pass
    
    # Синхронизируем current_participants и проверяем статус перед сериализацией
    requests_list = list(requests)
    for req in requests_list:
        active_count = Participation.objects.filter(
            request=req,
            status='approved'
        ).count()
        needs_save = False
        if req.current_participants != active_count:
            req.current_participants = active_count
            needs_save = True
        
        # ВСЕГДА проверяем статус на основе актуального количества участников
        if active_count >= req.max_participants and req.status == 'active':
            req.status = 'filled'
            needs_save = True
        elif active_count < req.max_participants and req.status == 'filled':
            req.status = 'active'
            needs_save = True
        
        if needs_save:
            req.save(update_fields=['current_participants', 'status'])
    
    serializer = RequestSerializer(requests_list, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def request_detail(request, pk):
    """Детали заявки"""
    try:
        req = Request.objects.get(pk=pk)
        
        # Синхронизируем current_participants
        active_count = Participation.objects.filter(
            request=req,
            status='approved'
        ).count()
        needs_save = False
        if req.current_participants != active_count:
            req.current_participants = active_count
            needs_save = True
        
        # ВСЕГДА проверяем статус на основе актуального количества участников
        if active_count >= req.max_participants and req.status == 'active':
            req.status = 'filled'
            needs_save = True
        elif active_count < req.max_participants and req.status == 'filled':
            req.status = 'active'
            needs_save = True
        
        if needs_save:
            req.save(update_fields=['current_participants', 'status'])
        
        serializer = RequestSerializer(req, context={'request': request})
        return Response(serializer.data)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_create(request):
    """Создание заявки"""
    data = request.data.copy()
    data['creator'] = request.user.id
    
    serializer = RequestSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        req = serializer.save(creator=request.user)
        
        # Создаём уведомления для пользователей с интересами в этой активности
        from apps.accounts.models import Interest
        from apps.notifications.models import Notification
        
        # Получаем пользователей с интересами в этой активности
        interested_users = Interest.objects.filter(
            activity=req.activity
        ).exclude(user=request.user).values_list('user', flat=True).distinct()
        
        # Отправляем уведомления (можно добавить фильтр по геолокации)
        for user_id in interested_users[:50]:  # Ограничение для производительности
            from apps.accounts.models import User
            try:
                user = User.objects.get(pk=user_id)
                Notification.objects.create(
                    user=user,
                    notification_type='new_request_nearby',
                    title='Новая заявка по вашим интересам',
                    message=f'Создана новая заявка "{req.title}" по активности "{req.activity.name}"',
                    related_request=req,
                    related_user=request.user
                )
            except User.DoesNotExist:
                pass
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def request_edit(request, pk):
    """Редактирование заявки"""
    try:
        req = Request.objects.get(pk=pk, creator=request.user)
        old_status = req.status
        old_date = req.date
        
        serializer = RequestSerializer(req, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            req = serializer.save()
            
            # Синхронизируем current_participants и проверяем статус
            active_count = Participation.objects.filter(
                request=req,
                status='approved'
            ).count()
            needs_save = False
            if req.current_participants != active_count:
                req.current_participants = active_count
                needs_save = True
            
            # Автоматически устанавливаем статус "набрана" если все слоты заполнены
            if active_count >= req.max_participants and req.status == 'active':
                req.status = 'filled'
                needs_save = True
            elif active_count < req.max_participants and req.status == 'filled':
                req.status = 'active'
                needs_save = True
            
            if needs_save:
                req.save(update_fields=['current_participants', 'status'])
            
            # Проверяем изменения статуса и даты для уведомлений
            from apps.notifications.models import Notification
            
            new_status = req.status
            new_date = req.date
            
            # Уведомление об отмене
            if new_status == 'cancelled' and old_status != 'cancelled':
                # Уведомляем всех участников
                participations = Participation.objects.filter(
                    request=req,
                    status='approved'
                )
                for participation in participations:
                    Notification.objects.create(
                        user=participation.user,
                        notification_type='request_cancelled',
                        title='Заявка отменена',
                        message=f'Заявка "{req.title}" была отменена',
                        related_request=req,
                        related_user=request.user
                    )
            
            # Уведомление о переносе (если изменилась дата)
            if new_date != old_date and new_status == 'active':
                participations = Participation.objects.filter(
                    request=req,
                    status='approved'
                )
                for participation in participations:
                    Notification.objects.create(
                        user=participation.user,
                        notification_type='request_rescheduled',
                        title='Заявка перенесена',
                        message=f'Заявка "{req.title}" перенесена на {new_date}',
                        related_request=req,
                        related_user=request.user
                    )
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена или нет прав на редактирование'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def request_delete(request, pk):
    """Удаление заявки (создателем или модератором)"""
    try:
        req = Request.objects.get(pk=pk)
        
        # Проверяем права: создатель или модератор
        is_creator = req.creator == request.user
        is_mod = is_moderator(request.user)
        
        if not is_creator and not is_mod:
            return Response(
                {'error': 'Недостаточно прав на удаление'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Получаем причину удаления (для модераторов)
        reason = request.data.get('reason', '') if is_mod else ''
        
        # Сохраняем информацию о создателе перед удалением
        creator = req.creator
        request_title = req.title
        
        # Удаляем заявку
        req.delete()
        
        # Если удалил модератор и указана причина - отправляем уведомление
        if is_mod and reason and creator:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=creator,
                notification_type='request_cancelled',
                title='Заявка удалена модератором',
                message=f'Ваша заявка "{request_title}" была удалена модератором. Причина: {reason}',
                related_user=request.user
            )
        
        return Response({'message': 'Заявка удалена'}, status=status.HTTP_200_OK)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def participate(request, pk):
    """Отклик на заявку"""
    try:
        req = Request.objects.get(pk=pk)
        
        # Проверяем, не откликался ли уже
        existing_participation = Participation.objects.filter(request=req, user=request.user).first()
        if existing_participation:
            if existing_participation.status == 'excluded':
                return Response(
                    {'error': 'Вы были исключены из этой заявки и не можете снова участвовать'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return Response(
                {'error': 'Вы уже откликнулись на эту заявку'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, не создатель ли это
        if req.creator == request.user:
            return Response(
                {'error': 'Нельзя откликнуться на свою заявку'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, не заполнена ли заявка
        current_participants = Participation.objects.filter(
            request=req,
            status='approved'
        ).count()
        
        if current_participants >= req.max_participants:
            return Response(
                {'error': 'Заявка уже заполнена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаём участие со статусом 'approved' (автоматическое одобрение)
        participation = Participation.objects.create(
            request=req,
            user=request.user,
            message=request.data.get('message', ''),
            status='approved'
        )
        
        # Обновляем количество участников
        req.current_participants = current_participants + 1
        
        # Если все слоты заполнены, меняем статус на "набрана"
        if req.current_participants >= req.max_participants and req.status == 'active':
            req.status = 'filled'
        
        req.save(update_fields=['current_participants', 'status'])
        
        # Создаём уведомление для создателя заявки
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=req.creator,
            notification_type='new_response',
            title='Кто-то вступил в вашу заявку',
            message=f'{request.user.username} вступил в заявку "{req.title}"',
            related_request=req,
            related_user=request.user
        )
        
        serializer = ParticipationSerializer(participation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorites_list(request):
    """Список избранных заявок пользователя"""
    favorites = Favorite.objects.filter(user=request.user)
    requests = [favorite.request for favorite in favorites]
    serializer = RequestSerializer(requests, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, pk):
    """Добавление/удаление из избранного"""
    try:
        req = Request.objects.get(pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, request=req)
        
        if request.method == 'GET':
            # Просто проверяем статус
            return Response({'is_favorite': True})
        
        if request.method == 'DELETE' or (request.method == 'POST' and not created):
            favorite.delete()
            return Response({'is_favorite': False})
        
        serializer = FavoriteSerializer(favorite)
        return Response({'is_favorite': True, **serializer.data}, status=status.HTTP_201_CREATED)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def participation_exclude(request, pk, participation_id):
    """Исключение участника (помечаем статусом 'excluded')"""
    try:
        req = Request.objects.get(pk=pk, creator=request.user)
        participation = Participation.objects.get(pk=participation_id, request=req)
        
        # Сохраняем данные для уведомления
        excluded_user = participation.user
        
        # Меняем статус на 'excluded' вместо удаления
        participation.status = 'excluded'
        participation.save()
        
        # Обновляем количество участников (исключенные не считаются)
        active_count = Participation.objects.filter(
            request=req, 
            status='approved'
        ).count()
        req.current_participants = active_count
        
        # Если слотов стало меньше, чем max_participants, и статус "набрана", возвращаем в "активна"
        if active_count < req.max_participants and req.status == 'filled':
            req.status = 'active'
        # Если все слоты заполнены, меняем статус на "набрана"
        elif active_count >= req.max_participants and req.status == 'active':
            req.status = 'filled'
        
        req.save(update_fields=['current_participants', 'status'])
        
        # Создаём уведомление для исключённого участника
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=excluded_user,
            notification_type='participation_rejected',
            title='Вас исключили из активности',
            message=f'Вас исключили из активности "{req.title}"',
            related_request=req,
            related_user=request.user
        )
        
        return Response({'message': 'Участник исключён'}, status=status.HTTP_200_OK)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена или нет прав'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Participation.DoesNotExist:
        return Response(
            {'error': 'Участие не найдено'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def request_participations(request, pk):
    """Список участников заявки (только для создателя заявки)"""
    try:
        req = Request.objects.get(pk=pk)
        # Только создатель заявки может видеть список участников
        if req.creator != request.user:
            return Response(
                {'error': 'Нет доступа к списку участников'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Не показываем исключенных и отклоненных участников
        participations = Participation.objects.filter(
            request=req,
            status='approved'
        ).order_by('-created_at')
        serializer = ParticipationSerializer(participations, many=True)
        return Response(serializer.data)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_requests(request):
    """Мои заявки"""
    requests = Request.objects.filter(creator=request.user)
    serializer = RequestSerializer(requests, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_participations(request):
    """Заявки, в которых я участвую"""
    participations = Participation.objects.filter(user=request.user, status='approved')
    request_ids = participations.values_list('request_id', flat=True)
    requests = Request.objects.filter(id__in=request_ids)
    serializer = RequestSerializer(requests, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_requests(request):
    """Поиск заявок"""
    query = request.query_params.get('q', '')
    results = search_requests_func(query, request.query_params)
    serializer = RequestSerializer(results, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def reviews_list(request, user_id=None):
    """Список отзывов пользователя"""
    if user_id:
        reviews = Review.objects.filter(reviewed_user_id=user_id)
    else:
        # Если user_id не указан, возвращаем пустой список
        reviews = Review.objects.none()
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_create(request, pk):
    """Создание отзыва (только после завершения активности)"""
    
    try:
        req = Request.objects.get(pk=pk)
        
        # Любой пользователь может оставить отзыв по любой заявке
        # Проверяем только, что нельзя ставить отзыв самому себе
        
        # Определяем, кому ставим отзыв
        reviewed_user_id = request.data.get('reviewed_user_id')
        if not reviewed_user_id:
            # Если не указан, ставим отзыв создателю (если это не создатель)
            if req.creator == request.user:
                return Response(
                    {'error': 'Необходимо указать пользователя, которому ставите отзыв'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            reviewed_user_id = req.creator.id
        else:
            reviewed_user_id = int(reviewed_user_id)
        
        # Нельзя ставить отзыв самому себе
        if reviewed_user_id == request.user.id:
            return Response(
                {'error': 'Нельзя ставить отзыв самому себе'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получаем пользователя, которому ставим отзыв
        from apps.accounts.models import User
        reviewed_user = User.objects.get(pk=reviewed_user_id)
        
        # Проверяем, что reviewed_user - это создатель заявки или участник
        # Но не требуем обязательного участия - любой может оставить отзыв
        
        # Проверяем, не оставлял ли уже отзыв этому пользователю по этой заявке
        existing_review = Review.objects.filter(
            request=req,
            reviewer=request.user,
            reviewed_user_id=reviewed_user_id
        ).first()
        
        if existing_review:
            return Response(
                {'error': 'Вы уже оставили отзыв этому пользователю по этой заявке'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаём отзыв
        review = Review.objects.create(
            request=req,
            reviewer=request.user,
            reviewed_user=reviewed_user,
            rating=request.data.get('rating'),
            comment=request.data.get('comment', '')
        )
        
        # Рейтинг будет автоматически пересчитан через сигнал post_save
        
        # Создаём уведомление
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=reviewed_user,
            notification_type='new_review',
            title='Новый отзыв',
            message=f'{request.user.username} оставил вам отзыв по заявке "{req.title}"',
            related_request=req,
            related_user=request.user
        )
        
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Request.DoesNotExist:
        return Response(
            {'error': 'Заявка не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь не найден'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_photo(request):
    """Загрузка фото для заявки"""
    if 'photo' not in request.FILES:
        return Response(
            {'error': 'Фото не предоставлено'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    photo = request.FILES['photo']
    
    # Проверяем размер файла (максимум 5MB)
    if photo.size > 5 * 1024 * 1024:
        return Response(
            {'error': 'Размер файла не должен превышать 5MB'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем тип файла
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if photo.content_type not in allowed_types:
        return Response(
            {'error': 'Неподдерживаемый тип файла. Используйте JPEG, PNG, GIF или WebP'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Сохраняем файл с уникальным именем
    try:
        file_ext = os.path.splitext(photo.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = default_storage.save(f'requests/photos/{unique_filename}', ContentFile(photo.read()))
        file_url = default_storage.url(file_path)
        
        # Относительный URL — делаем абсолютным, чтобы фото грузилось с любого фронта
        if file_url.startswith('/'):
            file_url = request.build_absolute_uri(file_url)
        
        return Response({'url': file_url}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': f'Ошибка загрузки файла: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def is_moderator(user):
    """Проверка, является ли пользователь модератором"""
    return user.is_authenticated and (user.is_moderator or user.is_staff)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def category_create(request):
    """Создание категории (только для модераторов)"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def category_edit(request, pk):
    """Редактирование категории (только для модераторов)"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        category = Category.objects.get(pk=pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Категория не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def category_delete(request, pk):
    """Удаление категории (только для модераторов)"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        category = Category.objects.get(pk=pk)
        category.delete()
        return Response({'message': 'Категория удалена'}, status=status.HTTP_204_NO_CONTENT)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Категория не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activity_create(request):
    """Создание активности (только для модераторов)"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = ActivitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def activity_edit(request, pk):
    """Редактирование активности (только для модераторов)"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        activity = Activity.objects.get(pk=pk)
        serializer = ActivitySerializer(activity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Activity.DoesNotExist:
        return Response(
            {'error': 'Активность не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def activity_delete(request, pk):
    """Удаление активности (только для модераторов)"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        activity = Activity.objects.get(pk=pk)
        activity.delete()
        return Response({'message': 'Активность удалена'}, status=status.HTTP_204_NO_CONTENT)
    except Activity.DoesNotExist:
        return Response(
            {'error': 'Активность не найдена'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistics(request):
    """Статистика для модераторов"""
    if not is_moderator(request.user):
        return Response(
            {'error': 'Недостаточно прав'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from apps.accounts.models import User
    
    # Статистика по заявкам
    total_requests = Request.objects.count()
    requests_by_type = Request.objects.values('request_type').annotate(count=Count('id'))
    requests_by_status = Request.objects.values('status').annotate(count=Count('id'))
    
    # Популярные активности
    popular_activities = Activity.objects.annotate(
        request_count=Count('requests')
    ).order_by('-request_count')[:10]
    
    # Статистика по отменам
    cancelled_requests = Request.objects.filter(status='cancelled').count()
    cancelled_percentage = (cancelled_requests / total_requests * 100) if total_requests > 0 else 0
    
    # Активные пользователи
    active_users = User.objects.annotate(
        requests_count=Count('created_requests'),
        participations_count=Count('participations', filter=Q(participations__status='approved'))
    ).filter(
        Q(requests_count__gt=0) | Q(participations_count__gt=0)
    ).order_by('-requests_count', '-participations_count')[:10]
    
    # Статистика по датам создания заявок
    from django.db.models.functions import TruncDate
    requests_by_date = list(Request.objects.annotate(
        date_created=TruncDate('created_at')
    ).values('date_created').annotate(count=Count('id')).order_by('-date_created')[:30])
    
    return Response({
        'total_requests': total_requests,
        'requests_by_type': list(requests_by_type),
        'requests_by_status': list(requests_by_status),
        'popular_activities': [
            {'id': a.id, 'name': a.name, 'count': a.request_count}
            for a in popular_activities
        ],
        'cancelled_requests': cancelled_requests,
        'cancelled_percentage': round(cancelled_percentage, 2),
        'active_users': [
            {
                'id': u.id,
                'username': u.username,
                'requests_count': u.requests_count,
                'participations_count': u.participations_count
            }
            for u in active_users
        ],
        'requests_by_date': list(requests_by_date)
    })
