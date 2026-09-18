import httpx
import asyncio
import logging
import time
import json
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime, timedelta
from src.ecommerce_mcp.config import settings
from src.ecommerce_mcp.utils.error_handler import (
    EcommerceMCPError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    TimeoutError,
    ServiceUnavailableError,
    ClientError,
    ServerError,
)

logger = logging.getLogger(__name__)


class CacheManager:
    """TTL-based in-memory cache for API responses."""

    def __init__(self, ttl_seconds: int = settings.cache_ttl):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Store value with TTL."""
        self.cache[key] = (value, time.time() + self.ttl)
        logger.debug(f"Cache set: {key}")

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

    def delete(self, key: str) -> None:
        """Delete specific cache entry."""
        if key in self.cache:
            del self.cache[key]


class RequestDeduplicator:
    """Prevent duplicate concurrent requests."""

    def __init__(self):
        self._pending: Dict[str, asyncio.Task] = {}

    async def deduplicate(self, key: str, coro):
        """Execute coro or return existing task if same request is in-flight."""
        if key in self._pending:
            logger.debug(f"Request deduplication hit: {key}")
            return await self._pending[key]

        task = asyncio.create_task(coro)
        self._pending[key] = task

        try:
            return await task
        finally:
            if key in self._pending:
                del self._pending[key]


class EcommerceMCPClient:
    """Enhanced async HTTP client with pooling, retries, caching, and error handling."""

    def __init__(self, base_url: str = settings.fastapi_base_url):
        self.base_url = base_url
        self.max_retries = settings.max_retries
        self.backoff_factor = settings.retry_backoff_factor

        limits = httpx.Limits(
            max_connections=settings.connection_pool_size,
            max_keepalive_connections=settings.max_keepalive_connections,
        )

        self.client = httpx.AsyncClient(
            base_url=base_url,
            limits=limits,
            timeout=httpx.Timeout(settings.request_timeout),
        )

        self.cache = CacheManager() if settings.cache_enabled else None
        self.deduplicator = RequestDeduplicator()
        self._request_counter = 0

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff for retries."""
        delay = self.backoff_factor**attempt
        logger.debug(f"Backoff attempt {attempt + 1}: sleeping {delay}s")
        await asyncio.sleep(delay)

    def _make_cache_key(self, method: str, endpoint: str, params: Optional[dict] = None) -> str:
        """Generate cache key for request."""
        params_str = json.dumps(params or {}, sort_keys=True, default=str)
        return f"{method}:{endpoint}:{params_str}"

    async def _handle_response(self, response: httpx.Response, endpoint: str) -> dict:
        """Handle HTTP response and convert to dict."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)

        try:
            return response.json()
        except ValueError as e:
            logger.error(f"JSON decode error for {endpoint}: {e}")
            raise ServerError(
                f"Invalid JSON response from {endpoint}",
                "INVALID_JSON_RESPONSE",
            )

    async def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Convert HTTP errors to domain-specific exceptions."""
        status = error.response.status_code
        message = f"HTTP {status}: {error.response.text[:200]}"

        if status == 400:
            raise ClientError(message, "BAD_REQUEST")
        elif status == 404:
            raise NotFoundError(message)
        elif status == 409:
            raise ConflictError(message)
        elif status == 429:
            retry_after = error.response.headers.get("Retry-After", "60")
            raise RateLimitError(message, retry_after=int(retry_after))
        elif status == 503:
            raise ServiceUnavailableError(message)
        elif status == 504:
            raise TimeoutError(message)
        elif 400 <= status < 500:
            raise ClientError(message, f"CLIENT_ERROR_{status}")
        elif 500 <= status < 600:
            raise ServerError(message, f"SERVER_ERROR_{status}")
        else:
            raise EcommerceMCPError(message, f"HTTP_{status}", status_code=status)

    async def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        cache: bool = True,
        timeout: Optional[int] = None,
    ) -> dict:
        """GET request with caching and retries."""
        cache_key = self._make_cache_key("GET", endpoint, params) if cache else None

        if cache_key and self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        async def _do_get():
            for attempt in range(self.max_retries):
                try:
                    response = await self.client.get(
                        endpoint,
                        params=params,
                        timeout=timeout or settings.request_timeout,
                    )
                    result = await self._handle_response(response, endpoint)

                    if cache and cache_key and self.cache:
                        self.cache.set(cache_key, result)

                    return result
                except (TimeoutError, ServiceUnavailableError) as e:
                    if attempt < self.max_retries - 1:
                        await self._backoff(attempt)
                        continue
                    raise
                except httpx.TimeoutException:
                    if attempt < self.max_retries - 1:
                        await self._backoff(attempt)
                        continue
                    raise TimeoutError(f"Request timeout after {self.max_retries} attempts")
                except httpx.ConnectError as e:
                    if attempt < self.max_retries - 1:
                        await self._backoff(attempt)
                        continue
                    raise ServiceUnavailableError(f"Connection error: {str(e)}")

        return await self.deduplicator.deduplicate(
            self._make_cache_key("GET", endpoint, params), _do_get()
        )

    async def post(
        self, endpoint: str, data: Optional[dict] = None, timeout: Optional[int] = None
    ) -> dict:
        """POST request with retries."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    endpoint,
                    json=data,
                    timeout=timeout or settings.request_timeout,
                )
                return await self._handle_response(response, endpoint)
            except (TimeoutError, ServiceUnavailableError):
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise TimeoutError(f"Request timeout after {self.max_retries} attempts")
            except httpx.ConnectError as e:
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise ServiceUnavailableError(f"Connection error: {str(e)}")

    async def put(
        self, endpoint: str, data: Optional[dict] = None, timeout: Optional[int] = None
    ) -> dict:
        """PUT request with retries."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.put(
                    endpoint,
                    json=data,
                    timeout=timeout or settings.request_timeout,
                )
                return await self._handle_response(response, endpoint)
            except (TimeoutError, ServiceUnavailableError):
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise TimeoutError(f"Request timeout after {self.max_retries} attempts")
            except httpx.ConnectError as e:
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise ServiceUnavailableError(f"Connection error: {str(e)}")

    async def delete(
        self, endpoint: str, timeout: Optional[int] = None
    ) -> dict:
        """DELETE request with retries."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.delete(
                    endpoint,
                    timeout=timeout or settings.request_timeout,
                )
                return await self._handle_response(response, endpoint)
            except (TimeoutError, ServiceUnavailableError):
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise
            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise TimeoutError(f"Request timeout after {self.max_retries} attempts")
            except httpx.ConnectError as e:
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
                    continue
                raise ServiceUnavailableError(f"Connection error: {str(e)}")

    async def close(self) -> None:
        """Close HTTP client session."""
        await self.client.aclose()
        logger.info("HTTP client closed")

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        if self.cache:
            self.cache.clear()


api_client = EcommerceMCPClient()
