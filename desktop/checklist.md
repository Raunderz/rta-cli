# RTA Desktop — Phase-Wise Checklist

## Phase 1: Fork & Branding

- [ ] Clone Adobe Brackets repository as `rta-desktop`
- [ ] Replace window title: "Brackets" → "RTA Desktop"
- [ ] Replace app name in `appshell/config.json` or equivalent
- [ ] Create RTA Desktop app icon (512x512 PNG, at least)
- [ ] Update `appshell/` icon references (macOS `.icns`, Windows `.ico`, Linux `.png`)
- [ ] Update splash screen with RTA branding (or disable/replace)
- [ ] Update about dialog text and image
- [ ] Update taskbar/dock label if separate from window title
- [ ] Run `npm install` and confirm no build errors
- [ ] Run `grunt dev` and confirm app launches with RTA branding
- [ ] Verify no functional changes to the editor itself
- [ ] Create `src/rta/` directory structure (empty, ready for Phase 2)

---

## Phase 2: RTA Dark Theme

- [ ] Create `src/rta/themes/rta-dark/` directory
- [ ] Create `src/rta/themes/rta-dark/package.json` (Brackets extension manifest)
- [ ] Create `src/rta/themes/rta-dark/theme.less`
- [ ] Define RTA Dark LESS variables:
  - [ ] Background color (editor, panels)
  - [ ] Foreground color (text)
  - [ ] Accent color (highlights, buttons)
  - [ ] Border colors
  - [ ] Selection color
  - [ ] Gutter background
- [ ] Override Brackets panel styles (file tree, editor tabs, status bar)
- [ ] Override CodeMirror theme variables
- [ ] Register theme in Brackets theme manager (`ThemeManager.loadUserTheme()` or config)
- [ ] Set RTA Dark as default theme in startup preferences
- [ ] Test in `grunt dev`:
  - [ ] Editor background correct
  - [ ] Text readable
  - [ ] Tabs styled correctly
  - [ ] Status bar visible
  - [ ] File tree contrast acceptable
- [ ] Confirm theme persists on restart

---

## Phase 3: AI Chat Panel

- [ ] Create `src/rta/ChatPanel.js` (main logic file)
- [ ] Create `src/rta/ChatPanel.html` (template/markup)
- [ ] Create `src/rta/ChatPanel.less` (styles)
- [ ] Register panel with Brackets' `PanelManager`:
  - [ ] Panel ID and title
  - [ ] Initial width/height
  - [ ] Resizable constraints
  - [ ] Toggle shortcut binding (Ctrl+Shift+A)
- [ ] Build chat message container (scrollable div)
- [ ] Create `src/rta/MessageRenderer.js`:
  - [ ] User message rendering (simple bubble style)
  - [ ] Assistant message rendering with Markdown support
  - [ ] Import and integrate `marked.js` for Markdown parsing
  - [ ] Code block syntax highlighting using CodeMirror colorizer
  - [ ] Escape HTML in code blocks to prevent injection
- [ ] Create `src/rta/ToolCards.js`:
  - [ ] Collapsible tool result card component
  - [ ] Show tool name, inputs (compact), output (scrollable)
  - [ ] Toggle expand/collapse on click
- [ ] Create `src/rta/ConversationManager.js`:
  - [ ] Store messages in memory (array of objects: {role, content, timestamp})
  - [ ] Add message (user or assistant)
  - [ ] Clear conversation on new workspace
  - [ ] Track current turn state (waiting for response, streaming, idle)
- [ ] Build input field:
  - [ ] Text input with placeholder "Type a message..."
  - [ ] Send button (click or Ctrl+Enter)
  - [ ] Shift+Enter inserts newline
  - [ ] Disable input while waiting for response
  - [ ] Clear input on send
- [ ] Add status line to panel:
  - [ ] Connection status indicator (● Connected / ✕ Disconnected)
  - [ ] Current model name/label
- [ ] Extend Brackets status bar:
  - [ ] Add model label display
  - [ ] Add connection status indicator
- [ ] Test in `grunt dev`:
  - [ ] Panel opens/closes with keyboard shortcut
  - [ ] Input field accepts text
  - [ ] Messages display without errors
  - [ ] Panel is resizable
  - [ ] Status indicators visible

---

## Phase 4: Node.js / RTA API Bridge

- [ ] Create `src/rta/node/` directory
- [ ] Create `src/rta/node/APIBridge.js`:
  - [ ] Load RTA API endpoint URL from config/env var
  - [ ] Export function to send message to RTA API
  - [ ] Implement HTTP/WebSocket connection to RTA API (use same protocol as CLI)
  - [ ] Handle streaming responses:
    - [ ] Receive chunks from API
    - [ ] Emit events to renderer via `NodeConnection.domains.rta.broadcast()`
    - [ ] Include chunk content and metadata (is_final, timestamp)
  - [ ] Store conversation history in memory (send with each API call if required)
  - [ ] Clear history on workspace change
  - [ ] Handle connection errors (retry, fallback, error message to UI)
  - [ ] Handle API authentication (API key/token from config)
