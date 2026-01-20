"""
Telegram бот для авторизации и подтверждения аккаунта
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
import django
import sys

# Настройка Django
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Загружаем переменные окружения перед настройкой Django
from dotenv import load_dotenv
env_path = os.path.join(backend_dir, '.env')
load_dotenv(dotenv_path=env_path)

django.setup()

from apps.accounts.models import User, Profile
from apps.accounts.telegram_auth import generate_auth_code
from decimal import Decimal
from asgiref.sync import sync_to_async

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для диалога регистрации
(REGISTER_USERNAME, REGISTER_PASSWORD, REGISTER_EMAIL, 
 REGISTER_FIRST_NAME, REGISTER_LAST_NAME) = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        
        if not user:
            logger.error("Не удалось получить информацию о пользователе из update")
            await update.message.reply_text('Произошла ошибка. Попробуй ещё раз.')
            return ConversationHandler.END
        
        # Проверяем, есть ли пользователь с таким Telegram ID (асинхронно)
        @sync_to_async
        def get_user_by_telegram_id(telegram_id):
            try:
                return User.objects.get(telegram_id=telegram_id)
            except User.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"Ошибка при поиске пользователя: {e}")
                return None
        
        @sync_to_async
        def save_user(user_obj):
            try:
                user_obj.save()
                return True
            except Exception as e:
                logger.error(f"Ошибка при сохранении пользователя: {e}")
                return False
        
        django_user = await get_user_by_telegram_id(user.id)
        
        if django_user:
            if django_user.telegram_verified:
                await update.message.reply_text(
                    f'Привет, {django_user.username}! Твой аккаунт уже подтверждён через Telegram. ✅'
                )
            else:
                # Подтверждаем аккаунт
                django_user.telegram_verified = True
                saved = await save_user(django_user)
                if saved:
                    await update.message.reply_text(
                        f'Отлично! Твой аккаунт {django_user.username} подтверждён через Telegram. ✅'
                    )
                else:
                    await update.message.reply_text(
                        'Произошла ошибка при подтверждении аккаунта. Попробуй ещё раз.'
                    )
            return ConversationHandler.END
        
        # Проверяем, есть ли параметр start=register
        start_param = context.args[0] if context.args and len(context.args) > 0 else None
        
        if start_param == 'register':
            # Начинаем регистрацию
            context.user_data['register_data'] = {
                'telegram_id': user.id,
                'telegram_username': user.username,
                'telegram_first_name': user.first_name,
                'telegram_last_name': user.last_name
            }
            await update.message.reply_text(
                '👋 Добро пожаловать! Давай зарегистрируем тебя на сайте.\n\n'
                '📝 Введи имя пользователя (username):\n'
                '(Это имя будет использоваться для входа на сайт)'
            )
            return REGISTER_USERNAME
        else:
            # Генерируем код для привязки аккаунта
            @sync_to_async
            def generate_code(telegram_id):
                try:
                    return generate_auth_code(telegram_id)
                except Exception as e:
                    logger.error(f"Ошибка генерации кода: {e}")
                    return None
            
            auth_code = await generate_code(user.id)
            
            if not auth_code:
                await update.message.reply_text(
                    'Произошла ошибка при генерации кода. Попробуй ещё раз.'
                )
                return ConversationHandler.END
            
            await update.message.reply_text(
                f'Привет! Для привязки Telegram к аккаунту используй этот код:\n\n'
                f'🔑 Код: `{auth_code}`\n\n'
                f'📝 Если у тебя уже есть аккаунт на сайте:\n'
                f'   → Перейди в свой профиль и введи этот код в разделе "Привязать Telegram"\n\n'
                f'🆕 Если у тебя ещё нет аккаунта:\n'
                f'   → Используй команду /register для регистрации через бота\n'
                f'   → Или используй этот код для регистрации на сайте\n\n'
                f'⏰ Код действителен 10 минут',
                parse_mode='Markdown'
            )
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}", exc_info=True)
        try:
            await update.message.reply_text(
                'Произошла ошибка. Попробуй ещё раз или обратись в поддержку.'
            )
        except:
            pass
        return ConversationHandler.END


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /verify - подтверждение аккаунта"""
    user = update.effective_user
    
    @sync_to_async
    def get_user_by_telegram_id(telegram_id):
        try:
            return User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return None
    
    @sync_to_async
    def save_user(user_obj):
        user_obj.save()
    
    django_user = await get_user_by_telegram_id(user.id)
    
    if django_user:
        if django_user.telegram_verified:
            await update.message.reply_text('Твой аккаунт уже подтверждён! ✅')
        else:
            django_user.telegram_verified = True
            await save_user(django_user)
            await update.message.reply_text('Аккаунт успешно подтверждён! ✅')
    else:
        await update.message.reply_text(
            'Сначала привяжи свой аккаунт через команду /start'
        )


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации через бота"""
    user = update.effective_user
    
    # Проверяем, не зарегистрирован ли уже пользователь (асинхронно)
    @sync_to_async
    def get_user_by_telegram_id(telegram_id):
        try:
            return User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return None
    
    django_user = await get_user_by_telegram_id(user.id)
    
    if django_user:
        await update.message.reply_text(
            f'У тебя уже есть аккаунт: {django_user.username}\n'
            f'Используй команду /start для получения кода привязки.'
        )
        return ConversationHandler.END
    
    # Начинаем процесс регистрации
    context.user_data['register_data'] = {
        'telegram_id': user.id,
        'telegram_username': user.username,
        'telegram_first_name': user.first_name,
        'telegram_last_name': user.last_name
    }
    
    await update.message.reply_text(
        '👋 Добро пожаловать! Давай зарегистрируем тебя на сайте.\n\n'
        '📝 Введи имя пользователя (username):\n'
        '(Это имя будет использоваться для входа на сайт)'
    )
    return REGISTER_USERNAME


async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода username"""
    username = update.message.text.strip()
    
    # Проверяем валидность username
    if len(username) < 3:
        await update.message.reply_text(
            '❌ Имя пользователя должно быть не менее 3 символов. Попробуй ещё раз:'
        )
        return REGISTER_USERNAME
    
    # Проверяем, не занят ли username (асинхронно)
    @sync_to_async
    def check_username_exists(username):
        return User.objects.filter(username=username).exists()
    
    username_exists = await check_username_exists(username)
    if username_exists:
        await update.message.reply_text(
            f'❌ Имя пользователя "{username}" уже занято. Выбери другое:'
        )
        return REGISTER_USERNAME
    
    context.user_data['register_data']['username'] = username
    
    await update.message.reply_text(
        '✅ Отлично! Теперь придумай пароль:\n'
        '(Пароль должен быть не менее 8 символов)'
    )
    return REGISTER_PASSWORD


