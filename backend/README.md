# Backend - Спортивный партнёр-поисковик

## Описание проекта

Backend-часть веб-приложения для поиска партнёров по спорту и совместным активностям. Реализован на Django REST Framework с поддержкой WebSocket через Django Channels для чата в реальном времени.

## Технологический стек

- **Django 4.2+** - веб-фреймворк
- **Django REST Framework** - REST API
- **Django Channels** - WebSocket поддержка для чата
- **PostgreSQL/SQLite** - база данных (SQLite по умолчанию)
- **python-telegram-bot** - интеграция с Telegram
- **Yandex Maps API** - геолокация и карты

## Структура проекта

```
backend/
├── config/                 # Основная конфигурация Django
│   ├── settings.py        # Настройки проекта (строки 1-190)
│   ├── urls.py            # Главный URL роутинг (строки 9-21)
│   ├── asgi.py            # ASGI конфигурация для WebSocket (строки 1-26)
│   ├── wsgi.py            # WSGI конфигурация
│   ├── middleware.py      # Кастомные middleware
│   └── routing.py         # WebSocket роутинг
│
├── apps/                  # Django приложения
│   ├── accounts/          # Управление пользователями и профилями
│   │   ├── models.py      # User, Profile, Interest модели (строки 1-79)
│   │   ├── views.py       # API endpoints для аутентификации
│   │   ├── serializers.py # Сериализаторы для API
│   │   ├── urls.py        # URL маршруты для accounts
│   │   ├── signals.py     # Django signals (автосоздание профиля)
│   │   └── telegram_auth.py # Telegram авторизация
│   │
│   ├── activities/        # Заявки и активности
│   │   ├── models.py      # Request, Participation, Favorite, Review (строки 1-184)
│   │   ├── views.py       # API endpoints для заявок (строки 1-963)
│   │   ├── serializers.py # Сериализаторы
│   │   ├── urls.py        # URL маршруты
│   │   ├── search.py      # Поиск по заявкам
│   │   └── signals.py     # Сигналы (уведомления, обновление рейтинга)
│   │
│   ├── chat/              # Чат система
│   │   ├── models.py      # ChatRoom, Message модели
│   │   ├── views.py       # REST API для чата
│   │   ├── consumers.py   # WebSocket consumer (строки 1-146)
│   │   ├── routing.py     # WebSocket роутинг
│   │   └── urls.py        # URL маршруты
│   │
│   ├── notifications/     # Система уведомлений
│   │   ├── models.py      # Notification модель
│   │   ├── views.py       # API endpoints
│   │   ├── signals.py     # Автоматические уведомления
│   │   └── telegram_sender.py # Отправка в Telegram
│   │
│   └── moderation/        # Модерация контента
│       ├── models.py      # Complaint, Ban модели
│       ├── views.py       # API для модерации
│       └── urls.py        # URL маршруты
│
├── telegram_bot/          # Telegram бот
│   └── bot.py            # Основной файл бота
│
├── manage.py             # Django management скрипт
└── requirements.txt      # Зависимости Python
```

## Основные модели данных

### User (apps/accounts/models.py:6-17)
Расширенная модель пользователя Django:
- `telegram_id` - ID пользователя в Telegram
- `telegram_verified` - статус верификации Telegram
- `is_moderator` - права модератора
- `phone_verified` - верификация телефона

### Profile (apps/accounts/models.py:19-38)
Профиль пользователя:
- `photo` - фото профиля
- `city` - город
- `rating` - рейтинг (0-5)
- `bio` - описание о себе
- `available_schedule` - расписание доступности (JSON)

### Request (apps/activities/models.py:41-134)
Заявка на участие в активности:
- `request_type` - тип (sport/entertainment)
- `activity` - активность (ForeignKey)
- `format` - формат (partner/company/group)
- `date`, `time` - дата и время
- `location_name`, `latitude`, `longitude` - место
- `max_participants` - максимальное количество участников
- `status` - статус (active/pending/filled/completed/cancelled)
- `visibility` - видимость (public/link)

### Participation (apps/activities/models.py:136-154)
Участие пользователя в заявке:
- `request` - заявка
- `user` - пользователь
- `status` - статус (pending/approved/rejected)
- `message` - сообщение от пользователя

## API Endpoints

### Аутентификация (apps/accounts/urls.py)
- `POST /api/auth/register/` - регистрация
- `POST /api/auth/login/` - вход
- `POST /api/auth/logout/` - выход
- `POST /api/auth/telegram/` - авторизация через Telegram

### Профили (apps/accounts/urls.py)
- `GET /api/profile/` - текущий профиль
- `GET /api/profile/{id}/` - профиль пользователя
- `PATCH /api/profile/` - обновление профиля
- `GET /api/profile/interests/` - интересы пользователя
- `POST /api/profile/interests/` - добавление интереса

