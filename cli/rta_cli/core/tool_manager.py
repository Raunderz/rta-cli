import json
import asyncio
from typing import Dict, List, Any, Optional
from .tool_base import BaseTool
from .types import ToolCall, ToolResult

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
        name = tool_call.function.name
        if name not in self.tools:
            return ToolResult(success=False, result=f"Error: Tool '{name}' not found.")

        tool = self.tools[name]
        try:
            # Parse arguments using the tool's Pydantic model
            args_dict = json.loads(tool_call.function.arguments)
            params = tool.parameters.model_validate(args_dict)
            
            # Execute
            return await tool.execute(params, cancel_event=cancel_event)
        except Exception as e:
            return ToolResult(success=False, result=f"Error executing tool '{name}': {str(e)}")
