#!/usr/bin/env python3
"""
Import OpenCode SQLite session data into the same CSV as Gemini sessions.

Usage:
    python import_opencode.py [--min-turns 2] [--out gemini_sessions.csv] [--append]

Uses system_prompt field as quality tag: [source:opencode] or [source:gemini]
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
DB_PATH = os.path.join(HOME, ".local/share/opencode/opencode.db")

# --- Scrubbing (shared with import_sessions.py) ---

SECRET_PATTERNS = [
    ("AWS",         re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GCP",         re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("OPENAI",      re.compile(r"sk-[a-zA-Z0-9]{48}")),
    ("ANTHROPIC",   re.compile(r"sk-ant-api03-[a-zA-Z0-9\-_]{93}")),
    ("STRIPE",      re.compile(r"sk_live_[0-9a-zA-Z]{24}")),
    ("GITHUB",      re.compile(r"ghp_[a-zA-Z0-9]{36}")),
    ("GITHUB_PAT",  re.compile(r"github_pat_[a-zA-Z0-9_]{80,}")),
    ("SUPABASE_JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("HCAPTCHA",    re.compile(r"ES_[a-f0-9]{32}")),
    ("GENERIC_SECRET", re.compile(
        r'(?i)(password|secret|api_key|token|auth|credential|private_key)'
        r'["\s:=]+([A-Za-z0-9\-._~+/]{20,})'
    )),
]
HOME_PATH_RE = re.compile(r"/home/[a-zA-Z0-9_-]+(?:/[^\s\"'<>,;:]+)*")
SECRET_KEY_VAL_RE = re.compile(r"(?i)(secret_key|api_key|api_secret|password)\s*[=:]\s*[A-Za-z0-9\-._]{15,}")
SUPABASE_URL_RE = re.compile(r"(?:https?://)?[a-z0-9]{20,}\.supabase\.co")
DEPLOYMENT_URL_RE = re.compile(
    r"(?:https?://)?[\w-]+\.onrender\.com"
    r"|(?:https?://)?[\w-]+\.vercel\.app"
    r"|(?:https?://)?[\w-]+\.hf\.space"
    r"|(?:https?://)?[\w-]+\.github\.io"
    r"|(?:https?://)?[\w-]+\.pythonanywhere\.com"
    r"|(?:https?://)?gitlab\.com/[\w-]+"
    r"|(?:https?://)?esm\.sh/gh/[\w-]+"
    r"|[\w-]+-github-io"
    r"|(?:https?://)?raw\.githubusercontent\.com/[\w-]+"
)
GIT_AUTHOR_RE = re.compile(r"Author:\s*[^<]+<[^>]+>")
GITHUB_USER_URL_RE = re.compile(r"github\.com[/:][\w-]+/[\w-]+")
SSH_HOST_RE = re.compile(r"git@github\.com-\w+:")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
NUMERIC_USERID_RE = re.compile(r"\d+\+[\w]+@users\.noreply\.github\.com")
WAKATIME_RE = re.compile(r"wakatime\.com/share/@[\w]+/[0-9a-f-]+")
UMAMI_ID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
WAKATIME_RE = re.compile(r"wakatime\.com/share/@[\w]+/[0-9a-f-]+")
UMAMI_ID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def scrub(text) -> str:
    if isinstance(text, list):
        text = "\n".join(str(t) for t in text)
    if not text:
        return ""
    text = str(text)
    for label, pat in SECRET_PATTERNS:
        if label == "GENERIC_SECRET":
            text = pat.sub(r"\1: [SCRUBBED]", text)
        else:
            text = pat.sub(f"[SCRUBBED_{label}]", text)
    text = HOME_PATH_RE.sub("/home/[USER]", text)
    text = SECRET_KEY_VAL_RE.sub(r"\1: [SCRUBBED]", text)
    text = SUPABASE_URL_RE.sub("[SCRUBBED_SUPABASE_URL]", text)
    text = DEPLOYMENT_URL_RE.sub("[SCRUBBED_URL]", text)
    text = GIT_AUTHOR_RE.sub("Author: [SCRUBBED] <[SCRUBBED]>", text)
    text = GITHUB_USER_URL_RE.sub("github.com/[USER]/[REPO]", text)
    text = SSH_HOST_RE.sub("git@github.com:[USER]/", text)
    text = EMAIL_RE.sub("[SCRUBBED_EMAIL]", text)
    text = NUMERIC_USERID_RE.sub("[SCRUBBED_EMAIL]", text)
    text = WAKATIME_RE.sub("wakatime.com/share/@[SCRUBBED]", text)
    text = UMAMI_ID_RE.sub("[SCRUBBED_UUID]", text)
    return text


def scrub_recursive(obj):
    if isinstance(obj, str):
        return scrub(obj)
    if isinstance(obj, dict):
        return {k: scrub_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub_recursive(v) for v in obj]
    return obj


def truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "[TRUNCATED]"


# --- DB helpers ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_sessions(conn):
    """Get all sessions with metadata."""
    rows = conn.execute("""
        SELECT id, title, project_id, model, 
               tokens_input, tokens_output, tokens_reasoning,
               tokens_cache_read, tokens_cache_write,
               time_created, time_updated, cost
        FROM session
        WHERE tokens_input > 0 OR tokens_output > 0
        ORDER BY time_created
    """).fetchall()
    return rows


def get_session_messages(conn, session_id):
    """Get all messages for a session, ordered by time."""
    rows = conn.execute("""
        SELECT id, data, time_created
        FROM message
        WHERE session_id = ?
        ORDER BY time_created
    """, (session_id,)).fetchall()
    return rows


def get_message_parts(conn, message_id):
    """Get all parts for a message, ordered by time."""
    rows = conn.execute("""
        SELECT data, time_created
        FROM part
        WHERE message_id = ?
        ORDER BY time_created
    """, (message_id,)).fetchall()
    return rows


# --- Part extraction ---

def extract_text_parts(parts):
    """Extract text content from part list."""
    texts = []
    for p in parts:
        try:
            d = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
        except (json.JSONDecodeError, TypeError):
            continue
        if d.get("type") == "text":
            texts.append(d.get("text", ""))
    return "\n".join(texts)


def extract_reasoning(parts):
    """Extract reasoning/chain-of-thought from part list."""
    texts = []
    for p in parts:
        try:
            d = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
        except (json.JSONDecodeError, TypeError):
            continue
        if d.get("type") == "reasoning":
            texts.append(d.get("text", ""))
    return "\n".join(texts)


def extract_tool_calls(parts):
    """Extract tool calls with inputs and outputs."""
    tools = []
    for p in parts:
        try:
            d = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
        except (json.JSONDecodeError, TypeError):
            continue
        if d.get("type") != "tool":
            continue
        state = d.get("state", {})
        inp = state.get("input", {})
        out = state.get("output", "")
        tools.append({
            "name": d.get("tool", ""),
            "args": inp if isinstance(inp, dict) else {"input": str(inp)},
            "result_preview": truncate(scrub(str(out)), 2000),
            "status": state.get("status", "unknown"),
        })
    return tools


def extract_patches(parts):
    """Extract patch file lists."""
    patches = []
    for p in parts:
        try:
            d = json.loads(p["data"]) if isinstance(p["data"], str) else p["data"]
        except (json.JSONDecodeError, TypeError):
            continue
        if d.get("type") == "patch":
            files = d.get("files", [])
            patches.extend(files)
    return patches


# --- Turn builder ---

def parse_model_field(model_str):
    """Extract model ID from OpenCode's model JSON field."""
    if not model_str:
        return ""
    try:
        m = json.loads(model_str) if isinstance(model_str, str) else model_str
        return m.get("id", str(model_str))
    except (json.JSONDecodeError, TypeError):
        return str(model_str)


