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
- публикация и обработка события `user_registered` через Kafka;
- базовая наблюдаемость: метрики, структурированные логи и trace_id.

Основная цель проекта — продемонстрировать построение backend-приложения с production-style архитектурой:

- разделение приложения на логические слои;
- dependency injection;
- middleware;
- работа с базой данных через ORM;
- structured logging;
- producer / consumer взаимодействие через Kafka;
- observability: HTTP-метрики, JSON-логи, trace/span-like события;
- service discovery через Consul.

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
- prometheus-client
- Consul
- Docker Compose

---

# Архитектура проекта

Проект разделён на несколько логических слоёв.

```text
Request
  ↓
Consul Service Discovery
  ↓
Observability Middleware
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
│   │   ├── consul.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── security.py
│   │   └── tracing.py
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
* path;
* статус ответа;
* время выполнения запроса;
* trace_id.

Middleware также собирает HTTP-метрики:

* `http_requests_total`;
* `http_errors_total`;
* `http_request_duration_seconds`.

Метрики доступны по endpoint `/metrics` в Prometheus-формате.

### Observability

В проекте реализованы три базовых сигнала наблюдаемости:

* метрики через `prometheus-client`;
* структурированные JSON-логи через `structlog`;
* базовая трассировка через `trace_id` и span-like события в логах.

Для каждого HTTP-запроса middleware создаёт `trace_id`, добавляет его в JSON-логи и возвращает в заголовке ответа `X-Trace-Id`.

Внутри request flow логируются отдельные шаги:

* `http_request_started`;
* `auth.register_user`;
* `db.user.get_by_email`;
* `db.user.create`;
* `kafka.publish_user_registered`;
* `http_request_finished`.

Все эти записи можно связать по одному `trace_id`.

### Consul

Приложение регистрирует FastAPI-сервис в Consul при старте и снимает регистрацию при остановке.

Параметры по умолчанию:

* service name: `fastapi-auth`;
* service id: `fastapi-auth-8000`;
* service address: `127.0.0.1`;
* service port: `8000`;
* health check: `http://host.docker.internal:8000/health`.

Consul выполняет HTTP health check endpoint `/health`.
Сервис можно найти по логическому имени `fastapi-auth` через Consul UI, HTTP API или DNS-имя `fastapi-auth.service.consul`.

Переменные окружения для настройки:

* `CONSUL_ENABLED`;
* `CONSUL_HTTP_ADDR`;
* `SERVICE_NAME`;
* `SERVICE_ID`;
* `SERVICE_ADDRESS`;
* `SERVICE_PORT`;
* `SERVICE_HEALTH_CHECK_URL`.

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

### GET /metrics

Endpoint с метриками приложения в Prometheus-формате.

Пример:

```bash
curl http://127.0.0.1:8000/metrics
```

В ответе будут доступны, например:

```text
http_requests_total
http_errors_total
http_request_duration_seconds
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

## 5. Запуск Consul

```bash
docker compose up -d consul
```

Consul UI будет доступен по адресу:

```bash
http://localhost:8500
```

## 6. Запуск приложения

```bash
uvicorn app.main:app --reload
```

При старте приложение зарегистрирует сервис `fastapi-auth` в Consul.

## 7. Запуск consumer

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

## Метрики

Метрики доступны по адресу:

```bash
http://127.0.0.1:8000/metrics
```

Проверить через терминал:

```bash
curl http://127.0.0.1:8000/metrics
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

# Проверка observability

## 1. Запустить сервис

```bash
docker compose up -d kafka
uvicorn app.main:app --reload
```

Consumer можно запустить отдельно, если нужно показать Kafka flow:

```bash
python -m app.kafka.consumer
```

## 2. Посмотреть метрики до запроса

```bash
curl http://127.0.0.1:8000/metrics
```

## 3. Выполнить регистрацию пользователя

```bash
curl -i -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"observable@example.com","password":"password123"}'
```

В ответе будет заголовок:

```text
X-Trace-Id: <trace_id>
```

## 4. Найти request flow в логах

В логах FastAPI нужно найти значение `trace_id` из ответа.

По этому `trace_id` будут видны события одного запроса:

```text
http_request_started
span_started / span_finished: auth.register_user
span_started / span_finished: db.user.get_by_email
span_started / span_finished: db.user.create
span_started / span_finished: kafka.publish_user_registered
published_user_registered
http_request_finished
```

Логи выводятся в JSON-формате и содержат `method`, `path`, `status_code`, `duration_ms` и `trace_id`.

## 5. Проверить, что метрики изменились

```bash
curl http://127.0.0.1:8000/metrics | grep http_requests_total
curl http://127.0.0.1:8000/metrics | grep http_request_duration_seconds
```

После запросов значения счётчиков и histogram buckets должны измениться.

# Проверка Consul service discovery

## 1. Запустить Consul

```bash
docker compose up -d consul
```

## 2. Запустить FastAPI

```bash
uvicorn app.main:app --reload
```

В логах приложения должна появиться запись:

```text
consul_service_registered
```

## 3. Проверить регистрацию сервиса

Через Consul HTTP API:

```bash
curl http://localhost:8500/v1/catalog/service/fastapi-auth
```

Ожидаемый результат: JSON со службой `fastapi-auth`, адресом `127.0.0.1` и портом `8000`.

Через Consul UI:

```bash
http://localhost:8500
```

В разделе Services должен быть сервис `fastapi-auth`.

## 4. Проверить health check

```bash
curl 'http://localhost:8500/v1/health/service/fastapi-auth?passing'
```

Если приложение работает, Consul вернёт сервис в списке passing checks.

Также можно открыть сервис в Consul UI и увидеть зелёный health check.

## 5. Проверить доступ по логическому имени

Через Consul DNS:

```bash
dig @127.0.0.1 -p 8600 fastapi-auth.service.consul
```

Ожидаемый результат: DNS-ответ с адресом `127.0.0.1`.

Проверить порт через SRV-запись:

```bash
dig @127.0.0.1 -p 8600 fastapi-auth.service.consul SRV
```

Ожидаемый результат: SRV-запись с портом `8000`.

После этого сервис доступен по найденному адресу:

```bash
curl http://127.0.0.1:8000/health
```

## 6. Показать сценарий отказа

Остановить FastAPI через `Ctrl+C`.

Подождать 10-20 секунд и проверить health:

```bash
curl 'http://localhost:8500/v1/health/service/fastapi-auth'
```

Ожидаемый результат: check перейдёт в состояние `critical`, потому что Consul больше не может открыть `/health`.

Если приложение завершилось штатно, оно также отправит deregister в Consul. Тогда сервис может исчезнуть из каталога:

```bash
curl http://localhost:8500/v1/catalog/service/fastapi-auth
```

Чтобы явно показать отказ именно через health check, можно завершить процесс нештатно или временно запустить приложение на другом порту без изменения `SERVICE_HEALTH_CHECK_URL`.
