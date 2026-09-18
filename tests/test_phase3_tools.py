"""Tests for Phase 3 supporting tools."""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from decimal import Decimal

from src.ecommerce_mcp.tools.promotions import (
    validate_coupon,
    list_active_promotions,
    apply_coupon_to_order,
    create_promotion,
)
from src.ecommerce_mcp.tools.analytics import (
    get_sales_metrics,
    get_customer_analytics,
    export_report,
)
from src.ecommerce_mcp.tools.communication import (
    send_customer_email,
    list_customer_notifications,
    update_contact_preferences,
)
from src.ecommerce_mcp.tools.returns import (
    create_return_request,
    get_return_status,
    list_returns,
)
from src.ecommerce_mcp.tools.batch import (
    import_bulk_products,
    bulk_update_orders,
)
from src.ecommerce_mcp.utils import ValidationError


class TestPromotions:
    """Tests for promotions tools."""

    @pytest.mark.asyncio
    async def test_validate_coupon_success(self, patch_httpx):
        """Test coupon validation."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "code": "SAVE10",
                "discount_amount": 10.0,
                "discount_percent": 10,
                "applicable": True,
                "expiry_date": "2024-12-31",
            }

            result = await validate_coupon("SAVE10", order_total=100.0)

            assert result["code"] == "SAVE10"
            assert result["applicable"] is True

    @pytest.mark.asyncio
    async def test_list_active_promotions_success(self, patch_httpx):
        """Test listing active promotions."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "promotion_id": "prm_1",
                        "name": "Summer Sale",
                        "discount_type": "percentage",
                        "discount_value": 20,
                    }
                ]
            }

            result = await list_active_promotions()
            assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_apply_coupon_to_order_success(self, patch_httpx):
        """Test applying coupon to order."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "order_id": "ord_123",
                "coupon_code": "SAVE10",
                "discount_applied": 10.0,
                "new_total": 90.0,
                "savings": 10.0,
            }

            result = await apply_coupon_to_order("ord_123", "SAVE10")
            assert result["discount_applied"] == 10.0

    @pytest.mark.asyncio
    async def test_create_promotion_success(self, patch_httpx):
        """Test creating promotion."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "promotion_id": "prm_1",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
            }

            tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
            next_month = (datetime.now() + timedelta(days=30)).isoformat()

            result = await create_promotion(
                name="Summer Sale",
                discount_type="percentage",
                discount_value=20.0,
                start_date=tomorrow,
                end_date=next_month,
            )

            assert result["promotion_id"] == "prm_1"


class TestAnalytics:
    """Tests for analytics tools."""

    @pytest.mark.asyncio
    async def test_get_sales_metrics_success(self, patch_httpx):
        """Test getting sales metrics."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "total_revenue": 50000.0,
                "order_count": 500,
                "average_order_value": 100.0,
                "growth_rate": 15.5,
                "top_products": ["Product A", "Product B"],
            }

            result = await get_sales_metrics("month")
            assert result["total_revenue"] == 50000.0
            assert result["growth_rate"] == 15.5

    @pytest.mark.asyncio
    async def test_get_customer_analytics_success(self, patch_httpx):
        """Test getting customer analytics."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "new_customers": 150,
                "repeat_customers": 450,
                "retention_rate": 85.5,
                "churn_rate": 5.2,
            }

            result = await get_customer_analytics("month", include_churn=True)
            assert result["retention_rate"] == 85.5

    @pytest.mark.asyncio
    async def test_export_report_success(self, patch_httpx):
        """Test exporting report."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "report_id": "rep_123",
                "file_url": "https://example.com/reports/rep_123.csv",
                "file_size": 12345,
                "generated_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-02-01T00:00:00Z",
            }

            result = await export_report(
                report_type="sales",
                format="csv",
                period="month",
            )

            assert result["report_id"] == "rep_123"
            assert "file_url" in result


class TestCommunication:
    """Tests for communication tools."""

    @pytest.mark.asyncio
    async def test_send_customer_email_success(self, patch_httpx):
        """Test sending email."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "email_id": "em_123",
                "sent_to": "customer@example.com",
                "status": "sent",
                "timestamp": "2024-01-01T00:00:00Z",
            }

            result = await send_customer_email(
                customer_id="cust_123",
                email_type="order_confirmation",
                subject="Order Confirmed",
                body="Your order has been confirmed.",
            )

            assert result["email_id"] == "em_123"
            assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_list_customer_notifications_success(self, patch_httpx):
        """Test listing notifications."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "notification_id": "notif_1",
                        "type": "email",
                        "subject": "Order Confirmed",
                        "status": "delivered",
                    }
                ]
            }

            result = await list_customer_notifications("cust_123")
            assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_update_contact_preferences_success(self, patch_httpx):
        """Test updating preferences."""
        with patch("src.ecommerce_mcp.client.api_client.put") as mock_put:
            mock_put.return_value = {
                "customer_id": "cust_123",
                "preferences_updated": True,
                "timestamp": "2024-01-01T00:00:00Z",
            }

            result = await update_contact_preferences(
                customer_id="cust_123",
                email_promotional=False,
                email_updates=True,
                frequency="weekly",
            )

            assert result["preferences_updated"] is True


class TestReturns:
    """Tests for returns tools."""

    @pytest.mark.asyncio
    async def test_create_return_request_success(self, patch_httpx):
        """Test creating return request."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "return_id": "ret_123",
                "rma_number": "RMA-2024-001",
                "status": "requested",
                "instructions": "Ship to...",
            }

            result = await create_return_request(
                order_id="ord_123",
                items=[
                    {"product_id": "1", "quantity": 1, "reason": "defective"}
                ],
            )

            assert result["return_id"] == "ret_123"
            assert result["status"] == "requested"

    @pytest.mark.asyncio
    async def test_get_return_status_success(self, patch_httpx):
        """Test getting return status."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "return_id": "ret_123",
                "rma_number": "RMA-2024-001",
                "status": "in_transit",
                "refund_status": "pending",
            }

            result = await get_return_status("ret_123")
            assert result["status"] == "in_transit"

    @pytest.mark.asyncio
    async def test_list_returns_success(self, patch_httpx):
        """Test listing returns."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "return_id": "ret_123",
                        "status": "approved",
                        "refund_status": "completed",
                    }
                ]
            }

            result = await list_returns()
            assert len(result["data"]) == 1


