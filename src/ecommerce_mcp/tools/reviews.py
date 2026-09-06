from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client

review_mcp = FastMCP(name="Review Tools")


@review_mcp.tool
async def get_reviews(
    limit: int = 100,
    offset: int = 0,
    customer_id: int | None = None,
    product_id: int | None = None,
    order_id: int | None = None,
) -> list[dict]:
    """Fetch a list of reviews from the Ecommerce API, optionally filtered.

    Args:
        limit (int): The maximum number of reviews to retrieve.
        offset (int): The number of reviews to skip.
        customer_id (int | None): Filter reviews by customer ID.
        product_id (int | None): Filter reviews by product ID.
        order_id (int | None): Filter reviews by order ID.

    Returns:
        list[dict]: A list of review dictionaries.
    """
    params = {"limit": limit, "offset": offset}
    if customer_id is not None:
        params["customer_id"] = customer_id
    if product_id is not None:
        params["product_id"] = product_id
    if order_id is not None:
        params["order_id"] = order_id
    return await api_client.get("/api/v1/reviews/", params=params)


@review_mcp.tool
async def get_review_by_id(review_id: int) -> dict:
    """Fetch a single review by ID.

    Args:
        review_id (int): The ID of the review to retrieve.

    Returns:
        dict: A dictionary representing the review.
    """
    return await api_client.get(f"/api/v1/reviews/{review_id}")


@review_mcp.tool
async def create_new_review(review_data: dict) -> dict:
    """Create a new review.

    Args:
        review_data (dict): A dictionary containing the review data.

    Returns:
        dict: A dictionary representing the newly created review.
    """
    return await api_client.post("/api/v1/reviews/", data=review_data)


@review_mcp.tool
async def update_existing_review(review_id: int, review_data: dict) -> dict:
    """Update an existing review.

    Args:
        review_id (int): The ID of the review to update.
        review_data (dict): A dictionary containing the updated review data.

    Returns:
        dict: A dictionary representing the updated review.
    """
    return await api_client.put(f"/api/v1/reviews/{review_id}", data=review_data)


@review_mcp.tool
async def delete_existing_review(review_id: int) -> dict:
    """Delete an existing review.

    Args:
        review_id (int): The ID of the review to delete.

    Returns:
        dict: A dictionary representing the result of the deletion.
    """
    return await api_client.delete(f"/api/v1/reviews/{review_id}")
