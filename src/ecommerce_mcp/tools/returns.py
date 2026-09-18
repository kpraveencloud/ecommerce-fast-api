"""Returns and RMA (Return Merchandise Authorization) tools."""

import logging
from typing import Optional, List
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    CreateReturnSchema,
    ValidationError,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

returns_mcp = FastMCP(name="Returns Tools")


@returns_mcp.tool
async def create_return_request(
    order_id: str,
    items: List[dict],
    comments: Optional[str] = None,
) -> dict:
    """Initiate a product return.

    Args:
        order_id: Order identifier
        items: Items to return - each with product_id, quantity, reason
               Reason: defective, wrong_item, not_as_described, changed_mind,
                      damaged_in_shipping, other
        comments: Additional comments

    Returns:
        dict with return_id, rma_number, status, instructions, return_shipping_label (if applicable)

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If order or products not found
    """
    if not settings.feature_returns:
        raise ValidationError("Returns feature is disabled", error_code="FEATURE_DISABLED")

    try:
        return_data = CreateReturnSchema(
            order_id=order_id,
            items=items,
            comments=comments,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "return_request"})

    try:
        result = await api_client.post(
            "/api/v1/returns",
            data={
                "order_id": return_data.order_id,
                "items": [item.dict() for item in return_data.items],
                "comments": return_data.comments,
            },
        )

        logger.info(f"Return request created: {result.get('return_id')} for order {order_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to create return request for order {order_id}: {str(e)}")
        raise


@returns_mcp.tool
async def get_return_status(return_id: str) -> dict:
    """Retrieve return request status and tracking.

    Args:
        return_id: Return identifier

    Returns:
        dict with return_id, rma_number, order_id, status, items, refund_status,
        refund_amount, estimated_completion, tracking_number (if shipped back)

    Raises:
        ValidationError: If return_id is invalid
        NotFoundError: If return not found
    """
    if not settings.feature_returns:
        raise ValidationError("Returns feature is disabled", error_code="FEATURE_DISABLED")

    if not return_id or not isinstance(return_id, str):
        raise ValidationError("return_id must be a non-empty string")

    try:
        result = await api_client.get(
            f"/api/v1/returns/{return_id}",
            cache=True,
        )

        logger.info(f"Return status retrieved: {return_id}, status={result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Failed to get return status for {return_id}: {str(e)}")
        raise


@returns_mcp.tool
async def list_returns(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List returns with filtering.

    Args:
        customer_id: Filter by customer
        status: Filter by status (requested, approved, in_transit, received, refunded, rejected)
        limit: Maximum results (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of returns and pagination metadata

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_returns:
        raise ValidationError("Returns feature is disabled", error_code="FEATURE_DISABLED")

    # Validate pagination
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    # Validate status if provided
    valid_statuses = ["requested", "approved", "in_transit", "received", "refunded", "rejected"]
    if status and status not in valid_statuses:
        raise ValidationError(f"status must be one of: {', '.join(valid_statuses)}")

    params = {"limit": limit, "offset": offset}
    if customer_id:
        if not isinstance(customer_id, str) or not customer_id.strip():
            raise ValidationError("customer_id must be a non-empty string")
        params["customer_id"] = customer_id
    if status:
        params["status"] = status

    try:
        result = await api_client.get(
            "/api/v1/returns",
            params=params,
            cache=True,
        )

        logger.info(f"Returns listed: {len(result.get('data', []))} items")
        return result
    except Exception as e:
        logger.error(f"Failed to list returns: {str(e)}")
        raise
