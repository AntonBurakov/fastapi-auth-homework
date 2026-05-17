import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.core.metrics import (
    HTTP_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)
from app.core.tracing import new_trace_id, trace_id_context

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id") or new_trace_id()
        token = trace_id_context.set(trace_id)
        bind_contextvars(trace_id=trace_id)

        start_time = time.perf_counter()
        path = request.url.path
        status_code = 500

        logger.info(
            "http_request_started",
            method=request.method,
            path=path,
        )

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            logger.error(
                "http_request_failed",
                method=request.method,
                path=path,
                status_code=status_code,
                error=str(exc),
            )
            raise
        finally:
            duration_seconds = time.perf_counter() - start_time
            duration_ms = round(duration_seconds * 1000, 2)
            status_code_label = str(status_code)

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=path,
                status_code=status_code_label,
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=path,
            ).observe(duration_seconds)

            if status_code >= 400:
                HTTP_ERRORS_TOTAL.labels(
                    method=request.method,
                    path=path,
                    status_code=status_code_label,
                ).inc()

            logger.info(
                "http_request_finished",
                method=request.method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )

            trace_id_context.reset(token)
            clear_contextvars()

        response.headers["X-Trace-Id"] = trace_id

        return response
