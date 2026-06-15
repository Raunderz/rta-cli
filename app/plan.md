# Rta — Cloud IDE for Mobile (Expo + React Native)

## Current Status (June 2026)

### ✅ Achievements
- **Restructuring**: App moved to `src/` hierarchy (`components/`, `App.js`, `index.js`).
- **Session Lifecycle**: "START CLOUD" / "END" logic implemented in `App.js`. Connects to Go Executor via Python Proxy.
- **Header Forwarding**: Fixed `X-API-KEY` stripping in Python `executor_proxy.py`.
- **AI Sandbox Chat**: `Chat.js` now routes prompts to `/v1/executor/env/chat/{id}` when cloud active, executing `rta ask` in container.
- **Terminal UI**: `Terminal.js` integrated with `xterm.js` in a WebView with WebSocket support.
- **Terminal Keyboard Fix**: Resolved Android WebView focus/input issues using `injectJavaScript` for accessory buttons and a full-size `opacity: 0.01` textarea for native touch focus.
- **Infra (Server)**: `mobile_backend` Go service supports `upload`/`download` ZIP endpoints for workspace sync.

### ❌ Blockers / Stuck At
(none)

### 💡 Next Steps
- **Developer Accessory Bar**: Add a row of native buttons for `TAB`, `ESC`, `CTRL`, and arrows to improve mobile coding speed.

---


## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Mobile App    │────▶│  FastAPI Backend │────▶│   AI Agent      │
│  (Expo + JS)    │     │  (Auth/API Keys) │     │  (Your Service) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         │              ┌────────▼─────────┐
         │              │   Go Service     │
         └─────────────▶│ (Execution)      │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │ Docker Container │
                        │ + SSH Tunnel     │
                        └──────────────────┘
