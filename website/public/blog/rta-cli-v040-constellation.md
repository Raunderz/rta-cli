---
slug: rta-cli-v040-constellation
title: "Rta CLI v0.4.0: The Constellation Update"
date: "May 14, 2026"
readTime: "4 min read"
excerpt: "Dynamic MCP plugins, infinite extensibility, and the arrival of the tool constellation."
tags: ["MCP", "Plugins", "Architecture"]
---

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
- [Linux/macOS](/rta)
- [Windows](/rta.exe)
`
    },
    {