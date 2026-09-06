from fastmcp import FastMCP
from src.ecommerce_mcp.tools.customers import customer_mcp
from src.ecommerce_mcp.tools.orders import order_mcp
from src.ecommerce_mcp.tools.products import product_mcp
from src.ecommerce_mcp.tools.reviews import review_mcp
from src.ecommerce_mcp.tools.tickets import ticket_mcp

mcp = FastMCP(
    name="Ecommerce MCP",
    version="0.1.0",
)

mcp.mount(customer_mcp)
mcp.mount(order_mcp)
mcp.mount(product_mcp)
mcp.mount(review_mcp)
mcp.mount(ticket_mcp)

if __name__ == "__main__":
    mcp.run()
