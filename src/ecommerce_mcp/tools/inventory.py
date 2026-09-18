"""Inventory and warehouse management tools."""

import logging
from typing import Optional
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    StockAdjustmentSchema,
    ValidationError,
    InventoryError,
    format_success_response,
    format_paginated_response,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

inventory_mcp = FastMCP(name="Inventory Tools")


@inventory_mcp.tool
async def get_product_stock(
    product_id: int,
    warehouse_id: Optional[str] = None,
) -> dict:
    """Retrieve stock information for a product.

    Args:
        product_id: Product identifier
        warehouse_id: Specific warehouse ID (all warehouses if omitted)

    Returns:
        dict with product_id, available_quantity, reserved_quantity,
        warehouse_details (per-warehouse levels), reorder_point,
        last_restock_date, supplier_id

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If product not found
    """
    if not settings.feature_inventory:
        raise ValidationError("Inventory feature is disabled", error_code="FEATURE_DISABLED")

    # Validate inputs
    if not isinstance(product_id, int) or product_id <= 0:
        raise ValidationError("product_id must be a positive integer")

    params = {}
    if warehouse_id:
        if not isinstance(warehouse_id, str) or not warehouse_id.strip():
            raise ValidationError("warehouse_id must be a non-empty string")
        params["warehouse_id"] = warehouse_id

    try:
        result = await api_client.get(
            f"/api/v1/products/{product_id}/stock",
            params=params if params else None,
            cache=True,
        )

        logger.info(f"Product stock retrieved: product_id={product_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to get stock for product {product_id}: {str(e)}")
        raise


@inventory_mcp.tool
async def list_inventory(
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List inventory levels with filters.

    Args:
        warehouse_id: Filter by warehouse
        status: Filter by stock status (in_stock, low_stock, out_of_stock, overstock)
        category: Filter by product category
        limit: Maximum results (default: 100, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of inventory items and pagination metadata
        Each item contains: product_id, sku, available_quantity, status, warehouse_id

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_inventory:
        raise ValidationError("Inventory feature is disabled", error_code="FEATURE_DISABLED")

    # Validate pagination
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    # Validate status if provided
    valid_statuses = ["in_stock", "low_stock", "out_of_stock", "overstock"]
    if status and status not in valid_statuses:
        raise ValidationError(f"status must be one of: {', '.join(valid_statuses)}")

    params = {"limit": limit, "offset": offset}
    if warehouse_id:
        if not isinstance(warehouse_id, str) or not warehouse_id.strip():
            raise ValidationError("warehouse_id must be a non-empty string")
        params["warehouse_id"] = warehouse_id
    if status:
        params["status"] = status
    if category:
        if not isinstance(category, str) or not category.strip():
            raise ValidationError("category must be a non-empty string")
        params["category"] = category

    try:
        result = await api_client.get(
            "/api/v1/inventory",
            params=params,
            cache=True,
        )

        logger.info(f"Inventory listed: {len(result.get('data', []))} items")
        return result
    except Exception as e:
        logger.error(f"Failed to list inventory: {str(e)}")
        raise


@inventory_mcp.tool
async def adjust_stock(
    product_id: int,
    warehouse_id: str,
    quantity_change: int,
    reason: str,
    reference_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Adjust inventory levels (stock correction, returns, damage).

    Args:
        product_id: Product identifier
        warehouse_id: Warehouse identifier
        quantity_change: Quantity to add/subtract (positive or negative)
        reason: Reason for adjustment (restock, damage, loss, return, correction)
        reference_id: Related order/RMA ID
        notes: Additional notes

    Returns:
        dict with product_id, previous_quantity, new_quantity, warehouse_id, timestamp

    Raises:
        ValidationError: If input validation fails
        InventoryError: If adjustment would result in negative stock
        NotFoundError: If product or warehouse not found
    """
    if not settings.feature_inventory:
        raise ValidationError("Inventory feature is disabled", error_code="FEATURE_DISABLED")

    try:
        # Validate input
        adjustment_data = StockAdjustmentSchema(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_change=quantity_change,
            reason=reason,
            reference_id=reference_id,
            notes=notes,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "stock_adjustment"})

    try:
        result = await api_client.post(
            f"/api/v1/inventory/{adjustment_data.product_id}/adjust",
            data={
                "warehouse_id": adjustment_data.warehouse_id,
                "quantity_change": adjustment_data.quantity_change,
                "reason": adjustment_data.reason,
                "reference_id": adjustment_data.reference_id,
                "notes": adjustment_data.notes,
            },
        )

        logger.info(
            f"Stock adjusted: product_id={product_id}, change={quantity_change}, "
            f"reason={reason}"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to adjust stock for product {product_id}: {str(e)}")
        raise


@inventory_mcp.tool
async def list_warehouses(
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Retrieve warehouse information and locations.

    Args:
        limit: Maximum results (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of warehouses and pagination metadata
        Each warehouse contains: warehouse_id, name, address, city, state,
        postal_code, country, capacity, current_utilization, manager_contact

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_inventory:
        raise ValidationError("Inventory feature is disabled", error_code="FEATURE_DISABLED")

    # Validate pagination
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    try:
        result = await api_client.get(
            "/api/v1/warehouses",
            params={"limit": limit, "offset": offset},
            cache=True,
        )

        logger.info(f"Warehouses listed: {len(result.get('data', []))} items")
        return result
    except Exception as e:
        logger.error(f"Failed to list warehouses: {str(e)}")
        raise
