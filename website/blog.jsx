import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { Link, useLocation } from 'wouter';
import { marked } from 'marked';

export const BlogPage = ({ params }) => {
  const [, setLocation] = useLocation();
  const [selectedArticle, setSelectedArticle] = useState(null);
  const articles = [
    {
      slug: "rta-cli-domain-exploration",
      title: "Domain Exploration: Web Research Comes to Rta CLI",
      date: "May 31, 2026",
      readTime: "5 min read",
      excerpt: "fetch_url, multi-engine research expansion, and a roadmap for turning the CLI into a full research tool for AI-assisted development.",
      tags: ["CLI", "Research", "Web", "Architecture"],
      commit: "domain-exploration",
      body: `
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

- **HTML comment stripping** — `<!-- -->` blocks removed before any parsing
- **Structural tag removal** — `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` removed with their contents
- **Full tag stripping** — all remaining HTML tags removed, leaving only plain text
- **Pattern-based filtering** — regex detection of common injection patterns: "ignore previous instructions", fake `\`\`\`system` markdown blocks, `[System]` lines, persona-switching commands, and base64-encoded task payloads
- All matched patterns are replaced with `[redacted]` before the text reaches the LLM

This means the agent can safely read any URL — documentation, forums, blog posts, even adversarial content — without risk of prompt hijacking from the page itself.

## Multi-Query Depth

The biggest quality lever isn't adding sources — it's asking better questions. We're building a sub-query expander: when you ask one question, the agent generates 3-5 specific search queries, runs them all in parallel, and deduplicates the results.

\`\`\`
User: "How do I implement WebAuthn in Go?"
  → Sub-queries:
    "WebAuthn Go library example"
    "go webauthn registration flow"
    "passkeys implementation golang"
    "webauthn server configuration go"
  → 4 searches × 8 results = 32 deduplicated sources
\`\`\`

## What's Next

The research pipeline is becoming a first-class subsystem in the CLI, on par with the tool execution engine and the codebase index. Long-term, we want:

- **Research sessions** — persistent, saveable research contexts with visited URLs and extracted facts
- **Source credibility scoring** — prioritize official docs, trusted authors, recent content
- **Offline fallback** — cached results from previous sessions when the network is unavailable

The CLI is no longer just an agent — it's an explorer.
`
    },
    {
      slug: "cli-first-then-editor",
      title: "CLI-First, Then Editor: Why We're Building a VS Code Extension",
      date: "May 31, 2026",
      readTime: "4 min read",
      excerpt: "Halting work on the standalone Lite XL desktop IDE and refocusing on a VS Code extension that wraps our existing CLI agent.",
      tags: ["Desktop", "VS Code", "Extension", "Strategy"],
      commit: "cli-first-editor",
      body: `
# CLI-First, Then Editor: Why We're Building a VS Code Extension

For months, we've been working on a standalone desktop IDE — first based on Eclipse Theia, then pivoting to a Lite XL fork, with an Odin agent sidecar planned for Phase 3. We've written about it, we've committed code to it, and we've learned a lot.

We're halting that work.

Not because a desktop IDE is the wrong goal. But because we were building it the wrong way — from the editor inward, instead of from the agent outward.

## The CLI Is the Product

The Rta CLI is a complete AI coding agent. It has:

- Multi-engine web search and URL fetching
- MCP (Model Context Protocol) plugin support
- LSP integration (diagnostics, go-to-definition)
- Full git workflow (status, diff, log, commit, PR)
- File editing with apply_diff and AST-aware refactoring
- Semantic codebase search (BM25 index + repo skeleton)
- Memory persistence (memorize/recall across sessions)
- Session management, auto-update, and a modern async TUI

The CLI doesn't need an editor. The CLI *is* the editor — it modifies files, runs commands, searches code, and manages projects. What it needs is a good UI surface.

## Why Not Lite XL?

Lite XL is a beautiful piece of engineering. A tiny C core (~11K lines), extensive Lua plugin system, fast rendering. But maintaining a fork means:

- Keeping up with upstream Lite XL changes
- Building and debugging platform-specific C code (SDL3, Freetype, PCRE2, inotify/kqueue/FSEvents)
- Maintaining a plugin manager for distribution
- Bundling a terminal plugin, file tree, syntax highlighting — things VS Code already does perfectly

Every hour spent on editor infrastructure is an hour not spent on the agent.

## The VS Code Extension

The new plan: build a VS Code extension that wraps the existing \`rta\` CLI binary as a sidecar process.

\`\`\`
┌──────────────────────────────────────────────┐
│  VS Code Extension (pure JS)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Chat     │ │ Agentic  │ │ Codebase     │  │
│  │ Panel    │ │ Editing  │ │ Indexer      │  │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘  │
│       └────────────┼──────────────┘           │
│                    │ stdin/stdout JSON-RPC     │
│  ┌─────────────────┴──────────────────────┐   │
│  │  rta CLI (sidecar binary)              │   │
│  │  (web_search, MCP, LSP, git, tools)   │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
\`\`\`

The extension never calls an LLM. It delegates everything to the CLI — all existing tools, all future improvements, instantly.

## What This Unlocks

- **Full editor for free** — VS Code's file tree, git integration, syntax highlighting, terminal, multi-window
- **Cross-platform out of the box** — VS Code runs everywhere
- **Zero editor maintenance** — we don't fork, we extend
- **Instant feature parity** — every CLI improvement is an extension improvement
- **No C core** — the agent is Python, the extension is JS

## What About lite-xl?

The \`rta-desktop/\` directory stays. It's full of working code and lessons learned. The Lite XL knowledge — Lua plugins, rendering pipeline, process management — is valuable. But active development shifts to the extension.

## Phased Rollout

1. **Chat panel** — sidebar webview, streaming responses, file/selection context, slash commands
2. **Agentic editing** — diff review, multi-file changes, terminal integration
3. **Codebase awareness** — semantic indexing, @codebase retrieval, dependency graphs
4. **Self-hosted inline** — optional Ollama integration for local inline completions
5. **MCP tools** — expose VS Code capabilities as agent-callable tools

## The CLI-First Philosophy

The CLI is the source of truth. The extension is a surface. This means:

- Update the CLI = update the extension
- Use the CLI headlessly on servers, in CI, from mobile
- The extension is a desktop GUI for the same agent

We started by building an editor and trying to bolt an agent onto it. Now we're building an agent and wrapping it in an editor.

The difference is everything.
`
    },
    {
      slug: "securing-the-rta-ecosystem",
      title: "Securing the Rta Ecosystem: Hardening Phase Complete",
      date: "May 31, 2026",
      readTime: "4 min read",
      excerpt: "A deep dive into the technical measures we've taken to harden our full-stack infrastructure, from cloud terminal safety to advanced frontend sanitization.",
      tags: ["Security", "FastAPI", "Go", "Architecture"],
      commit: "security-hardening",
      body: `
# Securing the Rta Ecosystem: Hardening Phase Complete

As Rta grows from a prototype into a robust developer platform, security has moved from a feature to a foundation. We've just completed a project-wide security hardening phase, addressing every layer of our stack — from the browser to the ephemeral cloud containers.

## Frontend: Advanced Content Sanitization

In a platform that handles AI-generated code and technical documentation, preventing cross-site scripting (XSS) is paramount. We've integrated industry-standard sanitization libraries to ensure that every byte of Markdown-to-HTML conversion is scrubbed for malicious payloads.

This means you can safely analyze complex frontend code, including script-heavy templates, without risk to your browser session. Your environment is a sandbox, and we've reinforced the glass.

## Cloud Backend: Hardening the Edge

Our Go-based mobile backend handles the lifecycle of your remote development environments. We've implemented several critical hardening measures to protect this infrastructure:

- **Strict Resource Constraints**: Every cloud terminal now operates under a hardened set of HTTP timeouts and request body limits. This prevents denial-of-service attempts and ensures that resource-intensive operations remain stable.
- **WebSocket Origin Validation**: We've locked down our streaming terminal connections to only allow verified frontend origins, eliminating the risk of cross-site hijacking.
- **Mandatory Shell Authentication**: Terminal access now requires explicit API key verification during the WebSocket handshake. Only you can touch your containers.

## API Infrastructure: Production-Ready Defaults

The FastAPI-powered backend has been updated to align with the highest security standards:

- **Minimalist CORS**: We've restricted cross-origin policies to only the exact methods and headers required for system operation.
- **Zero-Trust Defaults**: Production environments now default to secure-only configurations. Auto-reload features and internal documentation endpoints are disabled by default, minimizing the public attack surface.
- **Robust Configuration**: Environment-driven security flags now control critical behaviors like cookie safety, ensuring that our development and production environments remain isolated and secure.

## A Continuous Commitment

Security isn't a one-time project; it's a culture. By completing this hardening phase, we've established a "Secure-by-Default" baseline for all future Rta developments. 

Whether you're coding from a hillside on your phone or building at your desk, you can trust that Rta is protecting your data, your credits, and your project's integrity.

Stay safe and keep building.
`
    },
    {
      slug: "rta-cli-v050-modern-core",
      title: "Rta CLI v0.5.0: The Modern Core Rewrite",
      date: "May 30, 2026",
      readTime: "7 min read",
      excerpt: "A complete async event-driven rewrite of the Rta CLI — faster, more reliable, and feature-complete with all legacy tools ported.",
      tags: ["CLI", "Architecture", "Async", "Python"],
      commit: "modern-core",
      body: `
# Rta CLI v0.5.0: The Modern Core Rewrite

The CLI has been rewritten from the ground up. Not a refactor — a full replacement of the synchronous chat loop with an async event-driven architecture. Every tool, every feature, every edge case from the legacy mode has been ported. But the engine underneath is completely new.

## Why Rewrite?

The original Rta CLI was built as a synchronous loop. It worked — you typed, it responded, tools executed in sequence, text printed to the terminal. But synchronous has hard limits:

- **No streaming**: The response appeared all at once, after the entire completion finished. Perceived latency was terrible.
- **No cancellation**: Ctrl+C could kill the process, but not gracefully stop a tool execution mid-flight.
- **No real-time UI**: Tool execution status, thinking blocks, and loading states were impossible to render incrementally.
- **Blocking I/O**: Every file read, bash command, and API call blocked the entire event loop.

The new architecture solves all of these.

## The Async Engine

The core is now a chain of async generators:

\`\`\`
User Input → Agent.run_turn() → Provider.stream() → events → TUI.render()
\`\`\`

Each layer yields typed \`Event\` objects (\`TextDeltaEvent\`, \`ToolStartEvent\`, \`UsageEvent\`, etc.) that flow downstream. The UI renders each event as it arrives — text appears token by token, tools show their execution status in real time, thinking blocks unfold inline.

The \`AsyncRtaProvider\` uses \`httpx.AsyncClient\` for non-blocking SSE streaming. When the backend sends \`{"type": "text", "content": "Hello"}\`, it becomes a \`TextDeltaEvent\` and the UI updates. When \`{"type": "usage"}\` arrives, token counts are accumulated for the session summary.

## Tool Architecture

Every tool is now a \`BaseTool\` subclass with a Pydantic parameter model and an async \`execute()\` method:

\`\`\`python
class BashParams(BaseModel):
    command: str = Field(description="The command to execute")
    timeout: int = Field(default=120)

class BashTool(BaseTool):
    name = "bash"
    description = "Execute a bash command"
    parameters = BashParams

    async def execute(self, params, cancel_event=None):
        proc = await asyncio.create_subprocess_shell(params.command, ...)
        stdout, stderr = await proc.communicate()
        return ToolResult(success=proc.returncode == 0, result=stdout)
\`\`\`

Legacy tools that were synchronous (file operations, git commands, web search, memory storage) are wrapped via \`asyncio.to_thread\`, preserving the original implementation while running in the async event loop.

## What's New

Beyond the architecture, v0.5.0 introduces several improvements:

### Session Stats on Exit
\`\`\`
─ Session: 2m 34s | In: 482 | Out: 26 ─
\`\`\`
Token usage and duration printed on exit, matching the legacy behavior. Falls back to character-based estimates when backend usage events aren't available.

### Slash Commands Handled Locally
\`/help\`, \`/clear\`, \`/exit\`, and any CLI subcommand (\`/status\`, \`/whoami\`) are intercepted before reaching the AI model. \`/help\` shows available commands instantly without consuming API quota.

### Rich TUI with Live Rendering
The \`RtaTUI\` class uses \`rich.live\` for real-time display updates. Loading spinner shows status messages while waiting for the first response token. Thinking blocks, text output, and tool executions each have their own rendering panel.

### Dynamic MCP Tool Integration
MCP servers (GitHub, Search, etc.) are loaded dynamically via \`MCPToolWrapper\`. Tool schemas are converted to OpenAI-compatible format using each MCP server's raw \`inputSchema\` rather than Pydantic's \`model_json_schema()\`, avoiding missing type fields that caused all upstream providers to reject the tool definitions.

## All Legacy Tools Ported

Every tool from the original CLI has been ported to the async architecture:

| Category | Tools |
|---|---|
| **Read/Write** | \`get_file_contents\`, \`get_files_info\`, \`write_file\`, \`delete_file\`, \`create_dir\`, \`list_directory\` |
| **Edit** | \`edit\`, \`apply_diff\`, \`edit_file_ast\` |
| **Search** | \`grep_search\`, \`glob_search\`, \`semantic_search\` |
| **Execute** | \`bash\` (with timeout, process tree killing, tail truncation) |
| **LSP** | \`get_diagnostics\`, \`go_to_definition\` |
| **Git** | \`git_status\`, \`git_diff\`, \`git_log\`, \`git_commit\`, \`git_create_pr\`, \`git_branch\` |
| **Web** | \`web_search\` (DuckDuckGo, SearXNG, Wikipedia) |
| **Reasoning** | \`sequential_thinking\` |
| **Memory** | \`memorize\`, \`recall\`, \`forget\` |
| **Meta** | \`discover_project\`, \`list_skills\`, \`get_repo_skeleton\`, \`question\` |
| **MCP** | Dynamic tools from any configured MCP server |

## Provider Compatibility

The backend communication layer was rebuilt to match the actual API contract. After discovering that the legacy endpoint path was incorrect (\`/v1/chat/completions\` instead of \`/v1/chat\`) and that the SSE response format uses custom event types (\`text\`, \`thought\`, \`tool_calls\`, \`usage\`, \`error\`, \`done\`) rather than the OpenAI \`choices[0].delta\` format, the provider now correctly parses the backend's schema.

Empty \`AssistantMessage\` entries (with \`content=None\` and \`tool_calls=None\`) that accumulated in session history from failed turns are filtered before sending — these ghost messages broke provider message alternation and caused all upstream models to return \`ProviderDownError\`.

## The Result

\`\`\`
uv run rta --modern

rta> hello
────────────────────────────────────────────────────────────────
**Hello! How can I assist you today?**
────────────────────────────────────────────────────────────────
\`\`\`

Faster startup. Real-time streaming. Graceful cancellation. Proper session persistence. All legacy tools. The same Rta experience, rebuilt for performance and reliability.

Run with \`--modern\` to try the new engine. Legacy mode remains available for comparison.
`
    },
    {
      slug: "mobile-terminal-keyboard",
      title: "The Mobile Terminal Keyboard Odyssey",
      date: "May 28, 2026",
      readTime: "6 min read",
      excerpt: "Getting Android to show a keyboard inside a WebView terminal took longer than building the entire backend. Here is the full saga.",
      tags: ["Mobile", "Android", "Terminal", "WebView"],
      commit: "main",
      body: `
# The Mobile Terminal Keyboard Odyssey

This is the story of how something as simple as a keyboard almost broke us.

We built a cloud terminal — bash inside a Docker container, streamed over WebSocket, rendered in a React Native WebView with xterm.js. The container orchestration runs on a [Go-based backend](https://schallten.github.io/container-provider/) (basic version is open source). The desktop version works on the first try. The mobile version took four full rewrites and a descent into the deepest corners of Android WebView.

Here is everything that went wrong and how we fixed it.

## Act 1: It Does Not Connect

The first problem was the easiest. The WebSocket URL was wrong.

We have a backend that manages the Docker containers and a proxy layer in front of it. The WebSocket URL our app was constructing didn't match the proxy's routing — it pointed at the wrong path. The proxy itself also had a routing bug where it forwarded connections to the wrong upstream endpoint.

Fix: align the URL path in the app with the proxy's routes, and fix the proxy's upstream path.

Result: WebSocket connects. Terminal displays output. We can see neofetch running on a phone. Victory lap? Not yet. We cannot type a single character.

## Act 2: The TextInput Trap

The obvious approach: put a \`TextInput\` overlay on top of the WebView, capture keystrokes, and forward them to the WebSocket.

\`\`\`jsx
<TextInput
  style={{ position: 'absolute', left: 0, top: 0, width: 1, height: 1, opacity: 0.01 }}
  onChangeText={(text) => ws.send(text)}
/>
\`\`\`

The cursor bleeds through the transparent overlay. You set \`color: transparent\` — the cursor is still there, a blinking vertical line floating on top of your terminal emulator. Set \`caretHidden={true}\` — gone. But now the input itself is unreliable. Sometimes keystrokes arrive, sometimes they disappear into the void. The \`TextInput\` overlay has a mind of its own.

We tried everything: \`pointerEvents\`, z-index stacking, \`position: absolute\` vs \`fixed\`, different opacity values. The \`TextInput\` would randomly lose focus, the keyboard would dismiss, and the user would be stuck staring at a terminal they could see but not touch.

After two rewrites of this approach, we abandoned it entirely.

## Act 3: The about:blank Curse

Next idea: skip React Native's input layer entirely. Handle everything inside the WebView. The WebView renders an HTML page with xterm.js. xterm.js creates a hidden \`<textarea>\` internally. On desktop, clicking the terminal focuses this textarea and you can type. On mobile, the hidden textarea (\`opacity: 0\`, \`left: -9999em\`) cannot be focused by Android — the system keyboard refuses to appear for elements that are fully invisible.

We tried everything to override the textarea's styles after xterm creates it:
- Setting \`opacity: 0.01\`
- Moving it to \`left: 0\`, \`top: 0\`
- Making it \`width: 1px\`, \`height: 1px\`
- Calling \`term.focus()\` in every lifecycle hook
- Polling with \`setTimeout\` every 200ms to find and fix the textarea

None of it worked reliably.

We also discovered a nasty restriction: when the WebView source is \`{ html: ... }\`, it renders from \`about:blank\`. Some WebView behaviors — particularly around autofocus and programmatic focus — are restricted on \`about:blank\` origins. We considered switching to a \`data:text/html\` URI but that came with its own set of CORS-like limitations for loading xterm from CDN.

## Act 4: postMessage Betrayal

Even if we could get the keyboard to show, we needed a reliable way to send keystrokes from React Native to the WebView. The canonical approach is \`postMessage\` — sending a JSON payload to the WebView's message handler.

On the WebView side, a \`window.addEventListener('message', ...)\` handler receives it.

This works 90% of the time. The other 10%, the message is silently dropped. No error, no warning — the data just never arrives. This is a known issue with \`postMessage\` on Android WebView when the WebView is still loading or when the JavaScript context is in certain states.

The alternative: \`injectJavaScript\`. It is less elegant but bulletproof. It directly executes a string in the WebView's JavaScript context. It always works.

This was the turning point. We rewrote all accessory bar buttons (TAB, ^C, ^D, arrow keys) to use \`injectJavaScript\`, storing the WebSocket reference globally for direct access.

## Act 5: The Final Shape

The solution that finally worked combined several insights:

1. **Make the textarea full-size and visible.** Instead of hiding xterm's textarea, we made it cover the entire terminal area with \`opacity: 0.01\`, \`width: 100%\`, \`height: 100%\`, \`position: absolute\`. This way, tapping anywhere on the terminal touches the textarea directly.

2. **Focus on tap.** Both \`click\` and \`touchend\` event handlers on the terminal container call \`textarea.focus()\`. This ensures the textarea receives focus regardless of how the user interacts.

3. **\`keyboardDisplayRequiresUserAction={false}\`.** This React Native WebView prop is essential. It tells Android to show the keyboard when a text input is programmatically focused, without requiring a direct user tap on the input itself.

4. **\`injectJavaScript\` for reliable communication.** All input from accessory buttons bypasses \`postMessage\` and goes directly through \`injectJavaScript\`.

5. **No TextInput overlay.** The xterm textarea itself is the input mechanism. \`term.onData()\` captures keystrokes and sends them through the WebSocket. The server echoes back, xterm displays.

## The Result

A React Native terminal component where:
- The Android keyboard appears when you tap the terminal
- Every keystroke reaches the server
- The WebSocket stays connected
- The accessory bar works reliably
- The cursor stays in its lane (no more z-order bleed)

The terminal now works on Android. It took four approaches, roughly 15 iterations, and an embarrassing number of commits with titles like "fix: reliable mobile keyboard trigger in terminal" followed by "fix: mobile keyboard not appearing in terminal WebView" followed by "fix: enable keyboard input in terminal WebView".

Some problems can only be solved by trying every wrong answer until the right one is the only option left.

The lesson: WebView + keyboard on Android is a minefield. Use \`injectJavaScript\`, not \`postMessage\`. Make your input element visible — \`opacity: 0.01\` is visible enough for Android but invisible to the user. And never assume something as simple as a keyboard will be simple.
`
    },
    {
      slug: "desktop-ide-evolution",
      title: "RTA Desktop: From Brackets to Lite XL",
      date: "May 25, 2026",
      readTime: "5 min read",
      excerpt: "Why we walked away from Eclipse Theia and forked a lightweight C editor instead.",
      tags: ["Architecture", "Desktop", "Lite XL"],
      commit: "lite-xl",
      body: `
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

The commit history tells the story. We had \`theia switch\`, then a cascade of \`fix: resolve npm install failures\`, \`migration done\`, and finally \`chore: remove entire desktop application source code and configuration\`.

We deleted the entire Theia codebase in a single commit. Thousands of lines of TypeScript, JSON configs, and fragile build scripts — gone.

It was the most productive day of the project.

## Life 3: Lite XL — The Fork That Changed Everything

We needed something radically different. Not another Electron shell pretending to be native. Not another TypeScript framework with a 200MB node\_modules graveyard.

We found **Lite XL**.

### Why Lite XL Won

Lite XL is written in **C with Lua scripting**. That's it. No Electron. No JavaScript runtime. No dependency tree from hell.

- **Startup time**: Under 100ms. It's instant.
- **Memory**: \~10MB baseline. It fits in L3 cache.
- **Build system**: Meson + Ninja. One command, no npm install, no node\_modules.
- **Extensibility**: Lua is embedded directly. You write plugins in the same language the editor uses internally.

### Forking Strategy

We didn't just use Lite XL — we **forked** it and made it our own:

1. **Rebranded the core**: RTA metadata, custom title, app icon, empty view.
2. **Kept the Odin agent**: Our AI engine remains a separate high-performance binary, communicating with the editor via process spawning.
3. **Lua plugin layer**: The integration surface is Lua — same language as Lite XL's core plugins. No FFI, no bridge code.

The migration plan says it best: *"Startup time under 1 second. Minimal memory footprint compared to Electron/Theia."*

We're comfortably exceeding both goals.

## What We Learned

| Phase | Editor | Memory | Startup | Outcome |
|-------|--------|--------|---------|---------|
| 1 | Brackets | ~80MB | 2-3s | Abandoned platform |
| 2 | Eclipse Theia | ~200MB | 5-10s | Deleted entire codebase |
| 3 | Lite XL (fork) | ~10MB | <100ms | Active development |

The pattern is clear: **complexity is the enemy of a good editor.**

Every abstraction layer, every runtime, every framework dependency adds cost — in memory, in startup time, in build fragility, in developer attention. Lite XL's C + Lua model is the antithesis of modern Electron-based editors. And that's precisely why it works.

## What's Next

The desktop IDE is live and available for Linux. It doesn't have AI agent features yet — those remain in the CLI for now. But the foundation is solid, fast, and endlessly hackable.

We're building the Lua plugin layer that will bridge the editor to the Odin agent. When that's done, RTA Desktop will have the same AI capabilities as the CLI, wrapped in a native editing experience that starts in under a second.

### A Note on the Core

Lite XL's C core has been a great foundation, but C is showing its age. Memory bugs, fragile cross-compilation, and the lack of modern tooling are recurring friction points. We've decided to **port the core from C to Nim**.

Why Nim? It compiles to C, so we can port one subsystem at a time — the Meson build system compiles Nim's C output alongside the remaining C files. There's no GC pause risk (we use ARC/ORC), C interop is a single \`{.importc.}\` declaration, and cross-compilation is built into the language. Same memory model, same performance, but with modern tooling, sum types, and a package manager that doesn't fight you.

The port is incremental and non-blocking — the editor ships throughout. We'll announce when the first Nim-based release is ready.

Download the binary from our [Releases page](/releases).
`
    },
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
