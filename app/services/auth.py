from typing import Optional

import structlog
from fastapi import HTTPException, status

from app.kafka.publisher import KafkaPublisher
from app.core.security import create_mock_token, hash_password, verify_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository, publisher: Optional[KafkaPublisher] = None):
        self.logger = structlog.get_logger()
        self.user_repo = user_repo
        self.publisher = publisher

    def register_user(self, data: UserCreate):
        existing_user = self.user_repo.get_by_email(data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        hashed_password = hash_password(data.password)

        user = self.user_repo.create(
            email=data.email,
            hashed_password=hashed_password,
        )

        try:
            if self.publisher:
                published = self.publisher.publish_user_registered(user)
                if not published:
                    self.logger.warning("user_registered_event_not_published", user_id=user.id)
        except Exception as exc:
            self.logger.error("unexpected_user_registered_publish_error", error=str(exc), user_id=user.id)

        return user

    def login_user(self, email: str, password: str) -> str:
        user = self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return create_mock_token(user.id)
