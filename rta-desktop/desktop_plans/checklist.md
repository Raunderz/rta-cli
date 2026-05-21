# RTA Desktop — Phase-Wise Checklist (Theia Version)

## Phase 1: Project Setup & Branding

- [ ] Scaffold new Theia extension project using `generator-theia-extension`
- [ ] Name the project and extension `rta-desktop` and update root `package.json`
- [ ] Configure `package.json` with window title: "RTA Desktop"
- [ ] Create RTA Desktop app icon (512x512 PNG, at least)
- [ ] Update Electron window configuration in `electron-app/` for icon on macOS (`.icns`), Windows (`.ico`), Linux (`.png`)
- [ ] Update or replace the default splash screen with RTA branding
- [ ] Update about dialog text, copyright, and image in `electron-app/`
- [ ] Run `yarn` and confirm no install errors
- [ ] Run `yarn browser start` and confirm the base Theia editor launches with RTA branding
- [ ] Verify no functional changes to the editor itself
- [ ] Create `rta-extension/src/` directory structure (ready for Phase 2)

---

## Phase 2: RTA Dark Theme

- [ ] Create `rta-extension/themes/rta-dark/` directory
- [ ] Create `rta-extension/themes/rta-dark/rta-dark-theme.css`
- [ ] Define RTA Dark CSS custom properties (or Theia variables):
  - [ ] Background color (editor, panels)
  - [ ] Foreground color (text)
  - [ ] Accent color (highlights, buttons)
  - [ ] Border colors
  - [ ] Selection color
  - [ ] Gutter background
- [ ] Override Monaco Editor colors using Theia's theme contribution point
- [ ] Override Theia panel styles (file tree, editor tabs, status bar) in `rta-dark-theme.css`
- [ ] Register theme in `rta-extension/src/browser/rta-frontend-module.ts` using `ThemeService`
- [ ] Set RTA Dark as the default theme in application configuration
- [ ] Test in `yarn browser start`:
  - [ ] Editor background correct
  - [ ] Text readable
  - [ ] Tabs styled correctly
  - [ ] Status bar visible
  - [ ] File tree contrast acceptable
- [ ] Confirm theme persists on restart

---

## Phase 3: AI Chat Panel

- [ ] Create `rta-extension/src/browser/chat-panel-widget.ts` (main widget logic)
- [ ] Create `rta-extension/src/browser/chat-panel-widget.css` (widget styles)
- [ ] Register widget with Theia's `WidgetManager`:
  - [ ] Widget ID (`rta-chat-panel`)
  - [ ] Initial position (right sidebar)
  - [ ] Resizable constraints
  - [ ] Toggle command and keybinding (Ctrl+Shift+A)
- [ ] Build chat message container (scrollable `div`)
- [ ] Create `rta-extension/src/browser/message-renderer.tsx`:
  - [ ] User message rendering (simple bubble style)
  - [ ] Assistant message rendering with Markdown support
  - [ ] Import `react-markdown` for Markdown parsing
  - [ ] Code block syntax highlighting using Monaco (`MonacoEditorService`)
  - [ ] Escape HTML in code blocks to prevent injection
- [ ] Create `rta-extension/src/browser/tool-card.tsx`:
  - [ ] Collapsible tool result card component
  - [ ] Show tool name, inputs (compact), output (scrollable)
  - [ ] Toggle expand/collapse on click
- [ ] Create `rta-extension/src/common/chat-protocol.ts`:
  - [ ] Define message data types (user, assistant, tool)
  - [ ] Store messages in memory (array of `ChatMessage` objects)
  - [ ] Track current turn state (`waiting`, `streaming`, `idle`)
  - [ ] Interface for clearing conversation on new workspace
- [ ] Build input field in widget:
  - [ ] Text input with placeholder "Type a message..."
  - [ ] Send button (click or Ctrl+Enter)
  - [ ] Shift+Enter inserts newline
  - [ ] Disable input while waiting for response
  - [ ] Clear input on send
- [ ] Add status line to panel:
  - [ ] Connection status indicator (● Connected / ✕ Disconnected)
  - [ ] Current model name/label
- [ ] Extend Theia status bar using `StatusBar` contribution:
  - [ ] Add model label display
  - [ ] Add connection status indicator
- [ ] Test in `yarn browser start`:
  - [ ] Panel opens/closes with keyboard shortcut
  - [ ] Input field accepts text
  - [ ] Messages display without errors
  - [ ] Panel is resizable
  - [ ] Status indicators visible

---

## Phase 4: RTA API Backend Bridge

