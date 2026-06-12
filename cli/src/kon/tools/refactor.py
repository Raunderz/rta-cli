import asyncio
import os
from typing import Literal

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool

try:
    import libcst as cst
    import libcst.matchers as m
except ImportError:
    cst = None
    m = None  # type: ignore


class RefactorParams(BaseModel):
    file_path: str = Field(..., description="Path to the Python file")
    action: Literal["rename_function", "rename_class"] = Field(
        ..., description="The refactoring action to perform"
    )
    old_name: str = Field(..., description="Current name of the entity")
    new_name: str = Field(..., description="New name for the entity")


class RefactorPythonTool(BaseTool[RefactorParams]):
    name = "refactor_python"
    params = RefactorParams
    description = "Perform AST-aware refactoring on a Python file (e.g., rename function, rename class). Much safer than manual text editing for renames."
    mutating = True
    tool_icon = "🏗️"

    async def execute(
        self, params: RefactorParams, cwd: str, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        if cst is None or m is None:
            return ToolResult(
                success=False, result="Error: libcst not installed. AST refactoring unavailable."
            )

        abs_path = os.path.abspath(os.path.join(cwd, params.file_path))
        if not os.path.exists(abs_path):
            return ToolResult(success=False, result=f"File {params.file_path} not found.")

        try:
            with open(abs_path, encoding="utf-8") as f:
                code = f.read()

            assert cst is not None
            assert m is not None
            module = cst.parse_module(code)
            new_code = code

            if params.action == "rename_function":

                class RenameTransformer(cst.CSTTransformer):
                    def leave_FunctionDef(self, original_node, updated_node):  # noqa: N802
                        if original_node.name.value == params.old_name:
                            return updated_node.with_changes(name=cst.Name(params.new_name))  # type: ignore
                        return updated_node

                    def leave_Call(self, original_node, updated_node):  # noqa: N802
                        if m.matches(original_node.func, m.Name(params.old_name)):  # type: ignore
                            return updated_node.with_changes(func=cst.Name(params.new_name))  # type: ignore
                        return updated_node

                new_module = module.visit(RenameTransformer())
                new_code = new_module.code

            elif params.action == "rename_class":

                class RenameClassTransformer(cst.CSTTransformer):
                    def leave_ClassDef(self, original_node, updated_node):  # noqa: N802
                        if original_node.name.value == params.old_name:
                            return updated_node.with_changes(name=cst.Name(params.new_name))  # type: ignore
                        return updated_node

                    def leave_Annotation(self, original_node, updated_node):  # noqa: N802
                        if m.matches(original_node.annotation, m.Name(params.old_name)):  # type: ignore
                            return updated_node.with_changes(annotation=cst.Name(params.new_name))  # type: ignore
                        return updated_node

                new_module = module.visit(RenameClassTransformer())
                new_code = new_module.code

            if new_code == code:
                return ToolResult(success=True, result="No changes were necessary.")

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_code)

            return ToolResult(
                success=True,
                result=f"Successfully applied {params.action} to {params.file_path}",
                ui_summary=f"Refactored {params.old_name} -> {params.new_name}",
            )
        except Exception as e:
            return ToolResult(success=False, result=f"Refactoring Error: {e}")

    def format_call(self, params: RefactorParams) -> str:
        return f"{params.action}: {params.old_name} -> {params.new_name}"
