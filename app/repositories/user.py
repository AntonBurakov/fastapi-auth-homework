from sqlalchemy.orm import Session

from app.core.tracing import trace_span
from app.db.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        with trace_span("db.user.get_by_email", email=email):
            return (
                self.db.query(User)
                .filter(User.email == email)
                .first()
            )

    def get_by_id(self, user_id: int) -> User | None:
        with trace_span("db.user.get_by_id", user_id=user_id):
            return (
                self.db.query(User)
                .filter(User.id == user_id)
                .first()
            )

    def create(
        self,
        email: str,
        hashed_password: str,
    ) -> User:
        with trace_span("db.user.create", email=email):
            user = User(
                email=email,
                hashed_password=hashed_password,
            )

            self.db.add(user)

            self.db.commit()

            self.db.refresh(user)

            return user