async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода password"""
    password = update.message.text.strip()
    
    if len(password) < 8:
        await update.message.reply_text(
            '❌ Пароль должен быть не менее 8 символов. Попробуй ещё раз:'
        )
        return REGISTER_PASSWORD
    
    context.user_data['register_data']['password'] = password
    
    await update.message.reply_text(
        '✅ Пароль принят! Теперь введи email (необязательно):\n'
        '(Можешь отправить "пропустить" или "-" чтобы пропустить)'
    )
    return REGISTER_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода email"""
    email = update.message.text.strip().lower()
    
    # Пропуск email
    if email in ['пропустить', 'пропустить', '-', 'skip', '']:
        context.user_data['register_data']['email'] = ''
    else:
        # Простая проверка email
        if '@' not in email or '.' not in email.split('@')[1]:
            await update.message.reply_text(
                '❌ Неверный формат email. Попробуй ещё раз или отправь "пропустить":'
            )
            return REGISTER_EMAIL
        context.user_data['register_data']['email'] = email
    
    # Используем имя из Telegram, если есть
    first_name = context.user_data['register_data'].get('telegram_first_name', '')
    if first_name:
        await update.message.reply_text(
            f'✅ Email сохранён! Твоё имя из Telegram: {first_name}\n'
            f'Если хочешь изменить, введи новое имя, иначе отправь "пропустить":'
        )
    else:
        await update.message.reply_text(
            '✅ Email сохранён! Введи своё имя (необязательно):\n'
            '(Можешь отправить "пропустить" чтобы пропустить)'
        )
    return REGISTER_FIRST_NAME


