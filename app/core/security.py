import hashlib
import hmac

from passlib.context import CryptContext

from app.core.vault import get_token_secret

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_mock_token(user_id: int) -> str:
    payload = str(user_id)
    signature = hmac.new(
        get_token_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"mock-token-{payload}.{signature}"


def parse_mock_token(token: str) -> int | None:
    prefix = "mock-token-"

    if not token.startswith(prefix):
        return None

    raw_token = token.removeprefix(prefix)

    try:
        user_id_raw, signature = raw_token.split(".", maxsplit=1)
        user_id = int(user_id_raw)
    except ValueError:
        return None

    expected_signature = hmac.new(
        get_token_secret().encode("utf-8"),
        user_id_raw.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return None

    return user_id
