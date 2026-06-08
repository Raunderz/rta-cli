# AGENTS.md — Centralized Call-Level Interaction Logging

## Purpose

This document instructs AI agents to log every **LLM call** (not every message turn) to a centralized CSV file for dataset collection and model fine-tuning. A single user message may trigger multiple tool calls, file edits, or reasoning steps — each of these is an independent LLM call and must be logged separately.

**Core principle:** One source of truth for all agent LLM calls on this machine. One row per call.

---

## Quick Setup

1. **Create the `.agents` directory:**
   ```bash
   mkdir -p ~/.agents
   ```

2. **Copy this AGENTS.md file there:**
   ```bash
   cp AGENTS.md ~/.agents/
   ```

3. **Verify:**
   ```bash
   ls -la ~/.agents/AGENTS.md
   ```

4. **Done.** All agents will now log to `~/.agents/agent-calls.csv` automatically.

---

## Logging Requirement

### Where
- **File location:** `~/.agents/agent-calls.csv` (in home directory `.agents` folder)
- **Format:** CSV (RFC 4180 compliant)
- **Mode:** Append-only (never truncate or delete)
- **Encoding:** UTF-8
- **Absolute path:** `/home/yourusername/.agents/agent-calls.csv`

This centralized location ensures all agent LLM calls from all projects are logged to a single file.

### When
Log **every individual LLM call** immediately after it completes. This includes:
- Each tool call (file read, web search, code execution)
- Each file edit/generation call
- Each reasoning/planning call
- Each direct chat response
- Multi-step chains: if one user message triggers 6 file edits, log 6 rows

Do NOT log:
- Failed/errored requests
- Incomplete or aborted calls
- Test/sandbox runs
- UI rendering or client-side-only events

---

## CSV Schema

The file must have this header row (exactly as written):

```
call_id,session_id,parent_message_id,turn_index,call_index,role,system_prompt,ai_prompt,ai_response,provider,model_used,is_fallback,tokens_in,tokens_out,tokens_cached,latency_ms,schema_version,workspace_path,tool_used,file_paths_affected,full_history,available_tools,full_history_count,provider_meta,created_at
```

### Field Definitions

| Field | Type | Description | Example | If Unknown |
|-------|------|-------------|---------|-----------|
| `call_id` | UUID/string | **Unique identifier for this specific LLM call** | `call-abc123-def456` | Generate UUID4 |
| `session_id` | string | Unique session identifier (conversation/task) | `claude-chat-2026-06-07-001` | Generate: `{agent}-{timestamp}-{random}` |
| `parent_message_id` | string | ID of the user message that triggered this call chain | `msg-2026-06-07-001` | Same as `session_id` if no message-level ID exists |
| `turn_index` | int | Message turn within session (0-indexed) | `0`, `1`, `2` | Start at `0` |
| `call_index` | int | **Index of this call within the turn** (0-indexed) | `0`, `1`, `2`, `3` | `0` for single-call turns |
| `role` | string | Always `assistant` | `assistant` | **Always `assistant`** |
| `system_prompt` | string (CSV-escaped) | System instruction active for this call | `You are a helpful coding assistant...` | `""` if none |
| `ai_prompt` | string (CSV-escaped) | **The exact prompt/input for this specific call** (not the whole user message) | `Edit file src/main.py to add...` | Sanitize: strip API keys, passwords |
| `ai_response` | string (CSV-escaped) | **The full response for this specific call** | `--- src/main.py\n+++ src/main.py\n@@ -1,5 +1,7 @@` | Full response, no truncation |
| `provider` | string | LLM provider name | `anthropic`, `openai`, `local` | `unknown` |
| `model_used` | string | Exact model name/version | `claude-3-5-sonnet`, `gpt-4o` | `unknown` |
| `is_fallback` | boolean | Did the request fall back to a different model? | `true`, `false` | `false` |
| `tokens_in` | int | Prompt token count for this call | `1250` | `0` |
| `tokens_out` | int | Completion token count for this call | `340` | `0` |
| `tokens_cached` | int | Cached tokens for this call | `500` | `0` |
| `latency_ms` | int | Total request latency for this call | `1840` | `0` |
| `schema_version` | int | Version of this logging schema | `2` | **Always `2`** |
| `workspace_path` | string | Workspace or project root directory | `/Users/me/my-project` | `.` if unknown |
| `tool_used` | string | Name of the tool/function called, if any | `edit_file`, `read_file`, `web_search`, `chat` | `chat` if no tool |
| `file_paths_affected` | string (JSON, CSV-escaped) | Array of file paths modified/read by this call | `["src/main.py", "src/utils.py"]` | `"[]"` |
| `full_history` | string (JSON, CSV-escaped) | Conversation history *before* this call | `"[{""role"":""user"",""content"":""hi""}]"` | `"[]"` |
| `available_tools` | string (JSON, CSV-escaped) | Tools available to the LLM for this call | `"[""edit_file"",""read_file""]"` | `"[]"` |
| `full_history_count` | int | Total messages in conversation before this call | `5` | `0` |
| `provider_meta` | string (JSON, CSV-escaped) | Provider-specific metadata for this call | `"{"tool_name":"edit_file"}"` | `"{}"` |
| `created_at` | ISO 8601 timestamp | UTC timestamp of call completion | `2026-06-07T14:32:45.123Z` | `datetime.utcnow().isoformat()` + `Z` |

