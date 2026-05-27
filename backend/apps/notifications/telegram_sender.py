"""
Утилита для отправки уведомлений через Telegram бота
"""
import logging
import threading
import asyncio
from django.conf import settings
from apps.accounts.models import User

logger = logging.getLogger(__name__)


def send_telegram_notification(user: User, title: str, message: str, notification_type: str = None):
    """
    Отправляет уведомление пользователю через Telegram бота
    
    Args:
        user: Пользователь Django
        title: Заголовок уведомления
        message: Текст уведомления
        notification_type: Тип уведомления (опционально)
    """
    # Проверяем, что у пользователя есть Telegram ID и он подтверждён
    if not user.telegram_id or not user.telegram_verified:
        return False
    
    # Проверяем, что токен бота настроен
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен, уведомление не отправлено")
        return False
    
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        
        # Добавляем эмодзи в зависимости от типа уведомления
        emoji_map = {
            'request_created': '📝',
            'new_response': '👤',
            'participation_approved': '✅',
            'participation_rejected': '❌',
            'new_request_nearby': '📍',
            'activity_reminder': '⏰',
            'request_cancelled': '🚫',
            'request_rescheduled': '📅',
            'new_message': '💬',
            'new_review': '⭐',
        }
        
        emoji = emoji_map.get(notification_type, '🔔')
        text = f"{emoji} *{title}*\n\n{message}"
        
        # Создаём экземпляр бота
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Отправляем сообщение в отдельном потоке, чтобы не блокировать Django
        def send_in_thread():
            try:
                # Создаём новый event loop для потока
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                async def send():
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=text,
                            parse_mode='Markdown'
                        )
                        logger.info(f"Telegram уведомление отправлено пользователю {user.id}")
                        return True
                    except TelegramError as e:
                        logger.error(f"Ошибка Telegram API для пользователя {user.id}: {e}")
                        return False
                    except Exception as e:
                        logger.error(f"Ошибка отправки Telegram уведомления пользователю {user.id}: {e}")
                        return False
                
                result = new_loop.run_until_complete(send())
                new_loop.close()
                return result
            except Exception as e:
                logger.error(f"Ошибка в потоке отправки Telegram уведомления: {e}")
                return False
        
        # Запускаем в отдельном потоке (daemon=True, чтобы не блокировать завершение Django)
        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()
        # Не ждём завершения потока, чтобы не блокировать Django
        return True
        
    except ImportError:
        logger.error("python-telegram-bot не установлен")
        return False
    except Exception as e:
        logger.error(f"Ошибка отправки Telegram уведомления: {e}")
        return False


def send_telegram_notification_sync(user: User, title: str, message: str, notification_type: str = None):
    """
    Синхронная версия отправки уведомления (для использования в Django views)
    """
    return send_telegram_notification(user, title, message, notification_type)
