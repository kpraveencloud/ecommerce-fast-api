from fastmcp import FastMCP
from src.ecommerce_mcp.tools.customers import customer_mcp
from src.ecommerce_mcp.tools.orders import order_mcp
from src.ecommerce_mcp.tools.products import product_mcp
from src.ecommerce_mcp.tools.reviews import review_mcp
from src.ecommerce_mcp.tools.tickets import ticket_mcp
from src.ecommerce_mcp.tools.payments import payment_mcp
from src.ecommerce_mcp.tools.shipping import shipping_mcp
from src.ecommerce_mcp.tools.inventory import inventory_mcp
from src.ecommerce_mcp.tools.search import search_mcp

mcp = FastMCP(
    name="Ecommerce MCP",
    version="0.2.0",
)

# Core tools (existing)
mcp.mount(customer_mcp)
mcp.mount(order_mcp)
mcp.mount(product_mcp)
mcp.mount(review_mcp)
mcp.mount(ticket_mcp)

# Phase 2 tools (new)
mcp.mount(payment_mcp)
mcp.mount(shipping_mcp)
mcp.mount(inventory_mcp)
mcp.mount(search_mcp)

if __name__ == "__main__":
    mcp.run()
