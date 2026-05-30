from __future__ import annotations
import asyncio
import os
import fnmatch
import glob
from typing import List, Optional
from pydantic import BaseModel, Field
from .tool_base import BaseTool
from .types import ToolResult

class ListDirParams(BaseModel):
    path: str = Field(description="Directory path to list", default=".")

class ListDirTool(BaseTool):
    name = "list_directory"
    description = "List files and directories in a given path."
    parameters = ListDirParams
    icon = "📁"

    async def execute(self, params: ListDirParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        try:
            path = params.path
            if not os.path.exists(path):
                return ToolResult(success=False, result=f"Error: Path '{path}' does not exist.")
            
            items = os.listdir(path)
            res = []
            for item in sorted(items):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    res.append(f"[DIR]  {item}")
                else:
                    res.append(f"[FILE] {item}")
            
            return ToolResult(success=True, result="\n".join(res) or "(empty directory)")
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {str(e)}")

class GrepParams(BaseModel):
    pattern: str = Field(description="Regex pattern to search for")
    path: str = Field(description="File or directory to search in", default=".")
    include: Optional[str] = Field(description="Glob pattern for files to include", default=None)

class GrepTool(BaseTool):
    name = "grep_search"
    description = "Search for a regex pattern in file contents."
    parameters = GrepParams
    icon = "🔍"

    async def execute(self, params: GrepParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        # Simple implementation for now, using grep if available or manual walk
        cmd = f"grep -rnE \"{params.pattern}\" {params.path}"
        if params.include:
            cmd += f" --include=\"{params.include}\""
        
        # We reuse the logic from a bash-like execution but simpler
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        res = stdout.decode() + stderr.decode()
        return ToolResult(success=True, result=res or "No matches found.")

class GlobParams(BaseModel):
    pattern: str = Field(description="Glob pattern (e.g. src/**/*.py)")

class GlobTool(BaseTool):
    name = "glob_search"
    description = "Find files matching a glob pattern."
    parameters = GlobParams
    icon = "🌐"

    async def execute(self, params: GlobParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        files = glob.glob(params.pattern, recursive=True)
        return ToolResult(success=True, result="\n".join(files) or "No files matched.")
