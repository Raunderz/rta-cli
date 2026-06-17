---
slug: rta-cli-v030-raw
title: "Rta CLI v0.3.0: Going Raw"
date: "May 9, 2026"
readTime: "3 min read"
excerpt: "Why we stripped the UI, removed Rich, and moved to a minimalist v0.3.0 architecture."
tags: ["CLI", "Performance", "Minimalism"]
---

# Rta CLI v0.3.0: Going Raw

Today we're releasing Rta CLI v0.3.0. It's a fundamental shift in our philosophy.

We stripped the UI. We removed the \`rich\` library. We went raw.

## Why Strip the UI?

In v0.2.0, we used the \`rich\` library for panels, tables, and colored ASCII art. It looked great in a modern terminal. But "looking great" is a distraction for a tool that's meant to be a high-performance extension of your brain.

We noticed three things:
1. **Binary Size**: \`rich\` and its dependencies (Pygments, etc.) added nearly 7MB to our binary.
2. **Startup Latency**: Even a few hundred milliseconds of import time is too much when you're jumping in and out of tasks.
3. **Fragility**: Fancy ASCII panels break in many environments (CI logs, old SSH sessions, constrained mobile terminals).

In v0.3.0, Rta is now **Raw**.

## Minimalist Architecture

- **Zero Heavy Dependencies**: We removed \`rich\` and moved to lightweight, raw ANSI escape codes for basic coloring.
- **Icon-Driven UI**: Replaced complex ASCII art and panels with simple, durable icons like \`>>\`.
- **Fast Startup**: v0.3.0 is near-instant. The cold start time has been reduced by ~60%.
- **Surgical Output**: No more fancy borders. You get the code, the logs, and the results — unadorned.

## New SOTA Features

Despite the UI diet, the engine is more powerful than ever. v0.3.0 introduces:
- **Streaming Responses**: The agent no longer waits for a full completion — text streams to your terminal token by token, cutting perceived latency to near zero.
- **apply_diff**: A new tool for atomic multi-file edits using standard unified diffs.
- **Session Resume**: Use \`rta chat --resume <id>\` to pick up exactly where you left off.
- **Workspace Tracking**: Rta now remembers your last workspace and tracks it across sessions.
- **AST-Aware Refactoring**: Surgical Python renames using \`libcst\`.
- **Lean RAG (Semantic Search)**: A pure Python BM25 indexer that provides smart code search without heavy ML dependencies. No 100MB model downloads — just fast, local, keyword-relevance ranking.
- **Repo Mapping (Skeleton)**: Automatically generates a high-level map of your project's architecture. The agent can "see" all classes and functions across your entire codebase in a single glance, making complex navigation trivial.
- **Micro-LSP Bridge**: Seamlessly connects to existing language servers (Pyright, clangd, gopls) on your machine. Gives the agent deep understanding of type errors and the ability to "Go to Definition" across your entire project.

## The Raw Philosophy

A developer tool should be invisible. It should feel like an extension of your terminal, not a guest application running inside it. 

Rta v0.3.0 is designed for the developer who values speed over screenshots. It's raw, it's fast, and it's ready.

Download the v0.3.0 binary:
- [Linux/macOS](https://rta-three.vercel.app/rta)
- [Windows](https://rta-three.vercel.app/rta.exe)
`
    },
    {