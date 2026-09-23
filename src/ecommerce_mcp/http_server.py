import asyncio
import json
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from src.ecommerce_mcp.main import mcp

app = FastAPI(title="Ecommerce MCP HTTP Server", version="0.1.0")

# Store tool information when the app starts
TOOLS_REGISTRY: Dict[str, Any] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize tools registry on startup."""
    # Get all tools from MCP server
    try:
        # Access mcp's tools
        if hasattr(mcp, "list_tools"):
            tools = await mcp.list_tools()
            for tool in tools:
                TOOLS_REGISTRY[tool.name] = tool
    except Exception as e:
        print(f"Error loading tools: {e}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "Ecommerce MCP HTTP Server is running"}


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, args: Dict[str, Any]):
    """Call a specific MCP tool with arguments."""
    try:
        result = await mcp.call_tool(tool_name, args)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tool call failed: {str(e)}")


@app.post("/call")
async def call_tool_from_body(request_body: Dict[str, Any]):
    """Call a tool via request body containing 'tool' and 'args' keys."""
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
        raise HTTPException(status_code=400, detail=f"Tool call failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
