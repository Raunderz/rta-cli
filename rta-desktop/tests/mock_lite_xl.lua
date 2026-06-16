-- Minimal mock of Lite XL runtime for testing rta_chat.lua functions.
-- Intercepts require() calls so rta_chat.lua can load without the real editor.

local M = {}

-- Shared state for test assertions
M.state = {
  log_messages = {},
  redraw_count = 0,
  active_view = nil,
  clip_rects = {},
  drawn_rects = {},
  drawn_text = {},
  threads = {},
}

function M.reset()
  M.state = {
    log_messages = {},
    redraw_count = 0,
    active_view = nil,
    clip_rects = {},
    drawn_rects = {},
    drawn_text = {},
    threads = {},
  }
end

-- Font mock: tracks calls, returns predictable widths/heights
local FONT = {
  _height = 16,
  _widths = {},
  get_height = function(self) return self._height end,
  get_width = function(self, text) return self._widths[text] or (#text * 8) end,
}

-- Style mock
local STYLE = {
  font = FONT,
  padding = { x = 8, y = 4 },
  background = { 0.1, 0.1, 0.1 },
  background2 = { 0.12, 0.12, 0.12 },
  background3 = { 0.15, 0.15, 0.15 },
  text = { 0.9, 0.9, 0.9 },
  dim = { 0.5, 0.5, 0.5, 1.0 },
  accent = { 0.3, 0.6, 1.0 },
  selection = { 0.2, 0.3, 0.5 },
  warn = { 1.0, 0.6, 0.2 },
  good = { 0.2, 0.8, 0.3 },
  caret = { 0.9, 0.9, 0.9 },
  caret_width = 2,
  divider = { 0.3, 0.3, 0.3 },
  divider_size = 1,
  scale = 1,
  scrollbar = { 0.3, 0.3, 0.3 },
  scrollbar2 = { 0.4, 0.4, 0.4 },
  drag_overlay = { 0.2, 0.2, 0.3 },
  line_limit = 80,
  syntax = { normal = { 0.9, 0.9, 0.9 } },
  expanded_scrollbar_size = 10,
  syntax_fonts = {},
  code_font = FONT,
}

-- Renderer mock
local RENDERER = {
  draw_rect = function(x, y, w, h, color)
    table.insert(M.state.drawn_rects, { x = x, y = y, w = w, h = h, color = color })
  end,
  draw_text = function(font, text, x, y, color)
    table.insert(M.state.drawn_text, { font = font, text = text, x = x, y = y, color = color })
  end,
}

-- Core mock
local CORE = {
  log = function(msg, ...)
    if ... then msg = string.format(msg, ...) end
    table.insert(M.state.log_messages, msg)
  end,
  redraw = false,
  set_active_view = function(view) M.state.active_view = view end,
  add_thread = function(fn)
    local id = #M.state.threads + 1
    M.state.threads[id] = { fn = fn, cr = coroutine.create(fn) }
    return id
  end,
  push_clip_rect = function(x, y, w, h)
    table.insert(M.state.clip_rects, { x = x, y = y, w = w, h = h })
  end,
  pop_clip_rect = function()
    table.remove(M.state.clip_rects)
  end,
  root_view = {
    root_node = {
      type = "leaf",
      locked = false,
      split = function(self, dir, view, opts, locked)
        local node = { type = "leaf", locked = locked, view = view }
        if view then view.node = node end
        return node
      end,
      close_view = function(self, root, view) end,
    },
    get_active_node = function(self)
      return self.root_node
    end,
  },
  root_project = function()
    return { path = "/test/project" }
  end,
  STEP_SIZE = 1 / 60,
}

-- Object/View mock (minimal)
local View = {}
View.__index = View
function View:extend()
  local cls = setmetatable({}, {
    __index = self,
    __call = function(c, ...)
      return c:new(...)
    end,
  })
  cls.__index = cls
  cls.super = self
  return cls
end
function View:new(o)
  local obj = o or setmetatable({}, { __index = self })
  obj.size = obj.size or { x = 0, y = 0 }
  obj.position = obj.position or { x = 0, y = 0 }
  obj.scroll = obj.scroll or { x = 0, y = 0, to = { x = 0, y = 0 } }
  obj.scrollable = false
  return obj
end

function View:extend()
  local parent = self
  local cls = setmetatable({}, {
    __index = parent,
  })
  cls.__index = cls
  cls.super = parent

  -- Wrap __call to always return the constructed instance
  local mt = getmetatable(cls)
  mt.__call = function(c, ...)
    -- Create the instance with correct metatable
    local obj = setmetatable({}, c)
    obj.size = { x = 0, y = 0 }
    obj.position = { x = 0, y = 0 }
    obj.scroll = { x = 0, y = 0, to = { x = 0, y = 0 } }
    obj.scrollable = false
    -- Call the actual new() (which may be overridden by the subclass)
    -- We need to call it with obj as self
    local new_fn = rawget(c, "new")
    if new_fn then
      new_fn(obj, ...)
    end
    return obj
  end

  return cls
end
function View:move_towards(obj, key, dest)
  obj[key] = dest
end
function View:update() end
function View:draw() end
function View:draw_background() end
function View:draw_scrollbar() end
function View:get_content_offset() return 0, 0 end
function View:supports_text_input() return false end
function View:on_text_input() end
function View:on_mouse_moved() end
function View:on_mouse_pressed() return false end

-- Common mock
local COMMON = {
  merge = function(defaults, overrides)
    local result = {}
    for k, v in pairs(defaults) do result[k] = v end
    if overrides then
      for k, v in pairs(overrides) do result[k] = v end
    end
    return result
  end,
  draw_text = function(font, color, text, align, x, y, w, h)
    table.insert(M.state.drawn_text, { font = font, text = text, x = x, y = y, color = color, align = align })
  end,
  splice = function(t, i, rem, ...)
    for j = 1, rem do table.remove(t, i) end
    local args = { ... }
    for j = #args, 1, -1 do table.insert(t, i, args[j]) end
  end,
}

-- Process mock
local PROCESS = {}
PROCESS.last_started = nil
PROCESS.start = function(command)
  PROCESS.last_started = command
  return {
    stdin = {
      write = function(self, data) end,
    },
    stdout = {
      read = function(self, mode) return nil end,
    },
    running = function(self) return true end,
    wait = function(self, timeout) return 0 end,
  }
end

-- Config mock
local CONFIG = {
  plugins = {
    rta_chat = {
      size = 340,
      visible = true,
    },
  },
}

-- Command mock
local COMMAND = {
  commands = {},
}
COMMAND.add = function(predicate, cmds)
  for name, fn in pairs(cmds) do
    COMMAND.commands[name] = fn
  end
end

-- Keymap mock
local KEYMAP = {
  bindings = {},
}
KEYMAP.add = function(bindings)
  for key, cmd in pairs(bindings) do
    KEYMAP.bindings[key] = cmd
  end
end

-- json mock (thin wrapper around dkjson or hand-rolled)
local JSON = {
  decode = function(str)
    -- Use load() to eval a simplified JSON-like format, or error
    -- For tests, we pre-populate this per-test
    error("json.decode not mocked for this test")
  end,
  encode = function(obj)
    return "{}"
  end,
}

-- LogView mock
local LogView_cls = View:extend()
function LogView_cls:new()
  local obj = View.new(self)
  return obj
end

-- Global SCALE (Lite XL default)
SCALE = SCALE or 1
renderer = renderer or {}
system = system or {}
renderer.draw_rect = renderer.draw_rect or function(x, y, w, h, color)
  table.insert(M.state.drawn_rects, { x = x, y = y, w = w, h = h, color = color })
end
renderer.draw_text = renderer.draw_text or function(font, text, x, y, color)
  table.insert(M.state.drawn_text, { font = font, text = text, x = x, y = y, color = color })
end

-- System mock (global)
system.get_window_mode = system.get_window_mode or function() return "normal" end
system.set_window_mode = system.set_window_mode or function(mode) end
system.absolute_path = system.absolute_path or function(p) return p end
system.get_process_id = system.get_process_id or function() return 0 end
system.path_compare = system.path_compare or function(a, b) return a < b end
system.sleep = system.sleep or function(t) end
system.wait_event = system.wait_event or function(t) end
system.raise_window = system.raise_window or function() end

-- Regex mock (global)
regex = regex or {}
regex.compile = regex.compile or function(pattern) return pattern end
regex.find_offsets = regex.find_offsets or function(r, str) return nil end
regex.match = regex.match or function() return nil end
regex.gmatch = regex.gmatch or function() return function() end end
regex.gsub = regex.gsub or function(s, p, r) return s, 0 end

-- System mock
local SYSTEM = {
  get_window_mode = function() return "normal" end,
  set_window_mode = function(mode) end,
  absolute_path = function(p) return p end,
  get_process_id = function() return 0 end,
  path_compare = function(a, b) return a < b end,
  sleep = function(t) end,
  wait_event = function(t) end,
  raise_window = function() end,
}

-- Regex mock
local REGEX = {
  compile = function(pattern) return pattern end,
  find_offsets = function(regex, str) return nil end,
  match = function() return nil end,
  gmatch = function() return function() end end,
  gsub = function(s, p, r) return s, 0 end,
}

-- Install package.preload interceptors
local function install_mocks()
  package.preload["core"] = function() return CORE end
  package.preload["core.common"] = function() return COMMON end
  package.preload["core.command"] = function() return COMMAND end
  package.preload["core.config"] = function() return CONFIG end
  package.preload["core.keymap"] = function() return KEYMAP end
  package.preload["core.style"] = function() return STYLE end
  package.preload["core.view"] = function() return View end
  package.preload["core.process"] = function() return PROCESS end
  package.preload["core.logview"] = function() return LogView_cls end
  package.preload["core.json"] = function() return JSON end
  package.preload["system"] = function() return SYSTEM end
  package.preload["regex"] = function() return REGEX end
  package.preload["core.status_view"] = function()
    return { visible = true, add_item = function() end, separator2 = "|" }
  end
end

-- Expose internals for test setup
M.core = CORE
M.style = STYLE
M.renderer = RENDERER
M.font = FONT
M.common = COMMON
M.process = PROCESS
M.config = CONFIG
M.command = COMMAND
M.keymap = KEYMAP
M.json = JSON
M.View = View
M.LogView = LogView_cls
M.SYSTEM = SYSTEM
M.REGEX = REGEX
M.install = install_mocks

return M
