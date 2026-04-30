# RTA Desktop

A fast, lightweight AI-powered code editor built with Tauri. Think of it as a streamlined VSCode focused on AI-assisted coding — Monaco editor on the right, AI chat on the left.

## Overview

RTA Desktop brings the CLI's AI agent into a visual workspace:

- **Monaco Editor** — The same editor that powers VSCode, with syntax highlighting, IntelliSense, and multi-language support
- **AI Chat Panel** — Sidebar where you chat with the AI, which can read/write files, run commands, and navigate your project
- **File Explorer** — Browse and manage your project files
- **Native Desktop** — Runs as a native app via Tauri (not Electron), keeping it lightweight and fast

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  RTA Desktop                                                │
├────────────────┬────────────────────────────────────────────┤
│                │  Tab1.tsx  │  Tab2.py  │  +               │
│   AI Chat      ├────────────────────────────────────────────┤
│                │                                            │
│  ┌──────────┐  │           Monaco Editor                    │
│  │ User msg │  │                                            │
│  ├──────────┤  │  1│ import { h } from 'preact';             │
│  │ AI resp  │  │  2│                                        │
│  ├──────────┤  │  3│ export function App() {                 │
│  │ Tool: 🔧 │  │  4│   return <div>Hello</div>;             │
│  └──────────┘  │  5│ }                                      │
│                │                                            │
│  ┌──────────┐  │                                            │
│  │ > Input  │  │                                            │
│  └──────────┘  │                                            │
├────────────────┴────────────────────────────────────────────┤
│  explorer/main.ts  │Ln 1, Col 1│ TypeScript│ ● Connected    │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Desktop Framework | **Tauri 2.x** (Rust backend) |
| Frontend | **Preact** (lightweight React alternative) |
| Code Editor | **Monaco Editor** (@monaco-editor/react) |
| Styling | **Tailwind CSS** |
| Build Tool | **Vite** |
| Package Manager | **Bun** |

## Implementation Phases

### Phase 1: Foundation & Authentication
- [x] Project setup with Tauri + Preact + Tailwind
- [x] Auth page with API key login
- [x] Splash screen with branding
- [ ] Main layout structure (header, sidebar, main area)

### Phase 2: Workspace & File Explorer
- [ ] Workspace folder selector (Tauri dialog)
- [ ] File explorer sidebar with tree view
- [ ] Directory navigation (click to expand/collapse)
- [ ] File icons by type (.js, .py, .json, etc.)
- [ ] Context menu: new file, new folder, delete, rename

### Phase 3: Monaco Editor Integration
- [ ] Monaco Editor component with theme
- [ ] Tab bar for open files
- [ ] Language detection from file extension
- [ ] Syntax highlighting (handled by Monaco)
- [ ] File save (Ctrl+S / Cmd+S)
- [ ] Unsaved changes indicator

### Phase 4: AI Chat Panel
- [ ] Chat message list (user + assistant messages)
- [ ] Input field with send button
- [ ] Markdown rendering in chat
- [ ] Code block formatting
- [ ] Loading state during AI response
- [ ] Connection status indicator

### Phase 5: AI Tool Integration
- [ ] Connect to `/v1/chat` backend endpoint
- [ ] Send messages with tool definitions
- [ ] Handle tool calls from AI
- [ ] Display tool execution results
- [ ] Streaming responses (optional)

### Phase 6: System Integration
- [ ] File system operations via Tauri FS plugin
- [ ] Execute shell commands via Tauri shell
- [ ] Keyboard shortcuts (save, close tab, etc.)
- [ ] Window controls (minimize, maximize, close)
- [ ] App icon and metadata

## Available AI Tools

The AI has access to these functions in your workspace:

| Tool | Description |
|------|-------------|
| `get_files_info` | List files in directory with metadata |
| `get_file_contents` | Read file content |
| `write_file` | Create or overwrite a file |
| `edit_file` | Make targeted edits to a file |
| `delete_file` | Delete a file or directory |
| `create_dir` | Create a new directory |
| `list_directory` | List directory contents |
| `run_command` | Execute shell commands |
| `run_python_file` | Run Python scripts |
| `grep_search` | Search text across files |
| `glob_search` | Find files by pattern |

## Project Structure

```
desktop/
├── src/                          # Frontend (Preact)
│   ├── App.jsx                  # Main app with auth + layout
│   ├── main.jsx                 # Entry point
│   ├── index.css                # Global styles + Tailwind
│   │
│   ├── components/              # UI components (to be built)
│   │   ├── Editor.jsx          # Monaco wrapper
│   │   ├── ChatPanel.jsx       # AI chat sidebar
│   │   ├── FileExplorer.jsx    # File tree view
│   │   ├── TabBar.jsx          # Editor tabs
│   │   └── StatusBar.jsx       # Bottom status bar
│   │
│   ├── hooks/                   # Custom hooks
│   │   ├── useWorkspace.js     # Workspace state
│   │   ├── useChat.js          # Chat + API calls
│   │   └── useFileSystem.js    # Tauri FS wrapper
│   │
│   ├── pages/
│   │   └── LandingPage.jsx     # Auth / login page
│   │
│   └── assets/
│       ├── icon.png
│       └── background.png
│
├── src-tauri/                   # Backend (Rust + Tauri)
│   ├── main.rs                 # Binary entry
│   ├── lib.rs                  # Library (mobile entry)
│   ├── Cargo.toml              # Rust deps + plugins
│   ├── tauri.conf.json         # App config
│   │
│   ├── capabilities/            # Security permissions
│   │   └── default.json
│   │
│   └── icons/                  # App icons
│
├── dist/                       # Build output (gitignored)
├── node_modules/              # Dependencies (gitignored)
│
├── index.html                  # HTML entry
├── vite.config.js              # Vite config
├── tailwind.config.js          # Tailwind config
├── postcss.config.js           # PostCSS config
├── package.json                # Node deps + scripts
└── .gitignore
```

## How to Run

### Prerequisites

```bash
# Install Bun (if not installed)
curl -fsSL https://bun.sh/install | bash

# Install Rust (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### First Time Setup

```bash
cd desktop
bun install
```

### Development Mode

```bash
bun run tauri:dev
```

This starts:
1. Vite dev server on `http://localhost:1420`
2. Tauri desktop window with hot reload

### Production Build

```bash
# Build frontend
bun run build

# Build desktop app (creates installable)
bun run tauri:build
```

Output binaries:
- **Linux**: `src-tauri/target/release/bundle/deb/` or `appimage/`
- **Windows**: `src-tauri/target/release/bundle/msi/` or `nsis/`
- **macOS**: `src-tauri/target/release/bundle/macos/`

## Available Scripts

| Command | What it does |
|---------|--------------|
| `bun run dev` | Start Vite dev server (frontend only) |
| `bun run build` | Build frontend for production |
| `bun run preview` | Preview production build |
| `bun run tauri:dev` | Run desktop app with hot reload |
| `bun run tauri:build` | Build desktop app for distribution |
| `bun run tauri` | Access Tauri CLI directly |

## Comparison: CLI vs Desktop

| Feature | CLI | Desktop |
|---------|-----|---------|
| AI Chat | Terminal interface | Sidebar panel |
| Code Display | Terminal text | Monaco Editor |
| File Editing | Via tools | Direct editing |
| File Navigation | Command line | File explorer |
| Setup | Terminal usage | Visual IDE |

## License

MIT