---

## Call-Level Granularity Examples

### Example 1: Single Chat Response
User says "Hello" → One LLM call → One row.

```
call-001,session-001,msg-001,0,0,assistant,"You are helpful.","Hello","Hello! How can I help?","anthropic","claude-3-5-sonnet",false,5,15,0,800,2,/home/user/project,"chat","[]","[]","[""chat""]",0,"{}",2026-06-07T14:32:45.123Z
```

### Example 2: Multi-File Edit
User says "Refactor auth and add tests" → Agent makes 5 calls:

| call_index | tool_used | file_paths_affected | ai_prompt (truncated) |
|------------|-----------|---------------------|----------------------|
| 0 | `read_file` | `["src/auth.py"]` | "Read src/auth.py to understand current auth logic" |
| 1 | `edit_file` | `["src/auth.py"]` | "Refactor auth.py to use JWT tokens" |
| 2 | `read_file` | `["tests/test_auth.py"]` | "Read existing auth tests" |
| 3 | `edit_file` | `["tests/test_auth.py"]` | "Add tests for JWT auth" |
| 4 | `chat` | `[]` | "Summarize changes made" |

**5 rows in CSV**, all with same `parent_message_id` and `turn_index=0`, but `call_index` 0-4.

---

## CSV Escaping Rules

**All string fields must follow RFC 4180 CSV escaping:**

1. If a field contains a comma (`,`), newline, or double-quote (`"`), wrap the entire field in double-quotes.
2. If a field contains a double-quote, escape it by doubling: `"` → `""`
3. JSON fields (`file_paths_affected`, `full_history`, `available_tools`, `provider_meta`) must be wrapped in quotes, with internal quotes doubled.

### Example Row (Multi-File Edit)

```
call-002,session-001,msg-001,0,1,assistant,"You are a helpful coding assistant.","Edit src/auth.py to use JWT tokens instead of session cookies","--- src/auth.py\n+++ src/auth.py\n@@ -1,10 +1,12 @@\n-import session\n+import jwt\n...",anthropic,claude-3-5-sonnet,false,2500,800,0,3200,2,/home/user/project,edit_file,"[""src/auth.py""]","[{""role"":""user"",""content"":""Refactor auth""}]","[""read_file"",""edit_file"",""chat""]",1,"{""tool_name"":""edit_file""}",2026-06-07T14:33:12.456Z
```

---

## Sensitive Data Scrubbing

**CRITICAL:** Before logging any field, agents MUST scrub sensitive information:

### Always Remove
- API keys, tokens, credentials
- Database connection strings
- Private URLs (internal services, private repos)
- Email addresses, phone numbers, usernames
- Filenames that reveal PII (e.g., `/home/alice/...`)
- Environment variable values that contain secrets

### Scrubbing Strategy
1. **API keys:** Replace with `[REDACTED_API_KEY]`
2. **Paths:** Replace `/home/username/` with `/home/USER/` or `.`
3. **Email:** Replace `user@example.com` with `[REDACTED_EMAIL]`
4. **Full connection strings:** Replace with `[REDACTED_CREDENTIALS]`

### Example
**Original prompt:**
```
Write a query: SELECT * FROM db WHERE api_key='sk-1234567890abcdef' AND user='alice@corp.com'
```

**Scrubbed:**
```
Write a query: SELECT * FROM db WHERE api_key='[REDACTED_API_KEY]' AND user='[REDACTED_EMAIL]'
```

---

## Implementation Guide

### Python Example

