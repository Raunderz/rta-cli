# VPS Provider Build Plan
## Lightweight Containerized Environment Platform

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Dashboard  │  │   Terminal   │  │   Exposed App     │ │
│  │  (Vanilla JS)│  │   (xterm.js) │  │  (Cloudflare URL) │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘ │
└─────────┼─────────────────┼─────────────────────┼────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      GO API SERVER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │  REST API    │  │  WS Proxy    │  │  Cloudflared      │ │
│  │  (Session    │  │  (ttyd       │  │  Config Manager   │ │
│  │   Lifecycle) │  │   Bridge)    │  │                   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘ │
│         │                 │                     │            │
│  ┌──────┴─────────────────┴─────────────────────┴──────┐   │
│  │              containerd (gRPC)                        │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    HOST SYSTEM                               │
│  ┌──────────────────────┴───────────────────────────────┐    │
│  │              CNI Bridge (cni0)                        │    │
│  │              10.88.0.1/16                            │    │
│  └──────┬──────────────┬──────────────┬───────────────────┘    │
│         │              │              │                       │
│    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐                │
│    │Cont A   │    │Cont B   │    │Cont C   │                │
│    │10.88.0.│    │10.88.0.│    │10.88.0.│                │
│    │   15    │    │   16    │    │   17    │                │
│    │:8080    │    │:8080    │    │:8080    │                │
│    └─────────┘    └─────────┘    └─────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Runtime | containerd + runc | Lightweight, no Docker daemon overhead |
| Networking | CNI (bridge plugin) | Simple L2 bridge, host can route to container IPs directly |
| Terminal | ttyd | WebSocket terminal server, battle-tested |
| API | Go 1.22+ | Concurrency, containerd client library, single binary |
| Dashboard | Vanilla JS + xterm.js | No build step, easy to discard later |
| Tunnel | cloudflared | Outbound-only, no open ports, dynamic subdomains |
| Base Image | Ubuntu 22.04 minimal + Python + Node | Full userland, no sudo needed |

---

## Phase 1: Foundation
**Goal:** containerd running on your PC, can create/destroy containers manually

### 1.1 Install containerd & CNI
- Install containerd (systemd service)
- Install CNI plugins (bridge, host-local, loopback)
- Configure containerd (`/etc/containerd/config.toml`)
- Configure CNI network (`/etc/cni/net.d/10-bridge.conf`)
- Test: `ctr version`, containerd service running

### 1.2 Build Base Image
- Create Dockerfile: Ubuntu 22.04 + Python 3.11 + Node 20 + git + build-essential + ttyd
- Build with Docker or nerdctl: `docker build -t vps-base:latest .`
- Import to containerd: `docker save | ctr images import -`
- Or use `nerdctl build` directly with containerd
- Verify: `ctr images ls` shows `vps-base:latest`

### 1.3 Manual Container Lifecycle
- Create container: `ctr run --rm vps-base:latest test-container /bin/bash`
- Verify networking: container gets IP on cni0 bridge
- Verify host can ping container IP
- Test ttyd inside container: bind to Unix socket, connect from host
- Destroy container: `ctr task kill -9 test-container`, `ctr container delete test-container`

### 1.4 Resource Limits Verification
- Test cgroup v2 limits: memory.max=512M, cpu.max
- Verify OOM behavior: run memory bomb, container gets killed
- Verify read-only rootfs works

**Deliverable:** Script `manual-test.sh` that creates container, starts ttyd, verifies network, destroys container

---

## Phase 2: Go API Core
**Goal:** REST API can create/destroy containers programmatically

### 2.1 Project Scaffold
```
vps-provider/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── api/
│   │   ├── handlers.go      # HTTP handlers
│   │   ├── middleware.go    # Logging, recovery
│   │   └── routes.go        # Route definitions
│   ├── container/
│   │   ├── client.go        # containerd gRPC client wrapper
│   │   ├── lifecycle.go     # Create, start, stop, delete
│   │   └── config.go        # Container spec builder (cgroups, caps, mounts)
│   ├── models/
│   │   └── session.go       # Session struct, status enums
│   └── store/
│       └── memory.go        # In-memory session store (thread-safe)
├── static/
│   └── (dashboard files later)
├── go.mod
└── go.sum
```

### 2.2 containerd Client
- Initialize containerd client (unix socket `/run/containerd/containerd.sock`)
- Pull image (or ensure local image exists)
- Create container with spec:
  - Namespace: `vps-provider`
  - Rootfs: read-only
  - Mounts: writable overlay upper layer at `/home/user`, `/tmp`
  - Capabilities: drop all, add minimal set
  - No new privileges
  - Seccomp default
  - Cgroups: memory.max=512M, cpu.max=50000, pids.max=64

### 2.3 Session Store
```go
type Session struct {
    ID            string
    Status        SessionStatus // creating, running, detached, destroying, destroyed
    ContainerID   string
    IP            string          // container IP from CNI
    CreatedAt     time.Time
    ExpiresAt     time.Time
    DetachedAt    *time.Time
    GracePeriod   time.Duration   // 15 minutes
    Resources     ResourceUsage
    TTYDSocket    string          // /run/vps/sessions/{id}/ttyd.sock
}
```
- Thread-safe map with RWMutex
- Operations: Create, Get, List, UpdateStatus, Delete

