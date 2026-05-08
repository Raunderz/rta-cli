# RTA Agent Implementation Plan (Odin)

This document outlines the roadmap for implementing the RTA Agent in the Odin programming language. The agent will run as a high-performance binary sidecar managed by the TypeScript-based Desktop backend (Theia).

## 1. Architectural Strategy

The agent will be a standalone, statically linked Odin binary. It communicates with the TypeScript backend via JSON-RPC over Standard Input/Output (Stdin/Stdout).

- **Odin Agent**: Handles the agentic loop, tool execution (FS, Search, Shell), and state management.
- **TypeScript Bridge**: A thin wrapper in `rta-desktop` that spawns the Odin process and marshals JSON-RPC calls.

## 2. Phase 1: Core Definitions & Odin Setup

Establish the foundation using Odin's `core` and `vendor` libraries.

- **Project Layout**:
  - `src/main.odin`: Entry point and JSON-RPC loop.
  - `src/agent/`: Core loop logic.
  - `src/tools/`: Tool implementations.
  - `src/protocol/`: JSON mappings for Messages, ToolCalls, and Usage.
- **JSON Handling**: Use `core:encoding/json` for fast parsing of LLM responses and tool results.

## 3. Phase 2: Configuration & Auth (Odin)

Port logic from `rta_cli/utils.py`.

- **Persistence**: Use `core:os` to read/write API keys in `~/.rta/credentials`.
- **Platform Abstraction**: Use Odin's `when ODIN_OS == .Windows` etc. for cross-platform path handling.
- **Networking**: Use a library like `odin-http` or raw sockets for communicating with the Rta backend (`/v1/chat`).

## 4. Phase 3: High-Performance Tool Layer

Implement the 11 core tools using Odin's low-level primitives.

- **File System**: Use `core:os` and `core:path/filepath`. Direct syscalls where performance is critical.
- **Project Discovery**: Port `discovery.py` logic to Odin. Scan for `package.json`, `pyproject.toml`, etc., to auto-detect test/build commands.
- **Search**:
  - `grep_search`: Implement using a fast multi-threaded buffer scan or wrap `ripgrep` as a dependency.
  - `glob_search`: Use `core:path/filepath` matching.
- **Execution**: Use `core:os/process` to spawn sub-processes for `run_command`.

## 5. Phase 4: The Agent Loop (The "Brain")

- **Memory Management**: Use Odin's explicit allocators (e.g., `Arena` or `Pool`) for per-turn message processing to prevent leaks and fragmentation.
- **Recursive Loop**: Implementation of the `for` loop that calls the backend, parses tool requests, executes tools, and recurses. This must handle multi-turn tool interactions (Agent -> Tool -> Backend -> Agent) as seen in `agent.py`.
- **Telemetry**: Log performance metrics (latency, memory usage) to the backend.

## 6. Phase 5: Desktop Integration (TS Bridge)

- **Process Manager**: TS class to manage the lifecycle of the `rta-agent` binary.
- **JSON-RPC Link**: Use `child_process.spawn` with `ndjson` (newline-delimited JSON) for low-latency communication.
- **Frontend Hook**: Map `RtaChatWidget` calls through the TS Bridge to the Odin process.

## 7. Projected Directory Structure (Odin Project)

```text
agent-odin/
├── build.bat / build.sh      # Build scripts
├── src/
│   ├── main.odin             # CLI Entry + RPC Loop
│   ├── agent/
│   │   ├── loop.odin         # Core recursion
│   │   └── state.odin        # Conversation history
│   ├── tools/
│   │   ├── filesystem.odin   # Read/Write/Edit/Delete/List
│   │   ├── search.odin       # Grep/Glob
│   │   └── execution.odin    # Process spawning
│   ├── protocol/
│   │   └── types.odin        # JSON mappings
│   └── shared/
│       ├── auth.odin         # Credential management
│       └── config.odin       # URL/Settings
└── tests/                    # Tool validation tests
```

## 8. Success Criteria

- Odin binary starts in <10ms.
- Memory footprint remains stable under heavy multi-turn tool usage.
- Parity with Python CLI for all 11 tool behaviors.
- Seamless integration with `~/.rta/credentials`.