```python
import csv
from datetime import datetime
import json
import os
import uuid

def log_call(
    session_id,
    parent_message_id,
    turn_index,
    call_index,
    system_prompt,
    ai_prompt,
    ai_response,
    provider,
    model_used,
    tool_used="chat",
    file_paths_affected=None,
    tokens_in=0,
    tokens_out=0,
    latency_ms=0,
    is_fallback=False,
    tokens_cached=0,
    workspace_path=".",
    full_history=None,
    available_tools=None,
    provider_meta=None,
):
    """Log a single LLM call to CSV."""
    
    call_id = str(uuid.uuid4())
    csv_path = os.path.expanduser("~/.agents/agent-calls.csv")
    
    row = {
        "call_id": call_id,
        "session_id": session_id,
        "parent_message_id": parent_message_id,
        "turn_index": turn_index,
        "call_index": call_index,
        "role": "assistant",
        "system_prompt": system_prompt or "",
        "ai_prompt": scrub_secrets(ai_prompt),
        "ai_response": scrub_secrets(ai_response),
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
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    
    agents_dir = os.path.expanduser("~/.agents")
    os.makedirs(agents_dir, exist_ok=True)
    
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row)


def scrub_secrets(text):
    """Remove API keys, credentials, and PII from text."""
    import re
    
    text = re.sub(r'(api[_-]?key|token|password|secret)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
                  r'\1=[REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                  '[REDACTED_EMAIL]', text)
    text = re.sub(r'/home/[a-zA-Z0-9_-]+/', '/home/USER/', text)
    text = re.sub(r'/Users/[a-zA-Z0-9_-]+/', '/Users/USER/', text)
    
    return text
```

### JavaScript Example

