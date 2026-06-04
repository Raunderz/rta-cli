import os

try:
    import libcst as cst
    import libcst.matchers as m
except ImportError:
    cst = None


def edit_file_ast(working_directory, file_path, action, **kwargs):
    if cst is None:
        return "Error: libcst not installed. AST-aware refactoring unavailable."

    abs_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not os.path.exists(abs_path):
        return f"Error: File {file_path} not found."

    with open(abs_path, "r") as f:
        code = f.read()

    try:
        module = cst.parse_module(code)
    except Exception as e:
        return f"Error parsing file: {e}"

    if action == "rename_function":
        old_name = kwargs.get("old_name")
        new_name = kwargs.get("new_name")

        class RenameTransformer(cst.CSTTransformer):
            def leave_FunctionDef(self, original_node, updated_node):
                if original_node.name.value == old_name:
                    return updated_node.with_changes(name=cst.Name(new_name))
                return updated_node

            def leave_Call(self, original_node, updated_node):
                if m.matches(original_node.func, m.Name(old_name)):
                    return updated_node.with_changes(func=cst.Name(new_name))
                return updated_node

        new_module = module.visit(RenameTransformer())
        new_code = new_module.code

    elif action == "rename_class":
        old_name = kwargs.get("old_name")
        new_name = kwargs.get("new_name")

        class RenameClassTransformer(cst.CSTTransformer):
            def leave_ClassDef(self, original_node, updated_node):
                if original_node.name.value == old_name:
                    return updated_node.with_changes(name=cst.Name(new_name))
                return updated_node

            def leave_Annotation(self, original_node, updated_node):
                if m.matches(original_node.annotation, m.Name(old_name)):
                    return updated_node.with_changes(annotation=cst.Name(new_name))
                return updated_node

        new_module = module.visit(RenameClassTransformer())
        new_code = new_module.code

    else:
        return f"Error: Unknown action '{action}'"

    if new_code == code:
        return "No changes made."

    with open(abs_path, "w") as f:
        f.write(new_code)

    return f"Successfully applied {action} to {file_path}"


schema_edit_file_ast = {
    "name": "edit_file_ast",
    "description": "Perform AST-aware refactoring on a Python file (e.g., rename function, rename class).",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the Python file"},
            "action": {
                "type": "string",
                "enum": ["rename_function", "rename_class"],
                "description": "The refactoring action to perform",
            },
            "old_name": {"type": "string", "description": "Current name of the entity"},
            "new_name": {"type": "string", "description": "New name for the entity"},
        },
        "required": ["file_path", "action", "old_name", "new_name"],
    },
}
