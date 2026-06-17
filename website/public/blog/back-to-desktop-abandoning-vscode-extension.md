---
slug: back-to-desktop-abandoning-vscode-extension
title: "Back to Desktop: Why We Abandoned the VS Code Extension"
date: "June 15, 2026"
readTime: "4 min read"
excerpt: "We tried building a VS Code extension. The binary was too big, the integration was too complex. So we went back to the desktop app — and it's working."
tags: ["Desktop", "VS Code", "Lite XL", "Strategy"]
---

# Back to Desktop: Why We Abandoned the VS Code Extension

Two weeks ago, we wrote about [building a VS Code extension](/blog/cli-first-then-editor) that wraps the \`rta\` CLI as a sidecar. The plan was clean: let VS Code handle the editor, let the CLI handle the AI.

We're abandoning that plan.

## The Size Problem

The \`rta\` binary is 60MB. That's the PyInstaller bundle — Python runtime, all dependencies, the entire agent. When we tried packaging it as a VS Code extension sidecar, the math didn't work:

- VS Code extension market limit: **50MB** (recommended)
- Our binary: **60MB**
- VS Code itself: **300MB+**

We'd be shipping an extension larger than most VS Code themes, containing a full Python runtime that duplicates half of what VS Code already has. Users would download 60MB just to get a chat sidebar.

VS Code has some of the best AI agents right now — Copilot, Cursor, Cline. They work because they're tightly integrated with the editor's internals. Our approach of bolting a Python binary onto the side was never going to compete with that level of integration.

## The Integration Complexity

Even if we solved the size issue, the integration was wrong. VS Code extensions live in a webview — a sandboxed iframe with limited access to the editor's rendering pipeline. Our agent needs:

- Streaming text display with proper formatting
- Tool approval buttons that feel native
- Session history and file tree integration
- Real-time diff previews
- Direct access to editor events (file open, save, cursor position)

Packing all of that into a VS Code webview meant fighting the extension API's limitations. No direct access to the editor's text buffer. No native UI controls. Everything through message passing and DOM manipulation.

The VS Code extension API is powerful for what it's designed for — language servers, syntax highlighting, sidebar panels. But an AI agent that needs deep process integration, real-time streaming, and native UI controls is a different beast entirely.

We also looked at existing open-source VS Code AI extensions like Cline and Continue.dev for reference. Their repos were massive — hundreds of thousands of lines of TypeScript we'd need to understand and extend. And honestly? We didn't know TypeScript. The learning curve plus the codebase size made it clear we'd spend months just understanding the existing code before writing a single line of our own.

Lua, on the other hand, we already knew. Lite XL's plugin system was familiar territory.

## Why Desktop Won

We already had a desktop app. Lite XL — 11K lines of C, Lua plugins, instant startup. The problem was never the editor. The problem was the agent.

When we [forked Kon](/blog/forking-kon-a-new-cli-foundation) and built the Python CLI with \`--stdio\` pipe mode, everything clicked:

- **Binary detection**: The desktop app finds \`rta\` on PATH or in \`~/.rta/cli_path\`
- **Pipe IPC**: JSON-lines over stdin/stdout — simple, debuggable, no HTTP overhead
- **Streaming**: Text deltas flow directly from the CLI process to the Lua renderer
- **Tool approval**: Auto-approved in desktop context, inline approve/deny when needed
- **Session history**: Reads JSONL files directly, no API calls needed

The entire integration is 800 lines of Lua. No webview sandbox. No message passing. Direct process communication. No 50MB binary limit. No extension marketplace constraints.

## What We Learned

The [desktop IDE evolution](/blog/desktop-ide-evolution) taught us that lightweight wins. The [CLI-first approach](/blog/cli-first-then-editor) taught us that the agent is the product. This iteration taught us that **the right container matters**.

VS Code is a fantastic editor with a mature extension ecosystem. But extending it with a 60MB Python binary creates more problems than it solves. A Lua plugin in a C editor gives us direct process access, native UI, and zero size overhead.

We're not competing with VS Code's AI features. We're building something different — a lightweight, agent-native desktop environment where the CLI is the engine and the editor is just the cockpit.

## What's Next

The desktop app is functional. Chat works, streaming works, tool calls work, session history works. What's left:

- **Diff previews**: Show file changes inline before applying
- **File tree integration**: Browse and open files from the chat
- **Keyboard shortcuts**: Navigate between chat and editor naturally
- **Theme integration**: Match the editor's color scheme

We're not abandoning IDE integration. We're just building it where it makes sense — in a lightweight container that doesn't fight us at every step.
      `
    },
    {