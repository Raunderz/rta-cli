# Reverse Proxy Plan: Python -> Go

## 1. Goal
Route all execution requests through the main Python backend to save ngrok tunnels and unify authentication.

**Path mapping:**
`https://rta-ngrok.app/v1/executor/{path}`  --> `http://localhost:8080/{path}`

---

## 2. Architecture
1. **Mobile App**: Calls `BACKEND_URL/v1/executor/env`.
2. **FastAPI**: 
   - Intercepts `/v1/executor`.
   - Validates `X-API-KEY`.
   - Uses `httpx` (async) to forward request to Go on `localhost:8080`.
   - Streams response back to Mobile.
3. **Go Backend**: Processes Docker logic as usual.

---

## 3. Implementation Details

### A. HTTP Proxy
- Use `httpx.AsyncClient` for forwarding.
- Map headers (`X-API-KEY`, Content-Type) correctly.
- Support streaming for `/env/chat` (AI responses).

### B. WebSocket Proxy (Tunnel Notifications/Shell)
- FastAPI must bridge WS connections.
- Use `fastapi.WebSocket` to receive from mobile, and a separate WS client to connect to Go.
- Pipe messages bidirectionally.

---

## 4. Preventing Overload (Efficiency)

Even with 2-3 users, Python can hang if handled poorly.

1. **Async Everything**: Use `await` for all IO. Never use blocking `requests` library.
2. **Timeouts**: Set strict connect/read timeouts (e.g., 5s connect, 60s read) so Python workers don't sit idle on dead connections.
3. **Connection Pooling**: Keep one `httpx.AsyncClient` alive (singleton) instead of creating one per request.
4. **Streaming**: For large file uploads/downloads (Zips), stream the bytes. Do not load the whole file into Python RAM.
5. **Worker Count**: Ensure Uvicorn/Gunicorn has at least 4 workers (`--workers 4`) to handle simultaneous proxy tasks + auth tasks.

---

## 5. Security
- Python handles the **Supabase Auth check**. 
- Go backend can remain **Firewalled** (only listen on `127.0.0.1:8080`).
- This prevents anyone from bypassing the API Key check by hitting Go directly.
