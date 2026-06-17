---
slug: rta-cli-domain-exploration
title: "Domain Exploration: Web Research Comes to Rta CLI"
date: "May 31, 2026"
readTime: "5 min read"
excerpt: "fetch_url, multi-engine research expansion, and a roadmap for turning the CLI into a full research tool for AI-assisted development."
tags: ["CLI", "Research", "Web", "Architecture"]
---

# Domain Exploration: Web Research Comes to Rta CLI

Research is one of the hardest things for an AI coding agent to do well. The model only knows what it was trained on. If your codebase uses a library released last week, or you need to understand a rapidly changing API, or you're debugging against live documentation — the agent is blind.

We've been slowly building out the CLI's ability to explore the web, not just search it. This post covers what shipped and what's coming.

## fetch_url: From Snippet to Substance

The original \`web_search\` tool was useful but shallow. It returned three lines of snippet text per result. The agent could see that a page existed, but couldn't read it. Like having a card catalog but no books.

\`fetch_url\` solves this. Give it a URL, and it:

1. Downloads the page (up to 512KB, 15s timeout)
2. Strips HTML, scripts, styles, nav, footer, headers
3. Decodes HTML entities (named and numeric)
4. Extracts the \`<title>\` tag
5. Returns up to 100KB of clean readable text

Now the agent can search → find an interesting result → read the full page. The research loop is complete.

\`\`\`
web_search("python 3.13 pattern matching")
  → gets 8 results with titles, snippets, URLs
fetch_url(result[0].url)
  → reads the full article, 80KB of clean text
  → agent understands the feature in depth
\`\`\`

## Multi-Engine Research Pipeline

The existing search already aggregates DuckDuckGo, SearXNG, and Wikipedia. But we're expanding to six sources:

| Engine | Type | Status |
|--------|------|--------|
| DuckDuckGo | General web | Live |
| SearXNG | Meta-search (3 instances) | Live |
| Wikipedia | Encyclopedia | Live |
| **ArXiv** | Technical papers | Planned |
| **GitHub search** | Code & repos | Planned |
| **Stack Exchange** | Q&A with code | Planned |
| **YouTube transcripts** | Tutorial content | Planned |

Each source is free, API-key-less, and adds a different flavor of knowledge. ArXiv gives you papers. GitHub gives you implementations. Stack Exchange gives you debugging wisdom. YouTube gives you walkthroughs.

## Prompt Injection Safety

Reading the open web means reading untrusted content. A malicious page could embed fake system prompts, markdown role blocks, or hidden instructions designed to hijack the agent's behavior. We've built a multi-layer defense:

- **HTML comment stripping** — \`${"<"}!-- -->\` blocks removed before any parsing
- **Structural tag removal** — \`${"<"}script>\