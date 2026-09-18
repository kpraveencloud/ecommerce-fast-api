"""Tests for inventory tools."""

import pytest
from unittest.mock import patch

from src.ecommerce_mcp.tools.inventory import (
    get_product_stock,
    list_inventory,
    adjust_stock,
    list_warehouses,
)
from src.ecommerce_mcp.utils import ValidationError


class TestGetProductStock:
    """Tests for get_product_stock tool."""

    @pytest.mark.asyncio
    async def test_get_product_stock_success(self, patch_httpx):
        """Test retrieving product stock."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "product_id": 1,
                "available_quantity": 100,
                "reserved_quantity": 10,
                "reorder_point": 20,
                "last_restock_date": "2024-01-01",
                "warehouse_details": [
                    {"warehouse_id": "wh_1", "quantity": 60},
                    {"warehouse_id": "wh_2", "quantity": 40},
                ],
            }

            result = await get_product_stock(1)

            assert result["product_id"] == 1
            assert result["available_quantity"] == 100
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_stock_invalid_id(self, patch_httpx):
        """Test with invalid product ID."""
        with pytest.raises(ValidationError):
            await get_product_stock(-1)  # Must be > 0


class TestListInventory:
    """Tests for list_inventory tool."""

    @pytest.mark.asyncio
    async def test_list_inventory_success(self, patch_httpx):
        """Test listing inventory."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "product_id": 1,
                        "sku": "TST-001",
                        "available_quantity": 100,
                        "status": "in_stock",
                        "warehouse_id": "wh_1",
                    }
                ],
                "pagination": {"limit": 100, "offset": 0, "total": 1},
            }

            result = await list_inventory()

            assert len(result["data"]) == 1
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_inventory_with_filters(self, patch_httpx):
        """Test listing with filters."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {"data": [], "pagination": {}}

            await list_inventory(
                warehouse_id="wh_1",
                status="low_stock",
                category="Electronics",
                limit=50,
            )

            call_args = mock_get.call_args
            assert call_args[1]["params"]["warehouse_id"] == "wh_1"
            assert call_args[1]["params"]["status"] == "low_stock"

    @pytest.mark.asyncio
    async def test_list_inventory_invalid_status(self, patch_httpx):
        """Test with invalid status."""
        with pytest.raises(ValidationError):
            await list_inventory(status="invalid_status")


class TestAdjustStock:
    """Tests for adjust_stock tool."""

    @pytest.mark.asyncio
    async def test_adjust_stock_success(self, patch_httpx):
        """Test adjusting stock."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "product_id": 1,
                "previous_quantity": 100,
                "new_quantity": 150,
                "warehouse_id": "wh_1",
                "timestamp": "2024-01-01T00:00:00Z",
            }

            result = await adjust_stock(
                product_id=1,
                warehouse_id="wh_1",
                quantity_change=50,
                reason="restock",
            )

            assert result["new_quantity"] == 150
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_adjust_stock_damage(self, patch_httpx):
        """Test adjusting stock for damage."""
        with patch("src.ecommerce_mcp.client.api_client.post") as mock_post:
            mock_post.return_value = {
                "product_id": 1,
                "previous_quantity": 100,
                "new_quantity": 90,
                "warehouse_id": "wh_1",
            }

            result = await adjust_stock(
                product_id=1,
                warehouse_id="wh_1",
                quantity_change=-10,
                reason="damage",
                notes="Water damage in storage",
            )

            assert result["new_quantity"] == 90
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_adjust_stock_zero_change(self, patch_httpx):
        """Test with zero quantity change."""
        with pytest.raises(ValidationError):
            await adjust_stock(
                product_id=1,
                warehouse_id="wh_1",
                quantity_change=0,  # Must be non-zero
                reason="restock",
            )


class TestListWarehouses:
    """Tests for list_warehouses tool."""

    @pytest.mark.asyncio
    async def test_list_warehouses_success(self, patch_httpx):
        """Test listing warehouses."""
        with patch("src.ecommerce_mcp.client.api_client.get") as mock_get:
            mock_get.return_value = {
                "data": [
                    {
                        "warehouse_id": "wh_1",
                        "name": "Main Warehouse",
                        "city": "Los Angeles",
                        "state": "CA",
                        "country": "US",
                        "capacity": 50000,
                        "current_utilization": 35000,
                    }
                ],
                "pagination": {"limit": 50, "offset": 0, "total": 1},
            }

            result = await list_warehouses()

            assert len(result["data"]) == 1
            assert result["data"][0]["warehouse_id"] == "wh_1"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_warehouses_invalid_limit(self, patch_httpx):
        """Test with invalid limit."""
        with pytest.raises(ValidationError):
            await list_warehouses(limit=1000)  # Max is 500
