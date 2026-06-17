---
slug: mobile-cloud-ide
title: "Building Rta: A Cloud IDE for Mobile"
date: "May 8, 2026"
readTime: "5 min read"
excerpt: "How we're reimagining mobile development with ephemeral containers, streaming terminals, and an AI-native workflow."
tags: ["Architecture", "Mobile", "AI"]
---

# Building Rta: A Cloud IDE for Mobile

What if you could build and ship software from your phone? Not just check commits or review PRs — actual development. Feature work, bug fixes, deployments. Everything.

That's what we're building with Rta.

## The Problem with Mobile Development Today

The best developers I know are constrained by their desk. They have powerful thinking time during commutes, coffee breaks, or waiting in lines — but their laptop isn't with them. So those ideas vanish.

The existing solutions are broken:

- **SSH into a server** — Clunky, disconnected from your workflow, no local files
- **Termux** — Powerful but requires manual setup, dependency management, and technical knowledge that becomes a barrier
- **GitHub mobile app** — Read-only. You can review, not build
- **Online IDEs (Gitpod, CodeSpaces)** — Desktop-first, heavy, unusable on mobile screens

There's a gap. Mobile hardware is now powerful enough. The use cases are real. But the tooling doesn't exist.

## Our Approach: The Cloud Execution Model

Rta isn't running code on your phone. Your phone is a thin client — a window into a remote execution environment.

Here's the flow:

1. **Start a session** — Your local project gets zipped and deployed to an ephemeral Docker container
2. **Code + Chat** — Edit files locally, chat with an AI that has full context of your project
3. **AI makes changes** — Proposed diffs appear in your editor. Accept or reject with a tap
4. **Preview** — Run \`npm run dev\` and get a public URL streamed directly to your phone
5. **End session** — Container dies, files sync back, commit locally

The key insight: **the container is the source of truth during a session, not your phone**. Your phone is the interface. This eliminates the hardest problem in mobile development — syncing state between a local editor and a remote execution environment.

## Why Ephemeral Containers?

A fresh Ubuntu container for every session. No cleanup, no drift, no "it worked on my machine" problems.

When you start a session, you get:
- A clean environment with your project installed
- A full terminal with internet access
- SSH tunneling for preview URLs
- All the compute you need, isolated from everyone else

When you end the session, the container dies. Files come back to your phone. You commit with git locally. It's clean.

This also means **zero setup**. You don't configure runtimes, install dependencies, or manage environments. The container has what you need. Always.

## The AI-Native Workflow

Traditional IDEs treat AI as a plugin. We treat AI as the primary interface.

When you're in a chat with Rta, you're not just prompting a language model. You're working with an agent that has:
- Full context of your project structure
- Access to run commands in your session
- The ability to propose file changes that you can review before accepting

You say "add authentication to the login endpoint" and the AI:
1. Reads your existing auth setup
2. Writes the necessary code changes
3. Shows you a diff in your editor
4. Offers to run tests

It's pair programming, but your partner never gets tired and works at the speed of inference.

## Technical Architecture

The mobile app is built with Expo + JavaScript. No TypeScript overhead, runs everywhere.

- **CodeMirror 6** in a WebView for the editor — native touch, mobile-optimized
- **xterm.js** for streaming terminal output via WebSocket
- **isomorphic-git** for offline local version control
- **expo-file-system** for persistent local storage

The execution layer is Go. A small, focused service that manages Docker container lifecycle, WebSocket bridges for the terminal, and SSH tunnels for preview URLs.

The backend is FastAPI — auth, API key validation, routing to our AI agent. The AI agent handles model selection and streaming.

## Zero Infrastructure Overhead

The clever part: we use \`localhost.run\` for tunneling. No self-hosted proxy servers, no domain management, no Cloudflare. Just SSH tunnels spun up inside each container, giving users public URLs for their preview servers.

This means we can run on free-tier cloud infrastructure. Oracle Cloud ARM nodes, Hetzner, whatever we can get hands on. Add a new node by spinning it up and having it call home to the FastAPI registry.

## What's Next

We're building in phases. Foundation first — the editor, the file tree, basic git operations. Then session management with real terminal access. AI integration comes after the basics are solid.

The vision is clear: developers should be able to build real software from their phone. Not as a novelty, but as a legitimate workflow.

We launch when this is true.
`
    },
    {