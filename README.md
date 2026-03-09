# Advertisement Service API (Часть 2)

FastAPI сервис для управления объявлениями с системой пользователей и JWT-авторизацией.

## Новые возможности (Часть 2)

- **JWT Авторизация**: Полноценная система входа (`POST /login`).
- **Управление пользователями**: Регистрация, получение профиля, обновление и удаление.
- **Роли**: Разделение на `user` и `admin`.
- **Владение объектами**: Только владелец или админ могут изменять/удалять свои данные и объявления.
- **Безопасность**: Хэширование паролей (bcrypt), токены со сроком действия 48 часов.

## Поля
- **User**: `id`, `username`, `password` (хэш), `role` (`user`/`admin`), `created_at`.
- **Advertisement**: `id`, `title`, `description`, `price`, `owner_id`, `created_at`.

## Основные Эндпоинты

### Авторизация и Пользователи
- `POST /login` — Вход, получение токена.
- `POST /user` — Регистрация (публично).
- `GET /user/{id}` — Получение профиля (публично).
- `PATCH /user/{id}` — Обновление (только владелец или админ).
- `DELETE /user/{id}` — Удаление (только владелец или админ).

### Объявления
- `GET /advertisement` — Поиск (публично).
- `GET /advertisement/{id}` — Получение (публично).
- `POST /advertisement` — Создание (только авторизованные).
- `PATCH /advertisement/{id}` — Изменение (владелец или админ).
- `DELETE /advertisement/{id}` — Удаление (владелец или админ).

## Запуск проекта

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите сервис:
```bash
python main.py
```

## Примеры использования

### 1. Регистрация
```bash
curl -X POST "http://localhost:8080/user" \
     -H "Content-Type: application/json" \
     -d '{"username": "ivan", "password": "mypassword"}'
```

### 2. Логин (получение токена)
```bash
curl -X POST "http://localhost:8080/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "ivan", "password": "mypassword"}'
```

### 3. Создание объявления (с токеном)
```bash
curl -X POST "http://localhost:8080/advertisement" \
     -H "Authorization: Bearer <ВАШ_ТОКЕН>" \
     -H "Content-Type: application/json" \
     -d '{"title": "iPhone", "description": "Good", "price": 1000}'
```

После запуска сервиса документация доступна по адресам:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- Главная страница: http://localhost:8080/

## Технологический стек

- **FastAPI**: Веб-фреймворк
- **SQLAlchemy**: ORM для работы с базой данных
- **SQLite**: База данных
- **Pydantic v2**: Валидация данных
- **Uvicorn**: ASGI сервер

## Примеры использования

### Создание объявления
```bash
curl -X POST "http://localhost:8080/advertisement" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "iPhone 15 Pro",
       "description": "Новый iPhone 15 Pro в отличном состоянии",
       "price": 999.99,
       "author": "John Doe"
     }'
```

### Поиск по описанию
```bash
curl "http://localhost:8080/advertisement?description=iphone&min_price=500&max_price=1500"
```

### Обновление цены
```bash
curl -X PATCH "http://localhost:8080/advertisement/1" \
     -H "Content-Type: application/json" \
     -d '{"price": 899.99}'
```
