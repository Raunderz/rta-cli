# AGENTS.md — Centralized Interaction Logging

## Purpose

This document instructs AI agents to log all LLM interactions to a centralized CSV file for dataset collection and model fine-tuning. Every agent interaction (Claude, Cursor, local models, etc.) must be captured in a consistent format.

**Core principle:** One source of truth for all agent interactions on this machine.

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

4. **Done.** All agents will now log to `~/.agents/agent-interactions.csv` automatically.

---

## Logging Requirement

### Where
- **File location:** `~/.agents/agent-interactions.csv` (in home directory `.agents` folder)
- **Format:** CSV (RFC 4180 compliant)
- **Mode:** Append-only (never truncate or delete)
- **Encoding:** UTF-8
- **Absolute path:** `/home/yourusername/.agents/agent-interactions.csv`

This centralized location ensures all agent interactions from all projects are logged to a single file.

### When
Log every interaction **immediately after an LLM generates a response**. This includes:
- Direct Claude conversations
- Code-generation tasks in Cursor / Claude Code
- Local model inference
- Multi-turn conversations

Do NOT log:
- Failed/errored requests
- Incomplete or aborted interactions
- Test/sandbox runs

---

## CSV Schema

The file must have this header row (exactly as written):

```
user_id,session_id,turn_index,role,system_prompt,ai_prompt,ai_response,provider,model_used,is_fallback,tokens_in,tokens_out,tokens_cached,latency_ms,schema_version,workspace_path,full_history,available_tools,full_history_count,provider_meta,created_at
```

### Field Definitions

| Field | Type | Description | Example | If Unknown |
|-------|------|-------------|---------|-----------|
| `user_id` | UUID/string | Machine identifier or user alias | `local-machine-001` | Use a consistent machine ID |
| `session_id` | string | Unique session identifier (conversation/task) | `claude-chat-2026-06-07-001` | Generate: `{agent}-{timestamp}-{random}` |
| `turn_index` | int | Message turn within session (0-indexed) | `0`, `1`, `2` | Start at `0` |
| `role` | string | Always `assistant` (the LLM response) | `assistant` | **Always `assistant`** |
| `system_prompt` | string (CSV-escaped) | Initial system instruction given to LLM | `You are a helpful coding assistant...` | `""` (empty) if none |
| `ai_prompt` | string (CSV-escaped) | The exact user/input prompt that triggered this response | `Write a Python function to...` | Sanitize: strip API keys, passwords |
| `ai_response` | string (CSV-escaped) | The full LLM response text | `def my_func(): ...` | Full response, no truncation |
| `provider` | string | LLM provider name | `anthropic`, `openai`, `local` | `unknown` if unable to determine |
| `model_used` | string | Exact model name/version | `claude-3-5-sonnet`, `gpt-4o`, `llama-2-7b` | Model name or `unknown` |
| `is_fallback` | boolean | Did the request fall back to a different model? | `true`, `false` | `false` if not applicable |
| `tokens_in` | int | Prompt token count | `1250` | `0` if unavailable |
| `tokens_out` | int | Completion token count | `340` | `0` if unavailable |
| `tokens_cached` | int | Cached tokens (if applicable) | `500` | `0` if N/A |
| `latency_ms` | int | Total request latency in milliseconds | `1840` | `0` if unavailable |
| `schema_version` | int | Version of this logging schema | `1` | **Always `1`** |
| `workspace_path` | string | Workspace or project root directory | `/Users/me/my-project` | `.` (current dir) if unknown |
| `full_history` | string (JSON, CSV-escaped) | Complete sanitized conversation history as JSON array | `"[{""role"":""user"",""content"":""hi""},{""role"":""assistant"",""content"":""hello""}]"` | `"[]"` (empty array) if unavailable |
| `available_tools` | string (JSON, CSV-escaped) | List of tools/functions the LLM could access | `"[""code_execution"",""web_search""]"` | `"[]"` if none |
| `full_history_count` | int | Total messages in conversation so far | `5` | Count of messages or `0` |
| `provider_meta` | string (JSON, CSV-escaped) | Additional provider-specific metadata | `"{"models_tried":["gpt-4","gpt-3.5"],"retry_count":0}"` | `"{}"` (empty object) |
| `created_at` | ISO 8601 timestamp | UTC timestamp of interaction | `2026-06-07T14:32:45.123Z` | Use `datetime.utcnow().isoformat()` + `Z` |