```

### Component Responsibilities

| Component | Tech | Role |
|-----------|------|------|
| **Mobile App** | Expo + JavaScript | Thin client: editor, chat-terminal, offline file storage |
| **FastAPI Backend** | Python (existing) | Auth, API key validation, telemetry |
| **AI Agent** | rta CLI (headless) | Token pool management, model routing, tool execution inside sandbox |
| **Execution Service** | Go (`net/http` stdlib) | Orchestrator: Docker lifecycle, Chat-over-CLI bridge, tunnel management |
| **Tunneling** | `cloudflared` | Secure public URLs for previewing web servers |
| **Container** | Ubuntu + Docker | Ephemeral execution environment with pre-installed `rta` CLI |

---

## Project Structure

```
rta/
├── app/                          # Expo + React Native mobile application
│   ├── src/
│   │   ├── components/           # Reusable UI (Chat, Editor, Files, GitUI, Terminal)
│   │   ├── screens/              # Main screens (Future use for navigation)
│   │   ├── navigation/           # Navigation configuration (Future use)
│   │   ├── hooks/                # Custom hooks (Future use)
│   │   ├── context/              # App-wide state (Future use)
│   │   ├── utils/                # API clients, constants, helpers (Future use)
│   │   ├── types/                # Type definitions (Future use)
│   │   ├── App.js                # Core App component
│   │   └── index.js              # Entry point
│   ├── assets/                   # Images, fonts
│   ├── .env                      # Local environment configuration
│   └── package.json
│
├── mobile-backend/               # ALL Go backend code (Execution service)
```

---

## Tech Stack

### Mobile App
| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | **Expo (bare workflow)** | Native modules support, mature ecosystem |
| Language | **JavaScript** | No compile step, no type system overhead, runs everywhere |
| Editor | **CodeMirror 6** | Lightweight, mobile-friendly touch, native diff view for AI changes |
| Terminal | **Chat-UI (Native)** | Native scrolling, easy copy-paste, better mobile UX than xterm.js |
| Local Git | **isomorphic-git** | Pure JS, works offline with Expo FileSystem shim |
| Local Files | **expo-file-system** | Native filesystem access, persists across sessions |
| State | **React Context + useReducer** | Built-in, no extra dependency, simple enough for this app |
| Styling | **StyleSheet** | No build step, no Tailwind config, React Native native |
| Lists | **FlatList** | Built-in, good enough for <1000 files |
| AI Streaming | **Chunked HTTP** | Streamed response from Go `rta ask` execution |
| Terminal Comms | **WebSocket** | For tunnel URL notifications and PTY shell (optional) |

### Execution Service (Go)
| Concern | Choice | Reason |
|---------|--------|--------|
| HTTP Server | **`net/http`** stdlib | No framework dependency, standard library, sufficient for this |
| WebSocket | **Gorilla WebSocket** | Standard, battle-tested (or `golang.org/x/net/websocket` for pure stdlib) |
| Docker | **docker client SDK** | Native Go bindings for container lifecycle |
| PTY | **creack/pty** | Pseudo-terminal for interactive shell sessions |
| Config | **os.Getenv** | No config library, 12-factor style |

### Infrastructure
| Concern | Choice | Reason |
|---------|--------|--------|
| Sandboxing | **Docker** + strict limits | 10 concurrent users max, manageable risk |
| Container OS | **Ubuntu** | glibc-compatible, avoids musl issues with some language runtimes |
| Resource Limits | `--memory=512m --cpus=0.5 --pids-limit=100` | Prevent abuse on shared infrastructure |
| Tunneling | **`localhost.run`** via SSH | Zero setup, no API keys, no self-hosted server, free |
| Domain | **None needed** | localhost.run gives random URLs per session |

---

## Data Flow

### Starting a Session
1. User opens project in mobile app (files loaded from local `expo-file-system`)
2. User taps **"Start Session"** — app zips local project
3. App sends: `{api_key, project_zip}` to Go Service
4. Go validates API key with FastAPI (one HTTP call)
5. Go pulls Docker image (cached), starts Ubuntu container, injects:
   - User's project zip (extracted to `/workspace`)
   - SSH client (pre-installed in Ubuntu)
6. Go opens WebSocket to mobile, starts PTY inside container
7. Go returns: `{session_id, ws_url}`
8. Mobile connects WebSocket, renders terminal via xterm.js

### AI Interaction (Chat-over-CLI)
1. User types in chat: *"Fix the bug in main.py"*
2. App sends: `{prompt}` via `POST /env/{id}/chat` to Go Service.
3. Go Service executes: `rta ask "Fix the bug in main.py" --workspace /workspace` inside the container.
4. **Inside Sandbox**: `rta` loads previous session history, uses tools (`read_file`, `edit_file`, `run_command`) to complete the task.
5. `rta` streams its thinking and final response back to Go, which streams it to the Mobile App.
6. Mobile App renders the response in a native Chat UI.

### Running a Web Server (Preview)
1. User (or AI) runs a server (e.g., `python3 -m http.server 8000`).
2. Go Service detects port binding or user triggers "Expose".
3. Go runs `cloudflared tunnel` inside the container.
4. Go parses the tunnel URL and sends it to the Mobile App via WebSocket.
5. Mobile App shows a "Preview" button/link.

### Ending a Session
1. User taps **"End Session"**
2. Go zips `/workspace` in container
3. Go sends zip to mobile app
4. Mobile extracts zip, updates local files via `expo-file-system`
5. User runs `git commit` via isomorphic-git (offline, local)
6. Go kills container, cleans up

---

## Build Plan: Phase by Phase

### Phase 0: Foundation ✅
**Done.** Expo shell with editor, chat, file tree, terminal, and session lifecycle all working.

---

### Phase 1: Local-First Git & Auth — MOSTLY DONE ✅
**isomorphic-git wired up, GitUI.js fully functional with init, status, add, commit, log.** Remaining:
- [ ] GitHub OAuth Integration (backend endpoint + WebView flow + secure token storage)
- [ ] Push/Pull remote sync

---

### Phase 2: Terminal + Session Management — MOSTLY DONE ✅
**Go service built, terminal works, session lifecycle works. Zip sync implemented.**

**Deliverable**: User taps "Start Session", terminal opens, can run commands.

---

### Phase 3: AI Integration ✅
**Done.** Chat routes to `/v1/executor/env/chat/{id}`, `rta ask` executes in container, streaming works.

---

### Phase 4: File Sync & Session Persistence (Days 11–12)
**Goal**: Seamless two-way sync between local and container.

- [ ] Implement zip download: container `/workspace` → mobile on session end
- [ ] Build conflict resolution: if local and container diverged, show diff
- [ ] Auto-save: periodically zip and send to container (optional, configurable)
- [ ] Session recovery: if app crashes, reconnect to existing container
- [ ] Add progress indicators for zip upload/download
- [ ] Optimize zip size: exclude `node_modules`, `.git`, build artifacts

**Deliverable**: Start session → edit → end session → local files updated → git commit.

---

### Phase 5: Preview Tunneling ✅
**Done.** Go `/expose/` endpoint runs cloudflared in container, parses tunnel URL, sends to mobile via WebSocket.

---

### Phase 6: Polish & Hardening (Days 15–17)
**Goal**: Production-ready for 100 users.

- [ ] Add smart keyboard accessory (common symbols, tab, brackets)
- [ ] Implement gesture shortcuts (two-finger undo, swipe between files)
- [ ] Add voice input for AI prompts
- [ ] Build onboarding: sample projects, tutorial
- [ ] Add error boundaries and crash reporting
- [ ] Implement retry logic for WebSocket/SSE connections
- [ ] Add loading skeletons and optimistic UI
- [ ] Test on low-end Android devices (performance)
- [ ] Security audit: container escape vectors, resource limits, network egress
- [ ] Add admin dashboard (optional): view active sessions, resource usage

**Deliverable**: App feels polished, handles edge cases, ready for users.

---

### Phase 7: Scale Preparation (Days 18–20)
**Goal**: Ready to scale beyond single node.

- [ ] Add node registry to FastAPI: Go workers heartbeat, get assigned users
- [ ] Implement session affinity: user reconnects to same node
- [ ] Add container image caching across nodes
- [ ] Setup log aggregation (simple file logging)
- [ ] Add metrics: session duration, container startup time, AI latency
- [ ] Document deployment process for new free-tier nodes
- [ ] Build simple CLI tool to register new Go worker nodes

**Deliverable**: Can add more free-tier nodes, load balances across them.

---

## Environment Setup

### Mobile Development
```bash
# Install Bun (if not already)
curl -fsSL https://bun.sh/install | bash

