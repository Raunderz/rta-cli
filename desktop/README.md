# RTA Desktop

A fast, lightweight desktop application built with Tauri, Bun, Preact.js, and Tailwind CSS.

## Tech Stack

- **Tauri** - Desktop application framework
- **Bun** - Package manager and runtime
- **Preact.js** - Lightweight React alternative
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Build tool

## Project Structure

```
desktop/
├── src/                          # 🎨 FRONTEND - Preact.js application
│   ├── App.jsx                  # Main app component with splash screen logic
│   ├── main.jsx                 # Entry point (renders app to DOM)
│   ├── index.css                # Global styles + Tailwind + animations
│   └── pages/                   # Page components
│       └── LandingPage.jsx      # Home/landing page with hero + features
│
├── src-tauri/                    # ⚙️ BACKEND - Tauri/Rust desktop wrapper
│   ├── main.rs                  # Rust binary entry point
│   ├── lib.rs                   # Rust library (for mobile support)
│   ├── build.rs                 # Build script for Tauri
│   ├── Cargo.toml               # Rust dependencies + build profile
│   ├── tauri.conf.json          # Tauri app config (window, build, bundle)
│   │
│   ├── capabilities/            # 🔒 Security permissions
│   │   └── default.json         # Allowed Tauri APIs
│   │
│   ├── icons/                   # 🖼️ App icons (must be RGBA PNGs)
│   │   ├── 32x32.png           # Taskbar/tray icon
│   │   ├── 128x128.png         # Standard icon
│   │   ├── 128x128@2x.png      # Retina display icon
│   │   ├── icon.ico            # Windows icon
│   │   └── icon.icns           # MacOS icon
│   │
│   └── target/                  # 🚫 BUILD OUTPUT (gitignored)
│       └── release/bundle/      # Final distributable binaries
│
├── dist/                         # 🚫 BUILD OUTPUT (gitignored)
│   └── index.html               # Bundled frontend
│   └── assets/                  # Minified JS + CSS
│
├── node_modules/                 # 🚫 DEPENDENCIES (gitignored)
│
├── index.html                    # HTML entry point
├── vite.config.js               # Vite config (dev server, build, plugins)
├── tailwind.config.js           # Tailwind config (content paths, theme)
├── postcss.config.js            # PostCSS config (Tailwind + autoprefixer)
├── package.json                 # Project metadata + scripts + dependencies
└── .gitignore                   # Files to exclude from git
```

## Folder Guide

| Folder | Purpose | Safe to Commit? |
|--------|---------|-----------------|
| `src/` | Your frontend code (Preact components, styles) | ✅ Yes |
| `src-tauri/` | Tauri backend (Rust code, config, icons) | ✅ Yes |
| `src-tauri/capabilities/` | Security permissions for Tauri APIs | ✅ Yes |
| `src-tauri/icons/` | App icons for different platforms | ✅ Yes |
| `src-tauri/target/` | Compiled Rust binaries | ❌ No (gitignored) |
| `src-tauri/gen/` | Auto-generated Tauri code | ❌ No (gitignored) |
| `dist/` | Production build output | ❌ No (gitignored) |
| `node_modules/` | Installed dependencies | ❌ No (gitignored) |

## How to Run

### First Time Setup

```bash
# 1. Navigate to desktop folder
cd desktop

# 2. Install dependencies
bun install

# 3. Make sure Rust is installed
# If not: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Development Mode (with hot reload)

```bash
bun run tauri:dev
```

This will:
1. Start Vite dev server on `http://localhost:1420`
2. Launch the Tauri desktop window
3. Auto-reload on file changes

### Just Frontend Dev Server (no desktop window)

```bash
bun run dev
```

Open `http://localhost:1420` in your browser to preview.

### Production Build

```bash
# Build frontend only
bun run build

# Build full desktop app (creates installable binary)
bun run tauri:build
```

After `bun run tauri:build`, your app will be in:
- **Linux**: `src-tauri/target/release/bundle/deb/` or `appimage/`
- **MacOS**: `src-tauri/target/release/bundle/macos/`
- **Windows**: `src-tauri/target/release/bundle/msi/` or `nsis/`

### Preview Production Build

```bash
bun run preview
```

## Available Scripts

| Command | What it does |
|---------|--------------|
| `bun run dev` | Start Vite dev server (frontend only) |
| `bun run build` | Build frontend for production |
| `bun run preview` | Preview production build locally |
| `bun run tauri:dev` | **Run desktop app with hot reload** |
| `bun run tauri:build` | **Build desktop app for distribution** |
| `bun run tauri` | Access Tauri CLI directly |

## Features

- ⚡ Fast startup with animated splash screen
- 🪶 Lightweight (< 20KB JS bundle gzipped)
- 🎨 Modern UI with Tailwind CSS
- 🔄 Hot reload in development
- 📦 Native desktop app capabilities
- 🚀 Optimized build with LTO + size optimization

## License

MIT
