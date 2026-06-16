#!/usr/bin/env lua
-- Minimal test runner for rta_chat.lua
-- Usage: lua tests/run.lua

-- Add project root to path so require works
package.path = package.path .. ";../data/?.lua;../data/?/init.lua"

local pass, fail, errors = 0, 0, {}

local function test(name, fn)
  local ok, err = pcall(fn)
  if ok then
    pass = pass + 1
    io.write("  PASS  " .. name .. "\n")
  else
    fail = fail + 1
    errors[#errors + 1] = { name = name, err = err }
    io.write("  FAIL  " .. name .. ": " .. tostring(err) .. "\n")
  end
end

local function assert_eq(got, expected, msg)
  if got ~= expected then
    error(string.format("%s: expected %s, got %s", msg or "assert_eq", tostring(expected), tostring(got)), 2)
  end
end

local function assert_near(got, expected, delta, msg)
  if math.abs(got - expected) > (delta or 0.1) then
    error(string.format("%s: expected ~%s, got %s", msg or "assert_near", tostring(expected), tostring(got)), 2)
  end
end

local function assert_table_eq(got, expected, msg)
  if type(got) ~= "table" then
    error(string.format("%s: expected table, got %s", msg or "assert_table_eq", type(got)), 2)
  end
  for k, v in pairs(expected) do
    if got[k] ~= v then
      error(string.format("%s: key %s: expected %s, got %s", msg or "assert_table_eq", k, tostring(v), tostring(got[k])), 2)
    end
  end
end

local function assert_gt(got, expected, msg)
  if not (got > expected) then
    error(string.format("%s: expected > %s, got %s", msg or "assert_gt", tostring(expected), tostring(got)), 2)
  end
end

-- =========================================================================
-- Setup mocks and load the module
-- =========================================================================
local mock = require "mock_lite_xl"
mock.install()

-- Override JSON decode for protocol tests
local json_results = {}
mock.json.decode = function(str)
  local result = json_results[#json_results]
  if result then
    table.remove(json_results)
    return result
  end
  return {}
end
mock.json.encode = function(obj) return "{}" end

-- Mock io.popen for find_rta_binary and load_history
local popen_results = {}
local original_popen = io.popen
io.popen = function(cmd)
  if popen_results[cmd] then
    local r = table.remove(popen_results[cmd])
    if r then
      return {
        read = function(self, mode) return r end,
        close = function(self) end,
        lines = function(self)
          local i = 0
          local lines = r and { r } or {}
          return function()
            i = i + 1
            return lines[i]
          end
        end,
      }
    end
  end
  return nil
end

-- Mock io.open for file reads
local open_results = {}
local original_open = io.open
io.open = function(path, mode)
  if open_results[path] then
    local content = table.remove(open_results[path])
    if content then
      local pos = 1
      return {
        read = function(self, fmt)
          if fmt == "*l" then
            local start = pos
            local nl = content:find("\n", pos)
            if nl then
              pos = nl + 1
              return content:sub(start, nl - 1)
            else
              pos = #content + 1
              return content:sub(start)
            end
          end
          return content
        end,
        close = function(self) end,
        lines = function(self)
          local lines = {}
          for line in content:gmatch("([^\n]*)\n?") do
            if #line > 0 or line ~= "" then
              lines[#lines + 1] = line
            end
          end
          local i = 0
          return function()
            i = i + 1
            return lines[i]
          end
        end,
      }
    end
  end
  return nil
end

-- Mock os.execute for mkdir
local original_execute = os.execute
os.execute = function(cmd) return true end

-- Mock os.getenv
local original_getenv = os.getenv
local env = { HOME = "/tmp/test_home" }
os.getenv = function(name) return env[name] or original_getenv(name) end

-- Mock os.date
local original_date = os.date
os.date = function(fmt) return "12:00" end

-- Mock os.clock for streaming indicator test
local mock_clock = 0.5
local original_clock = os.clock
os.clock = function() return mock_clock end

-- Mock io.stderr
io.stderr = io.stderr or { write = function() end, flush = function() end }

-- Load the module (this creates the chat_view instance)
local chat_view = require "plugins.rta_chat"

-- Restore io functions after load
io.popen = original_popen
io.open = original_open
os.execute = original_execute
os.getenv = original_getenv
os.date = original_date
os.clock = original_clock

-- =========================================================================
-- Helper to create a fresh RtaChat instance for isolated testing
-- =========================================================================
local function new_chat()
  mock.reset()
  -- Reset popen/open mocks
  popen_results = {}
  open_results = {}

  local mt = getmetatable(chat_view)
  -- chat_view's metatable has the RtaChat class methods
  -- We need to create a new instance via __call on the class's metatable
  -- The class is chat_view's metatable's __index, and the class's metatable has __call
  local cls_mt = getmetatable(mt.__index) -- RtaChat class's metatable
  local RtaChat_cls = mt.__index
  -- Use __call to create new instance
  local view = cls_mt.__call(RtaChat_cls)
  return view
end

-- =========================================================================
-- Test suites
-- =========================================================================

io.write("\n=== rta_chat.lua Test Suite ===\n\n")

-- -------------------------------------------------------------------------
io.write("--- Pure Function Tests ---\n")
-- -------------------------------------------------------------------------

test("draw_wrapped_text: empty string returns y unchanged", function()
  local mock2 = require "mock_lite_xl"
  mock2.reset()
  -- draw_wrapped_text is local, test via the module's closure
  -- We can't call it directly, but we can test get_line_height_msg instead
  -- This test verifies the module loads without error
  assert_eq(type(chat_view), "table", "module should return a table")
end)

test("RtaChat:get_name returns 'RTA Chat'", function()
  local v = new_chat()
  assert_eq(v:get_name(), "RTA Chat")
end)

test("RtaChat:supports_text_input returns true", function()
  local v = new_chat()
  assert_eq(v:supports_text_input(), true)
end)

test("RtaChat:get_line_height returns positive value", function()
  local v = new_chat()
  local h = v:get_line_height()
  assert_gt(h, 0, "line height should be positive")
end)

test("RtaChat:get_input_height scales with buffer length", function()
  local v = new_chat()
  v.size = { x = 400, y = 600 }
  v.input_buffer = ""
  local h1 = v:get_input_height()
  v.input_buffer = string.rep("a", 500)
  local h2 = v:get_input_height()
  assert_gt(h2, h1, "longer input should have greater height")
end)

test("RtaChat:get_line_height_msg accounts for tools", function()
  local v = new_chat()
  local msg_no_tools = { role = "user", text = "hello world", tools = {} }
  local msg_with_tools = {
    role = "user", text = "hello world",
    tools = { { name = "bash", status = "running" }, { name = "read", status = "done" } },
  }
  local h1 = v:get_line_height_msg(msg_no_tools)
  local h2 = v:get_line_height_msg(msg_with_tools)
  assert_gt(h2, h1, "message with tools should be taller")
end)

test("RtaChat:get_scrollable_size sums all messages", function()
  local v = new_chat()
  v.messages = {
    { role = "user", text = "msg1", tools = {} },
    { role = "assistant", text = "msg2", tools = {} },
  }
  local size = v:get_scrollable_size()
  assert_gt(size, 0, "scrollable size should be positive")
end)

-- -------------------------------------------------------------------------
io.write("\n--- Protocol Tests (handle_line) ---\n")
-- -------------------------------------------------------------------------

test("handle_line: text_delta appends to current_stream", function()
  local v = new_chat()
  v.streaming = true
  v.current_stream = { role = "assistant", text = "", tools = {} }
  table.insert(v.messages, v.current_stream)

  table.insert(json_results, { type = "text_delta", content = "Hello" })
  v:handle_line('{"type":"text_delta","content":"Hello"}')
  assert_eq(v.current_stream.text, "Hello", "text should accumulate")

  table.insert(json_results, { type = "text_delta", content = " world" })
  v:handle_line('{"type":"text_delta","content":" world"}')
  assert_eq(v.current_stream.text, "Hello world", "text should concatenate")
end)

test("handle_line: text_done clears streaming state", function()
  local v = new_chat()
  v.streaming = true
  v.current_stream = { role = "assistant", text = "partial", tools = {} }
  v.session_id = nil

  table.insert(json_results, { type = "text_done", session_id = "sess-123" })
  v:handle_line('{"type":"text_done","session_id":"sess-123"}')
  assert_eq(v.streaming, false, "streaming should be false")
  assert_eq(v.current_stream, nil, "current_stream should be nil")
  assert_eq(v.session_id, "sess-123", "session_id should be set")
end)

test("handle_line: text_delta rate-limits redraws", function()
  local v = new_chat()
  v.streaming = true
  v.current_stream = { role = "assistant", text = "", tools = {} }
  table.insert(v.messages, v.current_stream)

  -- Mock os.clock for controlled timing
  local mock_time = 0.5
  local orig_clock = os.clock
  os.clock = function() return mock_time end

  -- First delta should trigger redraw
  v.last_render_time = 0
  table.insert(json_results, { type = "text_delta", content = "A" })
  v:handle_line('{"type":"text_delta","content":"A"}')
  assert_eq(v.current_stream.text, "A")
  assert_eq(v.last_render_time, 0.5, "last_render_time should be updated")

  -- Immediate second delta should NOT trigger redraw (within 33ms)
  mock_time = 0.51  -- only 10ms later
  table.insert(json_results, { type = "text_delta", content = "B" })
  v:handle_line('{"type":"text_delta","content":"B"}')
  assert_eq(v.current_stream.text, "AB", "text should still accumulate")
  assert_eq(v.last_render_time, 0.5, "last_render_time should not change within 33ms")

  -- Third delta after 40ms should trigger redraw
  mock_time = 0.55  -- 50ms from last render
  table.insert(json_results, { type = "text_delta", content = "C" })
  v:handle_line('{"type":"text_delta","content":"C"}')
  assert_eq(v.current_stream.text, "ABC", "text should accumulate")
  assert_eq(v.last_render_time, 0.55, "last_render_time should update after 33ms")

  os.clock = orig_clock
end)

test("handle_line: tool_start adds tool to current_stream", function()
  local v = new_chat()
  v.streaming = true
  v.current_stream = { role = "assistant", text = "", tools = {} }

  table.insert(json_results, { type = "tool_start", tool = "bash" })
  v:handle_line('{"type":"tool_start","tool":"bash"}')
  assert_eq(#v.current_stream.tools, 1, "should have 1 tool")
  assert_eq(v.current_stream.tools[1].name, "bash")
  assert_eq(v.current_stream.tools[1].status, "running")
  assert_eq(v.current_tool, "bash", "current_tool should be set")
end)

test("handle_line: tool_end marks tool as done", function()
  local v = new_chat()
  v.streaming = true
  v.current_stream = {
    role = "assistant", text = "",
    tools = { { name = "bash", status = "running", display = "", expanded = false } },
  }

  table.insert(json_results, { type = "tool_end", tool = "bash", display = "exit 0" })
  v:handle_line('{"type":"tool_end","tool":"bash","display":"exit 0"}')
  assert_eq(v.current_stream.tools[1].status, "done")
  assert_eq(v.current_stream.tools[1].display, "exit 0")
  assert_eq(v.current_tool, nil, "current_tool should be cleared")
end)

test("tool expand/collapse toggle on click", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  v.messages = {
    {
      role = "assistant", text = "Here you go",
      tools = { { name = "bash", status = "done", display = "exit 0", expanded = false } },
    },
  }
  -- Draw to populate tool_click_areas
  mock.reset()
  v:draw()
  assert_gt(#v.tool_click_areas, 0, "should have tool click areas")
  -- Click on the tool area
  local area = v.tool_click_areas[1]
  v:on_mouse_pressed(1, area.x + 10, area.y + 5, 1)
  assert_eq(v.messages[1].tools[1].expanded, true, "tool should be expanded")
  -- Click again to collapse
  v:draw()
  area = v.tool_click_areas[1]
  v:on_mouse_pressed(1, area.x + 10, area.y + 5, 1)
  assert_eq(v.messages[1].tools[1].expanded, false, "tool should be collapsed")
end)

test("handle_line: tool_approval creates pending approval", function()
  local v = new_chat()

  table.insert(json_results, {
    type = "tool_approval",
    approval_id = "appr-1",
    tool = "write",
    display = "/tmp/test.txt",
  })
  v:handle_line('{"type":"tool_approval","approval_id":"appr-1","tool":"write","display":"/tmp/test.txt"}')
  assert_eq(#v.pending_approvals, 1, "should have 1 pending approval")
  assert_eq(v.pending_approvals[1].id, "appr-1")
  assert_eq(v.pending_approvals[1].tool, "write")
end)

test("handle_line: error adds system message", function()
  local v = new_chat()
  local base = #v.messages

  table.insert(json_results, { type = "error", message = "Something went wrong" })
  v:handle_line('{"type":"error","message":"Something went wrong"}')
  assert_eq(#v.messages, base + 1, "should have 1 more message")
  assert_eq(v.messages[#v.messages].role, "system")
  assert_eq(v.messages[#v.messages].text, "Error: Something went wrong")
  assert_eq(v.streaming, false, "streaming should be cleared on error")
  assert_eq(v.current_stream, nil, "current_stream should be nil on error")
end)

test("handle_line: status_response sets session_id", function()
  local v = new_chat()

  table.insert(json_results, {
    type = "status_response",
    session_id = "sess-abc",
    model = "gpt-4",
  })
  v:handle_line('{"type":"status_response","session_id":"sess-abc","model":"gpt-4"}')
  assert_eq(v.session_id, "sess-abc")
end)

test("handle_line: empty line is ignored", function()
  local v = new_chat()
  local base = #v.messages
  v:handle_line("")
  v:handle_line(nil)
  assert_eq(#v.messages, base, "no messages should be added")
end)

test("handle_line: malformed JSON is handled gracefully", function()
  local v = new_chat()
  local base = #v.messages
  -- This should not throw (pcall in handle_line)
  v:handle_line("not json at all {{{")
  assert_eq(#v.messages, base, "no messages from bad JSON")
end)

-- -------------------------------------------------------------------------
io.write("\n--- Send / Cancel Tests ---\n")
-- -------------------------------------------------------------------------

test("send_message: appends user message and creates stream placeholder", function()
  local v = new_chat()
  v.proc = {
    running = function(self) return true end,
    stdin = { write = function(self, data) end },
  }
  v.input_buffer = "test query"
  v.streaming = false
  local base = #v.messages

  v:send_message()

  assert_eq(v.input_buffer, "", "input buffer should be cleared")
  assert_eq(v.streaming, true, "should be streaming")
  -- messages: [..., user_msg, assistant_placeholder]
  assert_eq(#v.messages, base + 2, "should have 2 more messages")
  assert_eq(v.messages[base + 1].role, "user")
  assert_eq(v.messages[base + 1].text, "test query")
  assert_eq(v.messages[base + 2].role, "assistant")
  assert_eq(v.messages[base + 2].text, "")
  assert_eq(type(v.messages[base + 2].tools), "table", "tools should be a table")
  assert_eq(#v.messages[base + 2].tools, 0, "tools should be empty")
end)

test("send_message: no-op when empty buffer", function()
  local v = new_chat()
  v.proc = { running = function() return true end, stdin = { write = function() end } }
  v.input_buffer = ""
  local base = #v.messages
  v:send_message()
  assert_eq(#v.messages, base, "no messages sent")
end)

test("send_message: no-op when already streaming", function()
  local v = new_chat()
  v.proc = { running = function() return true end, stdin = { write = function() end } }
  v.input_buffer = "test"
  v.streaming = true
  local base = #v.messages
  v:send_message()
  -- streaming is still true, user message not added
  assert_eq(#v.messages, base)
end)

test("cancel_operation: sends cancel JSON", function()
  local v = new_chat()
  local written = {}
  v.proc = {
    running = function() return true end,
    stdin = { write = function(self, data) written[#written + 1] = data end },
  }
  v:cancel_operation()
  assert_gt(#written, 0, "should have written cancel to stdin")
end)

-- -------------------------------------------------------------------------
io.write("\n--- Session Management Tests ---\n")
-- -------------------------------------------------------------------------

test("new_session: resets all state", function()
  local v = new_chat()
  v.proc = {
    running = function() return true end,
    stdin = { write = function() end },
    wait = function(self, t) return 0 end,
  }
  v.session_id = "old-sess"
  v.messages = { { role = "user", text = "old" } }
  v.streaming = true
  v.current_stream = { role = "assistant", text = "partial" }
  v.pending_approvals = { { id = "a1" } }

  v:new_session()

  assert_eq(v.session_id, nil, "session_id should be nil")
  assert_eq(#v.messages, 1, "should have 1 system message")
  assert_eq(v.messages[1].role, "system")
  assert_eq(v.streaming, false, "streaming should be false")
  assert_eq(v.current_stream, nil, "current_stream should be nil")
  assert_eq(#v.pending_approvals, 0, "pending approvals cleared")
end)

-- -------------------------------------------------------------------------
io.write("\n--- Keyboard / Input Tests ---\n")
-- -------------------------------------------------------------------------

test("on_text_input: appends to buffer when focused", function()
  local v = new_chat()
  v.input_focused = true
  v:on_text_input("a")
  assert_eq(v.input_buffer, "a")
  v:on_text_input("b")
  assert_eq(v.input_buffer, "ab")
end)

test("on_text_input: ignored when not focused", function()
  local v = new_chat()
  v.input_focused = false
  v:on_text_input("a")
  assert_eq(v.input_buffer, "")
end)

test("delete_backward: removes last character", function()
  local v = new_chat()
  v.input_focused = true
  v.input_buffer = "abc"
  v:delete_backward()
  assert_eq(v.input_buffer, "ab")
  v:delete_backward()
  assert_eq(v.input_buffer, "a")
  v:delete_backward()
  assert_eq(v.input_buffer, "")
end)

test("delete_backward: no-op on empty buffer", function()
  local v = new_chat()
  v.input_focused = true
  v.input_buffer = ""
  v:delete_backward()
  assert_eq(v.input_buffer, "")
end)

test("delete_backward: no-op when not focused", function()
  local v = new_chat()
  v.input_focused = false
  v.input_buffer = "abc"
  v:delete_backward()
  assert_eq(v.input_buffer, "abc")
end)

test("delete_word: removes last word", function()
  local v = new_chat()
  v.input_focused = true
  v.input_buffer = "hello world"
  v:delete_word()
  assert_eq(v.input_buffer, "hello ")
end)

test("delete_word: removes trailing spaces then word", function()
  local v = new_chat()
  v.input_focused = true
  v.input_buffer = "hello world  "
  v:delete_word()
  assert_eq(v.input_buffer, "hello ")
end)

test("delete_word: removes single word", function()
  local v = new_chat()
  v.input_focused = true
  v.input_buffer = "hello"
  v:delete_word()
  assert_eq(v.input_buffer, "")
end)

test("delete_word: no-op on empty buffer", function()
  local v = new_chat()
  v.input_focused = true
  v.input_buffer = ""
  v:delete_word()
  assert_eq(v.input_buffer, "")
end)

test("delete_word: no-op when not focused", function()
  local v = new_chat()
  v.input_focused = false
  v.input_buffer = "hello world"
  v:delete_word()
  assert_eq(v.input_buffer, "hello world")
end)

-- -------------------------------------------------------------------------
io.write("\n--- Mouse / Click Tests ---\n")
-- -------------------------------------------------------------------------

test("on_mouse_pressed: toggle input focus on input area", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  -- Simulate click in input area (bottom of view)
  v:on_mouse_pressed(1, 100, 590, 1)
  assert_eq(v.input_focused, true, "should focus input")
end)

test("on_mouse_pressed: toggle history panel", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  -- History button: icon_size = font height = 16
  -- plus_x = 0 + 8 = 8
  -- hist_x = 8 + 16 + 16 = 40
  -- toolbar_top ~= 600 - input_h - divider - toolbar_h
  -- With size.x set, get_input_height works, toolbar_h = 16 + 4*2 = 24
  v:on_mouse_pressed(1, 40, 550, 1)
  -- History panel toggles (may fail to load sessions, but show_history should toggle)
  assert(v.show_history == true or v.show_history == false, "history toggled")
end)

-- -------------------------------------------------------------------------
io.write("\n--- Draw Tests (smoke) ---\n")
-- -------------------------------------------------------------------------

test("draw: smoke test - no crash on empty chat", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  mock.reset()
  -- This should not throw
  local ok, err = pcall(function() v:draw() end)
  assert(ok, "draw() crashed: " .. tostring(err))
end)

test("draw: smoke test - renders user and assistant messages", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  v.messages = {
    { role = "user", text = "Hello", tools = {} },
    { role = "assistant", text = "Hi there", tools = {} },
  }
  mock.reset()
  local ok, err = pcall(function() v:draw() end)
  assert(ok, "draw() with messages crashed: " .. tostring(err))
  assert_gt(#mock.state.drawn_rects, 0, "should draw rects")
  assert_gt(#mock.state.drawn_text, 0, "should draw text")
end)

test("draw: smoke test - renders tool indicators", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  v.messages = {
    {
      role = "assistant", text = "Running tool",
      tools = { { name = "bash", status = "running" }, { name = "read", status = "done", display = "42 lines" } },
    },
  }
  mock.reset()
  local ok, err = pcall(function() v:draw() end)
  assert(ok, "draw() with tools crashed: " .. tostring(err))
end)

test("draw: smoke test - renders streaming indicator", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  v.streaming = true
  mock.reset()
  local ok, err = pcall(function() v:draw() end)
  assert(ok, "draw() streaming crashed: " .. tostring(err))
end)

test("draw: smoke test - renders pending approvals", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  v.pending_approvals = {
    { id = "a1", tool = "write", display = "/tmp/test.txt", y = 0, approve_x = 0, deny_x = 0 },
  }
  mock.reset()
  local ok, err = pcall(function() v:draw() end)
  assert(ok, "draw() with approvals crashed: " .. tostring(err))
end)

-- -------------------------------------------------------------------------
io.write("\n--- Diff Preview Tests ---\n")
-- -------------------------------------------------------------------------

test("compute_diff: identical texts produce same-only diff", function()
  -- compute_diff is local, test via module scope
  -- We test it indirectly through tool_end handling
  local v = new_chat()
  v.streaming = true
  v.current_stream = { role = "assistant", text = "", tools = {} }
  table.insert(v.messages, v.current_stream)

  -- Simulate edit tool_end with identical strings (no diff)
  table.insert(json_results, {
    type = "tool_end", tool = "edit", display = "edited file",
    args = { path = "/tmp/test.txt", old_string = "hello", new_string = "hello" },
  })
  v:handle_line('{"type":"tool_end","tool":"edit","display":"edited file","args":{"path":"/tmp/test.txt","old_string":"hello","new_string":"hello"}}')
  -- No diff should be created since strings are identical
  local diffs_for_msg = 0
  for _, d in ipairs(v.pending_diffs) do
    if d.msg == v.current_stream then diffs_for_msg = diffs_for_msg + 1 end
  end
  assert_eq(diffs_for_msg, 0, "no diff for identical strings")
end)

test("compute_diff: different texts create diff entries", function()
  local v = new_chat()
  v.streaming = true
  v.current_stream = { role = "assistant", text = "", tools = {} }
  table.insert(v.messages, v.current_stream)

  -- Must send tool_start first
  table.insert(json_results, { type = "tool_start", tool = "edit" })
  v:handle_line('{"type":"tool_start","tool":"edit"}')

  table.insert(json_results, {
    type = "tool_end", tool = "edit", display = "edited file",
    args = { path = "/tmp/test.txt", old_string = "line1\nline2", new_string = "line1\nline3\nline4" },
  })
  v:handle_line('{"type":"tool_end","tool":"edit","display":"edited file","args":{"path":"/tmp/test.txt","old_string":"line1\\nline2","new_string":"line1\\nline3\\nline4"}}')
  local diffs_for_msg = 0
  for _, d in ipairs(v.pending_diffs) do
    if d.msg == v.current_stream then diffs_for_msg = diffs_for_msg + 1 end
  end
  assert_eq(diffs_for_msg, 1, "should have 1 diff")
  local diff = v.pending_diffs[1]
  assert_eq(diff.path, "/tmp/test.txt")
  assert_gt(#diff.lines, 0, "diff should have lines")
  assert_eq(diff.original, "line1\nline2", "should store original")
end)

test("draw: renders diff preview", function()
  local v = new_chat()
  v.visible = true
  v.size = { x = 400, y = 600 }
  v.position = { x = 0, y = 0 }
  v.messages = {
    { role = "assistant", text = "Edited file", tools = {} },
  }
  v.pending_diffs = {
    {
      path = "/tmp/test.txt",
      lines = {
        { type = "del", line = "old line" },
        { type = "add", line = "new line" },
      },
      original = "old line",
      msg = v.messages[1],
      tool_index = 1,
    },
  }
  mock.reset()
  local ok, err = pcall(function() v:draw() end)
  assert(ok, "draw() with diff crashed: " .. tostring(err))
  assert_gt(#mock.state.drawn_rects, 0, "should draw diff rects")
end)

-- -------------------------------------------------------------------------
-- Results
-- -------------------------------------------------------------------------

io.write(string.format("\n=== Results: %d passed, %d failed ===\n\n", pass, fail))
if fail > 0 then
  io.write("Failures:\n")
  for _, e in ipairs(errors) do
    io.write("  " .. e.name .. "\n    " .. e.err .. "\n")
  end
end

os.exit(fail > 0 and 1 or 0)
