# RTA Desktop (Lite XL)

RTA Desktop is a lightweight, AI-powered IDE based on [Lite XL](https://github.com/lite-xl/lite-xl) and powered by the [RTA Agent (Odin)](./agent-odin).

## Overview

RTA Desktop pivots from the heavy Eclipse Theia architecture to Lite XL to provide a faster, more stable, and more responsive development experience.

- **Frontend**: Lite XL (C/Lua)
- **Engine**: RTA Agent (Odin)
- **Integration**: Lua plugins connecting Lite XL to the Odin-based agent.

## Project Structure

- `agent-odin/`: Source code for the RTA Agent in Odin.
- `src/`: Lite XL core C source code.
- `data/`: Lite XL Lua core and plugins.
- `migration_plan.md`: The roadmap for the transition from Theia to Lite XL.

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
- Odin (for the agent)

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

### Building the RTA Agent (Odin)

The agent is located in the `agent-odin` directory.

1. **Install Odin**: Ensure the [Odin compiler](https://odin-lang.org/) is installed.
2. **Build**:
   ```bash
   cd agent-odin
   odin build src -out:rta-agent -o:speed
   ```
   *Note: The agent is currently a standalone binary that will be integrated into the IDE via Lua plugins.*

## Proceeding Further

- **Lua Plugins**: The core integration logic should be placed in `data/plugins/rta_agent.lua`.
- **UI Customization**: Use `data/core/style.lua` to adjust colors and fonts to match RTA branding.
- **Odin Development**: Follow the `agent-odin/after_migration.md` plan to implement the agent's core loop and tools.

## License

MIT
