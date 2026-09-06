# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An MCP (Model Context Protocol) server that exposes e-commerce API operations as tools. Built with FastMCP, it acts as a bridge between MCP clients (like VS Code, Claude Desktop) and a FastAPI backend service.

## Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run python -m src.ecommerce_mcp.main

# Run a specific module directly
python -m src.ecommerce_mcp.main
```

No test suite or linter is configured yet.

## Architecture

```
MCP Client (VS Code/Claude) → FastMCP Server (this project) → FastAPI Backend (external)
```

**Three-layer design:**

1. **`main.py`** — FastMCP server definition and tool registration. Each tool is an async function decorated by FastMCP that delegates to the tools layer. This is the entry point (`mcp.run()`).

2. **`tools/customers.py`** — API operation functions. Each function maps to one REST endpoint on the backend (`/api/v1/customers/...`). Uses the shared `api_client` singleton from the client layer.

3. **`client.py`** — Async HTTP client wrapper around `httpx`. Provides `get/post/put/delete` methods with configured timeouts. Exposes a module-level `api_client` singleton that all tools import.

**Configuration** (`config.py`): Pydantic Settings loading from `.env`. Key setting is `fastapi_base_url` (defaults to `http://localhost:8000`).

## Key Patterns

- All tool functions are async — FastMCP requires this
- HTTP client is a singleton (`api_client`) instantiated at module level in `client.py`
- Tool functions in `tools/` return raw API response data; `main.py` tools handle the MCP interface
- Configuration is environment-driven via `.env` file and Pydantic Settings
- Backend API follows RESTful conventions at `/api/v1/customers`
