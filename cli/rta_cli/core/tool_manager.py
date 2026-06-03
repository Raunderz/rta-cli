import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from .tool_base import BaseTool
from .types import ToolCall, ToolResult

log = logging.getLogger("rta.tools")

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [{"type": "function", "function": t.get_schema()} for t in self.tools.values()]

    async def execute_call(
        self, 
        tool_call: ToolCall, 
        cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.debug import format_tool_error, is_debug

        name = tool_call.function.name
        if name not in self.tools:
            return ToolResult(success=False, result=f"Error: Tool '{name}' not found.")

        tool = self.tools[name]
        tool_input = None
        try:
            # Parse arguments using the tool's Pydantic model
            args_dict = json.loads(tool_call.function.arguments)
            tool_input = args_dict
            params = tool.parameters.model_validate(args_dict)
            
            # Execute
            return await tool.execute(params, cancel_event=cancel_event)
        except json.JSONDecodeError as e:
            log.warning("Tool '%s' received invalid JSON arguments: %s", name, e)
            return ToolResult(success=False, result=f"Error: Invalid JSON arguments for tool '{name}': {e}")
        except Exception as e:
            log.error("Tool '%s' failed: %s", name, e, exc_info=is_debug())
            return ToolResult(success=False, result=format_tool_error(name, e, tool_input))
