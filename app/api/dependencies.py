from typing import Annotated

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import parse_mock_token
from app.db.models import User
from app.db.session import SessionLocal
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.kafka.publisher import KafkaPublisher

security = HTTPBearer()
_kafka_publisher: KafkaPublisher | None = None


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_user_repository(
    db: Annotated[Session, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_kafka_publisher() -> KafkaPublisher:
    global _kafka_publisher

    if _kafka_publisher is not None:
        return _kafka_publisher

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "user_events")
    _kafka_publisher = KafkaPublisher(bootstrap_servers=bootstrap, topic=topic)
    return _kafka_publisher


def close_kafka_publisher() -> None:
    global _kafka_publisher

    if _kafka_publisher is not None:
        _kafka_publisher.close()
        _kafka_publisher = None


def get_auth_service(
    user_repo: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
    publisher: Annotated[
        KafkaPublisher,
        Depends(get_kafka_publisher),
    ],
) -> AuthService:
    return AuthService(user_repo, publisher)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(security),
    ],
    user_repo: Annotated[
        UserRepository,
        Depends(get_user_repository),
    ],
) -> User:
    token = credentials.credentials

    user_id = parse_mock_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
