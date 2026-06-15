# RTA Desktop (Lite XL)

RTA Desktop is a lightweight, AI-powered IDE based on [Lite XL](https://github.com/lite-xl/lite-xl), powered by the RTA Python CLI.

## Overview

RTA Desktop pivots from the heavy Eclipse Theia architecture to Lite XL to provide a faster, more stable, and more responsive development experience.

- **Frontend**: Lite XL (C/Lua)
- **Engine**: RTA Python CLI (`rta` binary)
- **Integration**: Lua plugins connecting Lite XL to the CLI via JSON-lines pipe IPC.

## Project Structure

- `bin/`: RTA CLI binary (gitignored, built from `cli/` source)
- `src/`: Lite XL core C source code.
- `data/`: Lite XL Lua core and plugins.
- `data/plugins/rta_chat.lua`: Chat plugin for RTA CLI integration.

## Quick Start

### Prerequisites

You will need the following tools installed:

- Meson (>=0.63)
- Ninja
- SDL2 (or SDL3 depending on the version)
- PCRE2
- FreeType2
- Lua 5.4
- A working C compiler (GCC / Clang)
- RTA CLI (`rta` binary, built from `cli/` source)

### Building RTA Desktop (Lite XL)

1. **Install Build Tools**: Ensure you have `meson`, `ninja`, and a C compiler (GCC/Clang) installed on your system.
2. **Setup Build Directory**:
   ```bash
   meson setup build --wrap-mode=forcefallback
   ```
   *Note: `--wrap-mode=forcefallback` ensures all dependencies like Lua, PCRE2, and FreeType2 are downloaded and built statically if not found on your system.*
3. **Compile**:
   ```bash
   meson compile -C build
   ```
4. **Run**:
   ```bash
   ./build/src/rta-desktop
   ```

### Building the RTA CLI

The CLI is a Python binary built from the `cli/` source directory.

1. **Build**: From the `cli/` directory:
   ```bash
   cd ../cli
   uv run python -m PyInstaller --clean --noconfirm rta.spec
   cp dist/rta ../rta-desktop/bin/rta
   ```
2. The binary is placed at `bin/rta` (gitignored).

## Proceeding Further

- **Lua Plugins**: The chat integration logic is in `data/plugins/rta_chat.lua`.
- **UI Customization**: Use `data/core/style.lua` to adjust colors and fonts to match RTA branding.

## License

MIT
