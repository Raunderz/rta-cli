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
  self.show_history = false
  self.history_sessions = {}
  self.history_hover = -1
  self.mouse_x = 0
  self.mouse_y = 0

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


local function draw_wrapped_text(font, color, text, x, y, max_w, line_h)
  if max_w <= 0 or #text == 0 then return y end
  local remaining = text
  local ty = y
  while #remaining > 0 do
    local cut = remaining
    while #cut > 0 and font:get_width(cut) > max_w do
      cut = cut:sub(1, -2)
    end
    if #cut == 0 then
      cut = remaining:sub(1, 1)
      remaining = remaining:sub(2)
    else
      remaining = remaining:sub(#cut + 1)
    end
    renderer.draw_text(font, cut, x, ty, color)
    ty = ty + line_h
  end
  return ty
end


function RtaChat:get_line_height_msg(msg)
  local lines = 1
  local max_w = self.size.x - style.padding.x * 3
  if max_w > 0 and #msg.text > 0 then
    local text_w = style.font:get_width(msg.text)
    lines = math.max(1, math.ceil(text_w / max_w))
  end
  local text_h = lines * (style.font:get_height() + style.padding.y)
  local tools_h = 0
  if msg.tools and #msg.tools > 0 then
    tools_h = #msg.tools * (style.font:get_height() + style.padding.y * 1.5) + style.padding.y
  end
  return text_h + tools_h + style.padding.y * 2
end

function RtaChat:get_scrollable_size()
  local total = 0
  for _, msg in ipairs(self.messages) do
    total = total + self:get_line_height_msg(msg)
  end
  -- Add toolbar+input height so View's scroll range accounts for the non-scrollable area
  local toolbar_h = style.font:get_height() + style.padding.y * 2 + style.divider_size * 2
  return total + self:get_input_height() + toolbar_h
end

function RtaChat:on_text_input(text)
  if not self.input_focused then return end
  self.input_buffer = self.input_buffer .. text
  core.redraw = true
end

function RtaChat:on_mouse_moved(x, y, dx, dy)
  self.mouse_x = x
  self.mouse_y = y
  RtaChat.super.on_mouse_moved(self, x, y, dx, dy)
end

function RtaChat:on_mouse_pressed(button, x, y, clicks)
  if RtaChat.super.on_mouse_pressed(self, button, x, y, clicks) then
    return true
  end
  local input_h = self:get_input_height()
  local toolbar_h = style.font:get_height() + style.padding.y * 2
  local input_top = self.position.y + self.size.y - input_h
  local toolbar_top = input_top - style.divider_size - toolbar_h

  -- History panel click (intercepts all clicks when open)
  if self.show_history then
    local title_h = style.font:get_height() + style.padding.y * 2
    local item_y = self.position.y + title_h + style.padding.y
    local item_h = style.font:get_height() + style.padding.y
    for i, sess in ipairs(self.history_sessions) do
      if y >= item_y and y < item_y + item_h then
        self:resume_session(sess.id)
        return true
      end
      item_y = item_y + item_h
    end
    self.show_history = false
    core.redraw = true
    return true
  end

  -- Toolbar icon clicks
  if y >= toolbar_top and y <= toolbar_top + toolbar_h then
    local icon_size = style.font:get_height()
    local plus_x = self.position.x + style.padding.x
    local hist_x = plus_x + icon_size + style.padding.x * 2
    if x >= plus_x and x <= plus_x + icon_size then
      self:new_session()
      return true
    end
    if x >= hist_x and x <= hist_x + icon_size then
      self.show_history = not self.show_history
      if self.show_history then
        self:load_history()
      end
      core.redraw = true
      return true
    end
    return true
  end

  -- Input area click
  if y >= input_top and y <= self.position.y + self.size.y then
    local btn_x = self.position.x + self.size.x - 65 * SCALE
    local btn_w = 60 * SCALE
    if x >= btn_x and x <= btn_x + btn_w then
      self:send_message()
      return true
    end
    if not self.input_focused then
      self.input_focused = true
      core.set_active_view(self)
      core.redraw = true
    end
    return true
  end

  -- Approval button clicks
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
  -- Create placeholder for assistant response so text_delta has something to append to
  self.current_stream = {
    role = "assistant",
    text = "",
    time = os.date("%H:%M"),
    tools = {},
  }
  table.insert(self.messages, self.current_stream)
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


--- Load session history from ~/.rta/sessions/ for the current project.
function RtaChat:load_history()
  self.history_sessions = {}
  local home = os.getenv("HOME") or ""
  local project = core.root_project()
  local cwd = project and project.path or ""
  if #cwd == 0 then return end

  local dir_name = cwd:gsub("^/", ""):gsub("/", "-")
  local sessions_dir = home .. "/.rta/sessions/" .. dir_name

  local handle = io.popen("ls -t " .. sessions_dir .. "/*.jsonl 2>/dev/null")
  if not handle then return end

  for line in handle:lines() do
    local f = io.open(line, "r")
    if f then
      local first = f:read("*l")
      f:close()
      if first then
        local ok, header = pcall(json.decode, first)
        if ok and header and header.type == "header" then
          local ts = header.timestamp or ""
          local short_ts = ts:sub(1, 16):gsub("T", " ")
          local short_id = (header.id or "?"):sub(1, 8)
          local preview = ""
          local f2 = io.open(line, "r")
          if f2 then
            for l in f2:lines() do
              local ok2, entry = pcall(json.decode, l)
              if ok2 and entry and entry.type == "message" and entry.message and entry.message.role == "user" then
                local content = entry.message.content
                if type(content) == "string" then
                  preview = content:sub(1, 40)
                end
                break
              end
            end
            f2:close()
          end
          table.insert(self.history_sessions, {
            id = header.id,
            display = short_ts .. "  " .. short_id,
            preview = preview,
            path = line,
          })
        end
      end
    end
  end
  handle:close()
end


--- Start a new session (kill current process, clear messages).
function RtaChat:new_session()
  if self.proc and self.proc:running() then
    self.proc.stdin:write(json.encode({type = "cancel"}) .. "\n")
    self.proc:wait(0.5)
  end
  self.proc = nil
  self.reader_thread = nil
  self.session_id = nil
  self.messages = {}
  self.streaming = false
  self.current_stream = nil
  self.pending_approvals = {}
  self.show_history = false

  if self.rta_path then
    table.insert(self.messages, {
      role = "system",
      text = "New session started.",
      time = os.date("%H:%M"),
    })
    self:start_process()
  end
  core.redraw = true
end


--- Resume a session by sending a continue request.
function RtaChat:resume_session(session_id)
  self.show_history = false
  self.messages = {}
  self.session_id = session_id
  self.streaming = false
  self.current_stream = nil
  self.pending_approvals = {}

  -- Find and read the session file directly
  local home = os.getenv("HOME") or ""
  local project = core.root_project()
  local cwd = project and project.path or ""
  if #cwd == 0 then return end

  local dir_name = cwd:gsub("^/", ""):gsub("/", "-")
  local sessions_dir = home .. "/.rta/sessions/" .. dir_name

  -- Find the session file by ID
  local handle = io.popen("ls " .. sessions_dir .. "/*.jsonl 2>/dev/null")
  if not handle then return end

  local session_file
  for line in handle:lines() do
    if line:find(session_id, 1, true) then
      session_file = line
      break
    end
  end
  handle:close()

  if not session_file then
    table.insert(self.messages, {
      role = "system",
      text = "Session file not found.",
      time = os.date("%H:%M"),
    })
    core.redraw = true
    return
  end

  -- Read the session JSONL and populate messages
  local f = io.open(session_file, "r")
  if f then
    for line in f:lines() do
      local ok, entry = pcall(json.decode, line)
      if ok and entry then
        if entry.type == "message" and entry.message then
          local role = entry.message.role
          if role == "user" or role == "assistant" then
            local content = entry.message.content
            local text = ""
            if type(content) == "string" then
              text = content
            elseif type(content) == "table" then
              -- Handle array of content parts
              local parts = {}
              for _, part in ipairs(content) do
                if type(part) == "table" and part.type == "text" and part.text then
                  parts[#parts + 1] = part.text
                end
              end
              text = table.concat(parts, "")
            end
            if #text > 0 then
              table.insert(self.messages, {
                role = role,
                text = text,
                time = os.date("%H:%M"),
              })
            end
          end
        end
      end
    end
    f:close()
  end

  -- Ensure process is running for new messages
  if not self.proc or not self.proc:running() then
    self:start_process()
  end

  core.redraw = true
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
  local toolbar_h = style.font:get_height() + style.padding.y * 2
  local msg_start_y = self.position.y + style.padding.y

  -- Messages (clipped to exclude toolbar and input)
  local y = msg_start_y - self.scroll.y
  local clip_h = self.size.y - self:get_input_height() - toolbar_h - style.divider_size * 2
  core.push_clip_rect(self.position.x, self.position.y, w, clip_h)

  for _, msg in ipairs(self.messages) do
    local mlh = self:get_line_height_msg(msg)
    local msg_top = y
    local msg_bottom = y + mlh
    if msg_bottom > self.position.y and msg_top < self.position.y + self.size.y - input_h then
      local pad = style.padding.x
      local text_w = w - pad * 2

      -- Calculate actual text height
      local text_h = 0
      if #msg.text > 0 and text_w > 0 then
        local remaining = msg.text
        while #remaining > 0 do
          local cut = remaining
          while #cut > 0 and style.font:get_width(cut) > text_w do
            cut = cut:sub(1, -2)
          end
          if #cut == 0 then cut = remaining:sub(1, 1); remaining = remaining:sub(2)
          else remaining = remaining:sub(#cut + 1) end
          text_h = text_h + style.font:get_height() + style.padding.y
        end
      else
        text_h = style.font:get_height() + style.padding.y
      end

      -- Calculate tool height
      local tools_h = 0
      if msg.tools and #msg.tools > 0 then
        tools_h = #msg.tools * lh + style.padding.y
      end

      mlh = text_h + tools_h + style.padding.y * 2

      -- Separator line between messages
      if _ ~= 1 then
        renderer.draw_rect(self.position.x + pad, msg_top, text_w, style.divider_size, style.divider)
      end

      if msg.role == "user" then
        -- User: indented, selection bg, accent text
        renderer.draw_rect(self.position.x + 6, msg_top, w - 12, mlh, style.selection)
        renderer.draw_rect(self.position.x + 6, msg_top, 3, mlh, style.accent)
        common.draw_text(style.font, style.accent, "you", nil,
          self.position.x + pad + 6, msg_top + style.padding.y * 0.3, text_w, style.font:get_height())
        draw_wrapped_text(style.font, style.accent, msg.text,
          self.position.x + pad + 6, msg_top + style.padding.y * 0.3 + style.font:get_height(), text_w, style.font:get_height() + style.padding.y)

      elseif msg.role == "assistant" then
        -- Assistant: full width, left accent bar
        renderer.draw_rect(self.position.x, msg_top, 3, mlh, style.accent)
        if #msg.text > 0 then
          draw_wrapped_text(style.font, style.text, msg.text,
            self.position.x + pad, msg_top + style.padding.y * 0.5, text_w, style.font:get_height() + style.padding.y)
        end

      else
        -- System: dim centered
        common.draw_text(style.font, style.dim, msg.text, "center",
          self.position.x + pad, msg_top + style.padding.y * 0.5, text_w, style.font:get_height())
      end

      -- Tool indicators below text
      if msg.tools and #msg.tools > 0 then
        local ty = msg_top + text_h + style.padding.y * 0.5
        for _, tool in ipairs(msg.tools) do
          local icon = tool.status == "running" and "~" or "+"
          local color = tool.status == "running" and style.warn or style.good
          local label = string.format("[%s %s]", icon, tool.name)
          if tool.display and #tool.display > 0 then
            label = label .. " " .. tool.display:sub(1, 40)
          end
          renderer.draw_rect(self.position.x + pad, ty, text_w, lh, style.background3)
          common.draw_text(style.font, color, label, nil,
            self.position.x + pad + style.padding.x * 0.5, ty, text_w - style.padding.x, lh)
          ty = ty + lh
        end
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

  -- History panel overlay
  if self.show_history then
    local panel_h = self.size.y - input_h - toolbar_h
    renderer.draw_rect(self.position.x, self.position.y, w, panel_h, style.background)

    local title_h = style.font:get_height() + style.padding.y * 2
    common.draw_text(style.font, style.accent, "Session History", nil,
      self.position.x + style.padding.x, self.position.y + style.padding.y, w - style.padding.x * 2, title_h)

    renderer.draw_rect(self.position.x, self.position.y + title_h, w, style.divider_size, style.divider)

    self.history_hover = -1
    local item_y = self.position.y + title_h + style.padding.y
    local item_h = style.font:get_height() + style.padding.y
    if #self.history_sessions == 0 then
      common.draw_text(style.font, style.dim, "No sessions found.", nil,
        self.position.x + style.padding.x, item_y, w - style.padding.x * 2, item_h)
    else
      for i, sess in ipairs(self.history_sessions) do
        local is_hover = (self.mouse_y >= item_y and self.mouse_y < item_y + item_h)
        if is_hover then
          self.history_hover = i
          renderer.draw_rect(self.position.x, item_y, w, item_h, style.selection)
        end
        local col = is_hover and style.accent or style.text
        local label = sess.display
        if sess.preview and #sess.preview > 0 then
          label = label .. "  " .. sess.preview
        end
        common.draw_text(style.font, col, label, nil,
          self.position.x + style.padding.x, item_y, w - style.padding.x * 2, item_h)
        item_y = item_y + item_h
      end
    end
  end

  -- Toolbar: sits just above input area
  local toolbar_h = style.font:get_height() + style.padding.y * 2
  local input_top = self.position.y + self.size.y - input_h
  local toolbar_top = input_top - style.divider_size - toolbar_h

  -- Divider between toolbar and input
  renderer.draw_rect(self.position.x, input_top - style.divider_size, w, style.divider_size, style.divider)

  -- Toolbar background
  renderer.draw_rect(self.position.x, toolbar_top, w, toolbar_h, style.background3)

  -- Toolbar buttons: [+] (new session) and [=] (history)
  local icon_size = style.font:get_height()
  local icon_y = toolbar_top + (toolbar_h - icon_size) / 2

  -- + icon (new session)
  local plus_x = self.position.x + style.padding.x
  common.draw_text(style.font, style.dim, "+", nil, plus_x, icon_y, icon_size, icon_size)

  -- = icon (history) - using ASCII = that renders in all fonts
  local hist_x = plus_x + icon_size + style.padding.x * 2
  local hist_color = self.show_history and style.accent or style.dim
  common.draw_text(style.font, hist_color, "~", nil, hist_x, icon_y, icon_size, icon_size)

  -- Input area (at bottom, below toolbar)
  local input_area_y = self.position.y + self.size.y - input_h
  renderer.draw_rect(self.position.x, input_area_y, w, input_h, self.input_focused and style.background or style.background3)

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
if node then
  chat_view.node = node:split("right", chat_view, {x = true}, true)
end


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
    if v.show_history then
      v.show_history = false
      core.redraw = true
    else
      v:cancel_operation()
    end
  end,
})

command.add(nil, {
  ["rta-chat:toggle"] = function()
    chat_view.visible = not chat_view.visible
    core.redraw = true
  end,
  ["rta-chat:new-session"] = function()
    chat_view:new_session()
  end,
  ["rta-chat:history"] = function()
    chat_view.show_history = not chat_view.show_history
    if chat_view.show_history then
      chat_view:load_history()
    end
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
