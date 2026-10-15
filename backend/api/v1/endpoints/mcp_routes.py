from typing import Dict, Any
from fastapi import APIRouter, Depends, Body
from backend.mcp.mcp_server import mcp_server
from backend.security.jwt_auth import get_current_user

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])

@router.get("/tools")
def list_mcp_tools(current_user: dict = Depends(get_current_user)):
    """Lists MCP tool specifications, JSON schemas, and authorization levels."""
    return {
        "server": "FinGuard MCP Server v1.0",
        "protocol": "Model Context Protocol",
        "tools": mcp_server.list_tools()
    }

@router.post("/tools/call")
def invoke_mcp_tool(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Executes an authorized MCP tool with strict input schema validation."""
    tool_name = payload.get("name")
    arguments = payload.get("arguments", {})
    if not tool_name:
        return {"error": "Missing 'name' field in payload", "status": "INVALID_REQUEST"}

    result = mcp_server.call_tool(
        name=tool_name,
        arguments=arguments,
        user_role=current_user["role"],
        username=current_user["username"]
    )
    return {"tool": tool_name, "result": result}
