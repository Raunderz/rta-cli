import { h } from 'preact';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const Section = ({ id, title, children }) => (
  <div id={id} style="margin-bottom: 5rem;">
    <h3 style="font-size: clamp(1.4rem, 4vw, 1.8rem); margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;">
      {title}
    </h3>
    <div class="markdown-body" style="font-size: 1rem; line-height: 1.8; color: var(--text-secondary);">
      {children}
    </div>
  </div>
);

const Md = ({ text }) => (
  <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(text)) }} />
);

const Badge = ({ color, children }) => (
  <span style={{
    display: 'inline-block', padding: '2px 8px', borderRadius: 'var(--radius-sm)',
    fontSize: '11px', fontWeight: 600, letterSpacing: '0.03em',
    background: color === 'green' ? 'rgba(16,185,129,0.15)' : color === 'yellow' ? 'rgba(251,191,36,0.15)' : 'var(--primary-light)',
    color: color === 'green' ? '#10B981' : color === 'yellow' ? '#D97706' : 'var(--primary)',
  }}>{children}</span>
);

const docs = [
  // ── Getting Started ──
  {
    id: 'getting-started',
    title: 'Getting Started',
    content: `### Install the CLI

Rta is a single binary with no dependencies.

**Linux / macOS:**
\`\`\`bash
curl -fsSL https://rta-three.vercel.app/rta -o rta
chmod +x rta
sudo mv rta /usr/local/bin/
\`\`\`

**Windows:**
Download \`rta.exe\` from the [Releases](/releases) page and add it to your PATH.

### Authenticate

\`\`\`bash
rta login
\`\`\`

This opens a browser for GitHub authentication. Your API key is stored at \`~/.rta/credentials\`.

### Start Coding

\`\`\`bash
cd your-project
rta chat
\`\`\`

That's it. The agent can read, edit, and run code in your project.`
  },

  // ── CLI Reference ──
  {
    id: 'cli',
    title: 'CLI Reference',
    content: `### Modes

| Mode | Command | Description |
|------|---------|-------------|
| **TUI** | \`rta chat\` | Full terminal UI with streaming, tool approval, session management |
| **REPL** | \`rta --repl\` | Minimal type-and-send interface, no TUI widgets |
| **Headless** | \`rta -p "prompt"\` | Single prompt, prints result, exits |
| **Pipe** | \`rta --stdio\` | JSON-lines IPC for IDE integration |

### Flags

| Flag | Description |
|------|-------------|
| \`-m, --model\` | Override the default model |
| \`--provider\` | Force a specific provider (\`rta\`, \`openai\`, \`ollama\`, etc.) |
| \`-p, --prompt\` | Run a single prompt non-interactively |
| \`-c, --continue\` | Resume the most recent session |
| \`-r, --resume <id>\` | Resume a specific session by ID |
| \`--extra-tools\` | Enable extra tools (\`web_search,web_fetch,memorize\`) |
| \`--repl\` | Minimal REPL mode |
| \`--stdio\` | JSON-lines pipe mode |

### Slash Commands (TUI)

| Command | Action |
|---------|--------|
| \`/help\` | Show available commands |
| \`/clear\` | Clear conversation history |
| \`/new\` | Start a new session |
| \`/model\` | Switch model |
| \`/resume\` | Browse and resume past sessions |
| \`/tree\` | Navigate session tree |
| \`/session\` | Show session info and stats |
| \`/compact\` | Summarize and compress conversation |
| \`/export\` | Export session to HTML |
| \`/copy\` | Copy last response to clipboard |
| \`/settings\` | Themes, permissions, thinking mode |
| \`/login\` | Login to a provider |
| \`/logout\` | Logout from a provider |
| \`/whoami\` | Show current user info |
| \`/quit\` | Exit (also \`exit\`, \`q\`) |`
  },

  // ── Desktop IDE ──
  {
    id: 'desktop',
    title: 'Desktop IDE',
    content: `RTA Desktop is a lightweight IDE built on [Lite XL](https://github.com/lite-xl/lite-xl) with an integrated AI chat panel.

### Download

Get it from the [Releases](/releases) page (Desktop IDE tab). Currently available for Linux.

### Setup

1. Place the \`rta\` binary in your \`PATH\`, or create \`~/.rta/cli_path\` pointing to it
2. Launch \`rta-desktop\`

### Chat Panel

The chat panel appears on the right side. It connects to the RTA CLI via pipe IPC.

- **Streaming responses** with animated indicator
- **Tool calls** shown inline — click to expand/collapse
- **Diff previews** for file edits with undo support
- **Session history** — browse and load past sessions

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| \`Return\` | Send message |
| \`Ctrl+Return\` | Send message (alternative) |
| \`Ctrl+N\` | New session |
| \`Ctrl+H\` | Toggle session history |
| \`Ctrl+Backspace\` | Delete word |
| \`Escape\` | Cancel streaming / Close history |
| \`Ctrl+Shift+C\` | Toggle chat panel |
| \`Ctrl+Shift+L\` | Toggle log view |

### Bundled Plugins

RTA Desktop includes 7 extra plugins beyond the Lite XL defaults:

| Plugin | What it does |
|--------|-------------|
| **minimap** | Code overview sidebar (toggle via command palette) |
| **sticky_scroll** | Pins scope/function headers at top of view |
| **tab_switcher** | Fuzzy search open tabs (\`Alt+P\`) |
| **autosave** | Auto-saves files after 1s idle |
| **centerdoc** | Centers code on screen, zen mode (\`Ctrl+Alt+Z\`) |
| **eval** | Evaluate Lua expressions inline (\`Ctrl+Alt+Return\`) |
| **dragdropselected** | Drag and drop selected text |

### Building from Source

\`\`\`bash
# Build the editor
meson setup build --wrap-mode=forcefallback
meson compile -C build
ln -sf ../../data build/src/data

# Build the CLI binary
cd ../cli
uv run python -m PyInstaller --clean --noconfirm rta.spec
cp dist/rta ../rta-desktop/bin/rta

# Run
./build/src/rta-desktop
\`\`\`

See the full [BUILD.md](https://github.com/Raunderz/rta/blob/main/rta-desktop/BUILD.md) for Windows and macOS instructions.`
  },

  // ── Tools ──
  {
    id: 'tools',
    title: 'Agent Tools',
    content: `The agent has access to tools that let it read, write, and execute code.

### Default Tools

These are always enabled:

| Tool | Description |
|------|-------------|
| \`read\` | Read file contents (with optional offset/limit) |
| \`edit\` | Edit files with find-and-replace |
| \`write\` | Create or overwrite files |
| \`bash\` | Run shell commands |
| \`grep\` | Search file contents with regex |
| \`find\` | Find files by name pattern |

### Extra Tools

Enable with \`--extra-tools\` or config:

| Tool | Description |
|------|-------------|
| \`web_search\` | Search the web |
| \`web_fetch\` | Fetch and read web pages |
| \`deep_search\` | Multi-step web research |
| \`memorize\` | Save facts to long-term memory |
| \`recall\` | Retrieve facts from memory |
| \`sequential_thinking\` | Structured step-by-step reasoning |
| \`arxiv_search\` | Search academic papers |
| \`so_search\` | Search Stack Overflow |
| \`github_search\` | Search GitHub repos and code |
| \`youtube_transcript\` | Get YouTube video transcripts |
| \`semantic_search\` | Search codebase semantically |
| \`get_diagnostics\` | Get LSP errors/warnings |
| \`go_to_definition\` | Jump to symbol definition |

### MCP Tools

Connect external tools via the Model Context Protocol. See [MCP Configuration](#mcp) below.`
  },

  // ── Providers ──
  {
    id: 'providers',
    title: 'Providers & Models',
    content: `Rta routes through multiple AI providers with automatic fallback.

### Built-in Providers

| Provider | Models |
|----------|--------|
| **rta** (default) | \`rta-auto\` — auto-routes across providers for best speed/quality |
| **openai** | GPT-4o, GPT-4.1, O3, O4-mini |
| **ollama** | Any locally running model |

### Using \`rta-auto\`

The default \`rta-auto\` model automatically selects the best available provider. No configuration needed — just authenticate with \`rta login\`.

### Custom Provider

Set environment variables or edit \`~/.rta/config.toml\`:

\`\`\`toml
[llm]
provider = "openai"
model = "gpt-4o"

[llm.api_keys]
openai = "sk-..."
\`\`\`

### Local Models (Ollama)

\`\`\`bash
# Start Ollama
ollama serve

# Use with Rta
rta chat --provider ollama --model llama3
\`\`\`

See [Configuration](#config) for all options.`
  },

  // ── Configuration ──
  {
    id: 'config',
    title: 'Configuration',
    content: `### Config File

Location: \`~/.rta/config.toml\`

Created automatically on first run. Edit it to customize behavior.

### Key Settings

\`\`\`toml
[llm]
provider = "rta"          # Provider name
model = "rta-auto"        # Model ID
base_url = ""             # Custom API endpoint

[ui]
theme = "default"         # TUI theme
thinking = false          # Show thinking tokens

[tools]
default = ["read", "edit", "write", "bash", "grep", "find"]
extra = []                # e.g. ["web_search", "memorize"]

[permissions]
auto_approve = false      # Skip tool approval prompts

[agent]
system_prompt = ""        # Custom system prompt addition
\`\`\`

### File Locations

| Path | Purpose |
|------|---------|
| \`~/.rta/config.toml\` | Main configuration |
| \`~/.rta/credentials\` | API keys (base64 encoded) |
| \`~/.rta/sessions/\` | Session history (JSONL) |
| \`~/.rta/skills/\` | User-installed skills |
| \`.rta/skills/\` | Project-specific skills |
| \`~/.rta/kon.log\` | Debug log |`
  },

  // ── MCP ──
  {
    id: 'mcp',
    title: 'MCP Configuration',
    content: `The Model Context Protocol (MCP) lets Rta connect to external tools like GitHub, databases, or custom APIs.

### Setup

Create or edit \`~/.rta/mcp_config.json\`:

\`\`\`json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
\`\`\`

### Available MCP Servers

| Server | Package | What it does |
|--------|---------|-------------|
| GitHub | \`@modelcontextprotocol/server-github\` | Repo management, issues, PRs |
| Filesystem | \`@modelcontextprotocol/server-filesystem\` | Extended file operations |
| Brave Search | \`@modelcontextprotocol/server-brave-search\` | Web search |

### Using MCP Tools

Once configured, MCP tools appear alongside built-in tools. The agent uses them automatically when relevant.`
  },

  // ── Mobile ──
  {
    id: 'mobile',
    title: 'Mobile App',
    content: `The RTA mobile app connects to your CLI sessions via WebSocket.

### Features

- **Chat** with the AI agent from your phone
- **Session sync** — resume conversations started on desktop
- **File preview** — view code changes made by the agent

### Limitations

Mobile provides chat and telemetry only. Full autonomous agent capabilities (file editing, shell execution) require the CLI or Desktop IDE.

### Setup

1. Install the app (scan QR code from [Releases](/releases))
2. Login with your RTA account
3. The app connects to your active CLI session automatically`
  },

  // ── Troubleshooting ──
  {
    id: 'troubleshooting',
    title: 'Troubleshooting',
    content: [
      '### CLI won\'t start',
      '',
      '- Check that `rta` is in your PATH: `which rta`',
      '- Verify credentials: `rta whoami`',
      '- Check logs: `cat ~/.rta/kon.log`',
      '',
      '### Desktop IDE shows "RTA CLI not found"',
      '',
      '- Place `rta` in your PATH, or',
      '- Create `~/.rta/cli_path` containing the absolute path to the binary',
      '- Restart the desktop',
      '',
      '### "Rate limit exceeded"',
      '',
      'Free tier limits: 10 calls/day. Check usage with `rta status` or upgrade at [Pricing](/pricing).',
      '',
      '### Tool permission prompts',
      '',
      'By default, the agent asks before running tools. To auto-approve:',
      '```toml',
      '# in ~/.rta/config.toml',
      '[permissions]',
      'auto_approve = true',
      '```',
      '',
      'Or use `rta chat --yolo` (use with caution).',
      '',
      '### Sessions not saving',
      '',
      'Sessions are stored at `~/.rta/sessions/`. Ensure the directory exists and is writable.',
    ].join('\n')
  },
];

