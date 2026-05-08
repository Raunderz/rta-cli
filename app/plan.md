# Rta — Cloud IDE for Mobile (Expo + React Native)

A mobile-first, AI-driven cloud development environment. Users write and edit code through an AI chat interface, with execution happening in ephemeral Docker containers streamed back to the device in real-time.

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
| **Mobile App** | Expo + JavaScript | Thin client: editor, terminal, chat, offline file storage |
| **FastAPI Backend** | Python (existing) | Auth, API key validation, routes requests to AI Agent |
| **AI Agent** | Your existing HTTP service | Token pool management, model routing (Qwen/Gemini/DeepSeek/etc.) |
| **Execution Service** | Go (`net/http` stdlib) | Dumb execution pipe: Docker lifecycle, WebSocket bridging, tunnel management |
| **Tunneling** | `localhost.run` via SSH | Zero-setup, no API keys, no self-hosted server |
| **Container** | Ubuntu + Docker | Ephemeral execution environment, glibc-compatible |

---

## Project Structure

```
rta/
├── app/                          # Expo + React Native mobile application
│   ├── src/
│   │   ├── components/           # Reusable UI (ChatBubble, FileTree, Terminal)
│   │   ├── screens/              # Main screens (Editor, Chat, Settings)
│   │   ├── navigation/           # Expo Router configuration
│   │   ├── hooks/                # Custom hooks (useSession, useAIStream, useGit)
│   │   ├── context/              # App-wide state (React Context + useReducer)
│   │   ├── utils/                # API clients, constants, helpers
│   │   └── types.js              # JSDoc typedefs
│   ├── assets/                   # Images, fonts
│   ├── App.js                    # Entry point
│   └── package.json
│
├── mobile-backend/               # ALL backend code
│   ├── python/                   # FastAPI auth service (your existing) in our backend folder in root. no need to remake its the same api cli and desktop ide use
│   │   ├── main.py
│   │   └── requirements.txt
│   │
│   ├── executor/                 # Go execution service
│   │   ├── main.go               # net/http entry point
│   │   ├── docker.go             # Container lifecycle
│   │   ├── websocket.go          # WS bridging (mobile ↔ container PTY)
│   │   ├── tunnel.go             # localhost.run SSH tunnel orchestration
│   │   ├── zip.go                # File sync (upload/download)
│   │   └── go.mod
│   │
│   └── scripts/
│       └── setup.sh
│
└── README.md
```

---

## Tech Stack

### Mobile App
| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | **Expo (bare workflow)** | Native modules support, mature ecosystem |
| Language | **JavaScript** | No compile step, no type system overhead, runs everywhere |
| Editor | **CodeMirror 6** | Lightweight, mobile-friendly touch, native diff view for AI changes |
| Terminal | **xterm.js** | Industry standard, runs in WebView |
| Local Git | **isomorphic-git** | Pure JS, works offline with Expo FileSystem shim |
| Local Files | **expo-file-system** | Native filesystem access, persists across sessions |
| State | **React Context + useReducer** | Built-in, no extra dependency, simple enough for this app |
| Styling | **StyleSheet** | No build step, no Tailwind config, React Native native |
| Lists | **FlatList** | Built-in, good enough for <1000 files |
| AI Streaming | **EventSource** (browser API) | No library needed, auto-reconnect, SSE support |
| Terminal Comms | **WebSocket** (browser API) | Bidirectional, needed for interactive shell |

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

### AI Interaction
1. User types in chat: *"Add error handling to the login function"*
2. App sends: `{api_key, session_id, message, current_file_context}` via SSE to FastAPI
3. FastAPI validates key, forwards to AI Agent
4. AI Agent selects model, streams response tokens back via SSE
5. Response arrives at mobile as stream — CodeMirror diff view highlights proposed changes
6. User taps **Accept** or **Reject**
7. If accept: app patches file locally, sends `git diff` to container via WebSocket command
8. If reject: discard, keep chatting

### Running a Web Server (Preview)
1. User (or AI) runs: `python -m http.server 8080` or `npm run dev`
2. Process binds to port inside container
3. Go detects port binding (via polling stdout or user-specified)
4. Go starts SSH tunnel inside container:
   ```bash
   ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 localhost.run
   ```
5. localhost.run gives public URL: `https://abc123.localhost.run`
6. Go parses URL from SSH stdout, sends to mobile via WebSocket
7. Mobile shows preview in WebView or external browser
8. On session end: container dies → SSH tunnel dies → URL 404s