- [ ] Load and register Node domain in Brackets:
  - [ ] Add `src/rta/node/APIBridge.js` to Node domain startup
  - [ ] Verify `NodeConnection` is available in renderer (`require('modules/rta/ChatPanel')`)
- [ ] Create IPC bridge in `src/rta/ChatPanel.js`:
  - [ ] Connect to Node domain: `NodeConnection.domains.rta`
  - [ ] On send button: call `nodeConnection.exec('sendMessage', userText)`
  - [ ] Listen for `NodeConnection.domains.rta.on('streaming')` events
  - [ ] Append streamed text to assistant message in real time
  - [ ] Listen for `'turn_complete'` event, enable input
  - [ ] Handle `'error'` events, display error message
- [ ] Test in `grunt dev`:
  - [ ] Type message in chat panel
  - [ ] Click send
  - [ ] Verify API call is made (check Node console / logs)
  - [ ] Receive response and display in chat
  - [ ] Confirm streaming chunks arrive and render progressively
  - [ ] Status indicator shows connected

---

## Phase 5: Tool Integration

- [ ] Create `src/rta/node/ToolExecutor.js`:
  - [ ] Port all 10 tools from Python agent
  - [ ] **get_file_contents**: Use `fs.readFile()`, handle encoding errors
  - [ ] **write_file**: Use `fs.writeFile()`, create directories if needed
  - [ ] **edit_file**: Implement search/replace logic (read → modify → write)
  - [ ] **delete_file**: Use `fs.unlink()` for files, `fs.rmdir()` for empty dirs, or `rimraf` for recursive
  - [ ] **create_dir**: Use `fs.mkdir()` with `recursive: true`
  - [ ] **list_directory**: Use `fs.readdir()` with `withFileTypes: true`, include metadata
  - [ ] **run_command**: Use `child_process.exec()`, capture stdout/stderr, set timeout
  - [ ] **run_python_file**: Use `child_process.spawn('python', [filepath])`, capture output
  - [ ] **grep_search**: Recursive directory walk + regex matching, return file paths and line numbers
  - [ ] **glob_search**: Use `glob` npm package, return matching file paths
- [ ] Integrate tool executor into `APIBridge.js`:
  - [ ] When API returns tool call: extract tool name and inputs
  - [ ] Call corresponding tool function from `ToolExecutor.js`
  - [ ] Capture output (or error)
  - [ ] Send tool result back to API in same conversation turn
  - [ ] Continue turn until API returns stop/end
- [ ] Add tool result rendering to chat panel:
  - [ ] After tool call, append `ToolCard` component
  - [ ] Show tool name, inputs (compact JSON or formatted)
  - [ ] Show output (scrollable, syntax-highlighted if code)
  - [ ] Show execution time/status
- [ ] Test each tool independently:
  - [ ] Create test files in workspace
  - [ ] Trigger each tool via chat (e.g., "read src/App.tsx")
  - [ ] Verify output is correct
  - [ ] Verify file system changes are reflected in editor
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
  - [ ] Ctrl+Shift+A to toggle AI panel
  - [ ] Ctrl+Shift+N to start new conversation
  - [ ] Register shortcuts in Brackets' `CommandManager`
- [ ] Error handling:
  - [ ] API connection lost: display error in chat, allow retry
  - [ ] Tool execution error: catch and send error message to API
  - [ ] File not found: handle gracefully
  - [ ] Permission denied: display user-friendly error
- [ ] Performance checks:
  - [ ] Stream large response (5000+ characters): confirm editor remains responsive
  - [ ] Open chat while editing: confirm no lag
  - [ ] Run command that produces 1MB+ output: confirm chat panel doesn't hang
- [ ] UI Polish:
  - [ ] Chat message timestamps (optional but nice)
  - [ ] Loading spinner during API call
  - [ ] Smooth scroll to bottom on new message
  - [ ] Input field focus after send
  - [ ] Prevent accidental double-send
- [ ] Documentation:
  - [ ] Comment all RTA-specific code files
  - [ ] Add inline docs for API bridge protocol
  - [ ] Document tool schema and expected inputs/outputs
- [ ] Final testing:
  - [ ] `grunt dev` starts without errors
  - [ ] `grunt release` builds without errors
  - [ ] App launches, chat panel works, file editing works
  - [ ] All 10 tools execute and produce correct output
  - [ ] No console errors or warnings

---

## Pre-Release Checklist

- [ ] Confirm all 6 phases complete
- [ ] No console errors in dev or release builds
- [ ] Test on at least one target platform (Linux/macOS/Windows)
- [ ] Create basic user documentation (how to open chat, how to send messages, example workflows)
- [ ] Test keyboard shortcuts
- [ ] Test theme persists across restarts
- [ ] Backup original Brackets fork before first release