def build_turns_from_session(conn, session):
    """Convert an OpenCode session into CSV rows."""
    session_id = session["id"]
    title = session["title"] or ""
    model = parse_model_field(session["model"])
    project_row = conn.execute(
        "SELECT name, worktree FROM project WHERE id = ?",
        (session["project_id"],)
    ).fetchone()
    if project_row:
        project = project_row["name"] or os.path.basename(project_row["worktree"] or "")
    else:
        project = "unknown"
    project = DEPLOYMENT_URL_RE.sub("[SCRUBBED_URL]", project)

    messages = get_session_messages(conn, session_id)
    if not messages:
        return []

    turns = []
    pending_user = None
    pending_user_parts = []
    acc_text = []
    acc_reasoning = []
    acc_tool_calls = []
    acc_patches = []
    acc_tokens = {"input": 0, "output": 0, "cached": 0}
    last_asst_ts = None
    first_user_ts = None

    for msg in messages:
        try:
            data = json.loads(msg["data"]) if isinstance(msg["data"], str) else msg["data"]
        except (json.JSONDecodeError, TypeError):
            continue

        role = data.get("role", "")
        parts = get_message_parts(conn, msg["id"])

        if role == "user":
            # Flush previous turn if we have accumulated content
            if pending_user is not None and (acc_text or acc_tool_calls):
                turns.append(_assemble_turn(
                    pending_user, pending_user_parts,
                    acc_text, acc_reasoning, acc_tool_calls, acc_patches,
                    acc_tokens, last_asst_ts, first_user_ts, model, session_id, project,
                ))

            pending_user = data
            pending_user_parts = parts
            acc_text = []
            acc_reasoning = []
            acc_tool_calls = []
            acc_patches = []
            acc_tokens = {"input": 0, "output": 0, "cached": 0}
            last_asst_ts = None
            first_user_ts = msg["time_created"]

        elif role == "assistant":
            if pending_user is None:
                continue

            # Accumulate parts from this assistant message
            acc_text.append(extract_text_parts(parts))
            acc_reasoning.append(extract_reasoning(parts))
            acc_tool_calls.extend(extract_tool_calls(parts))
            acc_patches.extend(extract_patches(parts))

            tokens = data.get("tokens", {})
            acc_tokens["input"] += tokens.get("input", 0) or 0
            acc_tokens["output"] += tokens.get("output", 0) or 0
            acc_tokens["cached"] += (tokens.get("cache") or {}).get("read", 0) or 0

            last_asst_ts = msg["time_created"]

    # Flush last turn
    if pending_user is not None and (acc_text or acc_tool_calls):
        turns.append(_assemble_turn(
            pending_user, pending_user_parts,
            acc_text, acc_reasoning, acc_tool_calls, acc_patches,
            acc_tokens, last_asst_ts, first_user_ts, model, session_id, project,
        ))

    return turns


