# RTA Agent Porting Plan (Python to TypeScript)

This document outlines the detailed roadmap for porting the RTA Python CLI logic into the TypeScript-based Desktop backend (Theia).

## 1. Architectural Strategy

The goal is to replicate the agentic loop and tool capabilities found in the `cli/` directory while adapting to the Node.js/Theia environment. The implementation will be split into a core Agent Service, a Tool Execution layer, and a Persistence/Auth layer.

## 2. Phase 1: Core Definitions & Protocols

Establish the shared types between the frontend and backend to ensure type safety across the JSON-RPC bridge.

- **Agent Protocol**: Define interfaces for `Message` (role, content), `ToolCall`, `ToolResult`, and `UsageStats`. This should mirror the OpenAI/Rta-Backend message format used in `agent.py`.
- **Stream Events**: Define an interface for the streaming response types: `text`, `tool_start`, `thought`, `usage`, and `error`.

## 3. Phase 2: Configuration & Auth Layer

Port the logic from `rta_cli/utils.py` and `rta_cli/auth.py`.

- **Storage**: Implement a cross-platform credential manager that stores the API key in `~/.rta/credentials` (or platform equivalent) to maintain compatibility with the CLI.
- **Fingerprinting**: Re-implement the stable device ID generation (UUID) logic.
- **Environment**: Create a configuration manager to handle `SERVER_URL` and other constants, allowing for overrides via local config files.

## 4. Phase 3: Tool Execution Layer (Surgical Port)

Port the 11 core tools from `rta_cli/functions/` to a structured TypeScript hierarchy.

- **Base Tool Class**: Create an abstract base class or interface that defines the tool schema (matching the Python dictionaries) and the execution signature.
- **File System Tools**: Port `get_file_contents`, `write_file`, `edit_file`, `delete_file`, `create_dir`, `list_directory`, and `get_files_info` using Node's `fs-extra` or native `fs` module. Ensure absolute path validation to prevent workspace escapes.
- **Search Tools**: Port `grep_search` and `glob_search`. For `grep`, use `child_process.exec` or a library like `ripgrep-js`. For `glob`, use the `fast-glob` package.
- **Execution Tools**: Port `run_command` and `run_python_file` using `child_process.spawn`. Handle timeouts and output streaming (STDOUT/STDERR) correctly.

## 5. Phase 4: The Agent Loop

Port the recursive logic from `rta_cli/agent.py`.

- **State Management**: Manage the conversation history, including message pruning/truncation logic found in `chat.py`.
- **The Loop**: Implement the async `for` loop that calls the Rta backend, handles tool calls, executes them via the Tool Executor, and feeds the results back.
- **Streaming**: Ensure the loop emits events in real-time to the frontend.
- **Error Handling**: Implement the retry logic and specific status code handling (401, 429, 502).

## 6. Phase 5: Theia Integration

Hook the new agent into the Theia application lifecycle.

- **Backend Module**: Register the `AgentService` in the `rta-desktop-backend-module.ts`.
- **JSON-RPC**: Expose the agent's `chat` and `auth` methods over the JSON-RPC connection.
- **Frontend Connection**: Update the `RtaChatWidget` to call the new TypeScript service instead of communicating with a separate process.

## 7. Projected Directory Structure

After implementation, the `src/node/agent/` directory should look like this:

```text
rta-desktop/src/node/agent/
├── agent-protocol.ts        # Shared interfaces and types
├── agent-service.ts         # Main agentic loop and state management
├── auth-manager.ts          # API key and device ID handling
├── config-manager.ts        # Server URL and system settings
├── tool-executor.ts         # Dispatcher for all tools
├── migration_plan.md        # This document
└── tools/                   # Individual tool implementations
    ├── base-tool.ts         # Abstract base/interface
    ├── filesystem/          # FS-related tools
    │   ├── read-file.ts
    │   ├── write-file.ts
    │   ├── edit-file.ts
    │   ├── delete-file.ts
    │   ├── create-dir.ts
    │   ├── list-directory.ts
    │   └── get-files-info.ts
    ├── search/              # Search-related tools
    │   ├── grep-search.ts
    │   └── glob-search.ts
    └── execution/           # Shell/Python execution
        ├── run-command.ts
        └── run-python-file.ts
```

## 8. Success Criteria

- The Desktop Agent uses the same `~/.rta/credentials` as the CLI.
- All 11 tools behave identically to their Python counterparts.
- The agent loop handles multi-turn tool interactions autonomously.
- Streaming UI updates are smooth and handle terminal output correctly.

