"""
Логика авторизации через Telegram
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.auth import login
from .models import User


def generate_auth_code(telegram_id: int) -> str:
    """
    Генерирует одноразовый код для привязки Telegram аккаунта
    Код действителен 10 минут
    """
    code = secrets.token_urlsafe(16)
    cache_key = f'telegram_auth_{code}'
    cache.set(cache_key, telegram_id, timeout=600)  # 10 минут
    return code


def verify_auth_code(code: str) -> int:
    """
    Проверяет код и возвращает Telegram ID
    Возвращает None если код неверный или истёк
    """
    cache_key = f'telegram_auth_{code}'
    telegram_id = cache.get(cache_key)
    if telegram_id:
        cache.delete(cache_key)  # Удаляем код после использования
    return telegram_id


def get_or_create_telegram_user(telegram_id: int, username: str = None, 
                                first_name: str = None, last_name: str = None) -> User:
    """
    Получает или создаёт пользователя по Telegram ID
    """
    try:
        user = User.objects.get(telegram_id=telegram_id)
        # Обновляем информацию если нужно
        if username and user.username != username:
            user.username = username
            user.save()
    except User.DoesNotExist:
        # Создаём нового пользователя
        username = username or f'telegram_{telegram_id}'
        # Убеждаемся, что username уникален
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{counter}'
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            telegram_id=telegram_id,
            telegram_verified=True,
            first_name=first_name or '',
            last_name=last_name or '',
        )
    
    return user
