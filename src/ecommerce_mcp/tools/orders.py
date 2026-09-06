from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client

order_mcp = FastMCP(name="Order Tools")


@order_mcp.tool
async def get_orders(limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch a list of orders from the Ecommerce API.

    Args:
        limit (int): The maximum number of orders to retrieve.
        offset (int): The number of orders to skip.

    Returns:
        list[dict]: A list of order dictionaries.
    """
    return await api_client.get(
        "/api/v1/orders/",
        params={"limit": limit, "offset": offset},
    )


@order_mcp.tool
async def get_order_by_id(order_id: int) -> dict:
    """Fetch a single order by ID.

    Args:
        order_id (int): The ID of the order to retrieve.

    Returns:
        dict: A dictionary representing the order.
    """
    return await api_client.get(f"/api/v1/orders/{order_id}")


@order_mcp.tool
async def create_new_order(order_data: dict) -> dict:
    """Create a new order.

    Args:
        order_data (dict): A dictionary containing the order data.

    Returns:
        dict: A dictionary representing the newly created order.
    """
    return await api_client.post("/api/v1/orders/", data=order_data)


@order_mcp.tool
async def update_existing_order(order_id: int, order_data: dict) -> dict:
    """Update an existing order.

    Args:
        order_id (int): The ID of the order to update.
        order_data (dict): A dictionary containing the updated order data.

    Returns:
        dict: A dictionary representing the updated order.
    """
    return await api_client.put(f"/api/v1/orders/{order_id}", data=order_data)


@order_mcp.tool
async def delete_existing_order(order_id: int) -> dict:
    """Delete an existing order.

    Args:
        order_id (int): The ID of the order to delete.

    Returns:
        dict: A dictionary representing the result of the deletion.
    """
    return await api_client.delete(f"/api/v1/orders/{order_id}")