const sidebarGroups = [
  { label: 'Overview', items: ['getting-started'] },
  { label: 'CLI', items: ['cli', 'tools', 'providers', 'config', 'mcp'] },
  { label: 'Clients', items: ['desktop', 'mobile'] },
  { label: 'Help', items: ['troubleshooting'] },
];

export const DocsPage = () => (
  <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
    <div class="docs-layout">
      <aside class="docs-sidebar">
        <h4 style="margin-bottom: 2rem; color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;">Documentation</h4>
        <nav style="display: flex; flex-direction: column; gap: 1.5rem;">
          {sidebarGroups.map(g => (
            <div key={g.label}>
              <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 600;">{g.label}</div>
              <div style="display: flex; flex-direction: column; gap: 0.4rem;">
                {g.items.map(id => {
                  const s = docs.find(d => d.id === id);
                  return s ? <a href={`#${s.id}`} class="nav-link" style="font-size: 0.85rem;" key={s.id}>{s.title}</a> : null;
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      <div style="flex: 1; max-width: 750px; width: 100%;">
        <div class="section-header" style="text-align: left; margin-bottom: 4rem;">
          <h2>Documentation</h2>
          <p>Everything you need to use RTA.</p>
        </div>

        {docs.map(s => (
          <Section id={s.id} title={s.title} key={s.id}>
            <Md text={s.content} />
          </Section>
        ))}
      </div>
    </div>
  </div>
);
