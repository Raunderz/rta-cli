# Backend Dockerization Plan

## Overview

Dockerize the FastAPI backend for deployment on container-friendly platforms (HuggingFace Spaces, Render, etc.). All Docker-related files live inside `backend/`.

---

## Files to Create

| # | File | Purpose |
|---|---|---|
| 1 | `backend/Dockerfile` | Multi-stage build: uv install → slim runtime |
| 2 | `backend/.dockerignore` | Exclude secrets, caches, venv from image |
| 3 | `backend/docker-compose.yml` | Dev profile: hot reload, mounted source |
| 4 | `backend/docker-compose.prod.yml` | Production profile: health check, restart policy |

---

## Port

Default **7860** (HuggingFace Spaces convention). Other platforms can override via `PORT` env var.

---

## Dockerfile (two stages)

### Stage 1 — Build

- Base image: `python:3.12-slim`
- Install `uv` via pip
- Copy `pyproject.toml` + `uv.lock`
- Run `uv sync --no-dev` to install only production dependencies

### Stage 2 — Runtime

- Base image: `python:3.12-slim`
- Create non-root user `app`
- Copy installed venv from stage 1
- Copy application source code
- Set working directory to `/app`
- Expose port 7860
- Entrypoint: `uvicorn rta_backend.main:app --host 0.0.0.0 --port 7860`

---

## .dockerignore

```
.env
__pycache__
*.pyc
.venv
.pytest_cache
*.egg-info
dist
build
.git
```

Prevents secrets and unnecessary files from being copied into the image.

---

## Compose Files

### `docker-compose.yml` (dev)

```yaml
services:
  backend:
    build: .
    env_file: .env
    ports:
      - "7860:7860"
    volumes:
      - .:/app
    command: uvicorn rta_backend.main:app --host 0.0.0.0 --port 7860 --reload
```

- Mounts source code for live reload
- Uses `RTA_RELOAD=true` behavior via explicit `--reload` flag

### `docker-compose.prod.yml` (production)

```yaml
services:
  backend:
    build: .
    env_file: .env
    ports:
      - "7860:7860"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:7860/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

- No volume mounts (code baked into image)
- Automatic restart on crash
- Health check via existing `/health` endpoint

---

## Code Change Required

`rta_backend/main.py` line 456 hardcodes port 8000. Update to read from env:

```python
port = int(os.getenv("PORT", "7860"))
uvicorn.run("rta_backend.main:app", host="0.0.0.0", port=port, reload=should_reload)
```

---

## .env.example Update

Add `PORT=7860` to the server configuration section.

---

## Platform Usage

| Platform | Setup |
|---|---|
| **HuggingFace Spaces** | Set Dockerfile path to `backend/Dockerfile` in Space settings. Port 7860 auto-detected. |
| **Render** | Create Docker service, point to `backend/Dockerfile`. Set port to 7860. |
| **Fly.io** | `fly launch` from `backend/` directory. |
| **Local dev** | `docker compose up --build` from `backend/`. |

---

## Run Commands

```bash
# Dev (with hot reload)
cd backend
docker compose up --build

# Production
cd backend
docker compose -f docker-compose.prod.yml up --build -d
```