---

## CSV Escaping Rules

**All string fields must follow RFC 4180 CSV escaping:**

1. If a field contains a comma (`,`), newline, or double-quote (`"`), wrap the entire field in double-quotes.
2. If a field contains a double-quote, escape it by doubling: `"` → `""`
3. JSON fields (full_history, available_tools, provider_meta) must be wrapped in quotes, with internal quotes doubled.

### Example Row

```
local-machine-001,claude-chat-2026-06-07-001,0,assistant,"You are a helpful assistant.","Write a Python function for Fibonacci","def fibonacci(n): return 1 if n<=1 else fibonacci(n-1)+fibonacci(n-2)",anthropic,claude-3-5-sonnet,false,1200,180,0,1840,1,/home/user/projects/ml-suite,"[{""role"":""user"",""content"":""Write a Fibonacci function""},{""role"":""assistant"",""content"":""def fibonacci(n)...\n""}]","[""code_execution""]",2,"{""models_tried"":[],""retry_count"":0}",2026-06-07T14:32:45.123Z
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
**Original:**
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

def log_interaction(
    session_id,
    turn_index,
    system_prompt,
    ai_prompt,
    ai_response,
    provider,
    model_used,
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
    """Log a single LLM interaction to CSV."""
    
    # Absolute path to central CSV location
    csv_path = os.path.expanduser("~/.agents/agent-interactions.csv")
    
    row = {
        "user_id": "local-machine-001",  # Replace with actual user/machine ID
        "session_id": session_id,
        "turn_index": turn_index,
        "role": "assistant",
        "system_prompt": system_prompt or "",
        "ai_prompt": scrub_secrets(ai_prompt),  # See scrub_secrets() below
        "ai_response": ai_response,
        "provider": provider,
        "model_used": model_used,
        "is_fallback": str(is_fallback).lower(),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_cached": tokens_cached,
        "latency_ms": latency_ms,
        "schema_version": 1,
        "workspace_path": workspace_path,
        "full_history": json.dumps(full_history or []),
        "available_tools": json.dumps(available_tools or []),
        "full_history_count": len(full_history) if full_history else 0,
        "provider_meta": json.dumps(provider_meta or {}),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    
    # Create ~/.agents directory if it doesn't exist
    agents_dir = os.path.expanduser("~/.agents")
    os.makedirs(agents_dir, exist_ok=True)
    
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        
        # Write header only if file is empty
        if f.tell() == 0:
            writer.writeheader()
        
        writer.writerow(row)


def scrub_secrets(text):
    """Remove API keys, credentials, and PII from text."""
    import re
    
    # Remove common API key patterns
    text = re.sub(r'(api[_-]?key|token|password|secret)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
                  r'\1=[REDACTED]', text, flags=re.IGNORECASE)
    
    # Remove email addresses
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                  '[REDACTED_EMAIL]', text)
    
    # Remove common path prefixes with usernames
    text = re.sub(r'/home/[a-zA-Z0-9_-]+/', '/home/USER/', text)
    text = re.sub(r'/Users/[a-zA-Z0-9_-]+/', '/Users/USER/', text)
    
    return text
```

### JavaScript Example

