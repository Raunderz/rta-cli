# Plan: Dockerize mobile_backend for Render

## Goal
Run `mobile_backend` Go app on Render using Docker.

## Steps
1. **Multistage Dockerfile**:
    - Build stage: `golang:1.21-alpine`.
    - Runtime stage: `alpine:latest`.
2. **Handle Port**:
    - Render provides `$PORT`.
    - Go app must listen on `0.0.0.0:$PORT`.
3. **Dependencies**:
    - Install `ca-certificates` for HTTPS.
4. **Binary**:
    - Compile `main.go`.
5. **Assets**:
    - Copy `public/` directory to runtime image.
6. **Config**:
    - Use environment variables for secrets.

## Implementation Details
- `Dockerfile.render` for Render-specific build.
- Update `main.go` to respect `$PORT` env var (check if it already does).
