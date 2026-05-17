from fastapi import FastAPI

from app.api.dependencies import close_kafka_publisher
from app.api.routes import auth, users
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.middlewares.logging import LoggingMiddleware

setup_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Auth Homework",
    description="REST-сервис для регистрации и авторизации пользователей",
    version="1.0.0",
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(users.router)


@app.on_event("shutdown")
def shutdown_event():
    close_kafka_publisher()


@app.get("/health")
def health_check():
    return {"status": "ok"}