```javascript
import fs from 'fs';
import path from 'path';
import os from 'os';

async function logInteraction({
  sessionId,
  turnIndex,
  systemPrompt,
  aiPrompt,
  aiResponse,
  provider,
  modelUsed,
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
  // Absolute path to central CSV location
  const agentsDir = path.join(os.homedir(), '.agents');
  const csvPath = path.join(agentsDir, 'agent-interactions.csv');
  
  // Create ~/.agents directory if it doesn't exist
  if (!fs.existsSync(agentsDir)) {
    fs.mkdirSync(agentsDir, { recursive: true });
  }
  
  const row = {
    user_id: 'local-machine-001',
    session_id: sessionId,
    turn_index: turnIndex,
    role: 'assistant',
    system_prompt: systemPrompt || '',
    ai_prompt: scrubSecrets(aiPrompt),
    ai_response: aiResponse,
    provider,
    model_used: modelUsed,
    is_fallback: isFallback.toString(),
    tokens_in: tokensIn,
    tokens_out: tokensOut,
    tokens_cached: tokensCached,
    latency_ms: latencyMs,
    schema_version: 1,
    workspace_path: workspacePath,
    full_history: JSON.stringify(fullHistory),
    available_tools: JSON.stringify(availableTools),
    full_history_count: fullHistory.length,
    provider_meta: JSON.stringify(providerMeta),
    created_at: new Date().toISOString(),
  };

  // Check if file exists and is empty
  const fileExists = fs.existsSync(csvPath);
  const isFileEmpty = !fileExists || fs.statSync(csvPath).size === 0;

  // CSV string with proper escaping
  const csvRow = Object.values(row)
    .map(v => {
      const str = String(v);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    })
    .join(',');

  // Write header if file is new
  const header = Object.keys(row).join(',') + '\n';
  const content = isFileEmpty ? header + csvRow + '\n' : csvRow + '\n';
  
  fs.appendFileSync(csvPath, content, 'utf8');
}

function scrubSecrets(text) {
  // Remove API keys
  text = text.replace(/(['\"`]?(?:api[_-]?key|token|password|secret)['\"`]?\s*[=:]\s*['\"`]?)([a-zA-Z0-9_\-]{20,})/gi,
    '$1[REDACTED]');
  
  // Remove emails
  text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    '[REDACTED_EMAIL]');
  
  // Anonymize home paths
  text = text.replace(/\/home\/[a-zA-Z0-9_-]+\//g, '/home/USER/');
  text = text.replace(/\/Users\/[a-zA-Z0-9_-]+\//g, '/Users/USER/');
  
  return text;
}
```

---

## Boundaries (Three-Tier Model)

### Always Do
- Log every successful LLM response
- Escape CSV fields correctly (double-quote strings with commas)
- Use UTF-8 encoding
- Include `created_at` timestamp in ISO 8601 format
- Scrub secrets from `ai_prompt` and `ai_response`
- Append to file in order (never shuffle, reorder, or delete)

### Ask First
- If the interaction involves external APIs (web search, file uploads): still log, but set `available_tools` to reflect what was accessible
- If tokens/latency unavailable: use `0` and continue
- If workspace unknown: use `.` and continue

### Never Do (Hard Stops)
- **Never** log credentials, API keys, or tokens (use scrubbing)
- **Never** log PII like email addresses, phone numbers, or usernames (use redaction)
- **Never** truncate or modify prior rows
- **Never** delete rows from the CSV
- **Never** change the CSV column order
- **Never** skip logging because "the data is incomplete"—use defaults instead (0, empty string, "unknown")
- **Never** commit the CSV to git if it contains actual API calls (add `agent-interactions.csv` to `.gitignore`)

---

## Validation Checklist

Before marking an interaction as logged, verify:

- [ ] CSV header exists (run once on first write)
- [ ] All required fields are present in the row
- [ ] Strings with commas/quotes are properly escaped
- [ ] Secrets are scrubbed from prompts and responses
- [ ] `created_at` is ISO 8601 with timezone (e.g., `2026-06-07T14:32:45.123Z`)
- [ ] `role` is exactly `"assistant"`
- [ ] Numeric fields (tokens, latency) are integers or 0
- [ ] JSON fields (full_history, available_tools) are valid JSON
- [ ] File is UTF-8 encoded
- [ ] Row is appended, not inserted or reordered

---

## Example Workflow

```
1. Agent receives user prompt: "Write a function to call my API with key sk-abc123"
2. Agent calls LLM (e.g., Claude)
3. LLM returns response with code
4. Agent scrubs prompt: "Write a function to call my API with key [REDACTED_API_KEY]"
5. Agent scrubs response (if needed)
6. Agent logs the row to agent-interactions.csv
7. CSV now contains the sanitized interaction for training data
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

---

## Future Extensions

This schema is versioned (`schema_version: 1`). If you add fields in the future:
1. Increment `schema_version` to `2`
2. Add new columns to the right of existing ones
3. Use safe defaults for old logs (backward compatibility)
4. Document breaking changes clearly

---

## Questions or Feedback?

This AGENTS.md is the single source of truth for logging. If an agent's behavior differs from this spec, the spec takes precedence.

**Last Updated:** 2026-06-07
