"""
Retry Logic Module

Provides retry decorator, context manager, and transient failure detection
for Fabric CLI and deployment operations.
"""
import time
import functools
from typing import Callable, TypeVar, Tuple, Type, Optional
from contextlib import contextmanager

# Retryable exceptions (transient failures)
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)

# HTTP status codes that indicate transient failure (when present in error message/response)
TRANSIENT_HTTP_CODES = (429, 500, 502, 503, 504)

# Fabric-specific error substrings that indicate retryable failure
FABRIC_RETRYABLE_SUBSTRINGS = (
    "rate limit",
    "rate_limit",
    "service unavailable",
    "temporarily unavailable",
    "timeout",
    "timed out",
    "connection reset",
    "503",
    "502",
    "504",
    "429",
)

T = TypeVar("T")


def is_transient_failure(exc: BaseException, output: str = "") -> bool:
    """
    Determine if a failure is transient and worth retrying.

    Args:
        exc: The exception that was raised
        output: Optional command/output string to inspect for HTTP codes or Fabric errors

    Returns:
        True if the failure appears transient
    """
    if type(exc) in RETRYABLE_EXCEPTIONS:
        return True

    text = (str(exc) + " " + (output or "")).lower()
    for code in TRANSIENT_HTTP_CODES:
        if str(code) in text:
            return True
    for substring in FABRIC_RETRYABLE_SUBSTRINGS:
        if substring.lower() in text:
            return True
    return False


def retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    retry_condition: Optional[Callable[[BaseException, str], bool]] = None,
):
    """
    Decorator that retries a function on transient failures with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default 3)
        initial_delay: Initial delay in seconds (default 1.0)
        backoff_multiplier: Multiplier for delay after each failure (default 2.0)
        retryable_exceptions: Tuple of exception types to retry (default: network/OS errors)
        retry_condition: Optional callable(exc, output) -> bool to decide if retry; overrides default
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            exc_types = retryable_exceptions if retryable_exceptions is not None else RETRYABLE_EXCEPTIONS
            last_exc = None
            last_output = ""
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    last_output = getattr(e, "output", "") or getattr(e, "stderr", "") or str(e)
                    if attempt >= max_retries:
                        raise
                    should_retry = (
                        retry_condition(last_exc, last_output)
                        if retry_condition
                        else is_transient_failure(last_exc, last_output)
                    )
                    if not should_retry:
                        raise
                    time.sleep(delay)
                    delay *= backoff_multiplier
            raise last_exc  # type: ignore

        return wrapper  # type: ignore

    return decorator


@contextmanager
def retry_context(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_multiplier: float = 2.0,
):
    """
    Context manager for manual retry control. Yields (attempt, max_retries).
    Caller raises on failure; context manager does not catch.
    """
    for attempt in range(max_retries + 1):
        yield attempt, max_retries
        if attempt < max_retries:
            time.sleep(initial_delay * (backoff_multiplier ** attempt))
