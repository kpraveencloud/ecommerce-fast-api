"""Tests for utility modules."""

import pytest
from datetime import datetime
from decimal import Decimal

from src.ecommerce_mcp.utils import (
    ValidationError,
    PaymentError,
    PaymentDeclinedError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    TimeoutError,
    PaymentSchema,
    RefundSchema,
    CreateShipmentSchema,
    SearchProductsSchema,
    format_success_response,
    format_error_response,
    format_paginated_response,
)


class TestErrorHandler:
    """Tests for custom exceptions."""

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input", {"field": "name"})
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.details == {"field": "name"}

    def test_payment_error(self):
        """Test PaymentError."""
        error = PaymentError("Payment failed")
        assert error.message == "Payment failed"
        assert error.error_code == "PAYMENT_ERROR"
        assert error.status_code == 400

    def test_payment_declined_error(self):
        """Test PaymentDeclinedError."""
        error = PaymentDeclinedError("Card declined")
        assert error.message == "Card declined"
        assert error.error_code == "PAYMENT_DECLINED"
        assert error.status_code == 400

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found")
        assert error.status_code == 404

    def test_conflict_error(self):
        """Test ConflictError."""
        error = ConflictError("Duplicate entry")
        assert error.status_code == 409
        assert error.error_code == "CONFLICT"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError(retry_after=60)
        assert error.status_code == 429
        assert error.details.get("retry_after") == 60

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timed out")
        assert error.status_code == 504


class TestPaymentValidator:
    """Tests for PaymentSchema validation."""

    def test_valid_payment(self):
        """Test valid payment data."""
        payment_data = {
            "order_id": "ord_123",
            "amount": Decimal("99.99"),
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_details": {"token": "tok_visa_4242"},
        }
        schema = PaymentSchema(**payment_data)
        assert schema.order_id == "ord_123"
        assert schema.amount == Decimal("99.99")
        assert schema.currency == "USD"

    def test_invalid_currency(self):
        """Test invalid currency code."""
        payment_data = {
            "order_id": "ord_123",
            "amount": Decimal("99.99"),
            "currency": "INVALID",  # Should be 3 uppercase letters
            "payment_method": "credit_card",
            "payment_details": {"token": "tok_visa_4242"},
        }
        with pytest.raises(ValueError):
            PaymentSchema(**payment_data)

    def test_invalid_amount(self):
        """Test invalid amount (negative or zero)."""
        payment_data = {
            "order_id": "ord_123",
            "amount": Decimal("0"),  # Must be > 0
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_details": {"token": "tok_visa_4242"},
        }
        with pytest.raises(ValueError):
            PaymentSchema(**payment_data)

    def test_invalid_payment_method(self):
        """Test invalid payment method."""
        payment_data = {
            "order_id": "ord_123",
            "amount": Decimal("99.99"),
            "currency": "USD",
            "payment_method": "invalid_method",
            "payment_details": {"token": "tok_visa_4242"},
        }
        with pytest.raises(ValueError):
            PaymentSchema(**payment_data)


class TestRefundValidator:
    """Tests for RefundSchema validation."""

    def test_valid_full_refund(self):
        """Test valid full refund."""
        refund_data = {
            "transaction_id": "txn_123",
            "reason": "customer_request",
        }
        schema = RefundSchema(**refund_data)
        assert schema.transaction_id == "txn_123"
        assert schema.reason == "customer_request"
        assert schema.amount is None

    def test_valid_partial_refund(self):
        """Test valid partial refund."""
        refund_data = {
            "transaction_id": "txn_123",
            "amount": Decimal("50.00"),
            "reason": "defective_item",
        }
        schema = RefundSchema(**refund_data)
        assert schema.amount == Decimal("50.00")


class TestShipmentValidator:
    """Tests for CreateShipmentSchema validation."""

    def test_valid_shipment(self):
        """Test valid shipment data."""
        shipment_data = {
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
        }
        schema = CreateShipmentSchema(**shipment_data)
        assert schema.order_id == "ord_123"
        assert len(schema.items) == 1
        assert schema.carrier == "fedex"

    def test_invalid_carrier(self):
        """Test invalid carrier."""
        shipment_data = {
            "order_id": "ord_123",
            "items": [{"product_id": "1", "quantity": 2, "sku": "TST-001"}],
            "carrier": "invalid_carrier",
            "shipping_address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "US",
            },
            "shipping_method": "standard",
        }
        with pytest.raises(ValueError):
            CreateShipmentSchema(**shipment_data)

    def test_invalid_quantity(self):
        """Test invalid item quantity."""
        shipment_data = {
            "order_id": "ord_123",
            "items": [{"product_id": "1", "quantity": 0, "sku": "TST-001"}],  # Must be > 0
            "carrier": "fedex",
            "shipping_address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "US",
            },
            "shipping_method": "standard",
        }
        with pytest.raises(ValueError):
            CreateShipmentSchema(**shipment_data)


class TestSearchValidator:
    """Tests for SearchProductsSchema validation."""

    def test_valid_search(self):
        """Test valid search query."""
        search_data = {
            "query": "laptop",
            "categories": ["electronics"],
            "price_range": {"min": Decimal("500"), "max": Decimal("2000")},
            "rating_min": 4.0,
            "in_stock_only": True,
            "sort_by": "relevance",
        }
        schema = SearchProductsSchema(**search_data)
        assert schema.query == "laptop"
        assert schema.price_range.min == Decimal("500")

    def test_invalid_rating(self):
        """Test invalid rating."""
        search_data = {
            "query": "laptop",
            "rating_min": 6.0,  # Max is 5.0
        }
        with pytest.raises(ValueError):
            SearchProductsSchema(**search_data)

    def test_price_range_validation(self):
        """Test price range validation."""
        search_data = {
            "query": "laptop",
            "price_range": {"min": Decimal("2000"), "max": Decimal("500")},  # max < min
        }
        with pytest.raises(ValueError):
            SearchProductsSchema(**search_data)


class TestFormatters:
    """Tests for response formatting functions."""

    def test_format_success_response(self):
        """Test success response formatting."""
        response = format_success_response({"id": "123", "name": "Test"})
        assert response["status"] == "success"
        assert response["data"] == {"id": "123", "name": "Test"}
        assert "timestamp" in response
        assert response["message"] == "Success"

    def test_format_error_response(self):
        """Test error response formatting."""
        error = ValidationError("Invalid input", {"field": "email"})
        response = format_error_response(error)
        assert response["status"] == "error"
        assert response["error_code"] == "VALIDATION_ERROR"
        assert response["message"] == "Invalid input"
        assert response["details"] == {"field": "email"}
        assert "timestamp" in response

    def test_format_paginated_response(self):
        """Test paginated response formatting."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = format_paginated_response(items, limit=10, offset=0, total=100)
        assert response["status"] == "success"
        assert response["data"] == items
        assert response["pagination"]["limit"] == 10
        assert response["pagination"]["offset"] == 0
        assert response["pagination"]["total"] == 100
        assert response["pagination"]["has_more"] is True
        assert response["pagination"]["page"] == 1

    def test_format_paginated_response_no_more(self):
        """Test paginated response when no more items."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = format_paginated_response(items, limit=10, offset=90, total=100)
        assert response["pagination"]["has_more"] is False
