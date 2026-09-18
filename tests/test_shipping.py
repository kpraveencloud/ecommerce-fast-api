"""Tests for shipping tools."""

import pytest
from unittest.mock import AsyncMock, patch

from src.ecommerce_mcp.tools.shipping import (
    get_shipment,
    list_shipments,
    create_shipment,
    update_shipment_status,
)
from src.ecommerce_mcp.utils import ValidationError


class TestGetShipment:
    """Tests for get_shipment tool."""

    @pytest.mark.asyncio
    async def test_get_shipment_success(self, patch_httpx):
        """Test retrieving shipment details."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "shipment_id": "ship_123",
                "order_id": "ord_123",
                "status": "in_transit",
                "carrier": "fedex",
                "tracking_number": "1234567890",
                "estimated_delivery": "2024-01-05",
            }

            result = await get_shipment("ship_123")

            assert result["shipment_id"] == "ship_123"
            assert result["status"] == "in_transit"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_shipment_invalid_id(self, patch_httpx):
        """Test getting shipment with invalid ID."""
        with pytest.raises(ValidationError):
            await get_shipment("")  # Empty string


class TestListShipments:
    """Tests for list_shipments tool."""

    @pytest.mark.asyncio
    async def test_list_shipments_success(self, patch_httpx):
        """Test listing shipments."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "shipment_id": "ship_123",
                        "order_id": "ord_123",
                        "status": "delivered",
                        "carrier": "fedex",
                        "tracking_number": "1234567890",
                    }
                ],
                "pagination": {"limit": 50, "offset": 0, "total": 1, "has_more": False},
            }

            result = await list_shipments()

            assert len(result["data"]) == 1
            assert result["data"][0]["shipment_id"] == "ship_123"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_shipments_with_filters(self, patch_httpx):
        """Test listing shipments with filters."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {"data": [], "pagination": {}}

            await list_shipments(
                order_id="ord_123",
                status="delivered",
                carrier="fedex",
                limit=20,
            )

            # Verify filters were passed
            call_args = mock_get.call_args
            assert call_args[1]["params"]["order_id"] == "ord_123"
            assert call_args[1]["params"]["status"] == "delivered"
            assert call_args[1]["params"]["carrier"] == "fedex"

    @pytest.mark.asyncio
    async def test_list_shipments_invalid_status(self, patch_httpx):
        """Test listing with invalid status."""
        with pytest.raises(ValidationError):
            await list_shipments(status="invalid_status")

    @pytest.mark.asyncio
    async def test_list_shipments_invalid_carrier(self, patch_httpx):
        """Test listing with invalid carrier."""
        with pytest.raises(ValidationError):
            await list_shipments(carrier="invalid_carrier")


class TestCreateShipment:
    """Tests for create_shipment tool."""

    @pytest.mark.asyncio
    async def test_create_shipment_success(self, patch_httpx):
        """Test creating shipment."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "shipment_id": "ship_456",
                "tracking_number": "FDX123456789",
                "estimated_delivery": "2024-01-05",
                "cost": 15.99,
            }

            result = await create_shipment(
                order_id="ord_123",
                items=[{"product_id": "1", "quantity": 2, "sku": "TST-001"}],
                carrier="fedex",
                shipping_address={
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                    "country": "US",
                },
                shipping_method="standard",
            )

            assert result["shipment_id"] == "ship_456"
            assert result["tracking_number"] == "FDX123456789"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_shipment_invalid_carrier(self, patch_httpx):
        """Test creating shipment with invalid carrier."""
        with pytest.raises(ValidationError):
            await create_shipment(
                order_id="ord_123",
                items=[{"product_id": "1", "quantity": 2, "sku": "TST-001"}],
                carrier="invalid_carrier",
                shipping_address={
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                    "country": "US",
                },
                shipping_method="standard",
            )

    @pytest.mark.asyncio
    async def test_create_shipment_invalid_quantity(self, patch_httpx):
        """Test creating shipment with invalid quantity."""
        with pytest.raises(ValidationError):
            await create_shipment(
                order_id="ord_123",
                items=[{"product_id": "1", "quantity": 0, "sku": "TST-001"}],  # Must be > 0
                carrier="fedex",
                shipping_address={
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "postal_code": "12345",
                    "country": "US",
                },
                shipping_method="standard",
            )


class TestUpdateShipmentStatus:
    """Tests for update_shipment_status tool."""

    @pytest.mark.asyncio
    async def test_update_shipment_status_success(self, patch_httpx):
        """Test updating shipment status."""
        with patch("src.ecommerce_mcp.client.api_client.put") as mock_put:
            mock_put.return_value = {
                "shipment_id": "ship_123",
                "status": "delivered",
                "updated_at": "2024-01-05T10:30:00Z",
            }

            result = await update_shipment_status(
                shipment_id="ship_123",
                status="delivered",
            )

            assert result["status"] == "delivered"
            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_shipment_status_with_tracking(self, patch_httpx):
        """Test updating shipment status with tracking update."""
        with patch("src.ecommerce_mcp.client.api_client.put") as mock_put:
            mock_put.return_value = {"shipment_id": "ship_123", "status": "in_transit"}

            await update_shipment_status(
                shipment_id="ship_123",
                status="in_transit",
                tracking_update={
                    "timestamp": "2024-01-04T15:00:00Z",
                    "location": "Los Angeles, CA",
                    "event_type": "in_transit",
                },
            )

            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_shipment_status_invalid_status(self, patch_httpx):
        """Test updating with invalid status."""
        with pytest.raises(ValidationError):
            await update_shipment_status(
                shipment_id="ship_123",
                status="invalid_status",
            )

    @pytest.mark.asyncio
    async def test_update_shipment_status_invalid_tracking(self, patch_httpx):
        """Test updating with invalid tracking update."""
        with pytest.raises(ValidationError):
            await update_shipment_status(
                shipment_id="ship_123",
                status="in_transit",
                tracking_update={"timestamp": "2024-01-04T15:00:00Z"},  # Missing location and event_type
            )
