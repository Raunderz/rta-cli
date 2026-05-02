# RTA Desktop

An AI-powered code editor built by forking Adobe Brackets and adding an integrated AI chat panel (right side), custom branding, and a dark theme. Uses RTA's own API backend (same as RTA CLI) for all agent operations.

---

## Overview

RTA Desktop keeps Brackets completely intact and adds:

- **AI Chat Panel** (right sidebar) — Chat with the AI agent; it reads/writes files, runs commands, edits code in the editor
- **RTA API Backend** — Brackets' Node.js domain calls RTA's own API endpoint (same one the CLI uses)
- **RTA Dark Theme** — Custom dark theme as default
- **RTA Branding** — App name, icons, splash screen, about dialog

Nothing from Brackets is removed. Features evaluated for removal only after months of stable real-world use.

---

## Layout

```
┌────────────────────────────────────────────────────┐
│  RTA Desktop                                       │
├────────────────────┬────────────────────────────────┤
│                    │ Tab1.tsx  │ Tab2.py  │ +      │
│  File Tree         ├────────────────────────────────┤
│                    │                                │
│  ┌──────────────┐  │     CodeMirror Editor          │
│  │ src/         │  │                                │
│  │  ├─ App.tsx  │  │  1│ import { h } from 'preact';│
│  │  └─ main.tsx │  │  2│                            │
│  │ public/      │  │  3│ export function App() {    │
│  └──────────────┘  │  4│   return <div>Hello</div>; │
│                    │  5│ }                          │
│                    │                                │
│  ┌──────────────┐  │ ┌──────────────────────────┐  │
│  │ > Search...  │  │ │ AI Chat Panel            │  │
│  └──────────────┘  │ ├──────────────────────────┤  │
│                    │ │ User: Build a form      │  │
│                    │ ├──────────────────────────┤  │
│                    │ │ AI: Creating form...    │  │
│                    │ │ Tool: write_file        │  │
│                    │ ├──────────────────────────┤  │
│                    │ │ > Type a message...     │  │
│                    │ └──────────────────────────┘  │
├────────────────────┴────────────────────────────────┤
│ main.tsx │Ln 1, Col 1│ TypeScript│ ● Connected      │
└────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer           | Technology                                |
| --------------- | ----------------------------------------- |
| Editor Base     | **Adobe Brackets** (forked, MIT)           |
| Code Editor     | **CodeMirror** (Brackets built-in)         |
| AI Backend      | **RTA's own API** (same as CLI)            |
| Node.js Domain  | Brackets' existing Node.js domain         |
| Frontend        | **HTML / CSS / LESS / jQuery**             |
| Desktop Shell   | **Brackets-Shell** (CEF)                   |
| Build Tool      | **Grunt**                                 |

---

## Fork Strategy

Purely additive. New code lives in `src/rta/`; existing Brackets files touched only for branding (window title, app name, icons, splash).

| Component      | Status                                    |
| -------------- | ----------------------------------------- |
| CodeMirror     | Untouched                                 |
| File tree      | Kept as-is                                |
| Brackets theme | RTA Dark extension added as default       |
| Node.js domain | AI tools added; file/command ops extended |
| UI panels      | AI Chat Panel added (right sidebar)       |

---

## Implementation Phases

### Phase 1: Fork & Branding
Clone the Brackets repository, replace app name/window title/splash/icons/about dialog with RTA branding. Confirm clean build and launch.

### Phase 2: RTA Dark Theme
Create theme extension at `src/rta/themes/rta-dark/`. Override LESS variables for colors. Set as default in startup preferences. Style panels, tabs, status bar, file tree.

### Phase 3: AI Chat Panel
Add resizable right panel (`src/rta/ChatPanel.js`) using Brackets' `PanelManager` API. Build message list (user/assistant/tool cards). Render Markdown with `marked.js`. Syntax-highlight code blocks using CodeMirror colorizer. Input field with Shift+Enter for newline, Enter to send. Add connection status and model label to status bar.

### Phase 4: Node.js / RTA API Bridge
Create `src/rta/node/APIBridge.js` in Brackets' Node.js domain. Connect to RTA's API endpoint (same as CLI uses). Implement message send, response receive, and streaming chunk handling. Maintain conversation history per workspace session. Stream chunks to renderer via `NodeConnection` events; chat panel renders progressively.

### Phase 5: Tool Integration
Create `src/rta/node/ToolExecutor.js`. Port all tools from the Python agent (get_file_contents, write_file, edit_file, delete_file, create_dir, list_directory, run_command, run_python_file, grep_search, glob_search). Each tool uses Node.js built-ins and Brackets' file system API. Tool calls are intercepted in Node domain, executed locally, results sent back to API to continue turn. Each tool renders as collapsible card in chat showing name, inputs, output.

### Phase 6: Testing & Polish
End-to-end: open workspace → send message → agent edits file → editor updates. Add keyboard shortcuts (Ctrl+Shift+A to toggle panel, Ctrl+Shift+N for new conversation). Handle API errors, tool failures, connection loss, long responses. Confirm streaming does not degrade editor performance.

---

## Project Structure

```
rta-desktop/
├── src/rta/                     # All RTA-specific code
│   ├── ChatPanel.js             # Chat UI logic
│   ├── ChatPanel.html           # Chat template
│   ├── ChatPanel.less           # Chat styles
│   ├── MessageRenderer.js       # Markdown + code rendering
│   ├── ConversationManager.js   # Chat history
│   ├── ToolCards.js             # Tool result cards
│   ├── StatusBarExtension.js    # Status bar additions
│   ├── node/
│   │   ├── APIBridge.js         # RTA API calls (Node domain)
│   │   └── ToolExecutor.js      # Tool execution
│   └── themes/rta-dark/
│       ├── theme.less
│       └── package.json
├── src/assets/icons/            # RTA icons
├── appshell/                    # Brackets-Shell (unchanged)
├── Gruntfile.js                 # Build config (unchanged)
└── package.json
```

---

## How to Run

**Prerequisites:**
```bash
node --version              # Node.js 18+
npm install -g grunt-cli
# Linux: sudo apt install libgtk-3-dev libgconf-2-dev libnss3-dev
# macOS: xcode-select --install
```

**Setup:**
```bash
git clone <your-fork-url>
cd rta-desktop
npm install
```

**Dev Mode:**
```bash
grunt dev
```

**Production Build:**
```bash
grunt release
```

Output: `dist/linux/RTA-Desktop.deb`, `dist/win/RTA-Desktop-Setup.exe`, `dist/mac/RTA-Desktop.dmg`

---

## Available Tools

All ported from the Python agent, execute in Node.js backend:

| Tool            | Description                      |
| --------------- | -------------------------------- |
| `get_file_contents` | Read file                    |
| `write_file`    | Create/overwrite file            |
| `edit_file`     | Targeted search/replace edits    |
| `delete_file`   | Delete file or directory         |
| `create_dir`    | Create directory                 |
| `list_directory` | List with metadata              |
| `run_command`   | Execute shell commands           |
| `run_python_file` | Run Python script              |
| `grep_search`   | Search text across files         |
| `glob_search`   | Find files by pattern            |

---

## License

MIT — same as Brackets.

