"""Tests for payment tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from src.ecommerce_mcp.tools.payments import (
    process_payment,
    get_payment_status,
    refund_payment,
    list_payment_methods,
    add_payment_method,
)
from src.ecommerce_mcp.utils import ValidationError, NotFoundError


class TestProcessPayment:
    """Tests for process_payment tool."""

    @pytest.mark.asyncio
    async def test_process_payment_success(self, patch_httpx):
        """Test successful payment processing."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "transaction_id": "txn_123",
                "status": "success",
                "amount": 99.99,
                "currency": "USD",
                "timestamp": "2024-01-01T00:00:00Z",
                "confirmation_code": "CONF-123",
            }

            result = await process_payment(
                order_id="ord_123",
                amount=99.99,
                currency="USD",
                payment_method="credit_card",
                payment_details={"token": "tok_visa_4242"},
                idempotency_key="idem_123",
            )

            assert result["status"] == "success"
            assert result["transaction_id"] == "txn_123"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_payment_invalid_currency(self, patch_httpx):
        """Test payment with invalid currency."""
        with pytest.raises(ValidationError):
            await process_payment(
                order_id="ord_123",
                amount=99.99,
                currency="INVALID",  # Must be 3 letters
                payment_method="credit_card",
                payment_details={"token": "tok_visa_4242"},
            )

    @pytest.mark.asyncio
    async def test_process_payment_zero_amount(self, patch_httpx):
        """Test payment with zero amount."""
        with pytest.raises(ValidationError):
            await process_payment(
                order_id="ord_123",
                amount=0,  # Must be > 0
                currency="USD",
                payment_method="credit_card",
                payment_details={"token": "tok_visa_4242"},
            )

    @pytest.mark.asyncio
    async def test_process_payment_invalid_method(self, patch_httpx):
        """Test payment with invalid payment method."""
        with pytest.raises(ValidationError):
            await process_payment(
                order_id="ord_123",
                amount=99.99,
                currency="USD",
                payment_method="invalid_method",
                payment_details={"token": "tok_visa_4242"},
            )


class TestGetPaymentStatus:
    """Tests for get_payment_status tool."""

    @pytest.mark.asyncio
    async def test_get_payment_status_success(self, patch_httpx):
        """Test retrieving payment status."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "transaction_id": "txn_123",
                "status": "success",
                "amount": 99.99,
                "method": "credit_card",
                "order_id": "ord_123",
                "timestamp": "2024-01-01T00:00:00Z",
            }

            result = await get_payment_status("txn_123")

            assert result["status"] == "success"
            assert result["transaction_id"] == "txn_123"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payment_status_invalid_id(self, patch_httpx):
        """Test getting status with invalid transaction ID."""
        with pytest.raises(ValidationError):
            await get_payment_status("")  # Empty string


class TestRefundPayment:
    """Tests for refund_payment tool."""

    @pytest.mark.asyncio
    async def test_refund_payment_full(self, patch_httpx):
        """Test full refund."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "refund_id": "ref_123",
                "status": "completed",
                "amount": 99.99,
                "timestamp": "2024-01-01T00:00:00Z",
            }

            result = await refund_payment(
                transaction_id="txn_123",
                reason="customer_request",
            )

            assert result["refund_id"] == "ref_123"
            assert result["status"] == "completed"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_refund_payment_partial(self, patch_httpx):
        """Test partial refund."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "refund_id": "ref_123",
                "status": "completed",
                "amount": 50.00,
                "timestamp": "2024-01-01T00:00:00Z",
            }

            result = await refund_payment(
                transaction_id="txn_123",
                amount=50.00,
                reason="defective_item",
            )

            assert result["amount"] == 50.00
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_refund_payment_invalid_reason(self, patch_httpx):
        """Test refund with invalid reason."""
        with pytest.raises(ValidationError):
            await refund_payment(
                transaction_id="txn_123",
                reason="invalid_reason",
            )


class TestListPaymentMethods:
    """Tests for list_payment_methods tool."""

    @pytest.mark.asyncio
    async def test_list_payment_methods_success(self, patch_httpx):
        """Test listing payment methods."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "method_id": "pm_123",
                        "type": "credit_card",
                        "last_four": "4242",
                        "expiry": "12/25",
                        "is_default": True,
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                ],
                "pagination": {"limit": 50, "offset": 0, "total": 1, "has_more": False},
            }

            result = await list_payment_methods("cust_123")

            assert len(result["data"]) == 1
            assert result["data"][0]["method_id"] == "pm_123"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_payment_methods_invalid_limit(self, patch_httpx):
        """Test listing with invalid limit."""
        with pytest.raises(ValidationError):
            await list_payment_methods("cust_123", limit=1000)  # Max is 500


class TestAddPaymentMethod:
    """Tests for add_payment_method tool."""

    @pytest.mark.asyncio
    async def test_add_payment_method_success(self, patch_httpx):
        """Test adding payment method."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "method_id": "pm_456",
                "type": "credit_card",
                "last_four": "5555",
                "status": "active",
            }

            result = await add_payment_method(
                customer_id="cust_123",
                method_type="credit_card",
                details={"token": "tok_visa_5555"},
                set_as_default=True,
            )

            assert result["method_id"] == "pm_456"
            assert result["status"] == "active"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_payment_method_invalid_type(self, patch_httpx):
        """Test adding payment method with invalid type."""
        with pytest.raises(ValidationError):
            await add_payment_method(
                customer_id="cust_123",
                method_type="invalid_type",
                details={"token": "tok_visa_5555"},
            )

    @pytest.mark.asyncio
    async def test_add_payment_method_empty_details(self, patch_httpx):
        """Test adding payment method with empty details."""
        with pytest.raises(ValidationError):
            await add_payment_method(
                customer_id="cust_123",
                method_type="credit_card",
                details={},  # Must not be empty
            )
