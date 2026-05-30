import asyncio
import difflib
import aiofiles
from typing import Optional
from pydantic import BaseModel, Field
from .tool_base import BaseTool
from .types import ToolResult

class EditParams(BaseModel):
    path: str = Field(description="Relative path to the file to edit")
    old_string: str = Field(description="Exact text to find and replace")
    new_string: str = Field(description="New text to replace old_string with")

class EditTool(BaseTool):
    name = "edit"
    description = "Surgically edit a file by replacing exact text blocks. Provides a diff preview."
    parameters = EditParams
    icon = "✏️"

    async def execute(self, params: EditParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        try:
            if not await self._file_exists(params.path):
                return ToolResult(success=False, result=f"Error: File '{params.path}' not found.")

            async with aiofiles.open(params.path, mode='r') as f:
                old_content = await f.read()

            if params.old_string not in old_content:
                return ToolResult(success=False, result=f"Error: 'old_string' not found in {params.path}.")

            new_content = old_content.replace(params.old_string, params.new_string, 1)

            async with aiofiles.open(params.path, mode='w') as f:
                await f.write(new_content)

            # Generate diff for UI
            diff = self._generate_diff(params.path, old_content, new_content)

            return ToolResult(
                success=True,
                result=f"Successfully edited {params.path}",
                ui_details=diff
            )

        except Exception as e:
            return ToolResult(success=False, result=f"Error: {str(e)}")

    async def _file_exists(self, path: str) -> bool:
        return await asyncio.to_thread(lambda: os.path.isfile(path))

    def _generate_diff(self, path: str, old: str, new: str) -> str:
        diff = difflib.unified_diff(
            old.splitlines(), 
            new.splitlines(), 
            fromfile=f"a/{path}", 
            tofile=f"b/{path}",
            lineterm=""
        )
        return "\n".join(diff)

import os # Needed for os.path.isfile
