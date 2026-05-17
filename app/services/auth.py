from fastapi import HTTPException, status

from app.core.security import create_mock_token, hash_password, verify_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, data: UserCreate):
        existing_user = self.user_repo.get_by_email(data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        hashed_password = hash_password(data.password)

        return self.user_repo.create(
            email=data.email,
            hashed_password=hashed_password,
        )

    def login_user(self, email: str, password: str) -> str:
        user = self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return create_mock_token(user.id)