from fastmcp import FastMCP
from src.ecommerce_mcp.client import api_client

ticket_mcp = FastMCP(name="Ticket Tools")


@ticket_mcp.tool
async def get_tickets(
    limit: int = 100,
    offset: int = 0,
    customer_id: int | None = None,
    product_id: int | None = None,
) -> list[dict]:
    """Fetch a list of tickets from the Ecommerce API, optionally filtered.

    Args:
        limit (int): The maximum number of tickets to retrieve.
        offset (int): The number of tickets to skip.
        customer_id (int | None): Filter tickets by customer ID.
        product_id (int | None): Filter tickets by product ID.

    Returns:
        list[dict]: A list of ticket dictionaries.
    """
    params = {"limit": limit, "offset": offset}
    if customer_id is not None:
        params["customer_id"] = customer_id
    if product_id is not None:
        params["product_id"] = product_id
    return await api_client.get("/api/v1/tickets/", params=params)


@ticket_mcp.tool
async def get_ticket_by_id(ticket_id: int) -> dict:
    """Fetch a single ticket by ID.

    Args:
        ticket_id (int): The ID of the ticket to retrieve.

    Returns:
        dict: A dictionary representing the ticket.
    """
    return await api_client.get(f"/api/v1/tickets/{ticket_id}")


@ticket_mcp.tool
async def create_new_ticket(ticket_data: dict) -> dict:
    """Create a new ticket.

    Args:
        ticket_data (dict): A dictionary containing the ticket data.

    Returns:
        dict: A dictionary representing the newly created ticket.
    """
    return await api_client.post("/api/v1/tickets/", data=ticket_data)


@ticket_mcp.tool
async def update_existing_ticket(ticket_id: int, ticket_data: dict) -> dict:
    """Update an existing ticket.

    Args:
        ticket_id (int): The ID of the ticket to update.
        ticket_data (dict): A dictionary containing the updated ticket data.

    Returns:
        dict: A dictionary representing the updated ticket.
    """
    return await api_client.put(f"/api/v1/tickets/{ticket_id}", data=ticket_data)


@ticket_mcp.tool
async def delete_existing_ticket(ticket_id: int) -> dict:
    """Delete an existing ticket.

    Args:
        ticket_id (int): The ID of the ticket to delete.

    Returns:
        dict: A dictionary representing the result of the deletion.
    """
    return await api_client.delete(f"/api/v1/tickets/{ticket_id}")
