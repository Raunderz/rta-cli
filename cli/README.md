<pre align="center">
 _  .-')   .-') _      ('-.     
( \( -O ) (  OO) )    ( OO ).-. 
 ,------.  /     '._   / . --. / 
|  /\'. |'--...__)  | \-.  \  
|  /  | |'--.  .--'.-'-'  |  | 
|  |_.' |   |  |    \| |_.'  | 
|  .  '.'   |  |     |  .-.  | 
|  |\  \    |  |     |  | |  | 
 \'--' '--'   \'--'     \'--' \'--'
</pre>
<p align="center">AI-native coding agent for your terminal</p>
<p align="center">
  <a href="https://github.com/Raunderz/rta-cli/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="https://www.python.org/downloads/"><img alt="Python" src="https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square" /></a>
  <a href="https://rta-three.vercel.app"><img alt="Homepage" src="https://img.shields.io/badge/homepage-rta--three.vercel.app-orange?style=flat-square" /></a>
</p>

---

**Rta CLI** is an AI-native coding agent that runs in your terminal. It uses the RTA backend for managed model access with tier-based rate limits — no API keys required. Bring your own key if you want, or just run `rta` and go.

> **By [Rounders](https://github.com/Raunderz)**

---

## Install

Download the source zip from the [releases page](https://github.com/Raunderz/rta-cli/releases) or clone the repo, then:

```bash
cd rta-cli
uv sync
uv run rta
```

That's it. No API key setup needed — Rta connects to the managed backend by default.

### Use your own API keys

If you prefer to use your own provider:

```bash
# Set your key
export OPENAI_API_KEY="sk-..."

# Run with your provider
uv run rta --provider openai -m gpt-4o
```

Supported providers: `openai`, `anthropic`, `deepseek`, `github-copilot`, `ollama`, and any OpenAI-compatible endpoint.

---

## Quick examples

```bash
uv run rta                          # Start with managed backend
uv run rta -c                       # Continue most recent session
uv run rta -r <session-id>          # Resume a specific session
uv run rta -p "fix the failing test" # Single prompt, then exit
uv run rta --extra-tools web_search,web_fetch  # Enable extra tools
```

---

## What it does

Rta reads, searches, edits, and writes code. It runs shell commands, searches the web, and connects to external tools — all from a single prompt in your terminal.

### Core tools

Enabled by default:

| Tool | What it does |
| --- | --- |
| `read` | Read file contents with pagination and image support |
| `edit` | Exact text replacement for surgical code changes |
| `write` | Create or fully overwrite files |
| `bash` | Run shell commands |
| `grep` | Regex search inside files |
| `find` | Glob-based file discovery with `.gitignore` awareness |

### Extra tools

Enable with `--extra-tools` or in config:

| Tool | What it does |
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

## TUI

Rta runs a full terminal UI with:

- **`@`** to fuzzy-search files and directories
- **Tab** for path completion
- **Enter** to queue prompts while the agent is running
- **Alt+Enter** to queue a steer message
- **Esc** to interrupt

### Slash commands

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

### Shell commands

| Prefix | Behavior |
| --- | --- |
| `!command` | Run and show result in chat |
| `!!command` | Run, show result, and send output to the LLM |

---

## Configuration

Config lives at `~/.rta/config.toml` and is created automatically on first run.

```toml
[llm]
default_provider = "rta"
default_model = "rta-auto"

[tools]
extra = ["web_search", "web_fetch"]

[ui]
theme = "gruvbox-dark"

[permissions]
mode = "prompt"
```

---

## Sessions

Sessions are stored as append-only JSONL files in `~/.rta/sessions/`.

```bash
uv run rta --continue          # Resume most recent session
uv run rta --resume <id>       # Resume specific session
```

---

## Providers

**Managed backend (default):** No API key needed. Just run `rta`.

**Bring your own key:**

- **OpenAI** — `OPENAI_API_KEY`
- **Anthropic** — `ANTHROPIC_API_KEY`
- **DeepSeek** — `DEEPSEEK_API_KEY`
- **GitHub Copilot** — OAuth via `/login`
- **Ollama** — local models, no key needed
- **OpenAI-compatible** — any `/v1` endpoint (LM Studio, vLLM, etc.)

```bash
uv run rta --provider openai --model gpt-4o
uv run rta --provider anthropic --model claude-sonnet-4-20250514
uv run rta --provider ollama --model llama3
uv run rta --base-url http://localhost:11434/v1 --model llama3
```

---

## Permissions

| Mode | Behavior |
| --- | --- |
| `prompt` | Ask before mutating tool calls (default) |
| `auto` | Skip approval prompts |

---

## Tool binaries

Rta uses these for fast file discovery and search:

- **[`fd`](https://github.com/sharkdp/fd)** — fast file discovery
- **[`ripgrep`](https://github.com/BurntSushi/ripgrep)** — fast content search

If missing, Rta can download them automatically.

---

## Building from source

```bash
git clone https://github.com/Raunderz/rta-cli.git
cd rta-cli
uv sync
uv run rta
```

### Build binary

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
