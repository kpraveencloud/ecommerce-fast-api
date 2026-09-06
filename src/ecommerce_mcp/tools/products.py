from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client

product_mcp = FastMCP(name="Product Tools")


@product_mcp.tool
async def get_products(limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch a list of products from the Ecommerce API.

    Args:
        limit (int): The maximum number of products to retrieve.
        offset (int): The number of products to skip.

    Returns:
        list[dict]: A list of product dictionaries.
    """
    return await api_client.get(
        "/api/v1/products/",
        params={"limit": limit, "offset": offset},
    )


@product_mcp.tool
async def get_product_by_id(product_id: int) -> dict:
    """Fetch a single product by ID.

    Args:
        product_id (int): The ID of the product to retrieve.

    Returns:
        dict: A dictionary representing the product.
    """
    return await api_client.get(f"/api/v1/products/{product_id}")


@product_mcp.tool
async def create_new_product(product_data: dict) -> dict:
    """Create a new product.

    Args:
        product_data (dict): A dictionary containing the product data.

    Returns:
        dict: A dictionary representing the newly created product.
    """
    return await api_client.post("/api/v1/products/", data=product_data)


@product_mcp.tool
async def update_existing_product(product_id: int, product_data: dict) -> dict:
    """Update an existing product.

    Args:
        product_id (int): The ID of the product to update.
        product_data (dict): A dictionary containing the updated product data.

    Returns:
        dict: A dictionary representing the updated product.
    """
    return await api_client.put(f"/api/v1/products/{product_id}", data=product_data)


@product_mcp.tool
async def delete_existing_product(product_id: int) -> dict:
    """Delete an existing product.

    Args:
        product_id (int): The ID of the product to delete.

    Returns:
        dict: A dictionary representing the result of the deletion.
    """
    return await api_client.delete(f"/api/v1/products/{product_id}")
