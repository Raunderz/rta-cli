---
slug: rta-cli-v050-modern-core
title: "Rta CLI v0.5.0: The Modern Core Rewrite"
date: "May 30, 2026"
readTime: "7 min read"
excerpt: "A complete async event-driven rewrite of the Rta CLI — faster, more reliable, and feature-complete with all legacy tools ported."
tags: ["CLI", "Architecture", "Async", "Python"]
---

# Rta CLI v0.5.0: The Modern Core Rewrite

The CLI has been rewritten from the ground up. Not a refactor — a full replacement of the synchronous chat loop with an async event-driven architecture. Every tool, every feature, every edge case from the legacy mode has been ported. But the engine underneath is completely new.

## Why Rewrite?

The original Rta CLI was built as a synchronous loop. It worked — you typed, it responded, tools executed in sequence, text printed to the terminal. But synchronous has hard limits:

- **No streaming**: The response appeared all at once, after the entire completion finished. Perceived latency was terrible.
- **No cancellation**: Ctrl+C could kill the process, but not gracefully stop a tool execution mid-flight.
- **No real-time UI**: Tool execution status, thinking blocks, and loading states were impossible to render incrementally.
- **Blocking I/O**: Every file read, bash command, and API call blocked the entire event loop.

The new architecture solves all of these.

## The Async Engine

The core is now a chain of async generators:

\`\`\`
User Input → Agent.run_turn() → Provider.stream() → events → TUI.render()
\`\`\`

Each layer yields typed \`Event\` objects (\`TextDeltaEvent\