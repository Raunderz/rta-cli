# RTA Desktop — Python Binary + Chatbar Plan

## Overview

Replace the placeholder Odin agent (`agent-odin/`) with the existing Python CLI binary (`rta`). The CLI already has a `--repl` mode with `input()`/`print()`. We need a pipe-based IPC mode for the Lua chat plugin to communicate with the CLI process.

**CLI binary**: Built and placed at `bin/rta` (gitignored). 60MB single binary built via PyInstaller from `cli/` source. Rebuild: `cd cli && uv run python -m PyInstaller --clean --noconfirm rta.spec` then copy `dist/rta` → `rta-desktop/bin/rta`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RTA Desktop (Lite XL)                     │
│                                                              │
│  ┌──────────────┐      stdin/stdout (JSON-lines)            │
│  │ rta_chat.lua │◄──────────────────────────────►│  rta CLI  │
│  │  (chat UI)   │      spawn + pipe IPC          │  binary   │
│  └──────────────┘                                └───────────┘
│                                                              │
│  Detection: which rta → ~/.rta/cli_path (persisted)         │
└─────────────────────────────────────────────────────────────┘
```

## Key Decisions

### Binary Detection
- Check `PATH` for `rta` binary
- If not found, prompt user: download link or manual path input
- Persist working path to `~/.rta/cli_path`
- User does NOT want to ship CLI with the editor

### IPC Protocol
- Explicit `--stdio` flag (not auto-detect) to avoid `echo "..." | rta` edge case
- JSON-lines over stdin/stdout pipes
- One JSON object per line, newline-delimited

### Tool Approval
- Inline approval in chat panel (user approves/denies tool calls directly in the chat UI)
- Keep it simple — no separate approval modal

### Odin Agent
- Delete `agent-odin/` directory entirely — it's just a 26-line HTTP GET placeholder
- Remove all references to Odin from README and docs

---

## Protocol Specification

### CLI Flags

```bash
rta --stdio                    # Enable JSON-lines pipe mode
rta --stdio --model auto       # With model selection
rta --stdio --session <id>     # Resume specific session
```

### Request Format (Lua → CLI via stdin)

```json
{"type": "chat", "message": "Fix the bug in auth.py", "session_id": null}
{"type": "chat", "message": "Continue", "session_id": "abc123"}
{"type": "cancel"}
{"type": "status"}
```

### Response Format (CLI → Lua via stdout)

```json
{"type": "text_delta", "content": "I'll "}
{"type": "text_delta", "content": "fix "}
{"type": "text_delta", "content": "that..."}
{"type": "tool_start", "tool": "read_file", "params": {"path": "auth.py"}}
{"type": "tool_end", "tool": "read_file", "result": "success"}
{"type": "tool_approval", "tool": "bash", "command": "rm -rf /tmp/test", "approval_id": "xyz"}
{"type": "text_done", "session_id": "abc123", "tokens_used": 1523}
{"type": "error", "message": "API key not found. Run 'rta login'."}
```

### Event Types

| Type | Direction | Description |
|------|-----------|-------------|
| `chat` | → CLI | User message to process |
| `cancel` | → CLI | Abort current operation |
| `status` | → CLI | Request CLI status/version |
| `text_delta` | CLI → | Streaming text chunk |
| `text_done` | CLI → | Response complete |
| `tool_start` | CLI → | Tool execution began |
| `tool_end` | CLI → | Tool execution finished |
| `tool_approval` | CLI → | Needs user approval |
| `tool_approved` | → CLI | User approved tool call |
| `tool_denied` | → CLI | User denied tool call |
| `error` | CLI → | Error occurred |
| `status_response` | CLI → | CLI version/info |

---

## Implementation Tasks

### T1: CLI Pipe-Mode Auto-Detection ✅

**File:** `cli/src/kon/cli.py`

Add `--stdio` flag to the CLI. When present:
- Disable all TUI widgets (no Rich, no prompt_toolkit)
- Read JSON-lines from stdin
- Write JSON-lines to stdout
- Log to `~/.rta/kon.log` only (not stdout)

```python
@click.option('--stdio', is_flag=True, help='JSON-lines pipe mode for IDE integration')
def main(stdio, ...):
    if stdio:
        run_stdio_mode()
    else:
        # existing REPL/TUI logic
```

### T2: JSON-Lines Protocol ✅

**File:** `cli/src/kon/stdio.py` (new)

Core protocol handler:
- `read_request()` — read one JSON line from stdin
- `write_response(obj)` — write one JSON line to stdout + flush
- `run_stdio_mode()` — main loop: read request → process → stream responses

Wire into existing `ConversationRuntime` + `Agent` loop. Use event system (15+ event types) to map agent events to JSON-line responses.

### T3: Remove agent-odin ✅

**Delete:** `rta-desktop/agent-odin/` directory entirely

**Update:** `rta-desktop/README.md`
- Remove all Odin references
- Remove "Building the RTA Agent (Odin)" section
- Update architecture to describe Python CLI integration

### T4: Update rta_chat.lua ✅

**File:** `rta-desktop/data/plugins/rta_chat.lua`

Major rewrite:
- Detect `rta` binary on startup (PATH → ~/.rta/cli_path)
- Spawn `rta --stdio` as child process via `process.start`
- JSON-lines IPC: write requests to stdin, read responses from stdout
- Handle streaming `text_delta` events — append to current message
- Handle `tool_start`/`tool_end` — show tool activity in chat
- Handle `tool_approval` — show inline approve/deny buttons
- Handle `text_done` — mark response complete
- Handle `error` — display error in chat

### T5: Binary-Not-Found UX ✅

**File:** `rta-desktop/data/plugins/rta_chat.lua`

When `rta` not found:
1. Show message in chat: "RTA CLI not found"
2. Option A: "Download" button → opens browser to releases page
3. Option B: "Browse" button → file picker to select `rta` binary
4. Persist chosen path to `~/.rta/cli_path`
5. On next startup, check `~/.rta/cli_path` first before PATH

### T6: Streaming Text Rendering ✅

**File:** `rta-desktop/data/plugins/rta_chat.lua`

Current chat shows messages after completion. Need streaming:
- Maintain `current_message` buffer during streaming
- Append each `text_delta` to buffer
- Re-render on each delta (with rate limiting to avoid flicker)
- Finalize message on `text_done`
- Show cursor/blinking indicator while streaming

---

## File Changes Summary

| File | Action |
|------|--------|
| `cli/src/kon/cli.py` | Add `--stdio` flag ✅ |
| `cli/src/kon/stdio.py` | **New** — protocol handler ✅ |
| `rta-desktop/agent-odin/` | **Delete** entire directory ✅ |
| `rta-desktop/README.md` | Remove Odin references ✅ |
| `rta-desktop/data/plugins/rta_chat.lua` | Rewrite for pipe IPC ✅ |
| `rta-desktop/plan.md` | This file |

---

## Testing

1. Manual: `echo '{"type":"chat","message":"hello"}' | rta --stdio`
2. Integration: Launch rta-desktop, verify chat panel connects to CLI
3. Streaming: Verify text appears word-by-word during response
4. Tool approval: Verify inline approve/deny buttons work
5. Error handling: Test with missing API key, network failure, invalid JSON

---

## Open Questions

- [ ] Tool approval UX: inline in chat vs separate panel? → **Decided: inline**
- [ ] `--stdio` flag vs auto-detect? → **Decided: explicit `--stdio`**
- [ ] Should we support `--session` for resuming? → Yes, pass through to CLI
