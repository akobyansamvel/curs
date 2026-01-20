# Frontend - Спортивный партнёр-поисковик

## Описание проекта

Frontend-часть веб-приложения для поиска партнёров по спорту и совместным активностям. Реализован на React с использованием Vite для сборки и React Router для навигации.

## Технологический стек

- **React 18.2+** - UI библиотека
- **React Router DOM 6.20+** - маршрутизация
- **Vite 5.0+** - сборщик и dev-сервер
- **Axios 1.6+** - HTTP клиент
- **Yandex Maps API** - карты и геолокация

## Структура проекта

```
frontend/
├── src/
│   ├── main.jsx              # Точка входа приложения (строки 1-11)
│   ├── App.jsx               # Корневой компонент (строки 1-17)
│   │
│   ├── router.jsx            # Маршрутизация приложения (строки 1-69)
│   │
│   ├── contexts/              # React Contexts
│   │   └── AuthContext.jsx    # Контекст аутентификации (строки 1-104)
│   │
│   ├── services/              # Сервисы для работы с API
│   │   ├── api.js            # Axios конфигурация (строки 1-33)
│   │   ├── websocket.js      # WebSocket клиент для чата
│   │   └── yandexMaps.js     # Интеграция с Yandex Maps
│   │
│   ├── pages/                 # Страницы приложения
│   │   ├── HomePage.jsx       # Главная страница
│   │   ├── LoginPage.jsx     # Страница входа/регистрации
│   │   ├── ProfilePage.jsx   # Страница профиля
│   │   ├── CreateRequestPage.jsx # Создание заявки
│   │   ├── RequestDetailPage.jsx # Детали заявки
│   │   ├── MyRequestsPage.jsx # Мои заявки
│   │   ├── SearchPage.jsx     # Поиск заявок
│   │   ├── FavoritesPage.jsx # Избранное
│   │   ├── ChatListPage.jsx  # Список чатов
│   │   ├── ChatPage.jsx       # Страница чата
│   │   ├── NotificationsPage.jsx # Уведомления
│   │   ├── ModerationPage.jsx # Модерация (для модераторов)
│   │   └── HelpPage.jsx       # Справка
│   │
│   ├── components/            # Переиспользуемые компоненты
│   │   ├── common/           # Общие компоненты
│   │   │   ├── Layout.jsx    # Основной layout с навигацией (строки 1-273)
│   │   │   ├── Breadcrumbs.jsx # Хлебные крошки
│   │   │   └── SearchBar.jsx  # Поисковая строка
│   │   │
│   │   ├── requests/         # Компоненты заявок
│   │   │   ├── RequestCard.jsx # Карточка заявки
│   │   │   ├── EditRequestForm.jsx # Форма редактирования
│   │   │   ├── DeleteRequestModal.jsx # Модалка удаления
│   │   │   └── ParticipantsList.jsx # Список участников
│   │   │
│   │   ├── profile/          # Компоненты профиля
│   │   │   ├── ProfileEdit.jsx # Редактирование профиля
│   │   │   ├── UserRequestsSection.jsx # Секция заявок пользователя
│   │   │   ├── TelegramConnect.jsx # Подключение Telegram
│   │   │   └── InterestsSelector.jsx # Выбор интересов
│   │   │
│   │   ├── reviews/          # Компоненты отзывов
│   │   │   ├── CreateReview.jsx # Создание отзыва
│   │   │   ├── CreateReviewFromProfile.jsx # Отзыв из профиля
│   │   │   └── ReviewsList.jsx # Список отзывов
│   │   │
│   │   ├── chat/             # Компоненты чата
│   │   │   ├── MessageList.jsx # Список сообщений
│   │   │   └── MessageInput.jsx # Ввод сообщения
│   │   │
│   │   ├── complaints/       # Компоненты жалоб
│   │   │   ├── CreateComplaint.jsx # Создание жалобы
│   │   │   └── ComplaintList.jsx # Список жалоб
│   │   │
│   │   ├── moderation/       # Компоненты модерации
│   │   │   ├── UserModeration.jsx # Модерация пользователей
│   │   │   ├── RequestsModeration.jsx # Модерация заявок
│   │   │   ├── BanUserModal.jsx # Блокировка пользователя
│   │   │   ├── CategoriesManagement.jsx # Управление категориями
│   │   │   └── StatisticsView.jsx # Статистика
│   │   │
│   │   ├── map/              # Компоненты карты
│   │   │   ├── MapPicker.jsx # Выбор места на карте
│   │   │   ├── NearbyRequests.jsx # Ближайшие заявки
│   │   │   └── NearbyEvents.jsx # Ближайшие события
│   │   │
│   │   ├── filters/          # Компоненты фильтров
│   │   │   ├── FilterPanel.jsx # Панель фильтров
│   │   │   └── CategorySelector.jsx # Выбор категории
│   │   │
│   │   └── activities/       # Компоненты активностей
│   │       └── PopularActivities.jsx # Популярные активности
│   │
│   └── styles/               # Глобальные стили
│       ├── index.css         # Базовые стили (строки 1-38)
│       └── App.css           # Стили приложения
│
├── index.html                # HTML шаблон
├── vite.config.js            # Конфигурация Vite
└── package.json              # Зависимости и скрипты
```

