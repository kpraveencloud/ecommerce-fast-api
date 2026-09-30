"""Serve the ecommerce MCP protocol and existing REST endpoints."""

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
import uvicorn

from src.ecommerce_mcp.main import mcp
from src.ecommerce_mcp.config import settings


# Create the Streamable HTTP MCP endpoint and initialize its session manager
# through the parent application's lifespan.
mcp_http_app = mcp.http_app(path="/mcp")

app = FastAPI(
    title="Ecommerce MCP HTTP Server",
    version="0.1.0",
    lifespan=mcp_http_app.lifespan,
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "Ecommerce MCP HTTP Server is running"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    return {"status": "ready", "message": "Ecommerce MCP HTTP Server is ready to serve requests"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools through the existing REST interface."""
    try:
        tools = await mcp.list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in tools
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, args: Dict[str, Any]):
    """Call a specific MCP tool through the existing REST interface."""
    try:
        result = await mcp.call_tool(tool_name, args)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tool call failed: {str(e)}") from e


@app.post("/call")
async def call_tool_from_body(request_body: Dict[str, Any]):
    """Call a tool via a request body containing 'tool' and 'args' keys."""
    try:
        tool_name = request_body.get("tool")
        args = request_body.get("args", {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing 'tool' parameter")

        result = await mcp.call_tool(tool_name, args)
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tool call failed: {str(e)}") from e


# Mount last so the REST routes above take priority. The child application
# defines /mcp, giving the final endpoint http://localhost:8005/mcp.
app.mount("/", mcp_http_app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
