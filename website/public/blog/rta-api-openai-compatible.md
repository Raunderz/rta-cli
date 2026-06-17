---
slug: rta-api-openai-compatible
title: "Rta API: OpenAI-Compatible Endpoints for AI-Powered Development"
date: "June 5, 2026"
readTime: "3 min read"
excerpt: "We've launched a public API with OpenAI-compatible response formats. Build your own tools, integrate with any SDK, and chain Rta into your workflows."
tags: ["API", "OpenAI", "Developer Tools"]
---

# Rta API: OpenAI-Compatible Endpoints for AI-Powered Development

Today we're opening up the Rta backend as a public API. If you've been using the CLI, you already know what Rta can do — multi-provider AI routing, automatic fallback, streaming responses. Now you can access all of it programmatically.

## Why an API?

The CLI is powerful, but it's not the only way to build. We kept hearing the same request: "I want to use Rta's provider routing in my own tools." Whether you're building a custom IDE plugin, a code review bot, a research assistant, or just want to experiment with multi-provider inference — the API gives you the building blocks.

## What's Available

Four endpoints, each with a clear purpose:

| Endpoint | Method | Description |
|----------|--------|-------------|
| \`/v1/chat\` | POST | Core AI chat — streaming and non-streaming |
| \`/v1/usage\` | GET | Check your token and call usage |
| \`/v1/status\` | GET | Public service status |
| \`/health\` | GET | Health check |

The chat endpoint is the main one. It supports all the provider routing, automatic fallback, and tool calling that the CLI uses internally.

## OpenAI-Compatible Format

By default, Rta returns its own event format. But we've added an \`"format": "openai"\` option that switches the response to OpenAI's standard Chat Completions format.

This means you can use any OpenAI-compatible SDK or client library:

\`\`\`python
import openai

client = openai.OpenAI(
    base_url="https://schallten-a2xtbb49ws.hf.space/v1",
    api_key="your_rta_api_key"
)

response = client.chat.completions.create(
    model="rta-auto",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
\`\`\`

Streaming works too — the SSE format matches OpenAI's exactly:

\`\`\`python
stream = client.chat.completions.create(
    model="rta-auto",
    messages=[{"role": "user", "content": "Write a quicksort in Rust"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
\`\`\`

## Multi-Provider Routing

When you send \`"model": "rta-auto"\