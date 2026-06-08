# AGENTS.md — Call-Level Logging

## ONE RULE: One Row Per Tool Call

Every tool call = one CSV row. No exceptions.

User says "edit 6 files" → 6 tool calls → **6 rows** in the CSV.
User says "read file, then edit it" → 2 tool calls → **2 rows**.
User says "hello" → 1 chat response → **1 row**.

**If you make multiple tool calls in one response and log only 1 row, you failed.**

---

## Mandatory Logging Workflow

After **every** tool call or LLM interaction, IMMEDIATELY:

1. Determine the `call_index` (increments per turn: 0, 1, 2, 3...)
2. Write one row to `~/.agents/agent-calls.csv` with that `call_index`
3. Then proceed to the next call

Do NOT batch logging. Do NOT log at the end of a turn. Log **inline, as each call completes**.

```
Tool call 0 (read_file) → LOG ROW (call_index=0) → 
Tool call 1 (edit_file) → LOG ROW (call_index=1) → 
Tool call 2 (edit_file) → LOG ROW (call_index=2) → 
Tool call 3 (read_file) → LOG ROW (call_index=3) → 
Done
```

**5 tool calls = 5 separate log() calls = 5 rows in CSV.**

---

## CSV Location

- **Path:** `~/.agents/agent-calls.csv`
- **Mode:** Append-only
- **Encoding:** UTF-8

---

## CSV Schema (header row, exact)

```
call_id,session_id,parent_message_id,turn_index,call_index,role,system_prompt,ai_prompt,ai_response,provider,model_used,is_fallback,tokens_in,tokens_out,tokens_cached,latency_ms,schema_version,workspace_path,tool_used,file_paths_affected,full_history,available_tools,full_history_count,provider_meta,created_at
```

## Field Rules

| Field | Rule |
|-------|------|
| `call_id` | UUID4, unique per row |
| `session_id` | `{agent}-{YYYY-MM-DD}-{seq}` e.g. `opencode-2026-06-08-001` |
| `parent_message_id` | ID of the user message that started this chain. Use `session_id` if no message ID exists |
| `turn_index` | 0-indexed turn number within the session |
| `call_index` | **0-indexed, increments with every tool call within a turn. Resets to 0 on each new turn.** |
| `role` | Always `assistant` |
| `system_prompt` | The system prompt active for this call. `""` if none |
| `ai_prompt` | **The exact prompt/input for THIS specific call** — not the whole user message. Scrub secrets |
| `ai_response` | **The full response for THIS specific call.** Scrub secrets |
| `provider` | e.g. `anthropic`, `openai`, `groq`, `opencode` |
| `model_used` | e.g. `claude-3-5-sonnet`, `mimo-v2.5-free` |
| `is_fallback` | `true` or `false` |
| `tokens_in` | Prompt token count. `0` if unknown |
| `tokens_out` | Completion token count. `0` if unknown |
| `tokens_cached` | Cached tokens. `0` if unknown |
| `latency_ms` | Request latency in ms. `0` if unknown |
| `schema_version` | Always `2` |
| `workspace_path` | Project root directory. `.` if unknown |
| `tool_used` | Tool name: `read_file`, `edit_file`, `write_file`, `bash`, `grep`, `glob`, `task`, `webfetch`, `websearch`, `skill`, `question`, `todowrite`, `chat` |
| `file_paths_affected` | JSON array of files touched by THIS call. `[]` if none |
| `full_history` | JSON conversation history before this call. `[]` if unavailable |
| `available_tools` | JSON array of tools available. `[]` if unavailable |
| `full_history_count` | Number of messages before this call. `0` if unknown |
| `provider_meta` | JSON metadata. `{}` if none |
| `created_at` | ISO 8601 UTC timestamp: `YYYY-MM-DDTHH:MM:SS.mmmZ` |

---

## WRONG vs RIGHT

### WRONG: Logging summary rows
```
User: "fix auth and add tests"
Agent: [reads auth.py, edits auth.py, reads tests, edits tests, summarizes]
Agent logs: 1 row with tool_used="chat" and ai_prompt="Summarize changes"
```
**WRONG.** This is 5 calls logged as 1 row. Missing 4 rows.

### RIGHT: Logging every call
```
User: "fix auth and add tests"
Agent: [reads auth.py, edits auth.py, reads tests, edits tests, summarizes]

Row 1: call_index=0, tool_used="read_file", file_paths_affected=["src/auth.py"]
Row 2: call_index=1, tool_used="edit_file", file_paths_affected=["src/auth.py"]
Row 3: call_index=2, tool_used="read_file", file_paths_affected=["tests/test_auth.py"]
Row 4: call_index=3, tool_used="edit_file", file_paths_affected=["tests/test_auth.py"]
Row 5: call_index=4, tool_used="chat", file_paths_affected=[]
```
**RIGHT.** 5 calls = 5 rows.

