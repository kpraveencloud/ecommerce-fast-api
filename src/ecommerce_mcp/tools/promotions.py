"""Promotional tools and discount management."""

import logging
from typing import Optional, List
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    CouponValidationSchema,
    PromotionSchema,
    ValidationError,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

promotions_mcp = FastMCP(name="Promotions Tools")


@promotions_mcp.tool
async def validate_coupon(
    coupon_code: str,
    order_total: Optional[float] = None,
    customer_id: Optional[str] = None,
) -> dict:
    """Validate and retrieve coupon details.

    Args:
        coupon_code: Coupon or discount code
        order_total: Order amount for validation
        customer_id: Customer for eligibility check

    Returns:
        dict with code, discount_amount, discount_percent, max_uses, current_uses,
        expiry_date, applicable, invalid_reason (if not applicable)

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If coupon not found
    """
    if not settings.feature_promotions:
        raise ValidationError("Promotions feature is disabled", error_code="FEATURE_DISABLED")

    try:
        from decimal import Decimal
        coupon_data = CouponValidationSchema(
            coupon_code=coupon_code,
            order_total=Decimal(str(order_total)) if order_total else None,
            customer_id=customer_id,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "coupon"})

    params = {"code": coupon_data.coupon_code}
    if coupon_data.order_total:
        params["order_total"] = float(coupon_data.order_total)
    if coupon_data.customer_id:
        params["customer_id"] = coupon_data.customer_id

    try:
        result = await api_client.get(
            f"/api/v1/coupons/{coupon_code}/validate",
            params=params,
            cache=True,
        )

        logger.info(f"Coupon validated: {coupon_code}, applicable={result.get('applicable')}")
        return result
    except Exception as e:
        logger.error(f"Failed to validate coupon {coupon_code}: {str(e)}")
        raise


@promotions_mcp.tool
async def list_active_promotions(
    category: Optional[str] = None,
    customer_tier: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Retrieve currently active promotions.

    Args:
        category: Filter by product category
        customer_tier: Filter by customer tier (silver, gold, platinum)
        limit: Maximum results (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        dict with list of promotions and pagination info
        Each promotion contains: promotion_id, name, discount_type, discount_value,
        start_date, end_date, applicable_products, terms

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_promotions:
        raise ValidationError("Promotions feature is disabled", error_code="FEATURE_DISABLED")

    # Validate pagination
    if limit < 1 or limit > 500:
        raise ValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise ValidationError("offset must be >= 0")

    # Validate customer_tier if provided
    valid_tiers = ["silver", "gold", "platinum"]
    if customer_tier and customer_tier not in valid_tiers:
        raise ValidationError(f"customer_tier must be one of: {', '.join(valid_tiers)}")

    params = {"limit": limit, "offset": offset}
    if category:
        if not isinstance(category, str) or not category.strip():
            raise ValidationError("category must be a non-empty string")
        params["category"] = category
    if customer_tier:
        params["customer_tier"] = customer_tier

    try:
        result = await api_client.get(
            "/api/v1/promotions/active",
            params=params,
            cache=True,
        )

        logger.info(f"Active promotions listed: {len(result.get('data', []))} items")
        return result
    except Exception as e:
        logger.error(f"Failed to list promotions: {str(e)}")
        raise


@promotions_mcp.tool
async def apply_coupon_to_order(
    order_id: str,
    coupon_code: str,
) -> dict:
    """Apply a coupon code to an order.

    Args:
        order_id: Order identifier
        coupon_code: Coupon code

    Returns:
        dict with order_id, coupon_code, discount_applied, new_total, savings

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If order or coupon not found
        ConflictError: If coupon already applied
    """
    if not settings.feature_promotions:
        raise ValidationError("Promotions feature is disabled", error_code="FEATURE_DISABLED")

    # Validate inputs
    if not order_id or not isinstance(order_id, str):
        raise ValidationError("order_id must be a non-empty string")
    if not coupon_code or not isinstance(coupon_code, str):
        raise ValidationError("coupon_code must be a non-empty string")

    try:
        result = await api_client.post(
            f"/api/v1/orders/{order_id}/coupons",
            data={"coupon_code": coupon_code},
        )

        logger.info(f"Coupon applied: order_id={order_id}, code={coupon_code}")
        return result
    except Exception as e:
        logger.error(f"Failed to apply coupon to order {order_id}: {str(e)}")
        raise


@promotions_mcp.tool
async def create_promotion(
    name: str,
    discount_type: str,
    discount_value: float,
    start_date: str,
    end_date: str,
    applicable_products: Optional[List[int]] = None,
    applicable_categories: Optional[List[str]] = None,
    max_uses: Optional[int] = None,
    customer_tiers: Optional[List[str]] = None,
    terms: Optional[str] = None,
) -> dict:
    """Create a new promotional campaign (admin).

    Args:
        name: Promotion name
        discount_type: Type (percentage, fixed_amount, buy_x_get_y, free_shipping)
        discount_value: Discount amount or percentage
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        applicable_products: Product IDs (all if omitted)
        applicable_categories: Category IDs
        max_uses: Maximum usage count
        customer_tiers: Customer tiers eligible
        terms: Terms and conditions

    Returns:
        dict with promotion_id, status, created_at

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_promotions:
        raise ValidationError("Promotions feature is disabled", error_code="FEATURE_DISABLED")

    try:
        from datetime import datetime
        from decimal import Decimal

        promotion_data = PromotionSchema(
            name=name,
            discount_type=discount_type,
            discount_value=Decimal(str(discount_value)),
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
            applicable_products=applicable_products,
            applicable_categories=applicable_categories,
            max_uses=max_uses,
            customer_tiers=customer_tiers,
            terms=terms,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "promotion"})

    try:
        result = await api_client.post(
            "/api/v1/promotions",
            data={
                "name": promotion_data.name,
                "discount_type": promotion_data.discount_type,
                "discount_value": float(promotion_data.discount_value),
                "start_date": promotion_data.start_date.isoformat(),
                "end_date": promotion_data.end_date.isoformat(),
                "applicable_products": promotion_data.applicable_products,
                "applicable_categories": promotion_data.applicable_categories,
                "max_uses": promotion_data.max_uses,
                "customer_tiers": promotion_data.customer_tiers,
                "terms": promotion_data.terms,
            },
        )

        logger.info(f"Promotion created: {result.get('promotion_id')} - {name}")
        return result
    except Exception as e:
        logger.error(f"Failed to create promotion {name}: {str(e)}")
        raise
