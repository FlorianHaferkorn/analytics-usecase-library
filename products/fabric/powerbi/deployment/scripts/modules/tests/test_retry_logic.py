"""
Tests for retry_logic module.

Run with: python -m pytest products/fabric/powerbi/deployment/scripts/modules/tests/test_retry_logic.py -v
"""

import pytest

from retry_logic import is_transient_failure, retry, RETRYABLE_EXCEPTIONS


class TestIsTransientFailure:
    """Test transient failure detection."""

    def test_connection_error_is_transient(self):
        exc = ConnectionError("connection refused")
        assert is_transient_failure(exc) is True

    def test_timeout_error_is_transient(self):
        exc = TimeoutError("timed out")
        assert is_transient_failure(exc) is True

    def test_os_error_is_transient(self):
        exc = OSError("network unreachable")
        assert is_transient_failure(exc) is True

    def test_value_error_is_not_transient(self):
        exc = ValueError("bad value")
        assert is_transient_failure(exc) is False

    def test_key_error_is_not_transient(self):
        exc = KeyError("missing")
        assert is_transient_failure(exc) is False

    def test_http_429_in_output(self):
        exc = RuntimeError("API call failed")
        assert is_transient_failure(exc, "HTTP 429 Too Many Requests") is True

    def test_http_503_in_output(self):
        exc = RuntimeError("API call failed")
        assert is_transient_failure(exc, "503 Service Unavailable") is True

    def test_http_502_in_exception_message(self):
        exc = RuntimeError("502 Bad Gateway")
        assert is_transient_failure(exc) is True

    def test_rate_limit_substring(self):
        exc = RuntimeError("rate limit exceeded")
        assert is_transient_failure(exc) is True

    def test_service_unavailable_substring(self):
        exc = RuntimeError("service unavailable")
        assert is_transient_failure(exc) is True

    def test_clean_error_not_transient(self):
        exc = RuntimeError("invalid parameter format")
        assert is_transient_failure(exc) is False


class TestRetryDecorator:
    """Test the retry decorator."""

    def test_no_retry_on_success(self):
        call_count = 0

        @retry(max_retries=3, initial_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_transient_failure(self):
        call_count = 0

        @retry(max_retries=3, initial_delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("connection refused")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        call_count = 0

        @retry(max_retries=2, initial_delay=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("connection refused")

        with pytest.raises(ConnectionError):
            always_fail()
        assert call_count == 3  # initial + 2 retries

    def test_no_retry_on_permanent_failure(self):
        call_count = 0

        @retry(max_retries=3, initial_delay=0.01)
        def permanent_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad input")

        with pytest.raises(ValueError):
            permanent_fail()
        assert call_count == 1  # no retries for non-transient errors

    def test_custom_retry_condition(self):
        call_count = 0

        @retry(
            max_retries=2,
            initial_delay=0.01,
            retry_condition=lambda exc, out: "retry_me" in str(exc),
        )
        def custom_fail():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("retry_me please")
            return "ok"

        result = custom_fail()
        assert result == "ok"
        assert call_count == 2
