"""Product search and navigation tools."""

import logging
from typing import Optional, List
from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client
from src.ecommerce_mcp.utils import (
    SearchProductsSchema,
    ValidationError,
    format_success_response,
    format_paginated_response,
)
from src.ecommerce_mcp.config import settings

logger = logging.getLogger(__name__)

search_mcp = FastMCP(name="Search Tools")


@search_mcp.tool
async def search_products(
    query: str,
    categories: Optional[List[str]] = None,
    price_range: Optional[dict] = None,
    rating_min: Optional[float] = None,
    in_stock_only: bool = True,
    brands: Optional[List[str]] = None,
    sort_by: str = "relevance",
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Full-text and faceted search across products.

    Args:
        query: Search query (full-text, supports boolean operators)
        categories: Filter by category IDs
        price_range: Filter by price with min, max keys (as floats)
        rating_min: Minimum rating (0-5)
        in_stock_only: Filter to in-stock items only
        brands: Filter by brand names
        sort_by: Sort order (relevance, price_asc, price_desc, rating, newest, popularity)
        limit: Maximum results (default: 20, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        dict with results array, total_count, and facets (category, price_ranges, brands, ratings)

    Raises:
        ValidationError: If input validation fails
    """
    if not settings.feature_search:
        raise ValidationError("Search feature is disabled", error_code="FEATURE_DISABLED")

    try:
        # Convert price_range to Decimal if provided
        from decimal import Decimal
        processed_price_range = None
        if price_range:
            processed_price_range = {
                "min": Decimal(str(price_range["min"])) if price_range.get("min") else None,
                "max": Decimal(str(price_range["max"])) if price_range.get("max") else None,
            }

        # Validate input
        search_data = SearchProductsSchema(
            query=query,
            categories=categories,
            price_range=processed_price_range,
            rating_min=rating_min,
            in_stock_only=in_stock_only,
            brands=brands,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )
    except ValueError as e:
        raise ValidationError(str(e), {"field": "search"})

    params = {
        "q": search_data.query,
        "sort_by": search_data.sort_by,
        "limit": search_data.limit,
        "offset": search_data.offset,
        "in_stock_only": search_data.in_stock_only,
    }

    if search_data.categories:
        params["categories"] = ",".join(search_data.categories)

    if search_data.price_range and (search_data.price_range.min or search_data.price_range.max):
        if search_data.price_range.min:
            params["price_min"] = float(search_data.price_range.min)
        if search_data.price_range.max:
            params["price_max"] = float(search_data.price_range.max)

    if search_data.rating_min:
        params["rating_min"] = search_data.rating_min

    if search_data.brands:
        params["brands"] = ",".join(search_data.brands)

    try:
        result = await api_client.get(
            "/api/v1/search/products",
            params=params,
            cache=True,
            timeout=settings.search_timeout,
        )

        logger.info(f"Product search executed: query='{query}', results={len(result.get('results', []))}")
        return result
    except Exception as e:
        logger.error(f"Product search failed: query='{query}', error={str(e)}")
        raise


@search_mcp.tool
async def get_product_recommendations(
    based_on: str,
    id: str,
    recommendation_type: Optional[str] = None,
    limit: int = 10,
) -> dict:
    """Get recommended products based on product or customer.

    Args:
        based_on: Recommendation type (product_id, customer_id)
        id: Product or customer ID
        recommendation_type: Type of recommendation (similar, complementary,
                           trending_in_category, frequently_bought_together)
        limit: Number of recommendations (default: 10, max: 50)

    Returns:
        list of dicts with product_id, name, price, match_score, reason

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If product or customer not found
    """
    if not settings.feature_search:
        raise ValidationError("Search feature is disabled", error_code="FEATURE_DISABLED")

    # Validate inputs
    if based_on not in ["product_id", "customer_id"]:
        raise ValidationError("based_on must be 'product_id' or 'customer_id'")

    if not id or not isinstance(id, str):
        raise ValidationError(f"{based_on} must be a non-empty string")

    if limit < 1 or limit > 50:
        raise ValidationError("limit must be between 1 and 50")

    # Validate recommendation_type if provided
    valid_types = ["similar", "complementary", "trending_in_category", "frequently_bought_together"]
    if recommendation_type and recommendation_type not in valid_types:
        raise ValidationError(f"recommendation_type must be one of: {', '.join(valid_types)}")

    params = {
        "based_on": based_on,
        "id": id,
        "limit": limit,
    }

    if recommendation_type:
        params["recommendation_type"] = recommendation_type

    try:
        result = await api_client.get(
            "/api/v1/recommendations",
            params=params,
            cache=True,
            timeout=settings.search_timeout,
        )

        logger.info(f"Recommendations retrieved: {based_on}={id}, count={len(result.get('data', []))}")
        return result
    except Exception as e:
        logger.error(f"Failed to get recommendations for {based_on}={id}: {str(e)}")
        raise


@search_mcp.tool
async def get_categories(
    parent_category: Optional[str] = None,
    include_product_count: bool = False,
) -> dict:
    """Retrieve product category hierarchy.

    Args:
        parent_category: Filter to subcategories of parent
        include_product_count: Include product count per category

    Returns:
        list of dicts with category_id, name, parent_id, description,
        product_count (if requested), children (nested subcategories)

    Raises:
        ValidationError: If input validation fails
        NotFoundError: If parent category not found
    """
    if not settings.feature_search:
        raise ValidationError("Search feature is disabled", error_code="FEATURE_DISABLED")

    params = {
        "include_product_count": include_product_count,
    }

    if parent_category:
        if not isinstance(parent_category, str) or not parent_category.strip():
            raise ValidationError("parent_category must be a non-empty string")
        params["parent"] = parent_category

    try:
        result = await api_client.get(
            "/api/v1/categories",
            params=params,
            cache=True,
            timeout=settings.search_timeout,
        )

        category_count = len(result.get('data', [])) if isinstance(result.get('data'), list) else 1
        logger.info(f"Categories retrieved: count={category_count}")
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve categories: {str(e)}")
        raise