def _assemble_turn(user_data, user_parts, text_list, reasoning_list,
                    tool_calls, patches, tokens, last_ts, first_ts,
                    model, session_id, project):
    """Assemble a turn from accumulated assistant data."""
    user_text = extract_text_parts(user_parts)
    user_text = scrub(user_text)
    if not user_text.strip() and not tool_calls:
        return None

    # Build response: reasoning + text + patch summary
    response_parts = []
    reasoning_combined = "\n".join(r for r in reasoning_list if r)
    if reasoning_combined:
        response_parts.append(f"[reasoning]\n{reasoning_combined}")
    text_combined = "\n".join(t for t in text_list if t)
    if text_combined:
        response_parts.append(text_combined)
    if patches:
        patch_list = ", ".join(os.path.basename(p) for p in patches[:10])
        response_parts.append(f"[patches: {patch_list}]")

    response = scrub("\n\n".join(response_parts))

    for tc in tool_calls:
        tc["args"] = scrub_recursive(tc["args"])
        tc["result_preview"] = truncate(scrub(tc["result_preview"]), 2000)

    latency_ms = 0
    if first_ts and last_ts:
        try:
            latency_ms = int(last_ts - first_ts)
        except (TypeError, ValueError):
            pass

    timestamp = ""
    if last_ts:
        try:
            timestamp = datetime.fromtimestamp(
                last_ts / 1000, tz=timezone.utc
            ).isoformat()
        except (TypeError, ValueError):
            pass

    full_history = json.dumps([
        {"role": "user", "content": truncate(user_text, 5000)},
        {"role": "assistant", "content": truncate(response, 5000)},
    ])

    return {
        "session_id": f"oc_{session_id}",
        "project": project,
        "turn_index": 0,  # set later
        "user_prompt": user_text,
        "assistant_response": response,
        "tool_calls": json.dumps(tool_calls) if tool_calls else "[]",
        "model": model,
        "tokens_in": tokens["input"],
        "tokens_out": tokens["output"],
        "tokens_cached": tokens["cached"],
        "timestamp": timestamp,
        "latency_ms": latency_ms,
        "system_prompt": f"[source:opencode]",
        "full_history": full_history,
    }