async def register_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода first_name"""
    first_name = update.message.text.strip()
    
    if first_name.lower() in ['пропустить', 'пропустить', '-', 'skip', '']:
        first_name = context.user_data['register_data'].get('telegram_first_name', '')
    
    context.user_data['register_data']['first_name'] = first_name
    
    # Используем фамилию из Telegram, если есть
    last_name = context.user_data['register_data'].get('telegram_last_name', '')
    if last_name:
        await update.message.reply_text(
            f'✅ Имя сохранено! Твоя фамилия из Telegram: {last_name}\n'
            f'Если хочешь изменить, введи новую фамилию, иначе отправь "пропустить":'
        )
    else:
        await update.message.reply_text(
            '✅ Имя сохранено! Введи свою фамилию (необязательно):\n'
            '(Можешь отправить "пропустить" чтобы пропустить)'
        )
    return REGISTER_LAST_NAME


async def register_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода last_name и завершение регистрации"""
    last_name = update.message.text.strip()
    
    if last_name.lower() in ['пропустить', 'пропустить', '-', 'skip', '']:
        last_name = context.user_data['register_data'].get('telegram_last_name', '')
    
    context.user_data['register_data']['last_name'] = last_name
    
    # Создаём пользователя (асинхронно)
    data = context.user_data['register_data']
    
    @sync_to_async
    def create_user_and_profile(user_data):
        try:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data.get('email', '') or '',
                password=user_data['password'],
                first_name=user_data.get('first_name', '') or '',
                last_name=user_data.get('last_name', '') or '',
                telegram_id=user_data['telegram_id'],
                telegram_verified=True
            )
            
            # Создаём профиль
            try:
                profile = user.profile
            except AttributeError:
                profile = Profile.objects.create(user=user, rating=Decimal('0.00'))
            
            return user, None
        except Exception as e:
            return None, e
    
    try:
        user, error = await create_user_and_profile(data)
        
        if error:
            raise error
        
        await update.message.reply_text(
            f'🎉 Регистрация завершена!\n\n'
            f'✅ Аккаунт создан: {user.username}\n'
            f'✅ Telegram привязан и подтверждён\n\n'
            f'Теперь ты можешь войти на сайт используя:\n'
            f'👤 Username: {user.username}\n'
            f'🔑 Пароль: (тот, что ты указал)\n\n'
            f'Перейди на сайт и войди в свой аккаунт!'
        )
        
        # Очищаем данные
        context.user_data.pop('register_data', None)
        
    except Exception as e:
        logger.error(f"Ошибка создания пользователя: {e}")
        await update.message.reply_text(
            '❌ Произошла ошибка при создании аккаунта. Попробуй ещё раз позже или обратись в поддержку.'
        )
    
    return ConversationHandler.END


async def register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    context.user_data.pop('register_data', None)
    await update.message.reply_text('❌ Регистрация отменена.')
    return ConversationHandler.END


def main():
    """Запуск бота"""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в настройках!")
        return
    
    try:
        application = Application.builder().token(token).build()
        
        # Обработчик регистрации через /register
        register_handler = ConversationHandler(
            entry_points=[CommandHandler("register", register_start)],
            states={
                REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
                REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
                REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
                REGISTER_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_first_name)],
                REGISTER_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_last_name)],
            },
            fallbacks=[CommandHandler("cancel", register_cancel)],
        )
        
        # Обработчик start может также начинать регистрацию (когда start=register)
        start_register_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
                REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
                REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
                REGISTER_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_first_name)],
                REGISTER_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_last_name)],
            },
            fallbacks=[CommandHandler("cancel", register_cancel)],
        )
        
        # Добавляем обработчики в правильном порядке (более специфичные первыми)
        # start_register_handler должен быть первым, так как он обрабатывает /start с параметрами
        application.add_handler(start_register_handler)
        application.add_handler(CommandHandler("verify", verify))
        application.add_handler(register_handler)
        
        logger.info("Telegram бот запущен...")
        logger.info(f"Токен бота: {'*' * (len(token) - 10) + token[-10:] if len(token) > 10 else '***'}")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)


if __name__ == '__main__':
    main()