```javascript
import fs from 'fs';
import path from 'path';
import os from 'os';
import { v4 as uuidv4 } from 'uuid';

async function logCall({
  sessionId,
  parentMessageId,
  turnIndex,
  callIndex,
  systemPrompt,
  aiPrompt,
  aiResponse,
  provider,
  modelUsed,
  toolUsed = 'chat',
  filePathsAffected = [],
  tokensIn = 0,
  tokensOut = 0,
  latencyMs = 0,
  isFallback = false,
  tokensCached = 0,
  workspacePath = '.',
  fullHistory = [],
  availableTools = [],
  providerMeta = {},
}) {
  const callId = uuidv4();
  const agentsDir = path.join(os.homedir(), '.agents');
  const csvPath = path.join(agentsDir, 'agent-calls.csv');
  
  if (!fs.existsSync(agentsDir)) {
    fs.mkdirSync(agentsDir, { recursive: true });
  }
  
  const row = {
    call_id: callId,
    session_id: sessionId,
    parent_message_id: parentMessageId,
    turn_index: turnIndex,
    call_index: callIndex,
    role: 'assistant',
    system_prompt: systemPrompt || '',
    ai_prompt: scrubSecrets(aiPrompt),
    ai_response: scrubSecrets(aiResponse),
    provider,
    model_used: modelUsed,
    is_fallback: isFallback.toString(),
    tokens_in: tokensIn,
    tokens_out: tokensOut,
    tokens_cached: tokensCached,
    latency_ms: latencyMs,
    schema_version: 2,
    workspace_path: workspacePath,
    tool_used: toolUsed,
    file_paths_affected: JSON.stringify(filePathsAffected),
    full_history: JSON.stringify(fullHistory),
    available_tools: JSON.stringify(availableTools),
    full_history_count: fullHistory.length,
    provider_meta: JSON.stringify(providerMeta),
    created_at: new Date().toISOString(),
  };

  const fileExists = fs.existsSync(csvPath);
  const isFileEmpty = !fileExists || fs.statSync(csvPath).size === 0;

  const csvRow = Object.values(row)
    .map(v => {
      const str = String(v);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    })
    .join(',');

  const header = Object.keys(row).join(',') + '\n';
  const content = isFileEmpty ? header + csvRow + '\n' : csvRow + '\n';
  
  fs.appendFileSync(csvPath, content, 'utf8');
}

function scrubSecrets(text) {
  text = text.replace(/(['\"`]?(?:api[_-]?key|token|password|secret)['\"`]?\s*[=:]\s*['\"`]?)([a-zA-Z0-9_\-]{20,})/gi,
    '$1[REDACTED]');
  text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    '[REDACTED_EMAIL]');
  text = text.replace(/\/home\/[a-zA-Z0-9_-]+\//g, '/home/USER/');
  text = text.replace(/\/Users\/[a-zA-Z0-9_-]+\//g, '/Users/USER/');
  return text;
}
```

---

## Boundaries (Three-Tier Model)

### Always Do
- Log **every individual LLM call** (not just the final response)
- Include `call_index` to preserve call order within a turn
- Set `tool_used` correctly (`chat`, `edit_file`, `read_file`, `web_search`, etc.)
- Populate `file_paths_affected` with actual files touched by this call
- Escape CSV fields correctly
- Use UTF-8 encoding
- Include `created_at` timestamp in ISO 8601 format
- Scrub secrets from `ai_prompt` **and** `ai_response`
- Append to file in order (never shuffle, reorder, or delete)

### Ask First
- If the call involves external APIs: still log, set `available_tools` accordingly
- If tokens/latency unavailable: use `0` and continue
- If workspace unknown: use `.` and continue
- If `parent_message_id` is unavailable: use `session_id` as fallback

### Never Do (Hard Stops)
- **Never** collapse multiple calls into one row
- **Never** log credentials, API keys, or tokens (use scrubbing)
- **Never** log PII (use redaction)
- **Never** truncate or modify prior rows
- **Never** delete rows from the CSV
- **Never** change the CSV column order
- **Never** skip logging because "the data is incomplete"—use defaults instead
- **Never** commit the CSV to git (add `agent-calls.csv` to `.gitignore`)

---

## Validation Checklist

Before marking a call as logged, verify:

- [ ] CSV header exists (run once on first write)
- [ ] `call_id` is unique (UUID4 recommended)
- [ ] `call_index` increments correctly within the turn
- [ ] `tool_used` reflects the actual call type
- [ ] `file_paths_affected` is accurate for this specific call
- [ ] All required fields are present
- [ ] Strings with commas/quotes are properly escaped
- [ ] Secrets are scrubbed from prompts and responses
- [ ] `created_at` is ISO 8601 with timezone
- [ ] `role` is exactly `"assistant"`
- [ ] Numeric fields are integers or 0
- [ ] JSON fields are valid JSON
- [ ] File is UTF-8 encoded
- [ ] Row is appended, not inserted or reordered

---

## Example Workflow

```
1. User says: "Refactor auth and add tests"
2. Agent plans: read auth.py → edit auth.py → read tests → edit tests → summarize
3. Call 0: read_file("auth.py") → log row with call_index=0, tool_used="read_file"
4. Call 1: edit_file("auth.py", <diff>) → log row with call_index=1, tool_used="edit_file"
5. Call 2: read_file("test_auth.py") → log row with call_index=2, tool_used="read_file"
6. Call 3: edit_file("test_auth.py", <diff>) → log row with call_index=3, tool_used="edit_file"
7. Call 4: chat("Done. Changed X, Y, Z.") → log row with call_index=4, tool_used="chat"
8. CSV now contains 5 rows for this single user message
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CSV file doesn't exist | Create it with the header row on first write |
| Rows aren't appending | Check file permissions; ensure append mode is used |
| Fields have extra quotes in CSV | Double all internal quotes: `"` → `""` |
| Data looks garbled | Verify UTF-8 encoding; check CSV parser settings |
| Some fields are missing | Use defaults: `0` for numbers, `""` for strings, `"[]"` for JSON |
| Secrets weren't scrubbed | Improve regex patterns in `scrub_secrets()`; test manually |
| `call_index` is wrong | Ensure it resets to 0 for each new `turn_index` |

---

## Future Extensions

This schema is versioned (`schema_version: 2`). If you add fields in the future:
1. Increment `schema_version` to `3`
2. Add new columns to the right of existing ones
3. Use safe defaults for old logs (backward compatibility)
4. Document breaking changes clearly

---

## Questions or Feedback?

This AGENTS.md is the single source of truth for call-level logging. If an agent's behavior differs from this spec, the spec takes precedence.

**Last Updated:** 2026-06-07
**Schema Version:** 2
```

---

**Key changes made:**

| Change | Why |
|--------|-----|
| **File renamed** to `agent-calls.csv` | Reflects call-level, not message-level |
| **`call_id` added** | Unique per call |
| **`call_index` added** | Orders calls within a turn |
| **`tool_used` added** | Identifies what kind of call it was |
| **`file_paths_affected` added** | Tracks which files each call touched |
| **`parent_message_id` added** | Groups calls that came from one user message |
| **`schema_version` bumped to 2** | Breaking change from v1 |
| **Examples updated** | Shows 5 rows for 1 user message |
| **`ai_prompt`/`ai_response` scoped** | Per-call, not per-message |
