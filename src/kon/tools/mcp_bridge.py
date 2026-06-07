import asyncio
import json
from typing import Any

from pydantic import BaseModel, Field, create_model

from ..core.types import ToolResult
from ..mcp import call_mcp_tool, list_mcp_tools, load_mcp_config
from .base import BaseTool


class MCPTool(BaseTool[BaseModel]):
    def __init__(self, server_name: str, mcp_tool_def: dict):
        self.server_name = server_name
        self.mcp_name = mcp_tool_def["name"]
        self.name = f"mcp_{server_name}_{self.mcp_name}"
        self.description = mcp_tool_def.get("description", "")
        self.tool_icon = "🔌"
        self.mutating = True  # Assume mutating for safety

        # Build pydantic model from inputSchema
        schema = mcp_tool_def.get("inputSchema", {"type": "object", "properties": {}})
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        fields = {}
        for prop_name, prop_def in properties.items():
            field_type: Any = Any
            if prop_def.get("type") == "string":
                field_type = str
            elif prop_def.get("type") == "integer":
                field_type = int
            elif prop_def.get("type") == "boolean":
                field_type = bool
            elif prop_def.get("type") == "number":
                field_type = float

            default = ... if prop_name in required else None
            fields[prop_name] = (
                field_type,
                Field(default, description=prop_def.get("description", "")),
            )

        self.params = create_model(f"{self.name}_Params", **fields)

    async def execute(
        self, params: BaseModel, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        args = params.model_dump(exclude_none=True)
        try:
            # MCP calls are usually fast but can be slow, run in executor if stdio
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, call_mcp_tool, self.server_name, self.mcp_name, args
            )

            if not res:
                return ToolResult(success=True, result="Tool executed successfully (no output).")

            if isinstance(res, dict) and "error" in res:
                return ToolResult(success=False, result=f"MCP Error: {res['error']}")

            # MCP result is usually { content: [{type: 'text', text: '...'}] }
            if isinstance(res, dict) and "content" in res:
                parts = []
                for item in res["content"]:
                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))
                res_text = "\n".join(parts)
            else:
                res_text = json.dumps(res, indent=2)

            return ToolResult(success=True, result=res_text, ui_summary=f"Executed {self.name}")
        except Exception as e:
            return ToolResult(success=False, result=f"MCP Bridge Error: {e}")


def get_all_mcp_tools() -> list[BaseTool]:
    tools = []
    config = load_mcp_config()
    servers = config.get("mcpServers", {})
    for server_name in servers:
        try:
            mcp_tools = list_mcp_tools(server_name)
            for t_def in mcp_tools:
                tools.append(MCPTool(server_name, t_def))
        except Exception:
            continue
    return tools