# Clone repo
cd rta/app

# Install dependencies
bun install

# Start development server
bun run start

# Run on specific platform
bun run android
bun run ios
```

### Go Service Development
```bash
cd rta/mobile-backend/executor

# Initialize Go module
go mod init rta-executor

# Install dependencies
go get github.com/docker/docker/client
go get github.com/creack/pty
go get github.com/gorilla/websocket

# Run locally (requires Docker)
go run main.go

# Build binary
go build -o rta-executor main.go
```

### localhost.run Test (Inside Container)
```bash
# Start a test server
python3 -m http.server 8080 &

# Tunnel it
ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 localhost.run

# Output will show: https://abc123.localhost.run
```

---

## Deployment (Free Tier Strategy)

### Main Node (Oracle Cloud ARM Always Free)
- **Services**: FastAPI (Python), Go executor, Docker daemon
- **Specs**: 4 ARM cores, 24GB RAM
- **OS**: Ubuntu 22.04
- **Ports**: 80, 443 (HTTP/HTTPS), 8080+ (Go service), 7000 (Docker)

### Worker Nodes (Additional Free Tiers)
- **Services**: Go executor, Docker daemon
- **Registration**: On boot, call FastAPI `/register` with IP and capacity
- **Assignment**: FastAPI assigns new sessions to least-loaded worker

### No Domain Needed
- `localhost.run` provides random URLs per session
- No DNS management, no SSL certs, no Cloudflare

---

## Security Checklist

- [ ] Docker containers run as non-root user
- [ ] `--read-only` rootfs where possible, `/workspace` as writable volume
- [ ] No `--privileged` flag, no host networking
- [ ] Network egress blocked by default (prevent crypto mining)
  - Block outbound except whitelisted ports (80, 443 for package installs)
- [ ] Resource limits enforced: memory, CPU, PIDs, disk
- [ ] API keys validated on every request
- [ ] WebSocket connections authenticated (token in query param)
- [ ] Container images scanned for vulnerabilities
- [ ] Rate limiting on FastAPI endpoints
- [ ] SSH tunnel runs as non-root inside container
- [ ] No secrets in container images (API keys passed at runtime)

---

## Performance Targets

| Metric | Target |
|--------|--------|
| App cold start | < 3 seconds |
| Container cold start | < 10 seconds (acceptable, user informed) |
| AI token latency | < 500ms first token, 50ms subsequent |
| Terminal response | < 100ms keystroke echo |
| File sync (zip) | < 5 seconds for 10MB project |
| Preview tunnel setup | < 5 seconds after port bind |
| List scroll (FlatList) | 60 FPS for 1000 files |

---

## Notes & Future Considerations

- **Alternative Frameworks**: LynxJS/VanJS evaluated for <200ms TTI. Stick with Expo for ecosystem maturity. Re-evaluate if performance becomes critical.
- **New Architecture (Fabric)**: Enable React Native's new architecture once stable for better editor performance.
- **Web Support**: Expo web build possible for tablet/desktop users. Share 90% of codebase.
- **Collaboration**: Operational Transform (OT) or Yjs for real-time collaborative editing. Not in MVP.
- **Local AI**: Consider running small models (Qwen 2.5 7B) inside containers for offline coding. Requires GPU free tier or ARM CPU inference.
- **Tunneling Upgrade**: If localhost.run becomes unreliable, switch to self-hosted FRP or buy domain + Cloudflare Tunnel. Both are drop-in replacements.
