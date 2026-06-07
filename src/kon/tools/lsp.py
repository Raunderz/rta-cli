import asyncio
import os

from pydantic import BaseModel, Field

from ..context.project import discover_project
from ..core.types import ToolResult
from ..lsp.manager import LSPManager, path_to_uri, uri_to_path
from .base import BaseTool

# Global manager instance
_lsp_manager: LSPManager | None = None


def _get_manager(workspace: str) -> LSPManager:
    global _lsp_manager
    workspace_abs = os.path.abspath(workspace)
    if _lsp_manager is None or _lsp_manager.workspace_path != workspace_abs:
        if _lsp_manager:
            _lsp_manager.stop_all()
        _lsp_manager = LSPManager(workspace_abs)
    return _lsp_manager


class GetDiagnosticsParams(BaseModel):
    file_path: str = Field(..., description="Path to the file to check for errors and warnings")


class GoToDefinitionParams(BaseModel):
    file_path: str = Field(..., description="Path to the file containing the symbol")
    line: int = Field(..., description="1-based line number of the symbol")
    character: int = Field(..., description="0-based character offset within the line")


class GetDiagnosticsTool(BaseTool[GetDiagnosticsParams]):
    name = "get_diagnostics"
    params = GetDiagnosticsParams
    description = "Returns type errors and warnings for a specific file using LSP. Useful for finding bugs and fixing lint errors."
    mutating = False
    tool_icon = "⚠️"

    async def execute(
        self, params: GetDiagnosticsParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        cwd = os.getcwd()
        abs_path = os.path.abspath(os.path.join(cwd, params.file_path))
        if not os.path.exists(abs_path):
            return ToolResult(success=False, result=f"File not found: {params.file_path}")

        info = discover_project(cwd)
        lang = info.language
        if not lang:
            return ToolResult(success=False, result="Could not detect language for LSP.")

        mgr = _get_manager(cwd)
        client = mgr.get_client(lang)
        if not client:
            return ToolResult(success=False, result=f"No LSP server found for {lang}.")

        uri = path_to_uri(abs_path)
        try:
            with open(abs_path) as f:
                content = f.read()

            client.send_notification(
                "textDocument/didOpen",
                {"textDocument": {"uri": uri, "languageId": lang, "version": 1, "text": content}},
            )

            # Wait for diagnostics
            await asyncio.sleep(1)
            relevant = [d for d in client._diagnostics if d["uri"] == uri]
            if not relevant:
                return ToolResult(success=True, result="No diagnostics found.")

            output = []
            for entry in relevant:
                for diag in entry.get("diagnostics", []):
                    line = diag["range"]["start"]["line"] + 1
                    msg = diag["message"]
                    severity = "Error" if diag.get("severity") == 1 else "Warning"
                    output.append(f"[{severity}] Line {line}: {msg}")

            res_text = "\n".join(output) if output else "No issues found."
            return ToolResult(
                success=True,
                result=res_text,
                ui_summary=f"Found {len(output)} issues" if output else "No issues found",
            )
        except Exception as e:
            return ToolResult(success=False, result=f"LSP Error: {e}")


class GoToDefinitionTool(BaseTool[GoToDefinitionParams]):
    name = "go_to_definition"
    params = GoToDefinitionParams
    description = "Finds the location where a symbol (function, class, variable) is defined."
    mutating = False
    tool_icon = "📍"

    async def execute(
        self, params: GoToDefinitionParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        cwd = os.getcwd()
        abs_path = os.path.abspath(os.path.join(cwd, params.file_path))

        info = discover_project(cwd)
        lang = info.language
        if not lang:
            return ToolResult(success=False, result="Could not detect language.")

        mgr = _get_manager(cwd)
        client = mgr.get_client(lang)
        if not client:
            return ToolResult(success=False, result=f"No LSP server found for {lang}.")

        uri = path_to_uri(abs_path)
        try:
            result = client.send_request(
                "textDocument/definition",
                {
                    "textDocument": {"uri": uri},
                    "position": {"line": params.line - 1, "character": params.character},
                },
            )

            if not result:
                return ToolResult(success=True, result="Definition not found.")

            if isinstance(result, list):
                if not result:
                    return ToolResult(success=True, result="Definition not found.")
                result = result[0]

            target_uri = result["uri"]
            target_path = uri_to_path(target_uri)
            target_line = result["range"]["start"]["line"] + 1

            rel_target = os.path.relpath(target_path, cwd)
            return ToolResult(
                success=True,
                result=f"Definition found in {rel_target} at line {target_line}",
                ui_summary=f"Found in {rel_target}:{target_line}",
            )
        except Exception as e:
            return ToolResult(success=False, result=f"LSP Error: {e}")
