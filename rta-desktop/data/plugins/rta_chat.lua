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


local function json_decode(str)
  local pos = 1
  local function skip_ws()
    while pos <= #str and str:sub(pos, pos):match("%s") do pos = pos + 1 end
  end
  local function parse_string()
    pos = pos + 1
    local parts = {}
    while pos <= #str do
      local c = str:sub(pos, pos)
      if c == '"' then pos = pos + 1; break end
      if c == "\\" then
        pos = pos + 1
        local esc = str:sub(pos, pos)
        if esc == '"' or esc == "\\" or esc == "/" then parts[#parts+1] = esc
        elseif esc == "b" then parts[#parts+1] = "\b"
        elseif esc == "f" then parts[#parts+1] = "\f"
        elseif esc == "n" then parts[#parts+1] = "\n"
        elseif esc == "r" then parts[#parts+1] = "\r"
        elseif esc == "t" then parts[#parts+1] = "\t"
        elseif esc == "u" then
          local hex = str:sub(pos+1, pos+4)
          parts[#parts+1] = utf8.char(tonumber(hex, 16))
          pos = pos + 4
        end
      else
        parts[#parts+1] = c
      end
      pos = pos + 1
    end
    return table.concat(parts)
  end
  local function parse_value()
    skip_ws()
    local c = str:sub(pos, pos)
    if c == "{" then
      pos = pos + 1
      local obj = {}
      skip_ws()
      if str:sub(pos, pos) == "}" then pos = pos + 1; return obj end
      while pos <= #str do
        local key = parse_string()
        skip_ws()
        if str:sub(pos, pos) == ":" then pos = pos + 1 end
        obj[key] = parse_value()
        skip_ws()
        c = str:sub(pos, pos)
        if c == "}" then pos = pos + 1; break end
        if c == "," then pos = pos + 1 end
      end
      return obj
    elseif c == "[" then
      pos = pos + 1
      local arr = {}
      skip_ws()
      if str:sub(pos, pos) == "]" then pos = pos + 1; return arr end
      while pos <= #str do
        arr[#arr+1] = parse_value()
        skip_ws()
        c = str:sub(pos, pos)
        if c == "]" then pos = pos + 1; break end
        if c == "," then pos = pos + 1 end
      end
      return arr
    elseif c == '"' then
      return parse_string()
    elseif c == "t" then pos = pos + 4; return true
    elseif c == "f" then pos = pos + 5; return false
    elseif c == "n" then pos = pos + 4; return nil
    else
      local _, e = str:find("^-?%d+%.?%d*[eE]?[+-]?%d*", pos)
      if e then
        local n = tonumber(str:sub(pos, e))
        pos = e + 1
        return n
      end
      return nil
    end
  end
  local val = parse_value()
  return val
end


local function json_encode(val)
  local t = type(val)
  if t == "string" then
    return '"' .. val:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n'):gsub('\r', '\\r'):gsub('\t', '\\t') .. '"'
  elseif t == "number" then
    if val % 1 == 0 then return tostring(math.floor(val)) end
    return tostring(val)
  elseif t == "boolean" then
    return tostring(val)
  elseif t == "nil" then
    return "null"
  elseif t == "table" then
    local is_array = #val > 0
    if is_array then
      local parts = {}
      for _, v in ipairs(val) do
        parts[#parts+1] = json_encode(v)
      end
      return "[" .. table.concat(parts, ",") .. "]"
    else
      local parts = {}
      for k, v in pairs(val) do
        parts[#parts+1] = json_encode(k) .. ":" .. json_encode(v)
      end
      return "{" .. table.concat(parts, ",") .. "}"
    end
  end
  return "null"
end


local function load_api_key()
  local home = os.getenv("HOME") or ""
  local path = home .. "/.rta/credentials"

  local f, err = io.open(path, "r")
  if not f then
    core.error("RTA Chat: Failed to open credentials file: %s", err or "unknown error")
    return nil
  end

  for line in f:lines() do
    local val = line:match("^rta_api_key%s*=%s*(.+)$")

    if val and #val > 0 then
      f:close()

      local ok, decoded = pcall(b64_decode, val)

      if not ok then
        core.error("RTA Chat: Failed to decode API key")
        return nil
      end

      if type(decoded) ~= "string" or #decoded == 0 then
        core.error("RTA Chat: Invalid decoded API key")
        return nil
      end

      return decoded
    end
  end

  f:close()
  core.error("RTA Chat: rta_api_key not found in credentials file")
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

  local body = json_encode({
    messages = messages_for_api,
    model = "auto",
    provider = "auto",
    stream = false,
    max_tokens = 2000,
  })

  local url = self.server_url .. "/v1/chat"
  local args = {
    "curl", "-s", "-X", "POST", url,
    "-H", "Content-Type: application/json",
    "-H", "X-API-KEY: " .. self.api_key,
    "-H", "X-Device-ID: " .. self.device_id,
    "-H", "X-CLI-Version: 0.4.0",
    "-H", "ngrok-skip-browser-warning: 69420",
    "-H", "User-Agent: rta-cli/1.0",
    "-d", body,
  }

  core.add_thread(function()
    local proc = process.start(args)
    local result = proc.stdout:read("a")
    local ok = proc:wait()

    if ok == 0 and result and #result > 0 then
      local data = json_decode(result)
      if data and data.choices and data.choices[1] and data.choices[1].message then
        local content = data.choices[1].message.content or "(no response)"
        table.insert(self.messages, {
          role = "assistant",
          text = content,
          time = os.date("%H:%M"),
        })
        self.scroll.to.y = self:get_scrollable_size()
      else
        table.insert(self.messages, {
          role = "system",
          text = "Error: Unexpected API response format.",
          time = os.date("%H:%M"),
        })
      end
    else
      local err = "Error: Request failed"
      if result and #result > 0 then
        err = err .. " - " .. result:sub(1, 200)
      end
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
      local text_color = is_user and style.accent or (msg.role == "system" and style.dim or style.text)

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

local view = RtaChat()
local node = find_doc_node(core.root_view.root_node) or core.root_view:get_active_node()
view.node = node:split("right", view, {x = true}, true)


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
    view.visible = not view.visible
    core.redraw = true
  end,
})

keymap.add {
  ["return"] = "rta-chat:submit",
  ["backspace"] = "rta-chat:backspace",
  ["ctrl+shift+c"] = "rta-chat:toggle",
}

return view
