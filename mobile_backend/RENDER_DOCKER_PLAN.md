# Plan: Dockerize mobile_backend for Render

## Goal
Run `mobile_backend` Go app on Render using Docker.

## Steps
1. **Multistage Dockerfile**:
    - Build stage: `golang:1.21-alpine`.
    - Runtime stage: `alpine:latest`.
2. **Handle Port**:
    - Render provides `$PORT`.
    - Update `main.go` to listen on `0.0.0.0:$PORT`.
3. **Dependencies**:
    - Install `ca-certificates` for HTTPS.
    - **RISK**: `mobile_backend` uses `docker` CLI. Render doesn't support Docker-in-Docker (DinD).
4. **Binary**:
    - Compile `main.go`.
5. **Assets**:
    - Copy `public/` directory to runtime image.
6. **Config**:
    - Use environment variables for secrets.

## Proxy Integration (backend/ -> mobile_backend/)
- Update `GO_EXECUTOR_URL` in `backend/.env` (or Render environment) to point to the new Render URL (e.g., `https://rta-mobile.onrender.com`).
- Ensure `backend` can handle the latency of Render's "spin up" if using the free tier.

## Critical Issues & Blockers
- **Docker-in-Docker**: `mobile_backend` spawns sandboxes via `docker run`. Render cannot do this.
    - *Solution A*: Use a VPS (EC2/DigitalOcean) instead of Render.
    - *Solution B*: Use Fly.io (supports Docker-in-Docker).
    - *Solution C*: Point `mobile_backend` to a remote Docker host via `DOCKER_HOST` env var.
- **Hardcoded Port**: `main.go` currently hardcoded to `:8080`.
- **Public Exposure**: Moving from `localhost:8080` to a public Render URL means `mobile_backend` is exposed. It has `X-API-KEY` auth, but we should ensure it's robust.
