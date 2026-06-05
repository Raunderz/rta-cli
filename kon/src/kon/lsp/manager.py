import os
import shutil
import logging
from typing import Optional, Dict
from pathlib import Path

from .client import LSPClient

log = logging.getLogger("kon.lsp")


class LSPManager:
    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.root_uri = Path(self.workspace_path).as_uri()
        self.clients: Dict[str, LSPClient] = {}
        self._restart_counts: Dict[str, int] = {}
        self._max_restarts = 3

    def get_client(self, language: str) -> Optional[LSPClient]:
        if language in self.clients:
            client = self.clients[language]
            if client.is_alive():
                return client
            # Client died — attempt restart
            log.warning("LSP server for '%s' died, attempting restart...", language)
            return self._restart_client(language)

        command = self._get_server_command(language)
        if not command:
            return None

        client = LSPClient(command, self.root_uri)
        if client.start():
            self.clients[language] = client
            self._restart_counts[language] = 0
            return client
        return None

    def _restart_client(self, language: str) -> Optional[LSPClient]:
        count = self._restart_counts.get(language, 0)
        if count >= self._max_restarts:
            log.error(
                "LSP server for '%s' crashed %d times, giving up.", language, count
            )
            return None

        self._restart_counts[language] = count + 1
        client = self.clients.get(language)
        if client:
            client.restart()
            if client.is_alive():
                log.info("LSP server for '%s' restarted successfully.", language)
                return client
        return None

    def _get_server_command(self, language: str) -> Optional[list]:
        servers = {
            "python": [
                ["pyright-langserver", "--stdio"],
                ["basedpyright-langserver", "--stdio"],
                ["pylsp"],
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