### Ending a Session
1. User taps **"End Session"**
2. Go zips `/workspace` in container
3. Go sends zip to mobile app
4. Mobile extracts zip, updates local files via `expo-file-system`
5. User runs `git commit` via isomorphic-git (offline, local)
6. Go kills container, cleans up

---

## Build Plan: Phase by Phase

### Phase 0: Foundation (Days 1–2)
**Goal**: Running Expo shell with editor and chat UI.

- [ ] Initialize Expo project with blank JavaScript template
- [ ] Setup basic folder structure (`src/components`, `src/screens`, etc.)
- [ ] Create React Context + useReducer for app state (session, files, chat)
- [ ] Setup Expo Router for navigation:
  - Editor screen (CodeMirror 6 in WebView)
  - Chat screen (sidebar or bottom sheet)
  - File tree screen
- [ ] Integrate CodeMirror 6 in WebView with basic JS/TS support
- [ ] Build chat UI components (message bubbles, input, streaming indicator)
- [ ] Use FlatList for file tree rendering
- [ ] Setup local file storage with `expo-file-system`
- [ ] Create project structure and sample files for testing

**Deliverable**: App opens, shows file tree, opens files in CodeMirror, chat UI functional (mock responses).

---

### Phase 1: Local-First Git (Days 3–4)
**Goal**: Offline file versioning works.

- [ ] Install and configure isomorphic-git with Expo FileSystem shim
- [ ] Implement `init`, `add`, `commit`, `log`, `status` operations
- [ ] Build Git UI: commit history, diff viewer, branch indicator
- [ ] Add "Initialize Repository" and "Commit" actions in UI
- [ ] Test full flow: edit file → stage → commit → view log
- [ ] Handle edge cases: empty repos, merge conflicts (alert user)

**Deliverable**: User can create repo, make commits, view history — all offline.

---

### Phase 2: Terminal + Session Management (Days 5–7)
**Goal**: Mobile connects to Go service, gets a working terminal.

- [ ] Build Go service skeleton (`net/http`, health endpoint)
- [ ] Implement Docker container lifecycle:
  - Pull Ubuntu image
  - Start container with resource limits (`--memory=512m --cpus=0.5`)
  - Inject workspace
  - Execute commands via Docker exec
- [ ] Add WebSocket endpoint: mobile ↔ Go ↔ container PTY
- [ ] Integrate xterm.js in WebView, connect to Go WebSocket
- [ ] Build session management UI:
  - "Start Session" button with loading state
  - "End Session" button
  - Connection status indicator
- [ ] Implement zip upload: mobile project → Go → container `/workspace`
- [ ] Add API key header validation (mock FastAPI response for now)

**Deliverable**: User taps "Start Session", terminal opens, can run `ls`, `echo hello`, `python`.

---

### Phase 3: AI Integration (Days 8–10)
**Goal**: Chat connects to your existing AI Agent, streams responses.

- [ ] Add EventSource (SSE) client in mobile app for AI streaming
- [ ] Connect FastAPI backend to forward chat requests to AI Agent
- [ ] Build CodeMirror diff view: highlight AI-proposed changes
- [ ] Implement Accept/Reject actions for AI suggestions
- [ ] On accept: patch local file, send command to container to sync
- [ ] Add context gathering: send current file + project structure to AI
- [ ] Handle AI commands (e.g., AI says "run `npm install`") — show "Run" button in chat
- [ ] Add error handling: AI down, rate limited, invalid API key

**Deliverable**: Full AI chat flow: ask → stream response → see diff → accept → file updates locally and in container.

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

### Phase 5: Preview Tunneling (Days 13–14)
**Goal**: Users can view running web servers from their phone.

- [ ] Test SSH tunnel inside Ubuntu container:
  ```bash
  ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 localhost.run
  ```
- [ ] Modify Go service to run SSH tunnel command inside container
- [ ] Parse tunnel URL from SSH stdout
- [ ] Send tunnel URL to mobile via WebSocket
- [ ] Build preview UI: open in WebView or external browser
- [ ] Handle tunnel cleanup on session end (SSH process dies with container)
- [ ] Test with common servers: Python HTTP, Vite dev server, Node Express

**Deliverable**: User runs `npm run dev` → gets `https://abc123.localhost.run` → opens preview.

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
