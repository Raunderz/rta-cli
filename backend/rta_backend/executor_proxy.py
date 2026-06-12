import os
import time
import logging
import asyncio
from typing import Optional

import httpx
import websockets
from fastapi import APIRouter, Depends, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from rta_backend.security import require_api_key, hash_key, _auth_cache, AUTH_CACHE_TTL
from rta_backend.db import get_supabase_client

logger = logging.getLogger(__name__)

GO_BASE_URL = os.getenv("GO_EXECUTOR_URL", "http://localhost:8080")
CONNECT_TIMEOUT = float(os.getenv("EXECUTOR_CONNECT_TIMEOUT", "5.0"))
READ_TIMEOUT = float(os.getenv("EXECUTOR_READ_TIMEOUT", "60.0"))
ENV_CONNECT_TIMEOUT = float(os.getenv("EXECUTOR_ENV_CONNECT_TIMEOUT", "15.0"))

_http_client: Optional[httpx.AsyncClient] = None

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}

executor_router = APIRouter(prefix="/executor", tags=["executor"])


def get_http_client() -> httpx.AsyncClient:
    """Return a shared httpx client for the Go executor, creating it on first call."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=GO_BASE_URL,
            timeout=httpx.Timeout(connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=READ_TIMEOUT, pool=5.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
    return _http_client


async def shutdown_http_client():
    """Close the shared executor httpx client on application shutdown."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def validate_ws_api_key(api_key: str) -> str:
    """Validate an API key for WebSocket connections. Returns user_id or raises."""
    now = time.time()
    hashed = hash_key(api_key)
    if hashed in _auth_cache:
        uid, expiry = _auth_cache[hashed]
        if now < expiry:
            return uid
    supabase = get_supabase_client()
    res = supabase.table("api_keys").select("user_id").eq("key_hash", hashed).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid API key")
    user_id = res.data[0]["user_id"]
    _auth_cache[hashed] = (user_id, now + AUTH_CACHE_TTL)
    return user_id

def sanitize_path(path: str) -> str:
    """Normalize a URL path and block directory traversal (..) attacks."""
    normalized = "/" + path.lstrip("/") if path else "/"
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Invalid path: traversal denied")
    return normalized.lstrip("/")


def scrub_headers(headers: dict) -> dict:
    """Remove sensitive headers (authorization, cookie) before forwarding to client."""
    return {k: v for k, v in headers.items() if k.lower() not in SENSITIVE_HEADERS}


def get_timeout_for_path(path: str) -> httpx.Timeout:
    """Return appropriate timeout settings based on the upstream path (longer for env/chat)."""
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
    
    # Extract and validate API key for authentication
    api_key = websocket.headers.get("X-API-KEY")
    if not api_key:
        api_key = websocket.query_params.get("api_key")
    
    if not api_key:
        await websocket.accept()
        await websocket.send_text("Error: Missing API key")
        await websocket.close(code=1008)
        return

    try:
        user_id = validate_ws_api_key(api_key)
    except HTTPException:
        await websocket.accept()
        await websocket.send_text("Error: Invalid API key")
        await websocket.close(code=1008)
        return

    await websocket.accept()
    logger.info(f"WS proxy accepted for user {user_id}: /v1/executor/ws/{safe_path}")

    upstream_ws_url = f"{WS_GO_BASE}/ws/{safe_path}"
        
    logger.info(f"WS proxy connecting upstream: {upstream_ws_url}")

    try:
        # Pass API key to upstream Go backend via custom header (not query param)
        async with websockets.connect(upstream_ws_url, additional_headers={"X-API-KEY": api_key}) as upstream_ws:
            logger.info(f"WS proxy upstream connected: {upstream_ws_url}")

            async def mobile_to_go():
                try:
                    while True:
                        data = await websocket.receive()
                        if data["type"] == "websocket.receive":
                            if "text" in data and data["text"] is not None:
                                logger.debug(f"WS proxy text→upstream: {data['text'][:100]}")
                                await upstream_ws.send(data["text"])
                            elif "bytes" in data and data["bytes"] is not None:
                                logger.debug(f"WS proxy bytes→upstream: {len(data['bytes'])}b")
                                await upstream_ws.send(data["bytes"])
                except WebSocketDisconnect:
                    logger.info("WS proxy: app disconnected (WebSocketDisconnect)")
                except Exception as e:
                    logger.warning(f"WS proxy: mobile_to_go error: {e}")

            async def go_to_mobile():
                try:
                    async for message in upstream_ws:
                        if isinstance(message, str):
                            logger.debug(f"WS proxy text→app: {message[:100]}")
                            await websocket.send_text(message)
                        else:
                            logger.debug(f"WS proxy bytes→app: {len(message)}b")
                            await websocket.send_bytes(message)
                except WebSocketDisconnect:
                    logger.info("WS proxy: app disconnected (go_to_mobile)")
                except Exception as e:
                    logger.warning(f"WS proxy: go_to_mobile error: {e}")

            await asyncio.gather(mobile_to_go(), go_to_mobile())
            logger.info("WS proxy: gather completed")
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WS proxy upstream WebSocket error: {e}")
        try:
            await websocket.send_text("Error: Upstream WebSocket unavailable")
        except Exception:
            pass
    except ConnectionRefusedError:
        logger.error("WS proxy: upstream connection refused — Go backend not running on localhost:8080?")
        try:
            await websocket.send_text("Error: Backend unavailable")
        except Exception:
            pass
    except OSError as e:
        logger.error(f"WS proxy: upstream OS error: {e}")
        try:
            await websocket.send_text("Error: Upstream service error")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"WS proxy unexpected error: {e}")
    finally:
        logger.info("WS proxy: closing")
        try:
            await websocket.close()
        except Exception:
            pass
