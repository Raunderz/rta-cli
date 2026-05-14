import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { Link, useLocation } from 'wouter';
import { marked } from 'marked';

export const BlogPage = ({ params }) => {
  const [, setLocation] = useLocation();
  const [selectedArticle, setSelectedArticle] = useState(null);
  const articles = [
    {
      slug: "rta-cli-v040-constellation",
      title: "Rta CLI v0.4.0: The Constellation Update",
      date: "May 14, 2026",
      readTime: "4 min read",
      excerpt: "Dynamic MCP plugins, infinite extensibility, and the arrival of the tool constellation.",
      tags: ["MCP", "Plugins", "Architecture"],
      commit: "v0.4.0",
      body: `
# Rta CLI v0.4.0: The Constellation Update

In v0.3.0, we went raw. We stripped the UI to find the engine's core.

In v0.4.0, we're expanding that engine into an ecosystem. We call this **The Constellation Update**.

## The Constellation Philosophy

A star is powerful, but a constellation defines a map. 

Until now, Rta's tools were fixed — hardcoded into the binary. If you wanted the agent to talk to GitHub, Slack, or a Postgres database, we had to write Python code for it. 

With v0.4.0, Rta is now a **Dynamic MCP Client**. It no longer just has a set of tools; it has an expanding constellation of them.

## Dynamic MCP Plugin System

We've implemented full support for the **Model Context Protocol (MCP)**. This means Rta can now connect to any MCP server — local or remote — and instantly inherit its capabilities.

- **Dynamic Discovery**: Rta scans your \`mcp_config.json\` on startup, connects to your configured servers, and automatically namespaces their tools (e.g., \`mcp_github_create_issue\`).
- **Zero-Code Integration**: You can add support for Google Search, GitHub, AWS, or your own internal company tools just by adding a few lines to a JSON file. No Rta updates required.
- **Persistent Transports**: We've built a global process cache. Once an MCP server starts, it stays alive. This eliminates cold-start latency, making external tool calls feel as fast as native ones.
- **Universal Schema Mapping**: Rta handles the complex task of converting MCP's JSON Schema definitions into the specific format required by our AI backend.

## New Default Tools

To showcase the power of the Constellation, v0.4.0 ships with two powerful integrations ready to be activated:

1. **Search (DuckDuckGo)**: Give the agent the ability to research documentation, find latest library versions, and browse the web without an API key.
2. **GitHub**: Full access to repositories, issues, and pull requests. The agent can now manage your project's lifecycle from within the chat.

## Under the Hood

- **Auto-Generating Config**: Rta now creates a documented \`~/.rta/mcp_config.json\` template on first run, making onboarding seamless.
- **Cross-Platform RPC**: Our JSON-RPC implementation has been refined for maximum stability across Windows, Linux, and macOS.
- **Review Mode Safety**: Dynamic MCP tools respect our \`/review\` mode. They are read-only by default until you grant them permission, keeping your codebase safe.

## Join the Constellation

The goal of Rta has always been to build the fastest, most capable AI-native terminal. By opening the doors to the MCP ecosystem, we're making Rta infinitely extensible.

Download the v0.4.0 binary:
- [Linux/macOS](https://rta-three.vercel.app/rta)
- [Windows](https://rta-three.vercel.app/rta.exe)
`
    },
    {
      slug: "rta-cli-v030-raw",
      title: "Rta CLI v0.3.0: Going Raw",
      date: "May 9, 2026",
      readTime: "3 min read",
      excerpt: "Why we stripped the UI, removed Rich, and moved to a minimalist v0.3.0 architecture.",
      tags: ["CLI", "Performance", "Minimalism"],
      commit: "v0.3.0",
      body: `
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
      slug: "mobile-cloud-ide",
      title: "Building Rta: A Cloud IDE for Mobile",
      date: "May 8, 2026",
      readTime: "5 min read",
      excerpt: "How we're reimagining mobile development with ephemeral containers, streaming terminals, and an AI-native workflow.",
      tags: ["Architecture", "Mobile", "AI"],
      commit: "mobile-cloud-ide",
      body: `
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
      slug: "why-built-rta",
      title: "Why We Built Rta",
      date: "May 7, 2026",
      readTime: "4 min read",
      excerpt: "Understanding the purpose and motivation behind Rta: A mobile-first, AI-assisted code editor.",
      tags: ["Product", "Vision"],
      commit: "initial",
      body: `
# Why We Built Rta

Rta is being built to address the difficulty of mobile-based development workflows, especially those relying on tools like Termux. While powerful, such tools often require manual setup, dependency management, and technical knowledge that can be a barrier for many users.

## Instant-Use Environment

Rta aims to simplify this experience by providing an instant-use environment for:
* Quick code edits
* Emergency bug fixes
* Viewing and understanding repositories on the go
* Lightweight development tasks without setup overhead

## Core Integration

It combines a lightweight code editor, Git integration, and AI assistance into a single mobile application. It is designed for developers who need fast access to code and intelligent support without setting up a full development environment. We want to bridge the gap between heavy desktop IDEs and completely unoptimized mobile experiences.
`
    },
    {
      slug: "cli-agent-architecture",
      title: "Building the RTA CLI Agent",
      date: "May 6, 2026",
      readTime: "6 min read",
      excerpt: "How we implemented project auto-discovery, context persistence, and parallel tool execution.",
      tags: ["CLI", "Python", "Architecture"],
      commit: "1cc10cb",
      body: `
# Rta CLI Agent Architecture

The CLI component is the foundation of Rta. We designed it to be highly context-aware without requiring backend modifications.

## Core Intelligence

We implemented project auto-discovery by scanning the workspace on startup. The CLI detects:
- **Language/Framework**: Reading \`pyproject.toml\`, \`package.json\`, \`Cargo.toml\`, etc.
- **Test Frameworks**: Identifying \`pytest\`, \`vitest\`, \`cargo test\`.
- **Linter Configs**: Checking for \`.eslintrc\`, \`ruff.toml\`.

This allows the agent to automatically deduce the correct commands when a user says "run tests" or "lint the project".

## Parallel Tool Execution

To speed up operations, we implemented a dependency graph for tool execution. If multiple tool calls are independent (e.g., \`get_files_info\` and \`list_directory\`), they execute concurrently. Dependent tools (e.g., \`grep_search\` followed by \`edit_file\`) execute sequentially.
`
    }
  ];

  useEffect(() => {
    if (params?.slug) {
      const article = articles.find(a => a.slug === params.slug);
      setSelectedArticle(article || null);
      if (article) window.scrollTo(0, 0);
    } else {
      setSelectedArticle(null);
    }
  }, [params?.slug]);

  if (selectedArticle) {
    const htmlContent = marked(selectedArticle.body);

    return (
      <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px; max-width: 800px;">
        <div style="margin-bottom: 2rem;">
          <Link href="/blog" class="nav-link" style="font-family: var(--font-mono); font-size: 0.75rem;">&larr; Back to Blog</Link>
        </div>
        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
          {selectedArticle.tags.map(tag => (
            <span class="mono" style="font-size: 0.6rem; padding: 4px 10px; border: 1px solid var(--border); color: var(--text-muted);" key={tag}>{tag}</span>
          ))}
        </div>
        <h2 style="margin-bottom: 1rem; font-size: clamp(2.2rem, 6vw, 3.5rem); line-height: 1; font-family: var(--font-display);">{selectedArticle.title}</h2>
        <div style="display: flex; gap: 2rem; margin-bottom: 3rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; flex-wrap: wrap;">
          <span class="mono" style="color: var(--text-secondary); font-size: 0.8rem;">{selectedArticle.date}</span>
          <span class="mono" style="color: var(--text-secondary); font-size: 0.8rem;">{selectedArticle.readTime}</span>
        </div>
        <div class="markdown-body" dangerouslySetInnerHTML={{ __html: htmlContent }} />
      </div>
    );
  }

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="section-header">
        <h2>Transmissions</h2>
        <p class="mono">Technical Blog</p>
      </div>
      <div style="display: flex; flex-direction: column; gap: 2rem; max-width: 800px; margin: 0 auto;">
        {articles.map(article => (
          <div class="feature-card" style="cursor: pointer;" onClick={() => setLocation(`/blog/${article.slug}`)} key={article.slug}>
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1.2rem; flex-wrap: wrap;">
              {article.tags.map(tag => (
                <span class="mono" style="font-size: 0.6rem; padding: 4px 10px; border: 1px solid var(--border); color: var(--text-muted);" key={tag}>{tag}</span>
              ))}
            </div>
            <h3 style="font-size: clamp(1.3rem, 4vw, 1.6rem); margin-bottom: 1rem; font-family: var(--font-display);">{article.title}</h3>
            <p style="margin-bottom: 2rem; color: var(--text-secondary);">{article.excerpt}</p>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 1.5rem; gap: 1rem; flex-wrap: wrap;">
              <span class="mono" style="font-size: 0.65rem; color: var(--text-muted);">{article.date}</span>
              <span class="mono" style="font-size: 0.65rem; color: var(--text-muted);">{article.readTime}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
