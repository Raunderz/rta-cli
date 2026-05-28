import os
import logging
import asyncio
from typing import Optional

import httpx
import websockets
from fastapi import APIRouter, Depends, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from rta_backend.security import require_api_key

logger = logging.getLogger(__name__)

GO_BASE_URL = os.getenv("GO_EXECUTOR_URL", "http://localhost:8080")
CONNECT_TIMEOUT = float(os.getenv("EXECUTOR_CONNECT_TIMEOUT", "5.0"))
READ_TIMEOUT = float(os.getenv("EXECUTOR_READ_TIMEOUT", "60.0"))
ENV_CONNECT_TIMEOUT = float(os.getenv("EXECUTOR_ENV_CONNECT_TIMEOUT", "15.0"))

_http_client: Optional[httpx.AsyncClient] = None

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}

executor_router = APIRouter(prefix="/executor", tags=["executor"])


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=GO_BASE_URL,
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=READ_TIMEOUT, pool=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
    return _http_client


async def shutdown_http_client():
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def sanitize_path(path: str) -> str:
    normalized = "/" + path.lstrip("/") if path else "/"
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Invalid path: traversal denied")
    return normalized.lstrip("/")


def scrub_headers(headers: dict) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in SENSITIVE_HEADERS}


def get_timeout_for_path(path: str) -> httpx.Timeout:
    stripped = path.lstrip("/")
    if stripped.startswith("env") and not stripped.startswith("env/chat"):
        return httpx.Timeout(connect=ENV_CONNECT_TIMEOUT, read=READ_TIMEOUT, write=READ_TIMEOUT, pool=5.0)
    return httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=READ_TIMEOUT, pool=5.0)


@executor_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy_http(
    path: str,
    request: Request,
    user_id: str = Depends(require_api_key),
):
    safe_path = sanitize_path(path)
    client = get_http_client()
    timeout = get_timeout_for_path(safe_path)

    # Prepare headers for forwarding
    forward_headers = {}
    for k, v in request.headers.items():
        if k.lower() not in SENSITIVE_HEADERS:
            forward_headers[k] = v
    
    # Ensure critical headers are present with correct case for upstream
    if "x-api-key" in request.headers:
        forward_headers["X-API-KEY"] = request.headers["x-api-key"]
    if "ngrok-skip-browser-warning" in request.headers:
        forward_headers["ngrok-skip-browser-warning"] = request.headers["ngrok-skip-browser-warning"]

    forward_headers["X-User-Id"] = user_id

    is_streaming = (
        "stream" in request.headers.get("content-type", "").lower()
        or request.headers.get("transfer-encoding", "").lower() == "chunked"
    )

    try:
        if is_streaming:
            async def body_stream():
                async for chunk in request.stream():
                    yield chunk

            resp = await client.request(
                method=request.method,
                url=f"/{safe_path}",
                content=body_stream(),
                headers=forward_headers,
                timeout=timeout,
            )
        else:
            raw_body = await request.body()
            resp = await client.request(
                method=request.method,
                url=f"/{safe_path}",
                content=raw_body if raw_body else None,
                headers=forward_headers,
                timeout=timeout,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Executor upstream timed out")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Executor unavailable")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Executor upstream error")

    resp_headers = scrub_headers(dict(resp.headers))

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp_headers,
        media_type=resp.headers.get("content-type"),
    )


WS_GO_BASE = GO_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")


@executor_router.websocket("/ws/{path:path}")
async def proxy_websocket(websocket: WebSocket, path: str):
    safe_path = sanitize_path(path)
    await websocket.accept()

    upstream_ws_url = f"{WS_GO_BASE}/{safe_path}"

    try:
        async with websockets.connect(upstream_ws_url) as upstream_ws:
            async def mobile_to_go():
                try:
                    while True:
                        data = await websocket.receive()
                        if data["type"] == "websocket.receive":
                            if "text" in data and data["text"] is not None:
                                await upstream_ws.send(data["text"])
                            elif "bytes" in data and data["bytes"] is not None:
                                await upstream_ws.send(data["bytes"])
                except WebSocketDisconnect:
                    pass
                except Exception:
                    pass

            async def go_to_mobile():
                try:
                    async for message in upstream_ws:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except WebSocketDisconnect:
                    pass
                except Exception:
                    pass

            await asyncio.gather(mobile_to_go(), go_to_mobile())
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"Upstream WebSocket error: {e}")
        await websocket.send_json({"type": "error", "content": "Upstream WebSocket unavailable"})
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
