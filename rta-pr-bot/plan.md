# RTA PR Bot — Minimal Plan

## Goal
A bot that reviews GitHub PRs and posts comments — using the **RTA API** (same backend the CLI talks to). No team learning, no CLI/IDE integration, no cross-file context. Just: fetch diff → analyze via RTA API → comment on PR.

## What It Does

1. **PR Summary** — brief description of what changed and why
2. **Line-by-line review** — inline comments on the diff for bugs, security, performance, code quality
3. **Post results** — summary as PR comment + optional inline review comments

## Flow

```
GitHub PR opened/updated
        │
        ▼
Fetch PR metadata + diff (GitHub API)
        │
        ▼
Send code + prompt to RTA API (/v1/chat)
        │
        ▼
Parse structured review output
        │
        ▼
Post review as PR comment(s) (GitHub API)
```

## What We DON'T Build

- ❌ Team pattern learning
- ❌ CLI / IDE integration (already handled by rta-cli and rta-desktop)
- ❌ Code graph / cross-file context (v1)
- ❌ One-click fixes (just comments)
- ❌ Learning / feedback loop

## Tech

- **Language**: Python (reuses rta-cli patterns)
- **GH API**: `PyGithub` or raw `httpx` with a GitHub App / PAT
- **RTA API**: POST to `/v1/chat` with the diff + review prompt
- **Deployment**: Standalone webhook service (e.g., FastAPI)

## Repo Structure

```
rta-pr-bot/
├── plan.md
├── bot/
│   ├── __init__.py
│   ├── main.py           # FastAPI app — receives webhooks, orchestrates
│   ├── github_client.py  # Fetch PR diff, post comments (GitHub API)
│   ├── rta_reviewer.py   # Call RTA API for review
│   └── formatter.py      # Format review output into markdown
├── requirements.txt
└── README.md
```

## Implementation

| Module | What it does |
|---|---|
| `main.py` | FastAPI server listening for GitHub `pull_request` webhooks → triggers review pipeline |
| `github_client.py` | Uses a GitHub App or PAT to fetch PR diff + metadata, post review comments via GitHub API |
| `rta_reviewer.py` | Sends diff text to RTA API (`/v1/chat`) with a structured prompt asking for review output |
| `formatter.py` | Converts structured findings into GitHub markdown (summary + inline comments) |

All the bot does is produce **review output** containing findings — bugs, security issues, style problems, etc. The "issues found" you saw in the example is just the bot's output format, not a separate feature or system.

## Flow

```
GitHub webhook (pull_request.opened/synchronize)
        │
        ▼
main.py receives event
        │
        ▼
github_client fetches PR diff + metadata
        │
        ▼
rta_reviewer sends diff to RTA API with review prompt
        │
        ▼
Parse structured JSON response (findings list)
        │
        ▼
formatter converts findings → markdown
        │
        ▼
github_client posts:
  • summary comment on the PR
  • optional inline review comments on specific lines
```

## Review Output Format

The bot asks the RTA API to return JSON like:
```json
{
  "summary": "Adds rate limiting to /api/auth/login...",
  "findings": [
    {
      "file": "src/api/auth.py",
      "line": 42,
      "severity": "bug",
      "title": "Missing null check",
      "description": "user can be None when...",
      "suggestion": "if user is None: raise HTTPException(401)"
    }
  ]
}
```

These findings are the **entire point** of the bot — it's not a separate feature, it's the core output the bot produces.
