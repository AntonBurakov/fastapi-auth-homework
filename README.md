# FastAPI Auth Homework

REST-сервис на FastAPI для регистрации и авторизации пользователей.

Проект реализован в рамках домашнего задания по теме:
**«FastAPI: архитектура production-сервиса»**.

---

# Назначение проекта

Сервис моделирует базовую backend-логику работы с пользователями:

- регистрация нового пользователя;
- авторизация пользователя;
- получение информации о текущем пользователе;
- работа с токенами доступа;
- логирование HTTP-запросов.

Основная цель проекта — продемонстрировать построение backend-приложения с production-style архитектурой:

- разделение приложения на логические слои;
- dependency injection;
- middleware;
- работа с базой данных через ORM;
- structured logging.

---

# Используемый стек

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Structlog
- Uvicorn

---

# Архитектура проекта

Проект разделён на несколько логических слоёв.

```text
Request
  ↓
API / Routes
  ↓
Services
  ↓
Repositories
  ↓
Database
```

# Структура проекта
```
fastapi-auth-homework/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── auth.py
│   │       └── users.py
│   ├── core/
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── middlewares/
│   │   └── logging.py
│   ├── repositories/
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/
│   │   └── auth.py
│   └── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Описание слоёв

### API / Routes

HTTP-слой приложения.

Содержит REST endpoints и обработку HTTP-запросов.

Примеры:

* /auth/register
* /auth/login
* /users/me

### Services

Слой бизнес-логики.

Отвечает за:

* регистрацию пользователя;
* проверку пароля;
* авторизацию;
* генерацию access token.


### Repositories

Слой работы с базой данных.

Изолирует SQLAlchemy и ORM-логику от бизнес-логики приложения.


### DB

Слой работы с БД.

Содержит:

* SQLAlchemy models;
* engine;
* session factory;
* базовую ORM-конфигурацию.

### Schemas

Pydantic-схемы запросов и ответов.

Используются для:

* валидации данных;
* сериализации ответов;
* генерации OpenAPI/Swagger.


### Middleware

Middleware для логирования HTTP-запросов.

Логируются:

* HTTP метод;
* URL;
* статус ответа;
* время выполнения запроса.

## Dependency Injection

В проекте используется dependency injection через FastAPI Depends.

Реализовано внедрение:

* DB session;
* repository;
* service;
* current user.

---

## Реализованные endpoints

### POST /auth/register

Регистрация нового пользователя.

Функционал

* принимает email и password;
* проверяет уникальность email;
* хэширует пароль;
* сохраняет пользователя в БД.

Пример запроса
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Пример ответа
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

### POST /auth/login

Авторизация пользователя.

Функционал

* проверяет email и пароль;
* возвращает access token.

Пример запроса
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Пример ответа
```json
{
  "access_token": "mock-token-1",
  "token_type": "bearer"
}
```


### GET /users/me

Получение информации о текущем пользователе.

Функционал

* принимает Bearer token;
* определяет текущего пользователя;
* возвращает данные пользователя.

Пример ответа
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

### GET /health

Healthcheck endpoint.

Пример ответа
```json
{
  "status": "ok"
}
```

# Запуск проекта
## 1. Создание виртуального окружения

```bash
python -m venv venv
```
## 2. Активация виртуального окружения

macOS / Linux
```bash
source venv/bin/activate
```

## 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 4. Запуск приложения

```bash
uvicorn app.main:app --reload
```

## Swagger UI
После запуска документация доступна по адресу:
```bash
http://127.0.0.1:8000/docs
```