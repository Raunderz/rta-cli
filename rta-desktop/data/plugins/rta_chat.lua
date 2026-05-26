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
  server_url = "https://divisive-herbs-jolly.ngrok-free.dev",
}, config.plugins.rta_chat)


local b64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

local function b64_decode(data)
  data = data:gsub("[^" .. b64chars .. "=]", "")

  return (data:gsub(".", function(x)
    if x == "=" then
      return ""
    end

    local r, f = "", (b64chars:find(x, 1, true) or 1) - 1

    for i = 6, 1, -1 do
      r = r .. ((f % 2^i - f % 2^(i - 1) > 0) and "1" or "0")
    end

    return r
  end):gsub("%d%d%d?%d?%d?%d?%d?%d?", function(x)
    if #x ~= 8 then
      return ""
    end

    local c = 0
    for i = 1, 8 do
      if x:sub(i, i) == "1" then
        c = c + 2^(8 - i)
      end
    end

    return string.char(c)
  end))
end


local LogView = require "core.logview"

local function stderr(...)
  local parts = {}
  for i = 1, select("#", ...) do
    parts[#parts+1] = tostring(select(i, ...))
  end
  io.stderr:write(table.concat(parts, "\t"), "\n")
  io.stderr:flush()
end


local json = require "core.json"

local function log(msg, ...)
  if ... then msg = string.format(msg, ...) end
  core.log("RTA Chat: %s", msg)
end

local function load_api_key()
  local home = os.getenv("HOME") or ""
  local path = home .. "/.rta/credentials"

  local f, err = io.open(path, "r")
  if not f then
    log("Failed to open credentials file: %s", err or "unknown error")
    return nil
  end

  for line in f:lines() do
    local val = line:match("^rta_api_key%s*=%s*(.+)$")

    if val and #val > 0 then
      f:close()

      local ok, decoded = pcall(b64_decode, val)

      if not ok then
        log("Failed to decode API key")
        return nil
      end

      if type(decoded) ~= "string" or #decoded == 0 then
        log("Invalid decoded API key")
        return nil
      end

      return decoded
    end
  end

  f:close()
  log("rta_api_key not found in credentials file")
  return nil
end


local function get_device_id()
  local home = os.getenv("HOME") or ""
  local f = io.open(home .. "/.rta/.device_id", "r")
  if f then
    local id = f:read("*l")
    f:close()
    return id
  end
  return "00000000-0000-0000-0000-000000000000"
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
  self.sending = false
  self.messages = {}
  self.input_focused = false
  self.api_key = load_api_key()
  self.device_id = get_device_id()
  self.server_url = config.plugins.rta_chat.server_url
  self.system_prompt = "You are Rta, a helpful coding assistant. Be concise and direct."

  if self.api_key then
    table.insert(self.messages, {
      role = "system",
      text = "Connected as Rta User. Type a message to start.",
      time = os.date("%H:%M"),
    })
  else
    table.insert(self.messages, {
      role = "system",
      text = "API key not found. Run 'rta login' in the terminal first.",
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
  return style.font:get_height() + style.padding.y * 2 + style.divider_size
end

function RtaChat:get_scrollable_size()
  local lh = self:get_line_height()
  return #self.messages * lh
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
  if x >= self.position.x + self.size.x - 70 * SCALE and x <= self.position.x + self.size.x - style.padding.x then
    if y >= input_y and y <= input_y + input_h then
      self:send_message()
      return true
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

function RtaChat:send_message()
  if self.sending or #self.input_buffer == 0 or not self.api_key then return end

  local user_msg = self.input_buffer
  table.insert(self.messages, {
    role = "user",
    text = user_msg,
    time = os.date("%H:%M"),
  })
  self.input_buffer = ""
  self.sending = true
  core.redraw = true

  local messages_for_api = {}
  table.insert(messages_for_api, { role = "system", content = self.system_prompt })
  for _, msg in ipairs(self.messages) do
    if msg.role ~= "system" then
      table.insert(messages_for_api, { role = msg.role, content = msg.text })
    end
  end

  local body = json.encode({
    messages = messages_for_api,
    model = "auto",
    provider = "auto",
    stream = false,
    max_tokens = 2000,
  })

  stderr("Sending request to", self.server_url, "body size:", #body)
  stderr("API key (first 8):", self.api_key and self.api_key:sub(1, 8) or "nil")

  local url = self.server_url .. "/v1/chat"
  local args = {
    "curl", "-s", "--max-time", "30", "-X", "POST", url,
    "-H", "Content-Type: application/json",
    "-H", "X-API-KEY: " .. self.api_key,
    "-H", "X-Device-ID: " .. self.device_id,
    "-H", "X-CLI-Version: 0.4.0",
    "-H", "ngrok-skip-browser-warning: 69420",
    "-H", "User-Agent: rta-cli/1.0",
    "-d", body,
  }

  core.add_thread(function()
    stderr(">> thread started, calling process.start")
    local proc = process.start(args)
    stderr(">> process.start returned, pid:", proc and proc:pid() or "nil")
    stderr(">> reading stdout...")
    local result = proc.stdout:read("a")
    stderr(">> read returned, result size:", result and #result or 0, "type:", type(result))
    local ok = proc:wait()

    stderr("curl exit code:", ok, "response size:", result and #result or 0)

    if ok == 0 and result and #result > 0 then
      stderr("Raw response (first 500):", result:sub(1, 500))
      local ok, data = pcall(json.decode, result)
      if not ok then
        stderr("JSON decode error:", data)
        log("JSON parse error: %s", tostring(data))
        table.insert(self.messages, {
          role = "system",
          text = "Error: Failed to parse API response.",
          time = os.date("%H:%M"),
        })
      else
        stderr("Parsed data keys:", data and table.concat(table.keys(data), ", ") or "nil")
        local content
        if data.choices and data.choices[1] then
          local choice = data.choices[1]
          if choice.message then
            content = choice.message.content
            stderr("Found content in choices[1].message.content, length:", #content)
          end
        end
        if not content and data.message and data.message.content then
          content = data.message.content
          stderr("Found content in data.message.content, length:", #content)
        end
        if not content and data.content then
          content = data.content
          stderr("Found content in data.content, length:", #content)
        end
        if content then
          table.insert(self.messages, {
            role = "assistant",
            text = content,
            time = os.date("%H:%M"),
          })
          self.scroll.to.y = self:get_scrollable_size()
        else
          stderr("No content found in response, full dump:", result)
          log("No content in API response")
          table.insert(self.messages, {
            role = "system",
            text = "Error: Unexpected response format.",
            time = os.date("%H:%M"),
          })
        end
      end
    else
      local err = "Error: Request failed"
      if result and #result > 0 then
        err = err .. " - " .. result:sub(1, 200)
      end
      stderr("Request failed:", err)
      table.insert(self.messages, {
        role = "system",
        text = err,
        time = os.date("%H:%M"),
      })
    end
    self.sending = false
    core.redraw = true
  end)
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
    end
    y = y + mlh
  end

  -- Loading indicator
  if self.sending then
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
  common.draw_text(style.font, text_col, display_text, nil, input_text_x, input_text_y, input_text_w, style.font:get_height())

  -- Cursor
  if self.input_focused and os.clock() % 1 < 0.5 then
    local cursor_x = input_text_x + style.font:get_width(self.input_buffer)
    renderer.draw_rect(cursor_x, input_text_y, style.caret_width, style.font:get_height(), style.caret)
  end

  -- Send button
  local btn_x = self.position.x + w - 65 * SCALE
  local btn_y = input_area_y + style.padding.y * 0.5
  local btn_w = 60 * SCALE
  local btn_h = input_h - style.divider_size - style.padding.y
  local can_send = #self.input_buffer > 0 and not self.sending and self.api_key
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
})

command.add(nil, {
  ["rta-chat:toggle"] = function()
    chat_view.visible = not chat_view.visible
    core.redraw = true
  end,
  ["log-view:toggle"] = toggle_log_view,
})

keymap.add {
  ["return"] = "rta-chat:submit",
  ["backspace"] = "rta-chat:backspace",
  ["ctrl+shift+c"] = "rta-chat:toggle",
  ["ctrl+shift+l"] = "log-view:toggle",
}

return chat_view
