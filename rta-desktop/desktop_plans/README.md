# RTA Desktop

An AI-powered code editor built on **Eclipse Theia**, a modern IDE framework. It adds an integrated AI chat panel (right side), custom branding, and a dark theme. Uses RTA's own API backend (same as RTA CLI) for all agent operations.

---

## Overview

RTA Desktop extends Theia's modular architecture and adds:

- **AI Chat Panel** (right sidebar) — Chat with the AI agent; it reads/writes files, runs commands, edits code in the editor
- **RTA API Backend** — Theia's backend services connect to RTA's own API endpoint (same one the CLI uses)
- **RTA Dark Theme** — Custom dark theme as default
- **RTA Branding** — App name, icons, splash screen, about dialog

This approach replaces the original plan's Brackets foundation with Theia, a framework designed for this exact purpose, making customization significantly easier and ensuring long-term viability.

---

## Layout

```
┌────────────────────────────────────────────────────┐
│  RTA Desktop                                       │
├────────────────────┬────────────────────────────────┤
│                    │ Tab1.tsx  │ Tab2.py  │ +      │
│  File Tree         ├────────────────────────────────┤
│                    │                                │
│  ┌──────────────┐  │     Monaco Editor             │
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
| IDE Framework   | **Eclipse Theia** (modern, extensible)     |
| Code Editor     | **Monaco Editor** (Theia built-in)         |
| AI Backend      | **RTA's own API** (same as CLI)            |
| Backend         | **Theia's Node.js/Express backend**        |
| Frontend        | **TypeScript / React / CSS**               |
| Desktop Shell   | **Electron** (via Theia)                   |
| Build Tool      | **Yarn & Theia CLI**                      |

---

## Customization Strategy

Purely additive. New code lives in `rta-extension/`; existing Theia files are touched only for branding and configuration. Theia's extension system is used for all new features.

| Component      | Status                                    |
| -------------- | ----------------------------------------- |
| Monaco Editor  | Untouched (Configured via Theia)          |
| File tree      | Untouched (Theia core)                    |
| Theia theme    | RTA Dark theme added as extension        |
| Backend services| AI tools added as new backend service    |
| UI panels      | AI Chat Panel added as custom widget     |

---

## Implementation Phases

### Phase 1: Project Setup & Branding
- Scaffold RTA Desktop using Theia's `generator-theia-extension`.
- Configure `package.json` with app name, window title, and icons.
- Replace default splash screen and about dialog with RTA branding.
- Confirm a clean build and launch of the base Theia editor.

### Phase 2: RTA Dark Theme
- Create a Theia theme extension in the `rta-extension` package.
- Define dark color palette for all UI components (editor, panels, status bar, tabs, file tree).
- Set as the default theme in the application configuration.
- Style all panels, tabs, status bar, and file tree consistently.

### Phase 3: AI Chat Panel
- Create a custom Theia widget (`rta-chat-panel`) for the right sidebar.
- Build message list UI with user, assistant, and tool call cards.
- Integrate a Markdown renderer (e.g., `react-markdown`) and use Monaco for syntax highlighting in code blocks.
- Add an input field with support for Enter to send and Shift+Enter for newline.
- Display connection status and the active model name in the status bar.

### Phase 4: RTA API Backend Bridge
- Implement an `RtaApiService` in the Theia backend.
- Connect to RTA's API endpoint (same as the CLI uses).
- Handle message sending, response receiving, and streaming chunk processing.
- Maintain conversation history per workspace session.
- Stream response chunks to the frontend widget for a progressive rendering experience.

### Phase 5: Tool Integration
- Create a `ToolExecutorService` in the Theia backend.
- Port all tools from the Python agent (get_file_contents, write_file, edit_file, delete_file, create_dir, list_directory, run_command, run_python_file, grep_search, glob_search).
- Each tool uses Node.js built-ins and Theia's `FileService` API.
- Tool calls are intercepted in the AI response, executed locally on the backend, and the results are sent back to the API to continue the agentic loop.
- Each tool usage is rendered as a collapsible card in the chat showing its name, inputs, and output.

### Phase 6: Testing & Polish
- End-to-end testing: open workspace → send message → agent edits file → editor updates.
- Add keyboard shortcuts (Ctrl+Shift+A to toggle panel, Ctrl+Shift+N for new conversation).
- Implement robust error handling for API issues, tool failures, connection loss, and long responses.
- Confirm streaming and tool execution does not degrade editor performance.

---

## Project Structure

```
rta-desktop/
├── rta-extension/                  # All RTA-specific code
│   ├── src/
│   │   ├── browser/
│   │   │   ├── chat-panel-widget.ts # Chat UI logic
│   │   │   ├── message-renderer.tsx # Markdown + code rendering
│   │   │   ├── tool-card.tsx        # Tool result cards
│   │   │   └── status-bar.ts        # Status bar additions
│   │   ├── node/
│   │   │   ├── rta-api-service.ts    # RTA API calls (backend)
│   │   │   └── tool-executor.ts     # Tool execution (backend)
│   │   └── common/
│   │       └── chat-protocol.ts     # Shared types & interfaces
│   ├── themes/
│   │   └── rta-dark/
│   │       └── rta-dark-theme.css   # RTA Dark theme colors
│   └── package.json
├── package.json                     # Root workspace
├── lerna.json                       # Monorepo config
└── yarn.lock
```

---

## How to Run

**Prerequisites:**
```bash
node --version              # Node.js 18+
npm install -g yarn
# Linux: sudo apt install build-essential libx11-dev libxkbfile-dev
# macOS: xcode-select --install
```

**Setup:**
```bash
git clone <your-fork-url>
cd rta-desktop
yarn
```

**Dev Mode:**
```bash
yarn browser start
```

**Production Build:**
```bash
yarn electron package
```

Output: Platform-specific binaries in `dist/`.

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
