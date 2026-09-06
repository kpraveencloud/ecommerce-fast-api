from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client

customer_mcp = FastMCP(name="Customer Tools")


@customer_mcp.tool
async def get_customers(limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch a list of customers from the Ecommerce API.

    Args:
        limit (int): The maximum number of customers to retrieve.
        offset (int): The number of customers to skip.

    Returns:
        list[dict]: A list of customer dictionaries.
    """
    return await api_client.get(
        "/api/v1/customers",
        params={"limit": limit, "offset": offset},
    )


@customer_mcp.tool
async def get_customer_by_id(customer_id: str) -> dict:
    """Fetch a single customer by ID.

    Args:
        customer_id (str): The ID of the customer to retrieve.

    Returns:
        dict: A dictionary representing the customer.
    """
    return await api_client.get(f"/api/v1/customers/{customer_id}")


@customer_mcp.tool
async def create_new_customer(customer_data: dict) -> dict:
    """Create a new customer.

    Args:
        customer_data (dict): A dictionary containing the customer data.

    Returns:
        dict: A dictionary representing the newly created customer.
    """
    return await api_client.post("/api/v1/customers/", data=customer_data)


@customer_mcp.tool
async def update_existing_customer(customer_id: str, customer_data: dict) -> dict:
    """Update an existing customer.

    Args:
        customer_id (str): The ID of the customer to update.
        customer_data (dict): A dictionary containing the updated customer data.

    Returns:
        dict: A dictionary representing the updated customer.
    """
    return await api_client.put(f"/api/v1/customers/{customer_id}", data=customer_data)


@customer_mcp.tool
async def delete_existing_customer(customer_id: str) -> dict:
    """Delete an existing customer.

    Args:
        customer_id (str): The ID of the customer to delete.

    Returns:
        dict: A dictionary representing the result of the deletion.
    """
    return await api_client.delete(f"/api/v1/customers/{customer_id}")
