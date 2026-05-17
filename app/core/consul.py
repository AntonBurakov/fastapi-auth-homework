import json
import os
import urllib.error
import urllib.request

import structlog

logger = structlog.get_logger()


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


def _request(method: str, url: str, body: dict | None = None) -> None:
    data = None
    headers = {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(request, timeout=3):
        return


def register_service() -> None:
    if not _env_bool("CONSUL_ENABLED", default=True):
        logger.info("consul_registration_disabled")
        return

    consul_addr = os.getenv("CONSUL_HTTP_ADDR", "http://localhost:8500")
    service_name = os.getenv("SERVICE_NAME", "fastapi-auth")
    service_id = os.getenv("SERVICE_ID", "fastapi-auth-8000")
    service_address = os.getenv("SERVICE_ADDRESS", "127.0.0.1")
    service_port = int(os.getenv("SERVICE_PORT", "8000"))
    health_check_url = os.getenv("SERVICE_HEALTH_CHECK_URL", "http://host.docker.internal:8000/health")

    payload = {
        "ID": service_id,
        "Name": service_name,
        "Address": service_address,
        "Port": service_port,
        "Tags": ["fastapi", "auth", "observability"],
        "Check": {
            "HTTP": health_check_url,
            "Interval": "10s",
            "Timeout": "2s",
            "DeregisterCriticalServiceAfter": "1m",
        },
    }

    try:
        _request("PUT", f"{consul_addr}/v1/agent/service/register", payload)
        logger.info(
            "consul_service_registered",
            service_id=service_id,
            service_name=service_name,
            service_address=service_address,
            service_port=service_port,
            health_check_url=health_check_url,
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("consul_service_registration_failed", error=str(exc))


def deregister_service() -> None:
    if not _env_bool("CONSUL_ENABLED", default=True):
        return

    consul_addr = os.getenv("CONSUL_HTTP_ADDR", "http://localhost:8500")
    service_id = os.getenv("SERVICE_ID", "fastapi-auth-8000")

    try:
        _request("PUT", f"{consul_addr}/v1/agent/service/deregister/{service_id}")
        logger.info("consul_service_deregistered", service_id=service_id)
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("consul_service_deregistration_failed", error=str(exc))
