# Plan: Run mobile_backend on Render

## Goal
Make Go executor service deployable to Render (no Docker-in-Docker).

---

## Problem
`main.go` relies on `docker run` / `docker exec` for sandbox containers. Render does not support Docker-in-DinD (DinD).

**Affected endpoints:**
- `POST /env` → `exec.Command("docker", "run", ...)`
- `GET /ws/env/{id}` → `exec.Command("docker", "exec", "-it", ...)`
- `POST /env/{id}/upload` → `exec.Command("docker", "cp", ...)`
- `GET /env/{id}/download` → `exec.Command("docker", "exec", ...)`
- `DELETE /env/{id}` → `exec.Command("docker", "rm", "-f", ...)`
- `POST /expose/{id}/{port}` → `exec.Command("docker", "exec", ...)`
- Background abuse detection → `exec.Command("docker", "exec", ...)`

---

## Architecture Decision: Two Options

### Option A: Remote Docker Host (Recommended)
Go app on Render talks to a Docker daemon on a small VPS.

**Architecture:**
```
Render (Go API)  ←HTTP API or DOCKER_HOST→  VPS (Docker daemon)
```

**Pros:** Full container isolation preserved. Minimal code changes.
**Cons:** Need small VPS ($5-10/mo DigitalOcean/EC2). Adds network hop.

**Changes required:**
1. Add `DOCKER_HOST` env var support in `main.go`
2. Replace `exec.Command("docker", ...)` with Docker API client (or set `DOCKER_HOST` env and keep `docker` CLI if binary present)
3. Add SSH tunnel or TLS cert for secure Docker remote access

**Deploy:**
- Go API → Render Web Service (Docker or Go native)
- Docker host → EC2 t4g.nano ($3.50/mo) or DO droplet ($4/mo)

### Option B: No Docker, Direct Process Execution (Simpler)
Drop container dependency. Run everything as child processes on Render.

**Architecture:**
```
Render (Go API) → exec.Command("bash", ...)  [no container]
```

**Pros:** Zero infra. Single deploy on Render. No extra cost.
**Cons:** No container isolation. All processes share same filesystem. Security weaker.

**Changes required:**
1. Replace `docker run` → `exec.Command("bash", "-c", "sleep infinity")` with `cmd.SysProcAttr` resource limits
2. Replace `docker exec -it bash` → spawn `bash` directly with PTY
3. Replace `docker cp` → direct filesystem ops
4. Replace `docker exec ps aux` → `os/exec` on host
5. Apply ulimit/RLIMIT via `setrlimit` for resource caps
6. Remove Docker sandbox image dependency entirely
7. The `tempdev:latest` sandbox image tools (python3, node, git, ttyd, rta CLI, cloudflared) must exist on Render

**Deploy:**
- Go binary + all tooling → Render Docker deploy (custom Dockerfile)
- Or use Render's native Go support + install deps via build command

---

## Recommended Path: Option A + Option B Hybrid

### Phase 1: Option B (Quick, Render-only)
Deploy without Docker isolation. Use Render's existing container as the sandbox boundary.

**Changes:**
1. `main.go`: Replace all `exec.Command("docker", ...)` with direct process spawning
2. `main.go`: Add `setrlimit` calls to cap CPU/mem per user session
3. `Dockerfile`: Build Go binary + include dev tools (python3, node, git, rta CLI, cloudflared)
4. `main.go`: Port from `:8080` to `$PORT` env var
5. Change `AllowedOrigins` to include Render frontend URL
6. Remove cloudflared tunnel feature (not needed — Render provides public URL)
7. Each "env" becomes a process group with PID tracking instead of container ID
8. Resource limits via ulimit, cgroups v2 (if available on Render)

### Phase 2: Option A (If isolation needed)
Optional: Add remote Docker host for paying users needing real sandbox isolation.

---

## Detailed Implementation: Phase 1

### 1. Refactor `main.go` — remove Docker dependency

**Env struct changes:**
```go
type Env struct {
    ID        string
    UserID    string
    APIKey    string
    Cmd       *exec.Cmd     // instead of container string
    Pid       int
    CreatedAt time.Time
    LastPing  time.Time
    TunnelURL string
    WS        *websocket.Conn
    mu        sync.Mutex
}
```

**handleCreateEnv — replace `docker run`:**
- Instead of `docker run -d --memory=512m ... tempdev:latest sleep infinity`
- Spawn `bash` directly with resource limits
- Track PID in Env struct

**handleShell — replace `docker exec -it bash`:**
- Instead of `docker exec -it {container} bash`
- Attach PTY directly to the bash process

**deleteEnv — replace `docker rm -f`:**
- Kill tracked PID instead of `docker rm -f`

**cleanupLoop:**
- Check process alive instead of docker inspect

**abuseDetectLoop:**
- `ps aux` on host, filtered to user PID

### 2. Port from `:8080` to `$PORT`
```go
port := os.Getenv("PORT")
if port == "" {
    port = "8080"
}
server.Addr = ":" + port
```

### 3. Update CORS
Add Render website URL to allowed origins:
```
"https://rta-three.vercel.app"
```

### 4. Dockerfile for Render
```dockerfile
# Build stage
FROM golang:1.26-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

# Runtime
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 python3-pip nodejs npm git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://rta-three.vercel.app/rta -o /usr/local/bin/rta && chmod +x /usr/local/bin/rta
COPY --from=builder /app/server /server
COPY public/ /public
EXPOSE $PORT
CMD ["/server"]
```

### 5. `GO_EXECUTOR_URL` update
In backend `.env`:
```
GO_EXECUTOR_URL=https://rta-executor.onrender.com
```

### 6. Remove cloudflared tunnel endpoints
`/expose/` endpoint removed entirely. Render provides public HTTPS URL.

---

## Files to modify
| File | Changes |
|------|---------|
| `main.go` | Replace docker commands, add `$PORT`, rlimits, PID tracking |
| `auth.go` | Update `BACKEND_URL` default to Render backend URL |
| `Dockerfile` | Complete rewrite for Render deploy |
| `backend/.env` | Update `GO_EXECUTOR_URL` |
| `backend/rta_backend/executor_proxy.py` | Update target URL |

---

## Files to delete
- `setup.sh`, `setup_aws.sh`, `deploy.sh` (AWS-specific)
- `test_tunnel.py` (cloudflared-specific)
- `RENDER_DOCKER_PLAN.md` (this file → rename-or-delete after done)

---

## Security concerns (Phase 1)
- No container isolation. Users share filesystem.
- Mitigation: Use `os/exec` with separate temp dirs per env (`/tmp/env-{id}`).
- Mitigation: Drop privileges via `syscall.SysProcAttr.Credential` (run as `nobody`).
- Mitigation: RLIMIT_NPROC prevents fork bombs.
- Cloudflared removed → no tunnel exposure risk.
- Existing X-API-KEY auth stays.

---

## Deploy steps

1. Fork this repo on Render
2. Create new **Web Service** → select repo → `mobile_backend/` as root
3. Runtime: Docker
4. Env vars: `BACKEND_URL`, `PORT`, `RENDER_INSTANCE_TYPE=free` (or `starter`)
5. Deploy
6. Update `GO_EXECUTOR_URL` in backend env to new Render URL
7. Test: `curl https://rta-executor.onrender.com/status`
