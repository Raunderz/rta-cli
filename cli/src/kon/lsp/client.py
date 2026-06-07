import contextlib
import json
import os
import subprocess
import threading
import time
from typing import Any


class LSPClient:
    def __init__(self, command: list[str], root_uri: str):
        self.command = command
        self.root_uri = root_uri
        self.process: subprocess.Popen | None = None
        self.request_id = 1
        self._responses: dict[int, Any] = {}
        self._diagnostics: list[Any] = []
        self._running = False

    def is_alive(self) -> bool:
        return self._running and self.process is not None and self.process.poll() is None

    def start(self) -> bool:
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0,
            )
            self._running = True
            self._responses.clear()
            threading.Thread(target=self._read_loop, daemon=True).start()

            # Initialize
            res = self.send_request(
                "initialize",
                {"processId": os.getpid(), "rootUri": self.root_uri, "capabilities": {}},
            )
            if res:
                self.send_notification("initialized", {})
                return True
        except Exception:
            pass
        return False

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def stop(self):
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                with contextlib.suppress(Exception):
                    self.process.kill()
            self.process = None

    def _send(self, data: dict[str, Any]):
        if not self.process or not self.process.stdin:
            return
        body = json.dumps(data).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        try:
            self.process.stdin.write(header + body)
            self.process.stdin.flush()
        except Exception:
            self._running = False

    def send_request(self, method: str, params: dict[str, Any], timeout: int = 5) -> Any | None:
        curr_id = self.request_id
        self.request_id += 1
        self._send({"jsonrpc": "2.0", "id": curr_id, "method": method, "params": params})

        start_time = time.time()
        while time.time() - start_time < timeout:
            if curr_id in self._responses:
                return self._responses.pop(curr_id)
            time.sleep(0.1)
        return None

    def send_notification(self, method: str, params: dict[str, Any]):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _read_loop(self):
        while self._running and self.process and self.process.stdout:
            try:
                line = self.process.stdout.readline().decode("ascii")
                if not line.startswith("Content-Length:"):
                    continue
                length = int(line.split(":")[1].strip())
                self.process.stdout.readline()  # \r\n
                body = self.process.stdout.read(length).decode("utf-8")
                data = json.loads(body)

                if "id" in data:
                    self._responses[data["id"]] = data.get("result") or data.get("error")
                elif "method" in data and data["method"] == "textDocument/publishDiagnostics":
                    self._diagnostics.append(data["params"])
            except Exception:
                break