## Архитектура приложения

### Точка входа (src/main.jsx)
Приложение инициализируется через `ReactDOM.createRoot` и рендерит компонент `App` (строки 6-10).

### Корневой компонент (src/App.jsx)
Обёртывает приложение в `AuthProvider` и `BrowserRouter` для управления состоянием аутентификации и маршрутизацией (строки 8-11).

### Маршрутизация (src/router.jsx)

#### Публичные маршруты:
- `/` - Главная страница ([HomePage.jsx](src/pages/HomePage.jsx))
- `/login` - Вход/регистрация ([LoginPage.jsx](src/pages/LoginPage.jsx))
- `/search` - Поиск заявок ([SearchPage.jsx](src/pages/SearchPage.jsx))
- `/help` - Справка ([HelpPage.jsx](src/pages/HelpPage.jsx))
- `/requests/:id` - Детали заявки ([RequestDetailPage.jsx](src/pages/RequestDetailPage.jsx))
- `/profile/:userId` - Публичный профиль ([ProfilePage.jsx](src/pages/ProfilePage.jsx))

#### Приватные маршруты (требуют авторизации):
- `/profile` - Мой профиль ([ProfilePage.jsx](src/pages/ProfilePage.jsx))
- `/requests/create` - Создание заявки ([CreateRequestPage.jsx](src/pages/CreateRequestPage.jsx))
- `/requests/my` - Мои заявки ([MyRequestsPage.jsx](src/pages/MyRequestsPage.jsx))
- `/favorites` - Избранное ([FavoritesPage.jsx](src/pages/FavoritesPage.jsx))
- `/chat` - Список чатов ([ChatListPage.jsx](src/pages/ChatListPage.jsx))
- `/chat/:id` - Чат ([ChatPage.jsx](src/pages/ChatPage.jsx))
- `/notifications` - Уведомления ([NotificationsPage.jsx](src/pages/NotificationsPage.jsx))
- `/moderation` - Модерация ([ModerationPage.jsx](src/pages/ModerationPage.jsx))

#### Компонент PrivateRoute (router.jsx:18-26)
Защищает маршруты, проверяя авторизацию через `useAuth()` и перенаправляя на `/login` при отсутствии пользователя.

## Контекст аутентификации (src/contexts/AuthContext.jsx)

### Функции:
- `checkAuth()` - проверка текущей авторизации (строки 20-29)
- `login(credentials)` - вход пользователя (строки 31-42)
- `register(userData)` - регистрация (строки 70-81)
- `telegramLogin(code, telegramData)` - вход через Telegram (строки 44-58)
- `logout()` - выход (строки 60-68)

