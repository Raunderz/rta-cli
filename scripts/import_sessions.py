#!/usr/bin/env python3
"""
Import Gemini CLI session history into a CSV dataset for fine-tuning.

Usage:
    python import_sessions.py [--min-turns 4] [--out gemini_sessions.csv]
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")

# --- Scrubbing ---

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

HOME_PATH_RE = re.compile(r"/home/[a-zA-Z0-9_-]+")
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


def scrub(text) -> str:
    if isinstance(text, list):
        text = extract_text(text)
    if not text:
        return ""
    for label, pat in SECRET_PATTERNS:
        if label == "GENERIC_SECRET":
            text = pat.sub(r"\1: [SCRUBBED]", text)
        else:
            text = pat.sub(f"[SCRUBBED_{label}]", text)
    text = HOME_PATH_RE.sub("/home/[USER]", text)
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


def truncate(text: str, limit: int) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "[TRUNCATED]"


# --- Parsing ---

def is_real_user_message(line: dict) -> bool:
    """True if this is a genuine user message (not a tool result callback)."""
    if line.get("type") != "user":
        return False
    content = line.get("content", [])
    if not content:
        return False
    # Tool result callbacks have functionResponse in content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and "functionResponse" in item:
                return False
    return True


def is_user_skill_activation(line: dict) -> bool:
    """True if user is activating a skill via slash command."""
    content = line.get("content", [])
    display = line.get("displayContent", [])
    if isinstance(content, list) and len(content) == 1:
        text = content[0].get("text", "")
        if text.startswith("Use the skill "):
            return True
    if isinstance(display, list) and len(display) == 1:
        text = display[0].get("text", "")
        if text.startswith("/"):
            return True
    return False


def is_assistant_noise(line: dict) -> bool:
    """True if assistant message is just a skill activation or empty."""
    tool_calls = line.get("toolCalls", [])
    content = line.get("content", "")
    text = extract_text(content) if content else ""

    if not tool_calls and not text:
        return True
    if tool_calls and not text:
        names = [tc.get("name", "") for tc in tool_calls]
        if all(n == "activate_skill" for n in names):
            return True
    # Skill activation confirmation messages
    if text and not tool_calls:
        lower = text.strip().lower()
        if lower.startswith("caveman mode active") or lower.startswith("ok. caveman"):
            return True
        if lower.endswith("activated.") and len(text) < 100:
            return True
    return False


def is_noise_line(line: dict) -> bool:
    """True if line should be skipped entirely."""
    t = line.get("type", "")
    if t in ("meta", "error", "info"):
        return True
    if "$set" in line:
        return True
    if "sessionId" in line and "projectHash" in line:
        return True
    return False


def extract_text(content) -> str:
    """Pull text out of Gemini content (string or array of objects)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(item["text"])
        return "\n".join(parts)
    return ""


def strip_session_context(text: str) -> str:
    """Remove <session_context>...</session_context> blocks."""
    return re.sub(r"<session_context>.*?</session_context>", "", text, flags=re.DOTALL).strip()


def truncate_file_refs(text: str) -> str:
    """Truncate 'Content from @file.md:' reference blocks."""
    def _truncate_ref(m):
        header = m.group(0)
        lines = header.split("\n")
        if len(lines) > 5:
            return "\n".join(lines[:5]) + "\n[...truncated...]"
        return header
    return re.sub(
        r"(?:Content from @\S+:\n)(?:.*\n){0,20}",
        _truncate_ref,
        text,
        flags=re.MULTILINE,
    )


def convert_tool_call(tc: dict) -> dict:
    """Convert Gemini tool call to compact dict."""
    args = tc.get("args", {})
    # Scrub path values in args
    if isinstance(args, dict):
        args = {k: scrub(str(v)) if isinstance(v, str) else v for k, v in args.items()}
    result_text = ""
    for r in tc.get("result", []):
        fr = r.get("functionResponse", {})
        if fr:
            result_text = fr.get("response", {}).get("output", "")
    return {
        "name": tc.get("name", ""),
        "args": args,
        "result_preview": truncate(scrub(result_text), 2000),
    }


def _build_turn(user_line, text_parts, tool_calls, tokens, last_ts, model) -> dict:
    """Build a single turn dict from accumulated assistant content."""
    user_text = extract_text(user_line.get("content", []))
    user_text = strip_session_context(user_text)
    user_text = truncate_file_refs(user_text)
    user_text = scrub(user_text)

    assistant_text = scrub("\n".join(text_parts))

    latency_ms = 0
    try:
        t_user = datetime.fromisoformat(
            user_line["timestamp"].replace("Z", "+00:00")
        )
        t_asst = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        latency_ms = int((t_asst - t_user).total_seconds() * 1000)
    except (KeyError, ValueError, TypeError):
        pass

    return {
        "user_prompt": user_text,
        "assistant_response": assistant_text,
        "tool_calls": json.dumps(tool_calls) if tool_calls else "[]",
        "model": model,
        "tokens_in": tokens["input"],
        "tokens_out": tokens["output"],
        "tokens_cached": tokens["cached"],
        "timestamp": last_ts or "",
        "latency_ms": latency_ms,
    }


def extract_system_prompt(lines: list) -> str:
    """Pull session_context from first user message as system prompt."""
    for line in lines:
        if line.get("type") == "user":
            content = extract_text(line.get("content", ""))
            m = re.search(r"<session_context>(.*?)</session_context>", content, re.DOTALL)
            if m:
                return scrub(m.group(1).strip())
            break
    return ""


