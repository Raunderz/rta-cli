import os
import shutil
from typing import Optional, Dict
from pathlib import Path

from rta_cli.lsp.client import LSPClient
from rta_cli.discovery import discover_project

class LSPManager:
    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.root_uri = Path(self.workspace_path).as_uri()
        self.clients: Dict[str, LSPClient] = {}

    def get_client(self, language: str) -> Optional[LSPClient]:
        if language in self.clients:
            return self.clients[language]
        
        command = self._get_server_command(language)
        if not command:
            return None
            
        client = LSPClient(command, self.root_uri)
        if client.start():
            self.clients[language] = client
            return client
        return None

    def _get_server_command(self, language: str) -> Optional[list]:
        servers = {
            "python": [
                ["pyright-langserver", "--stdio"],
                ["basedpyright-langserver", "--stdio"],
                ["pylsp"]
            ],
            "javascript": [["typescript-language-server", "--stdio"]],
            "typescript": [["typescript-language-server", "--stdio"]],
            "go": [["gopls"]],
            "rust": [["rust-analyzer"]],
            "c": [["clangd"]],
            "cpp": [["clangd"]],
        }
        
        candidates = servers.get(language, [])
        for cmd in candidates:
            if shutil.which(cmd[0]):
                return cmd
        return None

    def stop_all(self):
        for client in self.clients.values():
            client.stop()
        self.clients.clear()

def path_to_uri(path: str) -> str:
    return Path(os.path.abspath(path)).as_uri()

def uri_to_path(uri: str) -> str:
    if uri.startswith("file://"):
        return uri[7:]
    return uri
