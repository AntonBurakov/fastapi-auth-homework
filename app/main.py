from fastapi import FastAPI, Response

from app.api.dependencies import close_kafka_publisher
from app.api.routes import auth, users
from app.core.consul import deregister_service, register_service
from app.core.logging import setup_logging
from app.core.metrics import CONTENT_TYPE_LATEST, render_metrics
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


@app.on_event("startup")
def startup_event():
    register_service()


@app.on_event("shutdown")
def shutdown_event():
    deregister_service()
    close_kafka_publisher()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(
        content=render_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )
