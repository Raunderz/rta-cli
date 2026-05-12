import os
import time
from rta_cli.lsp.manager import LSPManager, path_to_uri, uri_to_path
from rta_cli.discovery import discover_project

# Global manager instance to keep servers alive during session
_lsp_manager = None

def _get_manager(workspace: str) -> LSPManager:
    global _lsp_manager
    if _lsp_manager is None or _lsp_manager.workspace_path != os.path.abspath(workspace):
        if _lsp_manager:
            _lsp_manager.stop_all()
        _lsp_manager = LSPManager(workspace)
    return _lsp_manager

def get_diagnostics(working_directory: str, file_path: str):
    """Get type errors and warnings for a file using LSP."""
    try:
        abs_path = os.path.abspath(os.path.join(working_directory, file_path))
        info = discover_project(working_directory)
        lang = info.get("language")
        if not lang:
            return "Error: Could not detect language for LSP."
            
        mgr = _get_manager(working_directory)
        client = mgr.get_client(lang)
        if not client:
            return f"Error: No LSP server found for {lang}. Install e.g. pyright-langserver for Python."

        uri = path_to_uri(abs_path)
        with open(abs_path, "r") as f:
            content = f.read()

        # Open file to trigger diagnostics
        client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": lang,
                "version": 1,
                "text": content
            }
        })
        
        # Wait for diagnostics (async notification)
        time.sleep(1) 
        
        relevant = [d for d in client._diagnostics if d["uri"] == uri]
        if not relevant:
            return "No diagnostics found."
            
        output = []
        for entry in relevant:
            for diag in entry.get("diagnostics", []):
                line = diag["range"]["start"]["line"] + 1
                msg = diag["message"]
                severity = "Error" if diag.get("severity") == 1 else "Warning"
                output.append(f"[{severity}] Line {line}: {msg}")
        
        return "\n".join(output) if output else "No issues found."
    except Exception as e:
        return f"Error getting diagnostics: {e}"

def go_to_definition(working_directory: str, file_path: str, line: int, character: int):
    """Find the definition of a symbol at a specific location."""
    try:
        abs_path = os.path.abspath(os.path.join(working_directory, file_path))
        info = discover_project(working_directory)
        lang = info.get("language")
        if not lang:
            return "Error: Could not detect language."

        mgr = _get_manager(working_directory)
        client = mgr.get_client(lang)
        if not client:
            return f"Error: No LSP server found for {lang}."

        uri = path_to_uri(abs_path)
        result = client.send_request("textDocument/definition", {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character}
        })

        if not result:
            return "Definition not found."

        # Result can be Location or Location[]
        if isinstance(result, list):
            result = result[0]
            
        target_uri = result["uri"]
        target_path = uri_to_path(target_uri)
        target_line = result["range"]["start"]["line"] + 1
        
        rel_target = os.path.relpath(target_path, working_directory)
        return f"Definition found in {rel_target} at line {target_line}"
    except Exception as e:
        return f"Error finding definition: {e}"

schema_get_diagnostics = {
    "name": "get_diagnostics",
    "description": "Returns type errors and warnings for a specific file. Useful for finding bugs and fixing lint errors.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file to check"}
        },
        "required": ["file_path"]
    }
}

schema_go_to_definition = {
    "name": "go_to_definition",
    "description": "Finds the location where a symbol (function, class, variable) is defined.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file containing the symbol"},
            "line": {"type": "integer", "description": "1-based line number"},
            "character": {"type": "integer", "description": "0-based character offset"}
        },
        "required": ["file_path", "line", "character"]
    }
}
