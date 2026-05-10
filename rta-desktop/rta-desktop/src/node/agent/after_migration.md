# Plan: Minimal AI Coding Agent in Odin

## Project Overview

This project is a lightweight, hackable coding agent written in pure Odin. It allows an LLM (large language model) to act as an autonomous coding assistant that can read, edit, and work inside a local codebase using tools.

**Core Goal**: Build a clean, high-performance, understandable agent harness that is easy to modify and extend. Keep the codebase small and transparent.

**Key Capabilities**:
- Communicate with LLMs (OpenAI, Anthropic, local models, etc.)
- Use tools: read/write files, run shell commands, search code, etc.
- Run a reliable agent loop with tool calling
- Persist conversations and sessions
- Provide good terminal UX (CLI + optional TUI)
- Stay minimal and performant

## Tech Stack

- **Language**: Odin (latest version)
- **JSON**: `core:encoding/json`
- **HTTP**: `laytan/odin-http` or manual `core:net`
- **TUI**: `RaphGL/TermCL`, `odin-tui`, or ANSI escape codes
- **Filesystem**: `core:os` + `core:path`
- **Subprocesses**: `core:os` for running commands
- **Build System**: Odin built-in (`odin build`)

## Project Structure

```
ai-agent-odin/
├── src/
│   ├── main.odin
│   ├── agent/
│   ├── llm/
│   ├── tools/
│   ├── session/
│   ├── config/
│   ├── ui/
│   └── utils/
├── AGENTS.md              # Default system prompt & agent instructions
├── sessions/              # Saved conversation logs (JSONL)
├── README.md
└── taskfile.yml           # Optional build helpers
```

---

## Development Phases

### Phase 0: Project Setup (1–2 days)
- Create Odin project structure
- Set up basic CLI argument parsing
- Implement configuration loading (flags + config file)
- Add simple logging and error handling
- Create basic session save/load (JSONL format)

**Milestone**: Program runs with `--help` and can load config.

### Phase 1: LLM Integration (2–4 days)
- Define a clean LLM provider interface
- Implement OpenAI chat completions (with streaming support)
- Implement Anthropic support
- Add function/tool calling schema generation
- Test sending messages and receiving responses

**Milestone**: Can chat with an LLM and parse basic responses.

### Phase 2: Core Agent Loop (3–5 days)
- Maintain conversation history
- Build prompts with tool definitions
- Parse LLM responses for text and tool calls
- Implement the main ReAct-style reasoning loop
- Add basic stopping conditions

**Milestone**: Agent can complete simple multi-turn interactions with dummy tools.

### Phase 3: Tool System (5–8 days)
Implement core tools:
- `read_file`, `write_file`, `edit_file` (with diff or line-based editing)
- `run_command` / shell execution
- `list_directory`, `grep_search`, `find_files`
- Tool permission system (ask / allow / deny / yolo mode)

Make the tool system extensible so new tools are easy to add.

**Milestone**: Agent can explore a project, read code, and make real file changes.

### Phase 4: Persistence & Safety (2–4 days)
- Full session saving and resuming (JSONL)
- Structured trace logging
- Safe tool execution with user approval for risky actions
- Workspace isolation

**Milestone**: Sessions can be saved, inspected, and resumed.

### Phase 5: User Interface & Polish (4–7 days)
- Rich terminal output with colors and formatting
- Optional full TUI (chat view + tool execution log)
- Headless / non-interactive mode
- Helpful error messages and debugging output

**Milestone**: Pleasant and informative interactive experience.

### Phase 6: Advanced Features (Optional)
- Support for multiple LLM providers and routing
- Context management / summarization
- Sub-agent support
- Web search tool
- Persistent REPL (Python or Odin)
- API / server mode

### Phase 7: Documentation & Testing
- Comprehensive README with examples
- Build and run instructions
- Example agent configurations in `AGENTS.md`
- Basic test cases and usage examples

---

## Success Criteria

- Codebase remains small and readable
- Produces a fast single static binary
- Successfully completes real coding tasks
- Easy to understand and modify the core agent loop
- Good performance and low resource usage

## Important Notes

- Start simple — implement non-streaming first, then add streaming
- Always prioritize safety with tool permissions
- Keep the design modular so pieces can be swapped easily
- Odin’s simplicity should help keep the total code size reasonable

