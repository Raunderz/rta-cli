# RTA Desktop (Lite XL)

RTA Desktop is a lightweight, AI-powered IDE based on [Lite XL](https://github.com/lite-xl/lite-xl), powered by the RTA Python CLI.

## Overview

- **Frontend**: Lite XL (C/Lua)
- **Engine**: RTA Python CLI (`rta` binary)
- **Integration**: Lua plugins connecting Lite XL to the CLI via JSON-lines pipe IPC.

## Chat Plugin

The built-in chat panel (`data/plugins/rta_chat.lua`) provides a sidebar for interacting with the RTA CLI agent.

### Features

- **Streaming responses** with 30fps rate-limited rendering
- **Tool call display** with expand/collapse (click tool indicators)
- **Diff previews** for file edits with undo support
- **Session history** — browse and load previous sessions
- **Auto-approve** — all tool calls are approved automatically in desktop mode

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Return` / `Ctrl+Return` | Send message |
| `Ctrl+N` | New session |
| `Ctrl+H` | Toggle session history |
| `Ctrl+Backspace` | Delete word |
| `Escape` | Cancel streaming / Close history |
| `Ctrl+Shift+C` | Toggle chat panel |

### Setup

1. Build the CLI binary (see below)
2. Either place `rta` in your `PATH`, or create `~/.rta/cli_path` containing the path to the binary
3. Launch `rta-desktop` — the chat panel appears on the right side

### Running Tests

```bash
cd rta-desktop/tests
lua run.lua
```

## Building

### Prerequisites

- Meson (>=0.63), Ninja, C compiler (GCC/Clang)
- SDL3, PCRE2, FreeType2, Lua 5.4
- RTA CLI binary

### Build Desktop

```bash
meson setup build --wrap-mode=forcefallback
meson compile -C build
ln -sf ../../data build/src/data
./build/src/rta-desktop
```

Or use the build script: `./scripts/build.sh`

### Build CLI Binary

```bash
cd ../cli
uv run python -m PyInstaller --clean --noconfirm rta.spec
cp dist/rta ../rta-desktop/bin/rta
```

The binary is placed at `bin/rta` (gitignored).

## License

MIT
