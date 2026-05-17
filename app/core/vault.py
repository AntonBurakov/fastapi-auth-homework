import json
import os
import urllib.error
import urllib.request
from functools import lru_cache

import structlog

logger = structlog.get_logger()


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_token_secret() -> str:
    if not _env_bool("VAULT_ENABLED", default=True):
        secret = os.getenv("APP_TOKEN_SECRET")
        if not secret:
            raise RuntimeError("APP_TOKEN_SECRET is required when VAULT_ENABLED=false")
        return secret

    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_TOKEN")
    secret_path = os.getenv("VAULT_TOKEN_SECRET_PATH", "secret/data/fastapi-auth")

    if not vault_token:
        raise RuntimeError("VAULT_TOKEN is required to read secrets from Vault")

    request = urllib.request.Request(
        url=f"{vault_addr}/v1/{secret_path}",
        headers={"X-Vault-Token": vault_token},
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not read token secret from Vault: {exc}") from exc

    secret = payload.get("data", {}).get("data", {}).get("token_secret")
    if not secret:
        raise RuntimeError(f"token_secret is missing in Vault path {secret_path}")

    logger.info("vault_secret_loaded", secret_path=secret_path, secret_key="token_secret")
    return secret
