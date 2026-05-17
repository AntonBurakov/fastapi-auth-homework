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
- логирование HTTP-запросов;
- публикация и обработка события `user_registered` через Kafka.

Основная цель проекта — продемонстрировать построение backend-приложения с production-style архитектурой:

- разделение приложения на логические слои;
- dependency injection;
- middleware;
- работа с базой данных через ORM;
- structured logging;
- producer / consumer взаимодействие через Kafka.

---

# Используемый стек

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Structlog
- Uvicorn
- Kafka
- kafka-python
- ZooKeeper
- Docker Compose

---

# Архитектура проекта

Проект разделён на несколько логических слоёв.

```text
Request
  ↓
API / Routes
  ↓
Services
  ↓            ↓
Repositories
  ↓            Kafka Producer → Kafka Topic → Kafka Consumer
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
│   ├── kafka/
│   │   ├── consumer.py
│   │   └── publisher.py
│   ├── repositories/
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   └── user.py
│   ├── services/
│   │   └── auth.py
│   └── main.py
├── requirements.txt
├── docker-compose.yml
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

### Kafka

Слой Kafka вынесен отдельно от HTTP-слоя:

* `app/kafka/publisher.py` публикует событие `user_registered`;
* `app/kafka/consumer.py` запускается отдельным процессом и читает topic;
* `AuthService` вызывает publisher после успешной регистрации пользователя;
* consumer использует consumer group и вручную коммитит offset после обработки сообщения.

Producer делает несколько попыток публикации, использует `acks=all` и не ломает регистрацию пользователя, если Kafka временно недоступна.
Consumer коммитит offset только после обработки сообщения. Для демонстрации идемпотентности он запоминает `event_id` уже обработанных событий в памяти процесса и пропускает дубликаты.

Локально Kafka запускается через Docker Compose вместе с ZooKeeper.

## Dependency Injection

В проекте используется dependency injection через FastAPI Depends.

Реализовано внедрение:

* DB session;
* repository;
* service;
* current user;
* Kafka publisher.

---

## Реализованные endpoints

### POST /auth/register

Регистрация нового пользователя.

Функционал

* принимает email и password;
* проверяет уникальность email;
* хэширует пароль;
* сохраняет пользователя в БД;
* публикует событие `user_registered` в Kafka.

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

## 4. Запуск Kafka

```bash
docker compose up -d kafka
```

Команда поднимет ZooKeeper и Kafka. Kafka будет доступна приложению по адресу:

```bash
localhost:9092
```

Topic `user_events` создаётся автоматически при первой публикации сообщения.

При первом запуске контейнерам может понадобиться несколько секунд, чтобы полностью стартовать.

## 5. Запуск приложения

```bash
uvicorn app.main:app --reload
```

## 6. Запуск consumer

В отдельном терминале:

```bash
python -m app.kafka.consumer
```

Consumer читает topic `user_events`, логирует событие и вручную коммитит offset после успешной обработки.

## Swagger UI
После запуска документация доступна по адресу:
```bash
http://127.0.0.1:8000/docs
```

# Проверка работы producer + consumer

## 1. Запустить Kafka

```bash
docker compose up -d kafka
```

Эта команда также запустит ZooKeeper, потому что Kafka зависит от него в `docker-compose.yml`.

## 2. Запустить FastAPI

```bash
uvicorn app.main:app --reload
```

## 3. Запустить consumer

```bash
python -m app.kafka.consumer
```

## 4. Зарегистрировать пользователя

В новом терминале:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

Ожидаемый результат:

* API вернёт созданного пользователя;
* в логах FastAPI появится `published_user_registered`;
* в логах consumer появится `consumed_event`;
* после обработки consumer залогирует `offset_committed`.

## 5. Проверить авторизацию

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

Пример ответа:

```json
{
  "access_token": "mock-token-1",
  "token_type": "bearer"
}
```

## 6. Проверить текущего пользователя

```bash
curl http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer mock-token-1"
```

# Kafka UI

Kafka UI не обязателен для выполнения задания. Producer и consumer можно продемонстрировать по логам приложения и consumer.

Если хочется визуально посмотреть topic и сообщения, можно запустить:

```bash
docker compose up -d kafka-ui
```

После этого Kafka UI будет доступен по адресу:

```bash
http://localhost:8080
```
