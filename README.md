# Rta

Rta is an AI-assisted development ecosystem spanning a Python CLI, a FastAPI backend, a Go container execution service, a Lite XL-based desktop IDE, a React Native mobile app, and a Preact marketing website.

It is designed as a practical alternative to complex development setups — providing a "ready-to-use" environment for AI-assisted coding, quick edits, Git operations, and lightweight development tasks across devices.

## Architecture

```
User
  ├── CLI (Python)              cli/
  ├── Desktop IDE (Lite XL)     rta-desktop/
  ├── Mobile App (Expo/RN)      app/
  └── Website (Preact)          website/
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
        Docker Containers
```

## Components

### CLI (`cli/`)

The most mature component — a full-featured AI coding agent with 30+ native tool schemas (file ops, git, search, LSP, MCP), interactive chat, session management, auto-update, and semantic search. Routes all AI calls through the Rta backend middleware.

### Backend (`backend/`)

FastAPI middleware providing authentication (API key + GitHub OAuth + hCaptcha), AI provider proxy with automatic fallback across 5 providers, tier-based rate limiting, telemetry logging to Supabase, and a reverse proxy to the Go execution service.

### Container Execution Service (`mobile_backend/`)

Go HTTP/WebSocket server managing ephemeral Docker containers for remote code execution. Features WebSocket PTY terminals, Cloudflare tunnel URLs for web previews, abuse detection, and automatic cleanup.

### Desktop IDE (`rta-desktop/`)

A lightweight AI-powered IDE forked from Lite XL (C/Lua), integrating an Odin agent via JSON-RPC 2.0 for AI orchestration. Provides a native editing experience with AI assistance.

### Mobile App (`app/`)

React Native (Expo) mobile app with file browser, CodeMirror-based editor, Git integration (isomorphic-git), terminal emulator, and AI chat interface.

### Website (`website/`)

Preact + Vite SPA hosted on Vercel with auth, pricing tiers, release downloads, docs, blog, dashboard, and a standalone chat interface.

## Status

This is an active long-term project. The CLI and backend are the most mature components, with the desktop IDE and mobile app under active development.

## Plan

1. **CLI** — Built and actively maintained (v0.4.0). Serves as the primary interface and testing ground for AI agent capabilities.
2. **Backend** — Fully functional middleware layer handling auth, AI proxying, rate limiting, and telemetry.
3. **Desktop IDE** — Lite XL fork with Odin agent integration in progress.
4. **Mobile App** — Expo/React Native client connected to the backend, under active development.
5. **Container Service** — Go-based Docker execution environment with WebSocket shell and tunneling.

## License

MIT

Copyright 2026 schallten
