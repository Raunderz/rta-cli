---
slug: desktop-ide-evolution
title: "RTA Desktop: From Brackets to Lite XL"
date: "May 25, 2026"
readTime: "5 min read"
excerpt: "Why we walked away from Eclipse Theia and forked a lightweight C editor instead."
tags: ["Architecture", "Desktop", "Lite XL"]
---

# RTA Desktop: From Brackets to Lite XL

The desktop IDE has gone through three distinct lives. Each taught us something critical about what developers actually need from an editor, and each failure brought us closer to the right answer.

## Life 1: Brackets — The False Start

The first version of RTA Desktop was built on **Brackets**, Adobe's open-source code editor. At the time it seemed like a reasonable choice — it was lightweight, built with web technologies, and had a decent extension system.

In practice, Brackets was a dead end. Adobe had largely abandoned active development. The extension API was limited, the performance was mediocre, and the project's momentum had stalled years before we adopted it. We spent more time working around Brackets' limitations than building actual features.

The lesson: **don't build on a platform that's already in hospice care.**

## Life 2: Eclipse Theia — Overengineering Everything

We migrated to **Eclipse Theia**, the open-source framework behind VS Code alternatives. It seemed like the obvious upgrade — it had a modern architecture, a massive ecosystem of VS Code extensions, and serious corporate backing from Eclipse Foundation and TypeFox.

This was a mistake.

### The Theia Tax

Theia is essentially VS Code's architecture without Microsoft's optimization resources. We inherited:

- **Electron overhead**: 200MB+ baseline memory. Every tab, every panel, every extension consumed RAM like it was free.
- **Build complexity**: The TypeScript compilation pipeline was fragile. A single type error in a dependency could break the entire build. We had commits like "fix: resolve npm install failures and enable VS Code extension support" that were just trying to keep the dependency graph from collapsing.
- **Startup latency**: Cold starts routinely took 5-10 seconds. For an editor.
- **Breaking updates**: Every Theia release came with migration headaches. APIs changed without notice. Our local patches broke between point releases.

### The Breaking Point

The commit history tells the story. We had \`theia switch\