- [ ] Create `rta-extension/src/node/rta-api-service.ts`:
  - [ ] Load RTA API endpoint URL from config/env var (use Theia's `EnvVariablesServer`)
  - [ ] Export function to send message to RTA API
  - [ ] Implement HTTP/WebSocket connection to RTA API (use same protocol as CLI)
  - [ ] Handle streaming responses:
    - [ ] Receive chunks from API
    - [ ] Emit events to frontend via `RpcProxy` or custom `JsonRpcServer`
    - [ ] Include chunk content and metadata (`is_final`, `timestamp`)
  - [ ] Store conversation history in memory (send with each API call if required)
  - [ ] Clear history on workspace change (listen to `WorkspaceService`)
  - [ ] Handle connection errors (retry, fallback, error message to UI)
  - [ ] Handle API authentication (API key/token from config)
- [ ] Load and register backend service in Theia:
  - [ ] Add `RtaApiService` to `rta-extension/src/node/rta-backend-module.ts`
  - [ ] Bind it as a `JsonRpcServer` and expose it to the frontend
- [ ] Consume backend service in the chat widget:
  - [ ] Inject `RtaApiService` via `@inject()` in `ChatPanelWidget`
  - [ ] On send button: call `sendMessage(userText)`
  - [ ] Subscribe to `onStreamingChunk` event
  - [ ] Append streamed text to assistant message in real time
  - [ ] Listen for `onTurnComplete` event, re-enable input
  - [ ] Handle `onError` events, display error message in chat
- [ ] Test in `yarn browser start`:
  - [ ] Type message in chat panel
  - [ ] Click send
  - [ ] Verify API call is made (check backend console/logs)
  - [ ] Receive response and display in chat
  - [ ] Confirm streaming chunks arrive and render progressively
  - [ ] Status indicator shows connected

---

## Phase 5: Tool Integration

- [ ] Create `rta-extension/src/node/tool-executor.ts`:
  - [ ] Port all 10 tools from Python agent
  - [ ] **get_file_contents**: Use `fs.readFile()`, handle encoding errors
  - [ ] **write_file**: Use `fs.writeFile()`, create directories if needed (Theia's `FileService`)
  - [ ] **edit_file**: Implement search/replace logic (read → modify → write)
  - [ ] **delete_file**: Use `fs.unlink()` for files, `fs.rmdir()` for empty dirs, or `rimraf` for recursive
  - [ ] **create_dir**: Use `fs.mkdir()` with `recursive: true`
  - [ ] **list_directory**: Use `fs.readdir()` with `withFileTypes: true`, include metadata
  - [ ] **run_command**: Use `child_process.exec()`, capture stdout/stderr, set timeout
  - [ ] **run_python_file**: Use `child_process.spawn('python', [filepath])`, capture output
  - [ ] **grep_search**: Recursive directory walk + regex matching, return file paths and line numbers
  - [ ] **glob_search**: Use `glob` npm package, return matching file paths
- [ ] Integrate tool executor into `RtaApiService`:
  - [ ] When API response contains a tool call: extract tool name and inputs
  - [ ] Call corresponding tool function from `ToolExecutor`
  - [ ] Capture output (or error)
  - [ ] Send tool result back to API in the same conversation turn
  - [ ] Continue agentic loop until API returns stop/end
- [ ] Add tool result rendering to chat widget:
  - [ ] After tool call, append `ToolCard` component
  - [ ] Show tool name, inputs (compact JSON or formatted)
  - [ ] Show output (scrollable, syntax-highlighted if code)
  - [ ] Show execution time/status
- [ ] Test each tool independently:
  - [ ] Create test files in workspace
  - [ ] Trigger each tool via chat (e.g., "read src/App.tsx")
  - [ ] Verify output is correct
  - [ ] Verify file system changes are reflected in the editor and file tree
- [ ] Test tool chaining:
  - [ ] Send a message that requires multiple tool calls
  - [ ] Verify each tool executes in sequence
  - [ ] Verify conversation continues until completion

---

## Phase 6: Testing & Polish

- [ ] End-to-end workflow test:
  - [ ] Open a workspace folder
  - [ ] Send message to AI: "Create a hello world app in TypeScript"
  - [ ] Verify AI creates file
  - [ ] Verify file appears in editor and file tree
  - [ ] Send another message: "Add a console.log"
  - [ ] Verify file is edited in place
  - [ ] Verify editor tabs refresh
- [ ] Add keyboard shortcuts:
  - [ ] Ctrl+Shift+A to toggle AI panel (bound to command)
  - [ ] Ctrl+Shift+N to start new conversation (bound to command)
  - [ ] Register keybindings in `rta-extension/src/browser/rta-keybindings.ts`
- [ ] Error handling:
  - [ ] API connection lost: display error in chat, allow retry
  - [ ] Tool execution error: catch and send error message to API
  - [ ] File not found: handle gracefully in tool executor
  - [ ] Permission denied: display user-friendly error in chat
- [ ] Performance checks:
  - [ ] Stream large response (5000+ characters): confirm editor remains responsive
  - [ ] Open chat while editing: confirm no lag in typing or scrolling
  - [ ] Run command that produces 1MB+ output: confirm chat widget doesn't hang
- [ ] UI Polish:
  - [ ] Chat message timestamps (optional)
  - [ ] Loading spinner during API call
  - [ ] Smooth scroll to bottom on new message
  - [ ] Input field focus after send
  - [ ] Prevent accidental double-send by disabling input appropriately
- [ ] Documentation:
  - [ ] Comment all RTA-specific code files with JSDoc/TSDoc
  - [ ] Add inline docs for the API bridge protocol
  - [ ] Document tool schema and expected inputs/outputs
- [ ] Final testing:
  - [ ] `yarn browser start` starts without errors
  - [ ] `yarn electron package` builds without errors
  - [ ] App launches, chat panel works, file editing works
  - [ ] All 10 tools execute and produce correct output
  - [ ] No console errors or warnings

---

## Pre-Release Checklist

- [ ] Confirm all 6 phases complete
- [ ] No console errors in dev or production builds
- [ ] Test on at least one target platform (Linux/macOS/Windows)
- [ ] Create basic user documentation (how to open chat, how to send messages, example workflows)
- [ ] Test keyboard shortcuts
- [ ] Test theme persists across restarts
- [ ] Create initial Git tag/commit for first release
