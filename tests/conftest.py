"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import httpx


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_api_client():
    """Mock API client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_response():
    """Create mock HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json = MagicMock(return_value={"status": "success", "data": {}})
    response.headers = {}
    response.text = ""
    return response


@pytest.fixture
def sample_customer():
    """Sample customer data for tests."""
    return {
        "id": "cust_123",
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1-555-0123",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_order():
    """Sample order data for tests."""
    return {
        "id": "ord_123",
        "customer_id": "cust_123",
        "status": "pending",
        "total": 99.99,
        "currency": "USD",
        "items": [{"product_id": 1, "quantity": 2, "price": 49.99}],
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_product():
    """Sample product data for tests."""
    return {
        "id": 1,
        "name": "Test Product",
        "sku": "TST-001",
        "price": 49.99,
        "description": "A test product",
        "stock_quantity": 100,
        "category": "Electronics",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_payment():
    """Sample payment data for tests."""
    return {
        "order_id": "ord_123",
        "amount": 99.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_details": {"token": "tok_visa_4242"},
        "idempotency_key": "idem_unique_123",
    }


@pytest.fixture
def sample_shipment():
    """Sample shipment data for tests."""
    return {
        "order_id": "ord_123",
        "items": [{"product_id": "1", "quantity": 2, "sku": "TST-001"}],
        "carrier": "fedex",
        "shipping_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "postal_code": "12345",
            "country": "US",
        },
        "shipping_method": "standard",
        "signature_required": False,
    }


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    settings = MagicMock()
    settings.fastapi_base_url = "http://localhost:8000"
    settings.max_retries = 3
    settings.retry_backoff_factor = 2.0
    settings.request_timeout = 30
    settings.cache_enabled = True
    settings.cache_ttl = 300
    return settings


class MockAsyncClient:
    """Mock AsyncClient for testing."""

    def __init__(self, *args, **kwargs):
        self.base_url = kwargs.get("base_url")
        self.timeout = kwargs.get("timeout")

    async def get(self, *args, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json = MagicMock(return_value={"status": "success"})
        response.raise_for_status = MagicMock()
        return response

    async def post(self, *args, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json = MagicMock(return_value={"status": "success"})
        response.raise_for_status = MagicMock()
        return response

    async def put(self, *args, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json = MagicMock(return_value={"status": "success"})
        response.raise_for_status = MagicMock()
        return response

    async def delete(self, *args, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.json = MagicMock(return_value={"status": "success"})
        response.raise_for_status = MagicMock()
        return response

    async def aclose(self):
        pass


@pytest.fixture
def patch_httpx():
    """Patch httpx.AsyncClient for tests."""
    with patch("httpx.AsyncClient", MockAsyncClient):
        yield
