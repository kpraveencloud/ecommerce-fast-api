"""Shipping and fulfillment management tools."""

import logging
from typing import Optional, List
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    CreateShipmentSchema,
    ValidationError,
    format_success_response,
    format_paginated_response,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

shipping_mcp = FastMCP(name="Shipping Tools")


@shipping_mcp.tool
async def get_shipment(shipment_id: str) -> dict:
    """Retrieve shipment details including tracking information.

    Args:
        shipment_id: Shipment identifier

    Returns:
        dict with shipment_id, order_id, status, carrier, tracking_number,
        origin_address, destination_address, estimated_delivery, actual_delivery,
        weight, dimensions, events (array of tracking events)

    Raises:
        ValidationError: If shipment_id is invalid
        NotFoundError: If shipment not found
    """
    if not settings.feature_shipping:
        raise ValidationError("Shipping feature is disabled", error_code="FEATURE_DISABLED")

    if not shipment_id or not isinstance(shipment_id, str):
        raise ValidationError("shipment_id must be a non-empty string")

    try:
        result = await api_client.get(
            f"/api/v1/shipments/{shipment_id}",
            cache=True,
            timeout=settings.shipping_timeout,
        )

        logger.info(f"Shipment details retrieved: {shipment_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to get shipment {shipment_id}: {str(e)}")
        raise


@shipping_mcp.tool
async def list_shipments(
    order_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    carrier: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List shipments with filtering and pagination.

    Args:
        order_id: Filter by order ID
        customer_id: Filter by customer ID
        status: Filter by status (pending, shipped, in_transit, delivered, delayed, returned)
        carrier: Filter by shipping carrier (fedex, ups, usps, dhl)
        limit: Maximum results (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of shipments and pagination metadata

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_shipping:
        raise ValidationError("Shipping feature is disabled", error_code="FEATURE_DISABLED")

    # Validate pagination
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    # Validate status if provided
    valid_statuses = ["pending", "shipped", "in_transit", "delivered", "delayed", "returned"]
    if status and status not in valid_statuses:
        raise ValidationError(f"status must be one of: {', '.join(valid_statuses)}")

    # Validate carrier if provided
    valid_carriers = ["fedex", "ups", "usps", "dhl"]
    if carrier and carrier not in valid_carriers:
        raise ValidationError(f"carrier must be one of: {', '.join(valid_carriers)}")

    params = {"limit": limit, "offset": offset}
    if order_id:
        params["order_id"] = order_id
    if customer_id:
        params["customer_id"] = customer_id
    if status:
        params["status"] = status
    if carrier:
        params["carrier"] = carrier

    try:
        result = await api_client.get(
            "/api/v1/shipments",
            params=params,
            cache=True,
            timeout=settings.shipping_timeout,
        )

        logger.info(f"Shipments listed: {len(result.get('data', []))} items")
        return result
    except Exception as e:
        logger.error(f"Failed to list shipments: {str(e)}")
        raise


@shipping_mcp.tool
async def create_shipment(
    order_id: str,
    items: List[dict],
    carrier: str,
    shipping_address: dict,
    shipping_method: str,
    signature_required: bool = False,
) -> dict:
    """Create a new shipment for an order.

    Args:
        order_id: Order identifier
        items: Items to ship - each with product_id, quantity, sku
        carrier: Shipping carrier (fedex, ups, usps, dhl)
        shipping_address: Destination address with street, city, state, postal_code, country
        shipping_method: Method (standard, express, overnight, international)
        signature_required: Require signature on delivery

    Returns:
        dict with shipment_id, tracking_number, estimated_delivery, cost

    Raises:
        ValidationError: If input validation fails
        InventoryError: If items not available for shipment
        NotFoundError: If order or products not found
    """
    if not settings.feature_shipping:
        raise ValidationError("Shipping feature is disabled", error_code="FEATURE_DISABLED")

    try:
        # Validate input
        shipment_data = CreateShipmentSchema(
            order_id=order_id,
            items=items,
            carrier=carrier,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            signature_required=signature_required,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "shipment"})

    try:
        result = await api_client.post(
            "/api/v1/shipments",
            data={
                "order_id": shipment_data.order_id,
                "items": [item.dict() for item in shipment_data.items],
                "carrier": shipment_data.carrier,
                "shipping_address": shipment_data.shipping_address.dict(),
                "shipping_method": shipment_data.shipping_method,
                "signature_required": shipment_data.signature_required,
            },
            timeout=settings.shipping_timeout,
        )

        logger.info(f"Shipment created: {result.get('shipment_id')} for order {order_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to create shipment for order {order_id}: {str(e)}")
        raise


@shipping_mcp.tool
async def update_shipment_status(
    shipment_id: str,
    status: str,
    tracking_update: Optional[dict] = None,
    notes: Optional[str] = None,
) -> dict:
    """Update shipment status (manual or webhook-based).

    Args:
        shipment_id: Shipment identifier
        status: New status (shipped, in_transit, out_for_delivery, delivered, exception)
        tracking_update: Carrier tracking event with timestamp, location, event_type
        notes: Additional notes about the update

    Returns:
        dict with updated shipment information

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If shipment not found
    """
    if not settings.feature_shipping:
        raise ValidationError("Shipping feature is disabled", error_code="FEATURE_DISABLED")

    # Validate status
    valid_statuses = ["shipped", "in_transit", "out_for_delivery", "delivered", "exception"]
    if status not in valid_statuses:
        raise ValidationError(f"status must be one of: {', '.join(valid_statuses)}")

    if not shipment_id or not isinstance(shipment_id, str):
        raise ValidationError("shipment_id must be a non-empty string")

    # Validate tracking_update if provided
    if tracking_update:
        if not isinstance(tracking_update, dict):
            raise ValidationError("tracking_update must be a dict")
        required_fields = ["timestamp", "location", "event_type"]
        if not all(field in tracking_update for field in required_fields):
            raise ValidationError(f"tracking_update must contain: {', '.join(required_fields)}")

    try:
        result = await api_client.put(
            f"/api/v1/shipments/{shipment_id}",
            data={
                "status": status,
                "tracking_update": tracking_update,
                "notes": notes,
            },
            timeout=settings.shipping_timeout,
        )

        logger.info(f"Shipment status updated: {shipment_id} -> {status}")
        return result
    except Exception as e:
        logger.error(f"Failed to update shipment {shipment_id}: {str(e)}")
        raise
