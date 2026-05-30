import asyncio
import os
from typing import Optional
from pydantic import BaseModel, Field
from .tool_base import BaseTool
from .types import ToolResult

class GetDiagnosticsParams(BaseModel):
    file_path: str = Field(description="Path to the file to check for errors and warnings")

class GoToDefinitionParams(BaseModel):
    file_path: str = Field(description="Path to the file containing the symbol")
    line: int = Field(description="1-based line number of the symbol")
    character: int = Field(description="0-based character offset within the line")

class GetDiagnosticsTool(BaseTool):
    name = "get_diagnostics"
    description = "Returns type errors and warnings for a specific file. Useful for finding bugs and fixing lint errors."
    parameters = GetDiagnosticsParams
    icon = "!"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(self, params: GetDiagnosticsParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        from rta_cli.functions.lsp_tools import get_diagnostics as sync_get_diagnostics
        try:
            result = await asyncio.to_thread(sync_get_diagnostics, self.working_directory, params.file_path)
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error getting diagnostics: {e}")

class GoToDefinitionTool(BaseTool):
    name = "go_to_definition"
    description = "Finds the location where a symbol (function, class, variable) is defined."
    parameters = GoToDefinitionParams
    icon = "->"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(self, params: GoToDefinitionParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        from rta_cli.functions.lsp_tools import go_to_definition as sync_go_to_definition
        try:
            result = await asyncio.to_thread(sync_go_to_definition, self.working_directory, params.file_path, params.line, params.character)
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error finding definition: {e}")
