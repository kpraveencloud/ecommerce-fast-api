"""Tests for the enhanced HTTP client."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import httpx

from src.ecommerce_mcp.client import EcommerceMCPClient, CacheManager, RequestDeduplicator
from src.ecommerce_mcp.utils.error_handler import (
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ServiceUnavailableError,
    ClientError,
)


class TestCacheManager:
    """Tests for CacheManager."""

    def test_cache_set_and_get(self):
        """Test setting and getting cached values."""
        cache = CacheManager(ttl_seconds=300)
        cache.set("key1", {"data": "value"})

        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_cache_expiry(self):
        """Test cache expiry."""
        cache = CacheManager(ttl_seconds=1)
        cache.set("key1", {"data": "value"})

        import time
        time.sleep(1.1)

        result = cache.get("key1")
        assert result is None

    def test_cache_delete(self):
        """Test deleting cache entry."""
        cache = CacheManager()
        cache.set("key1", {"data": "value"})
        cache.delete("key1")

        result = cache.get("key1")
        assert result is None

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = CacheManager()
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestRequestDeduplicator:
    """Tests for RequestDeduplicator."""

    @pytest.mark.asyncio
    async def test_deduplicate_prevents_duplicate_requests(self):
        """Test that duplicate requests are deduplicated."""
        dedup = RequestDeduplicator()

        call_count = 0

        async def slow_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"result": "success"}

        # Start two concurrent requests with same key
        task1 = asyncio.create_task(dedup.deduplicate("key1", slow_operation()))
        task2 = asyncio.create_task(dedup.deduplicate("key1", slow_operation()))

        result1, result2 = await asyncio.gather(task1, task2)

        assert result1 == {"result": "success"}
        assert result2 == {"result": "success"}
        assert call_count == 1  # Should only be called once


class TestEcommerceMCPClient:
    """Tests for EcommerceMCPClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization."""
        client = EcommerceMCPClient(base_url="http://test.local:8000")
        assert client.base_url == "http://test.local:8000"
        assert client.max_retries == 3
        assert client.cache is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful GET request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"data": "value"})
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()
            result = await client.get("/api/v1/test", params={"id": "123"})

            assert result == {"data": "value"}
            mock_client.get.assert_called_once()
            await client.close()

    @pytest.mark.asyncio
    async def test_post_success(self):
        """Test successful POST request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"id": "new_id"})
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()
            result = await client.post("/api/v1/test", data={"name": "test"})

            assert result == {"id": "new_id"}
            mock_client.post.assert_called_once()
            await client.close()

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test GET request with 404 response."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "404 Not Found", request=MagicMock(), response=mock_response
                )
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()

            with pytest.raises(NotFoundError):
                await client.get("/api/v1/nonexistent")

            await client.close()

    @pytest.mark.asyncio
    async def test_get_rate_limit(self):
        """Test GET request with rate limit error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 429
            mock_response.text = "Too many requests"
            mock_response.headers = {"Retry-After": "60"}
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "429 Too Many Requests", request=MagicMock(), response=mock_response
                )
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()

            with pytest.raises(RateLimitError):
                await client.get("/api/v1/test")

            await client.close()

    @pytest.mark.asyncio
    async def test_caching(self):
        """Test response caching."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"cached": True})
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()

            # First call should hit the API
            result1 = await client.get("/api/v1/test", params={"id": "1"}, cache=True)
            assert result1 == {"cached": True}
            assert mock_client.get.call_count == 1

            # Second call should use cache
            result2 = await client.get("/api/v1/test", params={"id": "1"}, cache=True)
            assert result2 == {"cached": True}
            assert mock_client.get.call_count == 1  # Not called again

            # Clear cache and call again
            client.clear_cache()
            result3 = await client.get("/api/v1/test", params={"id": "1"}, cache=True)
            assert result3 == {"cached": True}
            assert mock_client.get.call_count == 2  # Called again

            await client.close()

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry logic on timeout."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"success": True})
            mock_response.raise_for_status = MagicMock()

            # First call fails, second succeeds
            mock_client.get = AsyncMock(
                side_effect=[httpx.TimeoutException("Timeout"), mock_response]
            )
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()
            result = await client.get("/api/v1/test")

            assert result == {"success": True}
            assert mock_client.get.call_count == 2  # Called twice due to retry

            await client.close()

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test failure after max retries."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()

            with pytest.raises(TimeoutError):
                await client.get("/api/v1/test")

            # Should have attempted max_retries times
            assert mock_client.get.call_count == client.max_retries

            await client.close()


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_client_error_400(self):
        """Test handling of 400 errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "400 Bad Request", request=MagicMock(), response=mock_response
                )
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()

            with pytest.raises(ClientError):
                await client.get("/api/v1/test")

            await client.close()

    @pytest.mark.asyncio
    async def test_service_unavailable_503(self):
        """Test handling of 503 errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError(
                    "503 Service Unavailable",
                    request=MagicMock(),
                    response=mock_response,
                )
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = EcommerceMCPClient()

            with pytest.raises(ServiceUnavailableError):
                await client.get("/api/v1/test")

            await client.close()