### Состояние:
- `user` - текущий пользователь
- `loading` - состояние загрузки

### Использование:
```jsx
import { useAuth } from './contexts/AuthContext'

function Component() {
  const { user, login, logout } = useAuth()
  // ...
}
```

## Сервисы

### API клиент (src/services/api.js)
Настроенный экземпляр Axios:
- Базовый URL: `/api` (строка 4)
- `withCredentials: true` для отправки cookies (строка 5)
- Автоматическая обработка FormData (строки 11-21)
- Перехватчик 401 ошибок с редиректом на `/login` (строки 23-31)

### WebSocket клиент (src/services/websocket.js)
Клиент для подключения к WebSocket серверу чата.

### Yandex Maps (src/services/yandexMaps.js)
Утилиты для работы с Yandex Maps API.

## Основные компоненты

### Layout (src/components/common/Layout.jsx)
Основной layout приложения с:
- Навигационным меню (строки 59-253)
- Логотипом и ссылками
- Меню пользователя с выпадающим списком (строки 125-245)
- Футером (строки 261-268)

### RequestCard (src/components/requests/RequestCard.jsx)
Карточка заявки, отображающая:
- Название и описание
- Активность и формат
- Дату, время и место
- Количество участников
- Статус заявки

### MapPicker (src/components/map/MapPicker.jsx)
Компонент выбора места на карте с интеграцией Yandex Maps.

### FilterPanel (src/components/filters/FilterPanel.jsx)
Панель фильтров для поиска заявок:
- По категории
- По активности
- По уровню
- По формату

## Логика работы страниц

### HomePage (src/pages/HomePage.jsx)
Главная страница содержит:
- Поисковую строку ([SearchBar](src/components/common/SearchBar.jsx))
- Выбор категорий ([CategorySelector](src/components/filters/CategorySelector.jsx))
- Популярные активности ([PopularActivities](src/components/activities/PopularActivities.jsx))
- Ближайшие заявки ([NearbyRequests](src/components/map/NearbyRequests.jsx))
- Ближайшие события ([NearbyEvents](src/components/map/NearbyEvents.jsx))

### RequestDetailPage (src/pages/RequestDetailPage.jsx)
Страница деталей заявки:
- Отображение полной информации о заявке
- Управление участниками ([ParticipantsList](src/components/requests/ParticipantsList.jsx))
- Редактирование заявки ([EditRequestForm](src/components/requests/EditRequestForm.jsx))
- Создание отзыва ([CreateReview](src/components/reviews/CreateReview.jsx))
- Создание жалобы ([CreateComplaint](src/components/complaints/CreateComplaint.jsx))
- Групповой чат (если участников >= 3)

### ProfilePage (src/pages/ProfilePage.jsx)
Страница профиля:
- Редактирование профиля ([ProfileEdit](src/components/profile/ProfileEdit.jsx))
- Выбор интересов ([InterestsSelector](src/components/profile/InterestsSelector.jsx))
- Заявки пользователя ([UserRequestsSection](src/components/profile/UserRequestsSection.jsx))
- Отзывы ([ReviewsList](src/components/reviews/ReviewsList.jsx))
- Подключение Telegram ([TelegramConnect](src/components/profile/TelegramConnect.jsx))

### ChatPage (src/pages/ChatPage.jsx)
Страница чата:
- Список сообщений ([MessageList](src/components/chat/MessageList.jsx))
- Ввод сообщения ([MessageInput](src/components/chat/MessageInput.jsx))
- WebSocket подключение для real-time обновлений
- Автопрокрутка к новым сообщениям

### ModerationPage (src/pages/ModerationPage.jsx)
Страница модерации (только для модераторов):
- Вкладки: Жалобы, Пользователи, Категории, Статистика
- Список жалоб ([ComplaintList](src/components/complaints/ComplaintList.jsx))
- Модерация пользователей ([UserModeration](src/components/moderation/UserModeration.jsx))
- Управление категориями ([CategoriesManagement](src/components/moderation/CategoriesManagement.jsx))
- Статистика ([StatisticsView](src/components/moderation/StatisticsView.jsx))