### Заявки (apps/activities/urls.py)
- `GET /api/requests/` - список заявок с фильтрами
- `POST /api/requests/create/` - создание заявки
- `GET /api/requests/{id}/` - детали заявки
- `PATCH /api/requests/{id}/edit/` - редактирование заявки
- `DELETE /api/requests/{id}/delete/` - удаление заявки
- `POST /api/requests/{id}/participate/` - отклик на заявку
- `GET /api/requests/{id}/participations/` - список участников
- `POST /api/requests/{id}/favorite/` - добавить в избранное
- `DELETE /api/requests/{id}/favorite/` - убрать из избранного
- `GET /api/requests/search/` - поиск заявок
- `GET /api/requests/categories/` - список категорий
- `GET /api/requests/activities/` - список активностей

### Чат (apps/chat/urls.py)
- `GET /api/chat/rooms/` - список чатов
- `GET /api/chat/rooms/{id}/` - детали чата
- `GET /api/chat/rooms/{id}/messages/` - сообщения
- `POST /api/chat/rooms/{id}/send/` - отправить сообщение
- `POST /api/chat/create/{user_id}/` - создать личный чат
- `POST /api/chat/create-request/{request_id}/` - создать групповой чат

### Уведомления (apps/notifications/urls.py)
- `GET /api/notifications/` - список уведомлений
- `PATCH /api/notifications/{id}/read/` - отметить как прочитанное

### Модерация (apps/moderation/urls.py)
- `GET /api/moderation/complaints/` - список жалоб
- `POST /api/moderation/complaints/{id}/resolve/` - разрешить жалобу
- `GET /api/moderation/users/` - список пользователей
- `POST /api/moderation/bans/create/` - заблокировать пользователя
- `GET /api/moderation/statistics/` - статистика

## WebSocket

### Подключение
WebSocket endpoint: `ws://localhost:8000/ws/chat/{room_id}/`

### Consumer (apps/chat/consumers.py:12-146)
`ChatConsumer` обрабатывает WebSocket соединения:
- `connect()` - подключение к комнате (строки 13-40)
- `disconnect()` - отключение (строки 42-47)
- `receive()` - получение сообщения (строки 49-96)
- `chat_message()` - отправка сообщения в группу (строки 98-105)

### Роутинг (config/routing.py)
WebSocket маршруты настраиваются в `config/routing.py` и подключаются через `config/asgi.py` (строки 19-25).

## Логика работы

### Автоматическое создание профиля
При создании пользователя автоматически создаётся профиль через Django signal (apps/accounts/signals.py).

### Обновление статуса заявок
При запросе списка заявок автоматически помечаются прошедшие заявки как `completed` (apps/activities/views.py:56-68).

### Система рейтингов
Рейтинг пользователя рассчитывается на основе отзывов через сигналы (apps/activities/signals.py).

### Уведомления
Автоматические уведомления создаются через сигналы при:
- Новом отклике на заявку
- Одобрении/отклонении участия
- Новом сообщении в чате
- Отмене заявки

### Поиск заявок
Реализован в `apps/activities/search.py` с поддержкой:
- Текстового поиска
- Фильтров по категории, активности, уровню
- Геопоиска по координатам
- Быстрых фильтров (сегодня, выходные, рядом)

## Настройка

### Переменные окружения (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
TELEGRAM_BOT_TOKEN=your-bot-token
YANDEX_MAPS_API_KEY=your-api-key
```

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Миграции
```bash
python manage.py migrate
```

### Создание суперпользователя
```bash
python manage.py createsuperuser
```

### Запуск сервера
```bash
python manage.py runserver
```

### Запуск Telegram бота
```bash
python telegram_bot/bot.py
```

## Middleware

### DisableCSRFForAPI (config/middleware.py)
Отключает CSRF проверку для API запросов, так как используется token-based аутентификация.

## Сигналы (Django Signals)

### accounts/signals.py
- Автоматическое создание профиля при создании пользователя

### activities/signals.py
- Обновление рейтинга при создании/обновлении отзыва
- Создание уведомлений при событиях с заявками

### notifications/signals.py
- Отправка уведомлений в Telegram

## Команды управления

### apps/accounts/management/commands/
- `create_missing_profiles.py` - создание профилей для существующих пользователей

### apps/activities/management/commands/
- `create_activities.py` - создание активностей из справочника
- `send_activity_reminders.py` - отправка напоминаний о предстоящих активностях

## Безопасность

- Token-based аутентификация через DRF
- Проверка прав доступа через permissions
- Валидация данных через сериализаторы
- CSRF отключен для API (используется token auth)
- Проверка участников чата перед WebSocket подключением

## Производительность

- Использование `select_related` и `prefetch_related` для оптимизации запросов
- Индексы на часто используемых полях
- Кэширование категорий и активностей (можно добавить)

## Расширение функционала

### Добавление новой модели
1. Создать модель в соответствующем приложении
2. Создать миграцию: `python manage.py makemigrations`
3. Применить миграцию: `python manage.py migrate`
4. Создать сериализатор
5. Создать view и добавить в urls.py

### Добавление нового API endpoint
1. Создать функцию view в `views.py`
2. Добавить декораторы `@api_view` и `@permission_classes`
3. Зарегистрировать в `urls.py`

### Добавление WebSocket функционала
1. Создать consumer в `consumers.py`
2. Добавить роутинг в `routing.py`
3. Обновить `config/routing.py` если нужно
