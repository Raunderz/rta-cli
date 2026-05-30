import json
from typing import Any, Dict, Type, Optional
from pydantic import create_model, BaseModel
from .tool_base import BaseTool
from .types import ToolResult
from rta_cli.mcp import call_mcp_tool

class MCPToolWrapper(BaseTool):
    def __init__(self, server_name: str, mcp_tool_def: dict):
        self.server_name = server_name
        self.mcp_name = mcp_tool_def["name"]
        self.name = f"mcp_{server_name}_{self.mcp_name}"
        self.description = mcp_tool_def.get("description", "")
        self.icon = "🧩"
        
        # Create a dynamic Pydantic model from MCP inputSchema
        schema = mcp_tool_def.get("inputSchema", {"type": "object", "properties": {}})
        self.parameters = self._schema_to_pydantic(schema)

    def _schema_to_pydantic(self, schema: dict) -> Type[BaseModel]:
        # Very simple conversion, enough for basic tools
        props = schema.get("properties", {})
        fields = {}
        for name, prop in props.items():
            # For now, we just use 'Any' for simplicity in dynamic conversion
            # A more robust version would map types properly
            fields[name] = (Any, ...)
        
        return create_model(f"{self.name}_params", **fields)

    async def execute(self, params: Any, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        # call_mcp_tool is currently sync stdio, so we run in thread
        import asyncio
        args = params.model_dump()
        
        try:
            result = await asyncio.to_thread(
                call_mcp_tool, self.server_name, self.mcp_name, args
            )
            
            if "error" in result:
                return ToolResult(success=False, result=str(result["error"]))
            
            # MCP results usually have a 'content' field
            content = result.get("content", [])
            text_res = ""
            for item in content:
                if item.get("type") == "text":
                    text_res += item.get("text", "")
            
            return ToolResult(success=True, result=text_res or str(result))
        except Exception as e:
            return ToolResult(success=False, result=f"MCP Error: {str(e)}")

import asyncio
