<pre align="center">
░█░█░█▀█░█▀█
░█▀▄░█░█░█░█
░▀░▀░▀▀▀░▀░▀
</pre>
<p align="center">Minimal AI coding agent — fork of <a href="https://github.com/0xku/kon">Kon</a></p>
<p align="center">
  <a href="https://pypi.org/project/rta-cli/"><img alt="PyPI" src="https://img.shields.io/pypi/v/rta-cli?style=flat-square" /></a>
  <a href="https://www.python.org/downloads/"><img alt="Python" src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square" /></a>
  <a href="https://github.com/Raunderz/rta-cli/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="https://rta-three.vercel.app"><img alt="Homepage" src="https://img.shields.io/badge/homepage-rta--three.vercel.app-orange?style=flat-square" /></a>
</p>

---

**Rta CLI** is a minimal, fast AI coding agent for your terminal. Built on top of [Kon](https://github.com/0xku/kon) — a clean, minimal agent harness — with extra tools, provider support, and a focus on being lightweight and hackable.

> **By [Rounders](https://github.com/Raunderz)**

### Current Status

Right now, Rta CLI works with **your own API keys** — bring your own provider (OpenAI, Anthropic, DeepSeek, or any OpenAI-compatible endpoint). Full native provider support with built-in auth is planned for **v1.0.0**.

---

## Quick Start

### Install

```bash
pip install rta-cli
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install rta-cli
```

### Run

```bash
rta
```

### Common Examples

```bash
# Use your own API key
rta --provider openai -m gpt-4o

# Continue your latest session
rta -c

# Resume a specific session
rta -r <session-id>

# Enable extra tools
rta --extra-tools web_search,web_fetch

# Single prompt (headless)
rta -p "fix the failing test"
```

---

## Why Rta CLI

### Minimal by design

- **System prompt under 270 tokens** by default
- **6 core tools** for everyday coding work
- **11 extra tools** — web search, memory, LSP diagnostics, deep search, and more
- **Project instructions via `AGENTS.md`** — no bloat in the default harness
- **Lightweight TUI** with themes, session management, and slash commands

### Built on Kon

Rta CLI is a fork of [Kon](https://github.com/0xku/kon), a minimal coding agent with a clean architecture. We've extended it with:

| Extra Tool | What it does |
| --- | --- |
| `web_search` | Search the web with DuckDuckGo |
| `web_fetch` | Fetch and extract clean page content |
| `deep_search` | Multi-step web research |
| `memorize` / `recall` / `forget` | Persistent memory across sessions |
| `arxiv_search` | Search academic papers on arXiv |
| `so_search` | Search Stack Overflow |
| `github_search` | Search GitHub repositories and code |
| `youtube_transcript` | Extract YouTube video transcripts |
| `get_diagnostics` | Get LSP diagnostics from your editor |
| `go_to_definition` | Jump to symbol definitions |
| `semantic_search` | Embedding-based code search |
| `get_repo_skeleton` | Understand repo structure at a glance |
| `refactor_python` | Safe Python refactoring with CST |
| `sequential_thinking` | Step-by-step reasoning for complex tasks |
| MCP tools | Connect to any MCP server |

---

## Core Tools

Enabled by default:

| Tool | What it does |
| --- | --- |
| `read` | Read file contents with pagination and image support |
| `edit` | Exact text replacement for surgical code changes |
| `write` | Create or fully overwrite files |
| `bash` | Run shell commands |
| `grep` | Regex search inside files |
| `find` | Glob-based file discovery with `.gitignore` awareness |

---

## Interactive TUI

### Editor and Navigation

| Feature | How it works |
| --- | --- |
| File reference | Type `@` to fuzzy-search files and folders |
| Path completion | Press **Tab** to complete paths |
| Queued prompts | Press **Enter** while the agent is running to queue a follow-up |
| Steer queue | Press **Alt+Enter** to queue a steer message |
| Model switching | Use `/model` to switch interactively |
| Session browsing | Use `/resume` to browse prior sessions |

### Slash Commands

| Command | Description |
| --- | --- |
| `/new` | Start a new conversation |
| `/resume` | Browse and restore a saved session |
| `/model` | Switch model via picker |
| `/session` | Show session info and token stats |
| `/compact` | Compact the current conversation |
| `/handoff` | Create a focused handoff into a new session |
| `/themes` | Switch UI themes |
| `/permissions` | Switch permission mode |
| `/thinking` | Switch thinking level |
| `/export` | Export current session to HTML |
| `/copy` | Copy last assistant response to clipboard |
| `/login` | Authenticate with an OAuth provider |
| `/logout` | Remove provider credentials |
| `/help` | Show help and keybindings |
| `/quit` | Quit Rta |

### Shell Commands

| Prefix | Behavior |
| --- | --- |
| `!command` | Run and show result in chat |
| `!!command` | Run, show result, and send output to the LLM |

---

## Configuration

Config lives at `~/.config/kon/config.toml` and is created automatically on first run.

```toml
[llm]
default_provider = "openai"
default_model = "gpt-4o"

[tools]
extra = ["web_search", "web_fetch"]

[ui]
theme = "gruvbox-dark"

[permissions]
mode = "prompt"
```

Full config reference: [`src/kon/defaults/config.toml`](src/kon/defaults/config.toml)

---

## Sessions

Sessions are stored as append-only JSONL files in `~/.config/kon/sessions/`.

```bash
rta --continue          # Resume most recent session
rta --resume <id>       # Resume specific session
```

---

## Providers

Right now, use your own API keys with any supported provider:

- **OpenAI** — `OPENAI_API_KEY`
- **Anthropic** — `ANTHROPIC_API_KEY`
- **DeepSeek** — `DEEPSEEK_API_KEY`
- **GitHub Copilot** — OAuth via `/login`
- **OpenAI-compatible** — any `/v1` endpoint (Ollama, LM Studio, etc.)

```bash
rta --provider openai --model gpt-4o
rta --provider anthropic --model claude-sonnet-4-20250514
rta --base-url http://localhost:11434/v1 --model llama3
```

### v1.0.0 Roadmap

Native provider support with built-in auth — no API keys needed:

- RTA managed provider with fallback across multiple backends
- Tier-based rate limiting
- Built-in telemetry and usage tracking

---

## Permissions

| Mode | Behavior |
| --- | --- |
| `prompt` | Ask before mutating tool calls (default) |
| `auto` | Skip approval prompts |

```toml
[permissions]
mode = "prompt"
```

---

## Tool Binaries

Rta CLI depends on these for fast file discovery and search:

- **[`fd`](https://github.com/sharkdp/fd)** — fast file discovery
- **[`ripgrep`](https://github.com/BurntSushi/ripgrep)** — fast content search

If missing, Rta can download them automatically.

---

## Building from Source

```bash
git clone https://github.com/Raunderz/rta-cli.git
cd rta-cli
uv sync
uv run rta
```

### Build Binary

```bash
uv run pyinstaller rta.spec
```

---

## Documentation

- [Local models guide](docs/local-models.md)
- [Changelog](CHANGELOG.md)
- [Homepage](https://rta-three.vercel.app)

---

## Acknowledgements

- Built on [Kon](https://github.com/0xku/kon) by 0xku
- Inspired by [pi coding-agent](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent), Amp, Claude Code, and other terminal coding agents

---

## License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  <b>Rta — By <a href="https://github.com/Raunderz">Rounders</a></b>
</p>