## Стилизация

### Глобальные стили (src/styles/index.css)
- Сброс стилей (строки 1-5)
- Настройки шрифтов (строки 7-15)
- Базовые стили для ссылок и кнопок (строки 23-33)

### Компонентные стили
Каждый компонент имеет свой CSS файл в той же папке:
- `ComponentName.jsx` → `ComponentName.css`

## Установка и запуск

### Установка зависимостей
```bash
npm install
```

### Переменные окружения
Создайте файл `.env`:
```env
VITE_YANDEX_MAPS_API_KEY=your-api-key
```

### Запуск dev-сервера
```bash
npm run dev
```

### Сборка для production
```bash
npm run build
```

### Просмотр production сборки
```bash
npm run preview
```

## Особенности реализации

### Обработка ошибок
- Автоматический редирект на `/login` при 401 ошибке (api.js:26-28)
- Обработка ошибок в компонентах через try/catch

### Оптимизация
- Использование React hooks для управления состоянием
- Условный рендеринг для оптимизации производительности
- Lazy loading можно добавить для больших компонентов

### Доступность
- Семантические HTML элементы
- ARIA атрибуты где необходимо
- Клавиатурная навигация

## Интеграция с Backend

### API Endpoints
Все запросы идут через `/api`:
- Аутентификация: `/api/auth/*`
- Профили: `/api/profile/*`
- Заявки: `/api/requests/*`
- Чат: `/api/chat/*`
- Уведомления: `/api/notifications/*`
- Модерация: `/api/moderation/*`

### WebSocket
Подключение к WebSocket для чата:
- URL: `ws://localhost:8000/ws/chat/{room_id}/`
- Обработка через `services/websocket.js`

## Расширение функционала

### Добавление новой страницы
1. Создать компонент в `src/pages/`
2. Добавить маршрут в `src/router.jsx`
3. Добавить ссылку в навигацию `Layout.jsx` если нужно

### Добавление нового компонента
1. Создать компонент в соответствующей папке `src/components/`
2. Создать CSS файл для стилей
3. Импортировать и использовать в нужных местах

### Добавление нового API endpoint
1. Добавить метод в `services/api.js` или использовать напрямую
2. Вызвать в компоненте через `api.get/post/patch/delete()`

## Структура компонентов по категориям

### Common (общие)
Компоненты, используемые повсеместно:
- `Layout` - основной layout
- `Breadcrumbs` - навигационные крошки
- `SearchBar` - поисковая строка

### Requests (заявки)
Компоненты для работы с заявками:
- `RequestCard` - отображение заявки
- `EditRequestForm` - редактирование
- `ParticipantsList` - управление участниками
- `DeleteRequestModal` - подтверждение удаления

### Profile (профиль)
Компоненты профиля пользователя:
- `ProfileEdit` - редактирование
- `UserRequestsSection` - заявки пользователя
- `InterestsSelector` - выбор интересов
- `TelegramConnect` - подключение Telegram

### Chat (чат)
Компоненты чата:
- `MessageList` - список сообщений
- `MessageInput` - ввод сообщения

### Moderation (модерация)
Компоненты для модераторов:
- `UserModeration` - управление пользователями
- `RequestsModeration` - модерация заявок
- `BanUserModal` - блокировка пользователя
- `CategoriesManagement` - управление категориями
- `StatisticsView` - статистика

### Map (карта)
Компоненты для работы с картами:
- `MapPicker` - выбор места
- `NearbyRequests` - ближайшие заявки
- `NearbyEvents` - ближайшие события

### Filters (фильтры)
Компоненты фильтрации:
- `FilterPanel` - панель фильтров
- `CategorySelector` - выбор категории
