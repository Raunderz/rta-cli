---
slug: forking-kon-a-new-cli-foundation
title: "Forking Kon: Why We Replaced the CLI with a Better Engine"
date: "June 5, 2026"
readTime: "5 min read"
excerpt: "After six major releases of the original Rta CLI, we're replacing the entire engine with a forked and enhanced version of the open-source kon project. Here's why."
tags: ["CLI", "Architecture", "Technical Debt", "Kon"]
---

# Forking Kon: Why We Replaced the CLI with a Better Engine

Six versions. Dozens of tools. A full-featured AI coding agent with web search, LSP integration, MCP plugins, semantic codebase indexing, AST refactoring, and session management.

And yet, we knew we had to scrap the engine.

## The Problem

The original \`cli/\` codebase had accumulated significant technical debt. After several iterations (v0.1 through v0.5), two parallel architectures coexisted — a legacy synchronous loop (\`agent.py\