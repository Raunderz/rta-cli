---
slug: cli-agent-architecture
title: "Building the RTA CLI Agent"
date: "May 6, 2026"
readTime: "6 min read"
excerpt: "How we implemented project auto-discovery, context persistence, and parallel tool execution."
tags: ["CLI", "Python", "Architecture"]
---

# Rta CLI Agent Architecture

The CLI component is the foundation of Rta. We designed it to be highly context-aware without requiring backend modifications.

## Core Intelligence

We implemented project auto-discovery by scanning the workspace on startup. The CLI detects:
- **Language/Framework**: Reading \`pyproject.toml\