def _build_turn(user_data, user_parts, assistant_data, assistant_parts, model, session_ts):
    """Build a turn from raw data (for flush-at-end cases)."""
    user_text = extract_text_parts(user_parts)
    user_text = scrub(user_text)
    if not user_text.strip():
        return None

    return {
        "session_id": "",
        "project": "",
        "turn_index": 0,
        "user_prompt": user_text,
        "assistant_response": "",
        "tool_calls": "[]",
        "model": model,
        "tokens_in": 0,
        "tokens_out": 0,
        "tokens_cached": 0,
        "timestamp": "",
        "latency_ms": 0,
        "system_prompt": "[source:opencode]",
        "full_history": "",
    }


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Import OpenCode sessions to CSV")
    parser.add_argument("--min-turns", type=int, default=2,
                        help="Min messages per session (default: 2)")
    parser.add_argument("--out", default="gemini_sessions.csv",
                        help="Output CSV path (default: gemini_sessions.csv)")
    parser.add_argument("--append", action="store_true",
                        help="Append to existing CSV (default: overwrite)")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"OpenCode DB not found at {DB_PATH}")
        sys.exit(1)

    conn = get_db()
    sessions = get_sessions(conn)
    print(f"Found {len(sessions)} sessions with token data")

    all_rows = []
    skipped = 0

    for session in sessions:
        turns = build_turns_from_session(conn, session)
        turns = [t for t in turns if t is not None]
        if len(turns) >= args.min_turns:
            all_rows.extend(turns)
        else:
            skipped += 1

    conn.close()

    print(f"Imported {len(all_rows)} turns from {len(all_rows) // max(args.min_turns, 1)}+ sessions")
    print(f"Skipped {skipped} short sessions")

    if not all_rows:
        print("No data to write.")
        return

    # Read existing CSV if appending
    fieldnames = [
        "session_id", "project", "turn_index", "user_prompt", "assistant_response",
        "tool_calls", "model", "tokens_in", "tokens_out", "tokens_cached",
        "timestamp", "latency_ms", "system_prompt", "full_history",
    ]

    existing_rows = []
    if args.append and os.path.exists(args.out):
        import io, csv as csv_mod
        csv_mod.field_size_limit(sys.maxsize)
        with open(args.out, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
        print(f"Loaded {len(existing_rows)} existing rows from {args.out}")

    all_rows = [r for r in all_rows if r is not None]
    all_rows = existing_rows + all_rows

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    size_mb = os.path.getsize(args.out) / (1024 * 1024)
    print(f"Wrote {args.out} ({size_mb:.1f} MB, {len(all_rows)} rows)")

    # Stats
    projects = {}
    total_in = 0
    total_out = 0
    for r in all_rows:
        p = r["project"]
        projects[p] = projects.get(p, 0) + 1
        total_in += int(r["tokens_in"] or 0)
        total_out += int(r["tokens_out"] or 0)

    print(f"\nToken totals: {total_in:,} in / {total_out:,} out")

    # Source breakdown
    gemini = sum(1 for r in all_rows if "[source:gemini]" in (r.get("system_prompt") or ""))
    opencode = sum(1 for r in all_rows if "[source:opencode]" in (r.get("system_prompt") or ""))
    print(f"Sources: {gemini} gemini, {opencode} opencode")


if __name__ == "__main__":
    main()
