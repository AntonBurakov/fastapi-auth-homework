import time
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

import structlog

trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)


def new_trace_id() -> str:
    return uuid4().hex


def get_trace_id() -> str | None:
    return trace_id_context.get()


@contextmanager
def trace_span(name: str, **fields):
    logger = structlog.get_logger()
    start_time = time.perf_counter()

    logger.info(
        "span_started",
        span_name=name,
        **fields,
    )

    try:
        yield
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "span_failed",
            span_name=name,
            duration_ms=duration_ms,
            error=str(exc),
            **fields,
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        "span_finished",
        span_name=name,
        duration_ms=duration_ms,
        **fields,
    )