### 2.4 REST Endpoints (v1)
```
POST   /api/v1/sessions              → CreateSession
GET    /api/v1/sessions              → ListSessions
GET    /api/v1/sessions/:id          → GetSession
DELETE /api/v1/sessions/:id          → DestroySession
```

**Deliverable:** `curl` commands work end-to-end:
```bash
curl -X POST http://localhost:8080/api/v1/sessions
# Returns: {"id":"sess-abc123","status":"creating",...}
curl http://localhost:8080/api/v1/sessions/sess-abc123
# Returns: {"id":"sess-abc123","status":"running","ip":"10.88.0.15"}
curl -X DELETE http://localhost:8080/api/v1/sessions/sess-abc123
```

---

## Phase 3: Terminal & WebSocket
**Goal:** Browser terminal connects to container shell

### 3.1 ttyd Integration
- Container spec: start `ttyd` as PID 1 (or via init)
- ttyd config: `--unix-socket /tmp/ttyd.sock --once /bin/bash`
  - `--once`: closes when client disconnects (we handle reconnect)
  - Or without `--once` for reconnect support
- Alternative: custom init (tini) that starts ttyd + reaps zombies

### 3.2 WebSocket Proxy
- Endpoint: `WS /api/v1/sessions/:id/terminal`
- Flow:
  1. User opens WebSocket
  2. API looks up session, verifies status == running
  3. API dials Unix socket `/run/vps/sessions/{id}/ttyd.sock`
  4. Bidirectional copy: `io.Copy(ws, ttyd)` and `io.Copy(ttyd, ws)`
  5. Handle reconnect: if ttyd closed, attempt to re-exec ttyd in container

### 3.3 Session State Management
- On WS connect: status → running (if detached)
- On WS disconnect: status → detached, start grace timer (15m)
- Grace timer goroutine: after 15m, if still detached → destroy
- On explicit DELETE: immediate destroy, close all WS connections

### 3.4 Dashboard Terminal View
- Static HTML page: `/terminal.html?id=sess-abc123`
- xterm.js initialized with WebSocket URL
- Handle resize: `stty` rows/cols via xterm.js `onResize`
- Handle reconnect: exponential backoff, status banner

**Deliverable:** Open browser, create session via API, navigate to terminal page, get working bash prompt inside container

---

## Phase 4: TTL & Lifecycle Automation
**Goal:** Sessions self-destruct after 12h or 15m of disconnection

### 4.1 TTL Manager
- Background goroutine spawned per session on creation
- Loop: every 30s, check:
  - If `time.Now() > session.ExpiresAt` → destroy
  - If `session.Status == detached && time.Since(*session.DetachedAt) > session.GracePeriod` → destroy
- On WS reconnect: reset `DetachedAt`, extend `ExpiresAt` (optional: cap at original 12h)

### 4.2 Cleanup on Destroy
- containerd: `task.Kill()` → `task.Delete()` → `container.Delete()`
- Remove overlay upper layer directory
- Remove ttyd Unix socket
- Update store: status → destroyed
- Notify dashboard (SSE or WS broadcast)

### 4.3 Resource Tracking
- Periodic cgroup stats: memory usage, CPU usage
- Store in session object
- Expose via `GET /api/v1/sessions/:id` (optional for now)

**Deliverable:** Create session, disconnect, wait 15m, verify container gone. Or wait 12h, verify auto-cleanup.

---

## Phase 5: Cloudflare Tunnel Integration
**Goal:** Expose container ports to public URLs

### 5.1 Cloudflared Setup
- Install cloudflared on host
- Create named tunnel: `cloudflared tunnel create vps-provider`
- Get tunnel credentials JSON, store at `/etc/cloudflared/`
- DNS wildcard: `*.containers.yourdomain.com` → tunnel UUID

### 5.2 Config Management
- Config file: `/etc/cloudflared/config.yml`
- Dynamic ingress rules:
```yaml
tunnel: <uuid>
credentials-file: /etc/cloudflared/<uuid>.json

ingress:
  - hostname: max-flask.containers.yourdomain.com
    service: http://10.88.0.15:8080
  - hostname: alice-api.containers.yourdomain.com
    service: http://10.88.0.16:3000
  - service: http_status:404  # catch-all
```

### 5.3 API Integration
```
POST /api/v1/sessions/:id/ports
Body: { "container_port": 8080, "subdomain": "max-flask" }
Response: { "public_url": "https://max-flask.containers.yourdomain.com" }
```
- API appends ingress rule to config
- Reloads cloudflared: `cloudflared tunnel ingress validate && cloudflared tunnel route dns` or signal reload
- Alternative: cloudflared API (if available) or config write + process restart
- Store mapping in session: `ExposedPorts []ExposedPort`