class TestBatch:
    """Tests for batch operations tools."""

    @pytest.mark.asyncio
    async def test_import_bulk_products_success(self, patch_httpx):
        """Test bulk product import."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "import_id": "imp_123",
                "total_products": 10,
                "successful_imports": 9,
                "failed_imports": 1,
                "errors": [{"sku": "TST-999", "error": "Duplicate SKU"}],
            }

            result = await import_bulk_products(
                products=[
                    {
                        "name": f"Product {i}",
                        "sku": f"SKU-{i}",
                        "category": "Electronics",
                        "price": 99.99,
                        "stock_quantity": 100,
                    }
                    for i in range(3)
                ]
            )

            assert result["total_products"] == 10
            assert result["successful_imports"] == 9

    @pytest.mark.asyncio
    async def test_bulk_update_orders_success(self, patch_httpx):
        """Test bulk order update."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "updated_count": 9,
                "failed_count": 1,
                "errors": [{"order_id": "ord_999", "error": "Not found"}],
            }

            result = await bulk_update_orders(
                order_ids=["ord_1", "ord_2", "ord_3"],
                status="shipped",
                tags=["priority"],
            )

            assert result["updated_count"] == 9
            assert result["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_bulk_update_no_changes(self, patch_httpx):
        """Test bulk update with no changes."""
        with pytest.raises(ValidationError):
            await bulk_update_orders(
                order_ids=["ord_1", "ord_2"],
                # No status, tags, or custom_fields provided
            )

    @pytest.mark.asyncio
    async def test_import_empty_products(self, patch_httpx):
        """Test import with empty products list."""
        with pytest.raises(ValidationError):
            await import_bulk_products(
                products=[],  # Empty
            )


class TestValidationErrors:
    """Tests for validation errors."""

    @pytest.mark.asyncio
    async def test_list_promotions_invalid_tier(self, patch_httpx):
        """Test invalid customer tier."""
        with pytest.raises(ValidationError):
            await list_active_promotions(customer_tier="invalid_tier")

    @pytest.mark.asyncio
    async def test_list_notifications_invalid_type(self, patch_httpx):
        """Test invalid notification type."""
        with pytest.raises(ValidationError):
            await list_customer_notifications(
                customer_id="cust_123",
                notification_type="invalid",
            )

    @pytest.mark.asyncio
    async def test_get_customer_analytics_invalid_period(self, patch_httpx):
        """Test invalid period."""
        with pytest.raises(ValidationError):
            await get_customer_analytics(period="invalid")

    @pytest.mark.asyncio
    async def test_create_return_invalid_reason(self, patch_httpx):
        """Test invalid return reason."""
        with pytest.raises(ValidationError):
            await create_return_request(
                order_id="ord_123",
                items=[
                    {"product_id": "1", "quantity": 1, "reason": "invalid_reason"}
                ],
            )