### WRONG: Retroactive batch logging
```
Agent makes 10 tool calls, then at the end writes a Python script to log all 10 at once
```
**WRONG.** Logging must happen inline after each call, not retroactively. Retroactive logging leads to inaccurate `ai_prompt`/`ai_response` and wrong `created_at` timestamps.

### RIGHT: Inline logging
```
Agent reads a file → logs row immediately → edits a file → logs row immediately → ...
```

---

## Sensitive Data Scrubbing

Before writing ANY field, scrub:
- API keys, tokens → `[REDACTED_API_KEY]`
- Email addresses → `[REDACTED_EMAIL]`
- Home paths `/home/username/` → `/home/USER/`
- macOS paths `/Users/username/` → `/Users/USER/`
- Connection strings → `[REDACTED_CREDENTIALS]`

---

## CSV Escaping (RFC 4180)

1. Fields with commas, newlines, or double-quotes → wrap in double-quotes
2. Double-quotes inside fields → escape as `""`
3. JSON fields → wrap in quotes, internal quotes doubled

---

## Python Logging Helper

```python
import csv, json, os, uuid
from datetime import datetime, timezone

CSV_PATH = os.path.expanduser("~/.agents/agent-calls.csv")

def log_call(session_id, parent_message_id, turn_index, call_index,
             ai_prompt, ai_response, tool_used, provider="unknown",
             model_used="unknown", file_paths_affected=None, system_prompt="",
             tokens_in=0, tokens_out=0, tokens_cached=0, latency_ms=0,
             is_fallback=False, workspace_path=".", full_history=None,
             available_tools=None, provider_meta=None):
    """Log one tool call. Call this AFTER EVERY tool call."""
    row = {
        "call_id": str(uuid.uuid4()),
        "session_id": session_id,
        "parent_message_id": parent_message_id,
        "turn_index": turn_index,
        "call_index": call_index,
        "role": "assistant",
        "system_prompt": system_prompt or "",
        "ai_prompt": scrub(ai_prompt),
        "ai_response": scrub(ai_response),
        "provider": provider,
        "model_used": model_used,
        "is_fallback": str(is_fallback).lower(),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_cached": tokens_cached,
        "latency_ms": latency_ms,
        "schema_version": 2,
        "workspace_path": workspace_path,
        "tool_used": tool_used,
        "file_paths_affected": json.dumps(file_paths_affected or []),
        "full_history": json.dumps(full_history or []),
        "available_tools": json.dumps(available_tools or []),
        "full_history_count": len(full_history) if full_history else 0,
        "provider_meta": json.dumps(provider_meta or {}),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)

def scrub(text):
    """Scrub secrets from text."""
    import re
    text = re.sub(r'(api[_-]?key|token|password|secret)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
                  r'\1=[REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED_EMAIL]', text)
    text = re.sub(r'/home/[a-zA-Z0-9_-]+/', '/home/USER/', text)
    text = re.sub(r'/Users/[a-zA-Z0-9_-]+/', '/Users/USER/', text)
    return text
```

---

## Enforcement Rules

### Always Do
- Log after **every** tool call (read, edit, write, bash, grep, glob, task, webfetch, websearch, skill, question, todowrite)
- Log after direct chat responses too (tool_used="chat")
- `call_index` increments within a turn, resets to 0 on new turn
- Populate `file_paths_affected` with files touched by **this specific call**
- Populate `ai_prompt` with the prompt for **this specific call**, not the user's message
- Populate `ai_response` with the response for **this specific call**
- Scrub secrets from both `ai_prompt` and `ai_response`
- Use `created_at` = current UTC time when the call completes

### Never Do
- **Never** collapse multiple tool calls into one row
- **Never** log a summary row instead of individual call rows
- **Never** batch-log retroactively (logging 10 calls at once after making them)
- **Never** skip logging because "the data is incomplete" — use defaults
- **Never** log credentials, API keys, or PII
- **Never** truncate or delete existing rows
- **Never** commit `agent-calls.csv` to git

---

## Quick Reference: Common Mistakes

| Mistake | Fix |
|---------|-----|
| Logged 1 row for 5 file edits | Log 5 rows, one per edit |
| Logged a "summary" row with tool_used="chat" | Log individual call rows first, THEN a chat row |
| Retroactively wrote a Python script to batch-log | Log inline after each call as it happens |
| ai_prompt contains the full user message | ai_prompt should contain only the input for THIS call |
| ai_response is empty | Log the actual response/output for this call |
| call_index starts at 1 | Start at 0 |
| call_index doesn't reset between turns | Reset to 0 for each new turn_index |
| created_at is same for all rows | Each row gets its own timestamp when that call completes |

---

**Last Updated:** 2026-06-08
**Schema Version:** 2
