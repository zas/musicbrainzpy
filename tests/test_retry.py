"""Tests for the retry module."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from musicbrainzpy._retry import async_retry, sync_retry
from musicbrainzpy.exceptions import NotFoundError, RateLimitedError


class TestAsyncRetry:
    async def test_success_no_retry(self) -> None:
        func = MagicMock(return_value=42)

        async def _call() -> int:
            return func()

        result = await async_retry(_call, max_retries=3, base_delay=0)
        assert result == 42
        assert func.call_count == 1

    async def test_retries_on_transport_error(self) -> None:
        func = MagicMock(side_effect=[httpx.ConnectError("fail"), httpx.ReadTimeout("timeout"), 42])

        async def _call() -> int:
            return func()

        result = await async_retry(_call, max_retries=3, base_delay=0)
        assert result == 42
        assert func.call_count == 3

    async def test_retries_on_rate_limit(self) -> None:
        func = MagicMock(side_effect=[RateLimitedError("429", retry_after=0), 42])

        async def _call() -> int:
            return func()

        result = await async_retry(_call, max_retries=3, base_delay=0)
        assert result == 42
        assert func.call_count == 2

    async def test_no_retry_on_permanent_error(self) -> None:
        func = MagicMock(side_effect=NotFoundError("404"))

        async def _call() -> int:
            return func()

        with pytest.raises(NotFoundError):
            await async_retry(_call, max_retries=3, base_delay=0)
        assert func.call_count == 1

    async def test_exhausted_retries_raises(self) -> None:
        func = MagicMock(side_effect=httpx.ConnectError("fail"))

        async def _call() -> int:
            return func()

        with pytest.raises(httpx.ConnectError):
            await async_retry(_call, max_retries=2, base_delay=0)
        assert func.call_count == 3  # initial + 2 retries

    async def test_zero_retries_no_retry(self) -> None:
        func = MagicMock(side_effect=httpx.ConnectError("fail"))

        async def _call() -> int:
            return func()

        with pytest.raises(httpx.ConnectError):
            await async_retry(_call, max_retries=0, base_delay=0)
        assert func.call_count == 1


class TestSyncRetry:
    def test_success_no_retry(self) -> None:
        func = MagicMock(return_value=42)
        result = sync_retry(func, max_retries=3, base_delay=0)
        assert result == 42
        assert func.call_count == 1

    def test_retries_on_transport_error(self) -> None:
        func = MagicMock(side_effect=[httpx.ConnectError("fail"), 42])
        result = sync_retry(func, max_retries=3, base_delay=0)
        assert result == 42
        assert func.call_count == 2

    def test_no_retry_on_permanent_error(self) -> None:
        func = MagicMock(side_effect=NotFoundError("404"))
        with pytest.raises(NotFoundError):
            sync_retry(func, max_retries=3, base_delay=0)
        assert func.call_count == 1

    def test_exhausted_retries_raises(self) -> None:
        func = MagicMock(side_effect=RateLimitedError("503", retry_after=0))
        with pytest.raises(RateLimitedError):
            sync_retry(func, max_retries=1, base_delay=0)
        assert func.call_count == 2  # initial + 1 retry
