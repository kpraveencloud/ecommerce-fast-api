"""Batch operations and bulk import tools."""

import logging
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    BulkImportProductsSchema,
    BulkUpdateOrdersSchema,
    ValidationError,
    format_batch_response,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

batch_mcp = FastMCP(name="Batch Tools")


@batch_mcp.tool
async def import_bulk_products(
    products: List[dict],
    update_existing: bool = False,
    file_source: Optional[str] = None,
) -> dict:
    """Import multiple products via CSV or structured data.

    Args:
        products: Array of product objects with name, sku, category, price,
                 description, stock_quantity, supplier_id
        update_existing: Update if SKU exists (default: false)
        file_source: CSV file URL for import

    Returns:
        dict with import_id, total_products, successful_imports, failed_imports, errors

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_batch:
        raise ValidationError("Batch feature is disabled", error_code="FEATURE_DISABLED")

    try:
        import_data = BulkImportProductsSchema(
            products=products,
            update_existing=update_existing,
            file_source=file_source,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "bulk_import"})

    # Validate we have at least some products
    if not import_data.products or len(import_data.products) == 0:
        raise ValidationError("products list cannot be empty")

    try:
        result = await api_client.post(
            "/api/v1/batch/import-products",
            data={
                "products": [
                    {
                        "name": p.name,
                        "sku": p.sku,
                        "category": p.category,
                        "price": float(p.price),
                        "description": p.description,
                        "stock_quantity": p.stock_quantity,
                        "supplier_id": p.supplier_id,
                    }
                    for p in import_data.products
                ],
                "update_existing": import_data.update_existing,
                "file_source": import_data.file_source,
            },
        )

        logger.info(
            f"Bulk import processed: {result.get('total_products')} products, "
            f"successful={result.get('successful_imports')}, "
            f"failed={result.get('failed_imports')}"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to import products: {str(e)}")
        raise


@batch_mcp.tool
async def bulk_update_orders(
    order_ids: List[str],
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_fields: Optional[Dict[str, Any]] = None,
) -> dict:
    """Bulk update order statuses or properties.

    Args:
        order_ids: Order identifiers
        status: New status to apply
        tags: Add tags to orders
        custom_fields: Custom field updates

    Returns:
        dict with updated_count, failed_count, errors (if any)

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_batch:
        raise ValidationError("Batch feature is disabled", error_code="FEATURE_DISABLED")

    try:
        update_data = BulkUpdateOrdersSchema(
            order_ids=order_ids,
            status=status,
            tags=tags,
            custom_fields=custom_fields,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "bulk_update"})

    # Validate we have at least some order IDs
    if not update_data.order_ids or len(update_data.order_ids) == 0:
        raise ValidationError("order_ids list cannot be empty")

    # Validate we have at least one update field
    if not status and not tags and not custom_fields:
        raise ValidationError("At least one of status, tags, or custom_fields must be provided")

    try:
        result = await api_client.post(
            "/api/v1/batch/update-orders",
            data={
                "order_ids": update_data.order_ids,
                "status": update_data.status,
                "tags": update_data.tags,
                "custom_fields": update_data.custom_fields,
            },
        )

        logger.info(
            f"Bulk update processed: {result.get('updated_count')} updated, "
            f"{result.get('failed_count')} failed"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to update orders: {str(e)}")
        raise
