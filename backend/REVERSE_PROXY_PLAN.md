# Reverse Proxy Plan: Python -> Go

## 1. Goal
Route all execution requests through the main Python backend to save ngrok tunnels and unify authentication.

**Path mapping:**
`https://divisive-herbs-jolly.ngrok-free.dev/v1/executor/{path}`  --> `http://localhost:8080/{path}`

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

### A. Code Structure
- **File**: `backend/rta_backend/executor_proxy.py`
- **Method**: Fully **Asynchronous** (using `httpx.AsyncClient`). No manual threading required. 
- **Integration**: `main.py` will include `executor_router` to keep core logic separated.

### B. HTTP Proxy
- Use `httpx.AsyncClient` for forwarding.
...
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

## 6. Failure Points & Mitigation

### A. WebSocket Stability (The "Grip" Problem)
- **Risk**: Python bridges the connection. If Python crashes or restarts, the terminal session drops even if the container is alive.
- **Mitigation**: Implement `auto-reconnect` logic on the Mobile App. Python must handle `ConnectionClosed` gracefully without leaking file descriptors.

### B. Memory Exhaustion (RAM Spike)
- **Risk**: User uploads a 50MB project ZIP. If FastAPI loads the whole thing into `await request.body()`, RAM usage spikes per user.
- **Mitigation**: Use `request.stream()` and pipe chunks directly to `httpx.post(..., stream=True)`. RAM stays low (<1MB per upload).

### C. Connection Leaks (Zombies)
- **Risk**: `httpx.AsyncClient` not closed correctly or too many open connections to Go.
- **Mitigation**: Use a global `AsyncClient` lifetime (on startup/shutdown events). Use `aclose()` on all manual connections.

### D. Header Spoofing (Auth Bypass)
- **Risk**: Go backend thinks every request is valid because it's from "localhost".
- **Mitigation**: Go backend should verify a "Shared Secret" header sent by Python, or only listen on `127.0.0.1` (no public interface).

### E. Slow-Loris / Denial of Service
- **Risk**: A user opens a chat stream but reads very slowly, keeping a Python worker busy forever.
- **Mitigation**: Set strict `read_timeout` (e.g. 120s) and max request body size in Uvicorn.

### F. Docker Startup Latency
- **Risk**: `POST /env` takes 5s to start container. Python's default timeout is often 5s.
- **Mitigation**: Increase `connect_timeout` specifically for the `/env` path to 15s.

---

## 7. Security Hardening
1. **Sanitize Paths**: Ensure `/v1/executor/{path}` cannot be used for Path Traversal (e.g. `../../etc/passwd`).
2. **Scrub Headers**: Strip `Authorization` or `Cookie` headers before forwarding to Go if not needed.
3. **Log Scrubbing**: Ensure `X-API-KEY` is never printed in Python logs if proxying fails.
4. **Rate Limiting**: Apply SlowAPI limits *before* proxying to Go to protect Docker resources.
