-- mod-version:4
local core = require "core"
local common = require "core.common"
local command = require "core.command"
local config = require "core.config"
local keymap = require "core.keymap"
local style = require "core.style"
local View = require "core.view"
local process = require "core.process"

config.plugins.rta_chat = common.merge({
  size = 340 * SCALE,
  visible = true,
}, config.plugins.rta_chat)


local LogView = require "core.logview"
local json = require "core.json"


local function stderr(...)
  local parts = {}
  for i = 1, select("#", ...) do
    parts[#parts+1] = tostring(select(i, ...))
  end
  io.stderr:write(table.concat(parts, "\t"), "\n")
  io.stderr:flush()
end


local function log(msg, ...)
  if ... then msg = string.format(msg, ...) end
  core.log("RTA Chat: %s", msg)
end


--- Find the rta binary path.
--- Checks: ~/.rta/cli_path → PATH
local function find_rta_binary()
  local home = os.getenv("HOME") or ""

  local saved = home .. "/.rta/cli_path"
  local f = io.open(saved, "r")
  if f then
    local path = f:read("*l")
    f:close()
    if path and #path > 0 then
      local check = io.open(path, "r")
      if check then
        check:close()
        return path
      end
    end
  end

  local handle = io.popen("which rta 2>/dev/null")
  if handle then
    local path = handle:read("*l")
    handle:close()
    if path and #path > 0 then
      return path
    end
  end

  return nil
end


--- Persist the rta binary path.
local function save_rta_path(path)
  local home = os.getenv("HOME") or ""
  local dir = home .. "/.rta"
  os.execute("mkdir -p " .. dir)
  local f = io.open(dir .. "/cli_path", "w")
  if f then
    f:write(path)
    f:close()
  end
end


local RtaChat = View:extend()

function RtaChat:__tostring()
  return "RtaChat"
end

function RtaChat:new()
  RtaChat.super.new(self)
  self.scrollable = true
  self.visible = config.plugins.rta_chat.visible
  self.input_buffer = ""
  self.messages = {}
  self.input_focused = false
  self.rta_path = find_rta_binary()
  self.proc = nil
  self.reader_thread = nil
  self.streaming = false
  self.current_stream = nil
  self.current_tool = nil
  self.pending_approvals = {}
  self.session_id = nil

  if self.rta_path then
    table.insert(self.messages, {
      role = "system",
      text = "Connected to RTA CLI.",
      time = os.date("%H:%M"),
    })
    self:start_process()
  else
    table.insert(self.messages, {
      role = "system",
      text = "RTA CLI not found.\nPlace rta in your PATH\nor set ~/.rta/cli_path\nthen restart.",
      time = os.date("%H:%M"),
    })
  end
end

function RtaChat:get_name()
  return "RTA Chat"
end

function RtaChat:supports_text_input()
  return true
end

function RtaChat:get_input_height()
  local lines = 1
  if #self.input_buffer > 0 then
    local max_w = self.size.x - style.padding.x * 2 - 70 * SCALE
    if max_w > 0 then
      local text_w = style.font:get_width(self.input_buffer)
      lines = math.max(1, math.min(3, math.ceil(text_w / max_w)))
    end
  end
  return lines * (style.font:get_height() + style.padding.y) + style.padding.y * 2 + style.divider_size
end

function RtaChat:get_line_height()
  return style.font:get_height() + style.padding.y * 1.5
end

function RtaChat:get_line_height_msg(msg)
  local lines = 1
  local max_w = self.size.x - style.padding.x * 3
  if max_w > 0 then
    local text_w = style.font:get_width(msg.text)
    lines = math.max(1, math.ceil(text_w / max_w))
  end
  return lines * (style.font:get_height() + style.padding.y) + style.padding.y * 0.5
end

function RtaChat:get_scrollable_size()
  local total = 0
  for _, msg in ipairs(self.messages) do
    total = total + self:get_line_height_msg(msg)
  end
  return total
end

function RtaChat:on_text_input(text)
  if not self.input_focused then return end
  self.input_buffer = self.input_buffer .. text
  core.redraw = true
end

function RtaChat:on_mouse_pressed(button, x, y, clicks)
  if RtaChat.super.on_mouse_pressed(self, button, x, y, clicks) then
    return true
  end
  local input_y = self.position.y + self.size.y - self:get_input_height()
  local input_h = self:get_input_height()

  if y >= input_y + style.divider_size and y <= input_y + input_h then
    if not self.input_focused then
      self.input_focused = true
      core.set_active_view(self)
      core.redraw = true
    end
    return true
  end

  local btn_x = self.position.x + self.size.x - 65 * SCALE
  local btn_w = 60 * SCALE
  if x >= btn_x and x <= btn_x + btn_w then
    if y >= input_y and y <= input_y + input_h then
      self:send_message()
      return true
    end
  end

  for i, approval in ipairs(self.pending_approvals) do
    local ay = approval.y
    local ah = style.font:get_height() + style.padding.y * 2
    if y >= ay and y <= ay + ah then
      local approve_x = approval.approve_x
      local deny_x = approval.deny_x
      local bw = 50 * SCALE
      if x >= approve_x and x <= approve_x + bw then
        self:respond_approval(approval.id, true)
        table.remove(self.pending_approvals, i)
        core.redraw = true
        return true
      end
      if x >= deny_x and x <= deny_x + bw then
        self:respond_approval(approval.id, false)
        table.remove(self.pending_approvals, i)
        core.redraw = true
        return true
      end
    end
  end

  self.input_focused = false
  return true
end

function RtaChat:delete_backward()
  if not self.input_focused or #self.input_buffer == 0 then return end
  local byte_pos = #self.input_buffer
  while byte_pos > 0 and self.input_buffer:byte(byte_pos) >= 128 and self.input_buffer:byte(byte_pos) < 192 do
    byte_pos = byte_pos - 1
  end
  self.input_buffer = self.input_buffer:sub(1, byte_pos - 1)
  core.redraw = true
end


--- Start the rta --stdio process.
function RtaChat:start_process()
  if self.proc then return end
  if not self.rta_path then return end

  local proc = process.start({self.rta_path, "--stdio"})
  if not proc then
    log("Failed to start rta process")
    return
  end

  self.proc = proc
  self:start_reader()
end


--- Start the stdout reader coroutine.
function RtaChat:start_reader()
  if self.reader_thread then return end

  local self_ref = self
  self.reader_thread = core.add_thread(function()
    while self_ref.proc and self_ref.proc:running() do
      local line = self_ref.proc.stdout:read("line")
      if line then
        self_ref:handle_line(line)
      end
    end
    log("rta process exited")
    self_ref.proc = nil
    self_ref.reader_thread = nil
  end)
end


--- Handle a single JSON line from stdout.
function RtaChat:handle_line(line)
  if not line or #line == 0 then return end

  local ok, obj = pcall(json.decode, line)
  if not ok then
    stderr("JSON decode error:", obj)
    return
  end

  local t = obj.type
  if t == "status_response" then
    self.session_id = obj.session_id
    log("CLI session: %s, model: %s", obj.session_id or "?", obj.model or "?")

  elseif t == "text_delta" then
    if not self.streaming then
      self.streaming = true
      self.current_stream = {
        role = "assistant",
        text = "",
        time = os.date("%H:%M"),
        tools = {},
      }
      table.insert(self.messages, self.current_stream)
    end
    if self.current_stream then
      self.current_stream.text = self.current_stream.text .. (obj.content or "")
    end
    self.scroll.to.y = self:get_scrollable_size()
    core.redraw = true

  elseif t == "text_done" then
    self.streaming = false
    self.current_stream = nil
    self.session_id = obj.session_id or self.session_id
    core.redraw = true

  elseif t == "tool_start" then
    if self.current_stream then
      table.insert(self.current_stream.tools, {
        name = obj.tool or "unknown",
        status = "running",
      })
    end
    self.current_tool = obj.tool
    core.redraw = true

  elseif t == "tool_end" then
    if self.current_stream then
      for _, tool in ipairs(self.current_stream.tools) do
        if tool.name == obj.tool and tool.status == "running" then
          tool.status = "done"
          tool.display = obj.display or ""
          break
        end
      end
    end
    self.current_tool = nil
    core.redraw = true

  elseif t == "tool_approval" then
    local approval = {
      id = obj.approval_id,
      tool = obj.tool or "unknown",
      display = obj.display or "",
      y = 0,
      approve_x = 0,
      deny_x = 0,
    }
    table.insert(self.pending_approvals, approval)
    self.scroll.to.y = self:get_scrollable_size()
    core.redraw = true

  elseif t == "error" then
    table.insert(self.messages, {
      role = "system",
      text = "Error: " .. (obj.message or "Unknown error"),
      time = os.date("%H:%M"),
    })
    self.streaming = false
    self.current_stream = nil
    core.redraw = true
  end
end


--- Send a chat message to the rta process.
function RtaChat:send_message()
  if self.streaming or #self.input_buffer == 0 then return end

  if not self.proc or not self.proc:running() then
    self:start_process()
    if not self.proc or not self.proc:running() then
      table.insert(self.messages, {
        role = "system",
        text = "RTA CLI not running.\nCheck ~/.rta/cli_path.",
        time = os.date("%H:%M"),
      })
      self.streaming = false
      core.redraw = true
      return
    end
  end

  local user_msg = self.input_buffer
  table.insert(self.messages, {
    role = "user",
    text = user_msg,
    time = os.date("%H:%M"),
  })
  self.input_buffer = ""
  self.streaming = true
  core.redraw = true

  local request = json.encode({
    type = "chat",
    message = user_msg,
    session_id = self.session_id,
  })

  self.proc.stdin:write(request .. "\n")
  self.scroll.to.y = self:get_scrollable_size()
  core.redraw = true
end


--- Respond to a tool approval request.
function RtaChat:respond_approval(approval_id, approved)
  if not self.proc or not self.proc:running() then return end

  local req_type = approved and "tool_approved" or "tool_denied"
  local request = json.encode({
    type = req_type,
    approval_id = approval_id,
  })

  self.proc.stdin:write(request .. "\n")
end


--- Cancel the current operation.
function RtaChat:cancel_operation()
  if not self.proc or not self.proc:running() then return end
  self.proc.stdin:write(json.encode({type = "cancel"}) .. "\n")
end


function RtaChat:update()
  local dest = self.visible and config.plugins.rta_chat.size or 0
  self:move_towards(self.size, "x", dest)
  if self.size.x == 0 then return end
  RtaChat.super.update(self)
end

function RtaChat:draw()
  if not self.visible then return end
  self:draw_background(style.background2)
  local ox, oy = self:get_content_offset()
  local w = self.size.x
  local input_h = self:get_input_height()
  local lh = self:get_line_height()
  local msg_start_y = self.position.y + style.padding.y

  -- Messages
  local y = msg_start_y - self.scroll.y
  core.push_clip_rect(self.position.x, self.position.y, w, self.size.y - input_h)

  for _, msg in ipairs(self.messages) do
    local mlh = self:get_line_height_msg(msg)
    local msg_top = y
    local msg_bottom = y + mlh
    if msg_bottom > self.position.y and msg_top < self.position.y + self.size.y - input_h then
      local pad = style.padding.x
      local text_w = w - pad * 2
      local is_user = msg.role == "user"
      local bg_color = is_user and style.selection or (msg.role == "system" and style.background3 or style.background)
      local text_color = is_user and style.accent or (msg.role == "system" and style.warn or style.text)

      if msg.role == "assistant" then
        renderer.draw_rect(self.position.x + 2, msg_top, 3, mlh, style.accent)
      end

      common.draw_text(style.font, text_color, msg.text, nil,
        self.position.x + pad, msg_top + style.padding.y * 0.5, text_w, mlh)

      -- Draw tool indicators
      if msg.tools and #msg.tools > 0 then
        local ty = msg_top + style.font:get_height() + style.padding.y
        for _, tool in ipairs(msg.tools) do
          local icon = tool.status == "running" and "~" or "+"
          local color = tool.status == "running" and style.warn or style.dim
          local label = string.format("[%s %s]", icon, tool.name)
          if tool.display and #tool.display > 0 then
            label = label .. " " .. tool.display:sub(1, 40)
          end
          common.draw_text(style.font, color, label, nil,
            self.position.x + pad + style.padding.x, ty, text_w - style.padding.x, lh)
          ty = ty + lh
        end
        mlh = mlh + #msg.tools * lh
      end
    end
    y = y + mlh
  end

  -- Tool approval buttons
  for _, approval in ipairs(self.pending_approvals) do
    local ay = y - self.scroll.y
    local ah = style.font:get_height() + style.padding.y * 2
    approval.y = ay + self.position.y

    local pad = style.padding.x
    local label = string.format("[%s] %s", approval.tool, approval.display:sub(1, 50))
    common.draw_text(style.font, style.warn, label, nil,
      self.position.x + pad, ay + style.padding.y * 0.5, w - pad * 2, ah)

    local bw = 50 * SCALE
    local btn_y = ay + style.padding.y * 0.5
    local btn_h = style.font:get_height() + style.padding.y

    local approve_x = self.position.x + w - bw * 2 - style.padding.x * 2
    local deny_x = self.position.x + w - bw - style.padding.x
    approval.approve_x = approve_x
    approval.deny_x = deny_x

    renderer.draw_rect(approve_x, btn_y, bw, btn_h, style.background3)
    common.draw_text(style.font, style.accent, "Yes", "center", approve_x, btn_y, bw, btn_h)

    renderer.draw_rect(deny_x, btn_y, bw, btn_h, style.background3)
    common.draw_text(style.font, style.warn, "No", "center", deny_x, btn_y, bw, btn_h)

    y = y + ah
  end

  -- Streaming indicator
  if self.streaming then
    local dots = (os.clock() * 2) % 4
    local text = "Thinking" .. string.rep(".", math.floor(dots))
    common.draw_text(style.font, style.dim, text, nil,
      self.position.x + style.padding.x, y + style.padding.y * 0.5, w - style.padding.x * 2, lh)
  end

  core.pop_clip_rect()

  -- Divider above input
  local input_top = self.position.y + self.size.y - input_h
  renderer.draw_rect(self.position.x, input_top, w, style.divider_size, style.divider)

  -- Input background
  local input_area_y = input_top + style.divider_size
  renderer.draw_rect(self.position.x, input_area_y, w, input_h - style.divider_size, self.input_focused and style.background or style.background3)

  -- Input text
  local input_text_x = self.position.x + style.padding.x
  local input_text_y = input_area_y + style.padding.y
  local input_text_w = w - style.padding.x * 2 - 70 * SCALE
  local placeholder = self.input_focused and "" or "Type a message..."
  local display_text = #self.input_buffer > 0 and self.input_buffer or placeholder
  local text_col = #self.input_buffer > 0 and style.text or style.dim
  if input_text_w > 0 then
    local remaining = display_text
    local ty = input_text_y
    while #remaining > 0 do
      local cut = remaining
      while #cut > 0 and style.font:get_width(cut) > input_text_w do
        cut = cut:sub(1, -2)
      end
      if #cut == 0 then cut = remaining:sub(1, 1); remaining = remaining:sub(2)
      else remaining = remaining:sub(#cut + 1) end
      common.draw_text(style.font, text_col, cut, nil, input_text_x, ty, input_text_w, style.font:get_height())
      ty = ty + style.font:get_height() + style.padding.y
    end
  end

  -- Cursor
  if self.input_focused and os.clock() % 1 < 0.5 then
    local cursor_x = input_text_x
    local cursor_y = input_text_y
    if #self.input_buffer > 0 and input_text_w > 0 then
      local remaining = self.input_buffer
      while #remaining > 0 do
        local cut = remaining
        while #cut > 0 and style.font:get_width(cut) > input_text_w do
          cut = cut:sub(1, -2)
        end
        if #cut == 0 then cut = remaining:sub(1, 1); remaining = remaining:sub(2)
        else remaining = remaining:sub(#cut + 1) end
        cursor_x = input_text_x + style.font:get_width(cut)
        if #remaining > 0 then
          cursor_y = cursor_y + style.font:get_height() + style.padding.y
        end
      end
    end
    renderer.draw_rect(cursor_x, cursor_y, style.caret_width, style.font:get_height(), style.caret)
  end

  -- Send button
  local btn_x = self.position.x + w - 65 * SCALE
  local btn_y = input_area_y + style.padding.y * 0.5
  local btn_w = 60 * SCALE
  local btn_h = input_h - style.divider_size - style.padding.y
  local can_send = #self.input_buffer > 0 and not self.streaming
  local btn_color = can_send and style.accent or style.dim
  renderer.draw_rect(btn_x, btn_y, btn_w, btn_h, style.background3)
  common.draw_text(style.font, btn_color, "Send", "center", btn_x, btn_y, btn_w, btn_h)

  -- Scrollbar
  self:draw_scrollbar()
end


local function find_doc_node(node)
  if node.type ~= "leaf" then
    return find_doc_node(node.a) or find_doc_node(node.b)
  end
  if not node.locked then
    return node
  end
end

local chat_view = RtaChat()
local node = find_doc_node(core.root_view.root_node) or core.root_view:get_active_node()
chat_view.node = node:split("right", chat_view, {x = true}, true)


local log_view = LogView()
local function toggle_log_view()
  if log_view.node then
    log_view.node:close_view(core.root_view.root_node, log_view)
    log_view.node = nil
  else
    local ln = find_doc_node(core.root_view.root_node) or core.root_view:get_active_node()
    log_view.node = ln:split("right", log_view, {x = true}, true)
  end
  core.redraw = true
end


command.add(RtaChat, {
  ["rta-chat:submit"] = function(v)
    v:send_message()
  end,
  ["rta-chat:backspace"] = function(v)
    v:delete_backward()
  end,
  ["rta-chat:focus"] = function(v)
    v.input_focused = not v.input_focused
    if v.input_focused then core.set_active_view(v) end
    core.redraw = true
  end,
  ["rta-chat:cancel"] = function(v)
    v:cancel_operation()
  end,
})

command.add(nil, {
  ["rta-chat:toggle"] = function()
    chat_view.visible = not chat_view.visible
    core.redraw = true
  end,
  ["rta-chat:restart"] = function()
    if chat_view.proc and chat_view.proc:running() then
      chat_view.proc:wait(0)
    end
    chat_view.proc = nil
    chat_view.reader_thread = nil
    chat_view.rta_path = find_rta_binary()
    chat_view:start_process()
    core.redraw = true
  end,
  ["log-view:toggle"] = toggle_log_view,
})

keymap.add {
  ["return"] = "rta-chat:submit",
  ["backspace"] = "rta-chat:backspace",
  ["ctrl+shift+c"] = "rta-chat:toggle",
  ["ctrl+shift+l"] = "log-view:toggle",
  ["escape"] = "rta-chat:cancel",
}

return chat_view