### 5.4 Cleanup on Session Destroy
- Remove ingress rules for session's subdomains
- Reload cloudflared config
- DNS cleanup (optional: Cloudflare auto-cleans on tunnel delete)

**Deliverable:** Max creates session, runs Flask on 8080, calls expose API, gets public URL, visits it in browser

---

## Phase 6: Dashboard (Disposable)
**Goal:** Browser UI for session management

### 6.1 Session List Page
- `GET /` → serves `index.html`
- Fetch `GET /api/v1/sessions` on load
- Display cards: ID, status badge, time remaining, connect button
- Auto-refresh: polling every 5s (acceptable for 3 users)

### 6.2 New Session Flow
- Button: "New Session"
- Modal: select template (Blank, Python, Node)
- Optional: Git URL input
- POST to API, show spinner
- Redirect to terminal page on `status == running`

### 6.3 Terminal Page
- Full-screen xterm.js
- Connect to `WS /api/v1/sessions/:id/terminal`
- Toolbar: session info, time remaining, "Expose Port" button, "Destroy" button
- "Expose Port" modal: enter port number, optional subdomain, submit
- Display exposed URLs as clickable links

### 6.4 Styling
- Minimal CSS, no framework
- Dark theme (terminal aesthetic)
- Responsive enough for laptop screens

**Deliverable:** Complete browser-based workflow without touching `curl`

---

## Phase 7: Production Hardening
**Goal:** Ready for AWS + real users

### 7.1 Security
- Drop all capabilities except: `CAP_CHOWN`, `CAP_DAC_OVERRIDE`, `CAP_SETGID`, `CAP_SETUID`
- Read-only rootfs (`--read-only`)
- No new privileges (`NoNewPrivileges: true`)
- Seccomp default profile
- AppArmor/SELinux profile (optional)
- API rate limiting (per IP)
- Session ID entropy: 16+ random chars

### 7.2 Observability
- Structured logging (zerolog/slog)
- Session lifecycle events: create, connect, disconnect, destroy, OOM
- Metrics: active sessions, total sessions, avg lifetime (Prometheus optional)
- Container stdout/stderr: stream to API logs (no persistence)

### 7.3 AWS Deployment
- AMI: Ubuntu 22.04 + containerd + CNI + cloudflared
- Systemd services:
  - `containerd.service`
  - `vps-api.service` (your Go binary)
  - `cloudflared.service`
- Security group: outbound only (cloudflared handles ingress)
- Instance: `t3.medium` (2 vCPU, 4GB) for 3-5 users
- Or `t3.small` (2 vCPU, 2GB) for 2-3 users (test density)

### 7.4 Backup & Recovery
- Base image rebuild script
- Config backup (cloudflared credentials, CNI config)
- Session store: in-memory is fine (ephemeral), no persistence needed

**Deliverable:** Production-ready system on AWS with monitoring

---

## Phase 8: Future (Post-Dashboard)
**Goal:** API-only for power users

### 8.1 API Tokens
- User registration (minimal: email + API key)
- API key auth: `Authorization: Bearer <token>`
- Per-user session limits (e.g., 2 concurrent)

### 8.2 Programmatic Access
- CLI tool: `vps-cli` (Go binary)
  - `vps-cli sessions create --template python`
  - `vps-cli sessions connect <id>` (opens local terminal via WebSocket)
  - `vps-cli sessions expose <id> --port 8080`
- SDK: Go, Python, Node clients

### 8.3 Advanced Features
- Volume mounts: persist `/home/user` across sessions (optional)
- Custom base images: user-uploaded Dockerfile
- Multi-region: spawn containers on different hosts
- Metrics API: resource usage history

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| 1. Foundation | 2-3 days | 2-3 days |
| 2. Go API Core | 3-4 days | 5-7 days |
| 3. Terminal & WebSocket | 2-3 days | 7-10 days |
| 4. TTL & Lifecycle | 1-2 days | 8-12 days |
| 5. Cloudflare Tunnel | 2-3 days | 10-15 days |
| 6. Dashboard | 2-3 days | 12-18 days |
| 7. Production | 3-5 days | 15-23 days |
| **Total** | **~3 weeks** | |

*Assuming 2-3 hours/day, solo developer, familiar with Go and Linux*

---

## Risk Areas

| Risk | Mitigation |
|------|-----------|
| containerd networking bugs | Test CNI thoroughly in Phase 1, have fallback to Docker |
| WebSocket reconnection edge cases | Implement robust reconnect in xterm.js, test disconnect/reconnect loops |
| cloudflared config reload failures | Validate config before reload, fallback to restart, monitor with health checks |
| cgroup v2 compatibility | Test on Ubuntu 22.04+ (cgroups v2 default), verify limits actually enforce |
| Base image bloat | Strip unnecessary packages, use multi-stage build, target <500MB unpacked |

---

## Immediate Next Steps

1. Install containerd + CNI on your PC
2. Verify `ctr` works, create a test container manually
3. Build base image Dockerfile
4. Import image to containerd
5. Test ttyd inside container, connect from host via Unix socket

**Ready to proceed with Phase 1?**
