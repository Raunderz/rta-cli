---
slug: cli-first-then-editor
title: "CLI-First, Then Editor: Why We're Building a VS Code Extension"
date: "May 31, 2026"
readTime: "4 min read"
excerpt: "Halting work on the standalone Lite XL desktop IDE and refocusing on a VS Code extension that wraps our existing CLI agent."
tags: ["Desktop", "VS Code", "Extension", "Strategy"]
---

# CLI-First, Then Editor: Why We're Building a VS Code Extension

For months, we've been working on a standalone desktop IDE — first based on Eclipse Theia, then pivoting to a Lite XL fork, with an Odin agent sidecar planned for Phase 3. We've written about it, we've committed code to it, and we've learned a lot.

We're halting that work.

Not because a desktop IDE is the wrong goal. But because we were building it the wrong way — from the editor inward, instead of from the agent outward.

## The CLI Is the Product

The Rta CLI is a complete AI coding agent. It has:

- Multi-engine web search and URL fetching
- MCP (Model Context Protocol) plugin support
- LSP integration (diagnostics, go-to-definition)
- Full git workflow (status, diff, log, commit, PR)
- File editing with apply_diff and AST-aware refactoring
- Semantic codebase search (BM25 index + repo skeleton)
- Memory persistence (memorize/recall across sessions)
- Session management, auto-update, and a modern async TUI

The CLI doesn't need an editor. The CLI *is* the editor — it modifies files, runs commands, searches code, and manages projects. What it needs is a good UI surface.

## Why Not Lite XL?

Lite XL is a beautiful piece of engineering. A tiny C core (~11K lines), extensive Lua plugin system, fast rendering. But maintaining a fork means:

- Keeping up with upstream Lite XL changes
- Building and debugging platform-specific C code (SDL3, Freetype, PCRE2, inotify/kqueue/FSEvents)
- Maintaining a plugin manager for distribution
- Bundling a terminal plugin, file tree, syntax highlighting — things VS Code already does perfectly

Every hour spent on editor infrastructure is an hour not spent on the agent.

## The VS Code Extension

The new plan: build a VS Code extension that wraps the existing \`rta\` CLI binary as a sidecar process.

\`\`\`
┌──────────────────────────────────────────────┐
│  VS Code Extension (pure JS)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Chat     │ │ Agentic  │ │ Codebase     │  │
│  │ Panel    │ │ Editing  │ │ Indexer      │  │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       └────────────┼──────────────┘           │
│                    │ stdin/stdout JSON-RPC     │
│  ┌─────────────────┴──────────────────────┐   │
│  │  rta CLI (sidecar binary)              │   │
│  │  (web_search, MCP, LSP, git, tools)   │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
\`\`\`

The extension never calls an LLM. It delegates everything to the CLI — all existing tools, all future improvements, instantly.

## What This Unlocks

- **Full editor for free** — VS Code's file tree, git integration, syntax highlighting, terminal, multi-window
- **Cross-platform out of the box** — VS Code runs everywhere
- **Zero editor maintenance** — we don't fork, we extend
- **Instant feature parity** — every CLI improvement is an extension improvement
- **No C core** — the agent is Python, the extension is JS

## What About lite-xl?

The \`rta-desktop/\` directory stays. It's full of working code and lessons learned. The Lite XL knowledge — Lua plugins, rendering pipeline, process management — is valuable. But active development shifts to the extension.

## Phased Rollout

1. **Chat panel** — sidebar webview, streaming responses, file/selection context, slash commands
2. **Agentic editing** — diff review, multi-file changes, terminal integration
3. **Codebase awareness** — semantic indexing, @codebase retrieval, dependency graphs
4. **Self-hosted inline** — optional Ollama integration for local inline completions
5. **MCP tools** — expose VS Code capabilities as agent-callable tools

## The CLI-First Philosophy

The CLI is the source of truth. The extension is a surface. This means:

- Update the CLI = update the extension
- Use the CLI headlessly on servers, in CI, from mobile
- The extension is a desktop GUI for the same agent

We started by building an editor and trying to bolt an agent onto it. Now we're building an agent and wrapping it in an editor.

The difference is everything.
`
    },
    {