import asyncio
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from loguru import logger


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    retryable: tuple[type[Exception], ...] | None = None,
) -> Callable:
    """
    Decorator that retries an async function with exponential backoff.

    Args:
        max_attempts: Total number of attempts before raising.
        base_delay: Base delay in seconds; actual wait is base_delay * 2^attempt.
        retryable: Exception types eligible for retry. When ``None`` (default),
            all exceptions are retried (backward-compatible behaviour).
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if retryable and not isinstance(e, retryable):
                        raise

                    if attempt == max_attempts - 1:
                        raise

                    wait_time = base_delay * (2**attempt)
                    logger.warning(
                        f"{func.__name__}: attempt {attempt + 1} failed, "
                        f"retrying in {wait_time}s... ({e})"
                    )
                    await asyncio.sleep(wait_time)

        return wrapper

    return decorator
