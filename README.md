# Rta

**Notice:** The CLI component is being migrated from the original `cli/` directory to a forked `kon/` implementation. This shift provides a cleaner, well‑tested foundation and resolves accumulated technical debt. See `kon/plan.md` for details.

Rta is an AI-assisted development ecosystem spanning a Python CLI, a FastAPI backend, a Go container execution service, a Lite XL-based desktop IDE, a React Native mobile app, a Preact marketing website, a VS Code extension, and a PR review bot.

It is designed as a practical alternative to complex development setups — providing a "ready-to-use" environment for AI-assisted coding, quick edits, Git operations, code review, and lightweight development tasks across devices.

## Architecture

```
User
  ├── CLI (Python)              cli/              — AI coding agent in terminal
  ├── Desktop IDE (Lite XL)     rta-desktop/      — Native AI-powered IDE
  ├── Mobile App (Expo/RN)      app/              — IDE on your phone
  ├── Website (Preact)          website/          — Dashboard, docs, pricing
  ├── VS Code Extension         extensions/       — RTA inside VS Code
  └── PR Bot                    rta-pr-bot/       — Automated PR review
              │
              ▼
    FastAPI Backend             backend/
      ├── Auth (Supabase + hCaptcha)
      ├── AI Proxy (Groq, Cerebras, SambaNova, OpenRouter, Gemini)
      ├── Rate Limiting (tier-based)
      └── Telemetry (Supabase)
              │
              ▼
    Go Executor Service         mobile_backend/
      ├── Docker container lifecycle
      ├── WebSocket PTY shell
      ├── Cloudflare Tunnel
      └── Abuse detection
              │
              ▼
        Docker Containers        — Ephemeral sandbox environments
```

## Components

### CLI (`cli/`)

The most mature component — a full-featured AI coding agent with 30+ native tool schemas (file ops, git, search, LSP, MCP), interactive chat, session management, auto-update, semantic search, and standalone binary distribution. Routes all AI calls through the Rta backend middleware.

### Backend (`backend/`)

FastAPI middleware providing authentication (API key + GitHub OAuth + hCaptcha), AI provider proxy with automatic fallback across 5 providers (Groq, Cerebras, SambaNova, OpenRouter, Gemini), tier-based rate limiting, telemetry logging to Supabase, Stripe billing, and a reverse proxy to the Go execution service.

### Container Execution Service (`mobile_backend/`)

Go HTTP/WebSocket server managing ephemeral Docker containers for remote code execution. Features WebSocket PTY terminals, Cloudflare tunnel URLs for web previews, workspace upload/download, chat execution via `rta ask`, abuse detection, and automatic cleanup.

### Desktop IDE (`rta-desktop/`)

A lightweight AI-powered IDE forked from Lite XL (C/Lua), integrating an Odin agent via JSON-RPC 2.0 for AI orchestration. Provides a native editing experience with AI assistance.

### Mobile App (`app/`)

React Native (Expo) mobile app with file browser, CodeMirror-based editor, Git integration (isomorphic-git), terminal emulator, and AI chat interface. Connects to the container executor for cloud-based development.

### Website (`website/`)

Preact + Vite SPA hosted on Vercel with auth, pricing tiers, release downloads, docs, blog, dashboard, and a standalone chat interface.

### VS Code Extension (`extensions/`)

Embeds the RTA CLI agent inside VS Code via a sidecar process with JSON-RPC communication. Planned features include chat webview, agentic editing, codebase indexing, and MCP tool integration.

### PR Bot (`rta-pr-bot/`)

A standalone GitHub webhook bot that reviews pull requests using the RTA API. On PR open or update, it fetches the diff, sends it to the RTA backend for analysis, and posts review comments — summary + line-by-line findings for bugs, security, performance, and code quality issues.

## Status

Active long-term project. The CLI and backend are the most mature components, with the desktop IDE, mobile app, VS Code extension, and PR bot under active development.

## Plan

1. **CLI** — Built and actively maintained (v0.5.0). Primary interface and testing ground for AI agent capabilities.
2. **Backend** — Fully functional middleware layer handling auth, AI proxying, rate limiting, and telemetry (v0.1.0).
3. **Desktop IDE** — Lite XL fork with Odin agent integration in progress.
4. **Mobile App** — Expo/React Native client, under active development.
5. **Container Service** — Go-based Docker execution environment (v1.0.0).
6. **Website** — Preact SPA on Vercel (v1.0.0).
7. **VS Code Extension** — Sidecar-based integration, early development.
8. **PR Bot** — Webhook-based PR reviewer, planned.

## License

MIT

Copyright 2026 schallten
