from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_mock_token(user_id: int) -> str:
    return f"mock-token-{user_id}"


def parse_mock_token(token: str) -> int | None:
    prefix = "mock-token-"

    if not token.startswith(prefix):
        return None

    try:
        return int(token.removeprefix(prefix))
    except ValueError:
        return None