def parse_session(filepath: str, min_turns: int) -> list[dict]:
    """Parse a single session file into turn-pair rows."""
    lines = []
    session_id = ""
    project = os.path.basename(os.path.dirname(os.path.dirname(filepath)))
    project = DEPLOYMENT_URL_RE.sub("[SCRUBBED_URL]", project)

    with open(filepath) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                line = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if is_noise_line(line):
                continue
            if "sessionId" in line and "projectHash" in line:
                session_id = line["sessionId"]
                continue
            lines.append(line)

    if not session_id:
        session_id = os.path.splitext(os.path.basename(filepath))[0]

    # Extract system prompt
    system_prompt = extract_system_prompt(lines)

    # Reconstruct conversation turns
    # Gemini flow: user → [assistant(tool_call) → user(tool_result)]* → assistant(text)
    # We accumulate all assistant content between real user messages into one turn.
    turns = []
    pending_user = None
    acc_tool_calls = []
    acc_tokens = {"input": 0, "output": 0, "cached": 0}
    acc_text_parts = []
    last_assistant_ts = None
    last_model = ""

    for line in lines:
        if line.get("type") == "user":
            if is_user_skill_activation(line):
                continue
            if not is_real_user_message(line):
                continue
            # New real user message — flush previous turn if pending
            if pending_user is not None and (acc_text_parts or acc_tool_calls):
                turns.append(_build_turn(
                    pending_user, acc_text_parts, acc_tool_calls,
                    acc_tokens, last_assistant_ts, last_model,
                ))
            pending_user = line
            acc_tool_calls = []
            acc_tokens = {"input": 0, "output": 0, "cached": 0}
            acc_text_parts = []
            last_assistant_ts = None
            last_model = ""

        elif line.get("type") == "gemini":
            if is_assistant_noise(line):
                continue
            if pending_user is None:
                continue

            # Accumulate tool calls
            for tc in line.get("toolCalls", []):
                if tc.get("name") != "activate_skill":
                    acc_tool_calls.append(convert_tool_call(tc))

            # Accumulate text content
            content = line.get("content", "")
            text = extract_text(content) if content else ""
            if text:
                acc_text_parts.append(text)

            # Accumulate tokens
            tokens = line.get("tokens") or {}
            acc_tokens["input"] += tokens.get("input", 0) or 0
            acc_tokens["output"] += tokens.get("output", 0) or 0
            acc_tokens["cached"] += tokens.get("cached", 0) or 0

            last_assistant_ts = line.get("timestamp")
            if line.get("model"):
                last_model = line["model"]

    # Flush last turn
    if pending_user is not None and (acc_text_parts or acc_tool_calls):
        turns.append(_build_turn(
            pending_user, acc_text_parts, acc_tool_calls,
            acc_tokens, last_assistant_ts, last_model,
        ))

    if len(turns) < min_turns:
        return []

    # Build full_history for context
    full_history = []
    for t in turns:
        if t["user_prompt"]:
            full_history.append({"role": "user", "content": truncate(t["user_prompt"], 5000)})
        full_history.append({
            "role": "assistant",
            "content": truncate(t["assistant_response"], 5000),
        })

    # Attach metadata to first turn only (to avoid repeating in CSV)
    rows = []
    for i, t in enumerate(turns):
        row = {
            "session_id": session_id,
            "project": project,
            "turn_index": i + 1,
            "user_prompt": t["user_prompt"],
            "assistant_response": t["assistant_response"],
            "tool_calls": t["tool_calls"],
            "model": t["model"],
            "tokens_in": t["tokens_in"],
            "tokens_out": t["tokens_out"],
            "tokens_cached": t["tokens_cached"],
            "timestamp": t["timestamp"],
            "latency_ms": t["latency_ms"],
            "system_prompt": f"[source:gemini] {system_prompt}" if i == 0 and system_prompt else "[source:gemini]",
            "full_history": json.dumps(full_history) if i == 0 else "",
        }
        rows.append(row)

    return rows


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Import Gemini sessions to CSV")
    parser.add_argument("--min-turns", type=int, default=4,
                        help="Min user messages per session (default: 4)")
    parser.add_argument("--out", default="gemini_sessions.csv",
                        help="Output CSV path (default: gemini_sessions.csv)")
    args = parser.parse_args()

    source_pattern = os.path.join(HOME, ".gemini/tmp/*/chats/session-*.jsonl")
    files = sorted(glob.glob(source_pattern))
    print(f"Found {len(files)} session files")

    all_rows = []
    skipped = 0
    errors = 0

    for filepath in files:
        try:
            rows = parse_session(filepath, args.min_turns)
            if rows:
                all_rows.extend(rows)
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR parsing {filepath}: {e}", file=sys.stderr)
            errors += 1

    print(f"Imported {len(all_rows)} turns from {len(all_rows) // max(args.min_turns, 1)}+ sessions")
    print(f"Skipped {skipped} short sessions, {errors} errors")

    if not all_rows:
        print("No data to write.")
        return

    # Write CSV
    fieldnames = [
        "session_id", "project", "turn_index", "user_prompt", "assistant_response",
        "tool_calls", "model", "tokens_in", "tokens_out", "tokens_cached",
        "timestamp", "latency_ms", "system_prompt", "full_history",
    ]

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    size_mb = os.path.getsize(args.out) / (1024 * 1024)
    print(f"Wrote {args.out} ({size_mb:.1f} MB)")

    # Quick stats
    projects = {}
    total_in = 0
    total_out = 0
    for r in all_rows:
        p = r["project"]
        projects[p] = projects.get(p, 0) + 1
        total_in += r["tokens_in"]
        total_out += r["tokens_out"]

    print(f"\nToken totals: {total_in:,} in / {total_out:,} out")
    print(f"Projects: {dict(sorted(projects.items(), key=lambda x: -x[1]))}")


if __name__ == "__main__":
    main()
