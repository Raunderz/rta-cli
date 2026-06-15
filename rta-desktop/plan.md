# RTA Desktop — Chat Panel Polish Plan

## Overview

The core chat integration is complete: CLI pipe IPC, streaming, tool calls, session history. This plan covers UX polish features to make the chat panel feel more integrated and professional.

---

## Features

### F1: Diff Previews

**File:** `rta-desktop/data/plugins/rta_chat.lua`

When the agent edits a file, show a diff preview in the chat before/after the change.

- Capture file content before and after tool writes/edits
- Render side-by-side diff in chat (green additions, red deletions)
- Show file path as header above the diff
- Allow user to undo the change if they don't like it

**Implementation:**
- Hook into `tool_end` events for `write` and `edit` tools
- Read file content before tool execution (via `tool_start` with file params)
- Read file content after tool execution
- Compute diff (line-by-line comparison)
- Render diff blocks in chat with colored highlights

---

### F2: Keyboard Shortcuts

**File:** `rta-desktop/data/plugins/rta_chat.lua`

Add keyboard shortcuts for common chat actions.

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send message |
| `Ctrl+N` | New session |
| `Ctrl+H` | Toggle history |
| `Ctrl+Backspace` | Delete word |
| `Escape` | Cancel streaming / Close history |

**Implementation:**
- Add `on_key_pressed` handler to RtaChat
- Map key combos to existing commands
- Ensure shortcuts don't conflict with editor keybindings

---

### F3: Theme Integration

**File:** `rta-desktop/data/plugins/rta_chat.lua`

Better color usage that adapts to the editor's theme.

- User messages: use `style.selection` for bg, `style.accent` for text
- Assistant messages: use `style.background` for bg, `style.text` for text
- Tool calls: use `style.background3` for bg, `style.warn`/`style.good` for status
- System messages: use `style.dim`
- Streaming indicator: use `style.accent` with animation

**Current state:** Already partially implemented. Need to ensure all colors come from `style.*` and handle edge cases where theme colors might clash.

---

### F4: Streaming Rate Limiting

**File:** `rta-desktop/data/plugins/rta_chat.lua`

Current streaming re-renders on every text_delta which can cause flicker.

- Batch text deltas and re-render at 30fps max
- Use `core.redraw = true` only when needed
- Show blinking cursor indicator during streaming

**Implementation:**
- Track `last_render_time` in streaming state
- Only call `core.redraw = true` if 33ms since last render
- Append deltas to buffer, render batch on next frame

---

### F5: Tool Result Display

**File:** `rta-desktop/data/plugins/rta_chat.lua`

Show tool execution results inline in chat.

- When a tool completes, show a brief summary (file read → "read 42 lines", bash → "exit code 0")
- Collapsible tool output (click to expand/collapse)
- Color code: green for success, red for errors

**Implementation:**
- Parse `tool_end` events for result summaries
- Add collapsible state per tool result
- Render summary line with expand/collapse toggle

---

## Files to Modify

- `rta-desktop/data/plugins/rta_chat.lua` — all features

## Verification

1. Diff previews: Edit a file via chat, verify diff renders correctly
2. Keyboard shortcuts: Test all shortcuts don't conflict with editor
3. Theme: Switch themes, verify chat colors adapt
4. Streaming: Send long message, verify no flicker
5. Tool results: Run a bash command, verify result shows inline
