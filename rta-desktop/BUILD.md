# Building RTA Desktop

## Prerequisites

| Tool       | Version   |
|------------|-----------|
| Meson      | >= 0.63   |
| Ninja      | any       |
| C compiler | GCC / Clang |
| SDL3       | >= 3.2.8  |
| PCRE2      | any       |
| FreeType2  | any       |
| Lua 5.4    | any       |

System libraries can be installed via your package manager, or Meson will download and build them statically using `--wrap-mode=forcefallback`.

---

## Linux

### Quick build

```bash
# from the project root
meson setup build
meson compile -C build

# symlink data so the binary finds start.lua at runtime
ln -sf ../../data build/src/data

# run
./build/src/rta-desktop
```

### Using the build script

```bash
./scripts/build.sh
```

This runs `meson setup` + `meson compile` with release defaults and automatically creates the data symlink. See `./scripts/build.sh --help` for options (debug mode, PGO, LTO, portable packages, etc.).

### Installing system-wide

```bash
meson setup build --prefix=/usr
meson compile -C build
meson install -C build
rta-desktop
```

### Static dependencies (no system libraries required)

```bash
meson setup build --wrap-mode=forcefallback
meson compile -C build
```

This downloads and builds SDL3, PCRE2, FreeType2, and Lua statically.

---

## Windows

### Using MSYS2 / MinGW

1. Install [MSYS2](https://www.msys2.org/) and open the **UCRT64** environment.

2. Install dependencies:
   ```bash
   pacman -S --needed git mingw-w64-ucrt-x86_64-{meson,ninja,gcc,pcre2,freetype,lua51,curl,cmake}
   ```

3. Build:
   ```bash
   cd rta-desktop
   meson setup build
   meson compile -C build
   ```

4. The binary is at `build/rta-desktop.exe`. On Windows the build automatically enables portable mode, so data is embedded relative to the exe. Run directly:
   ```bash
   ./build/rta-desktop.exe
   ```

### Cross-compile from Linux

A cross-file for `darwin-aarch64` is in `resources/cross/`. Add your own for Windows targets:
```bash
meson setup build --cross-file resources/cross/my-windows-crossfile.txt
```

---

## Running from the build tree

The binary looks for `data/core/start.lua` relative to its own directory. After building, create a symlink (Linux/macOS) or copy (Windows):

```bash
# Linux / macOS
ln -sf ../../data build/src/data

# or copy instead
cp -r data build/src/data
```

The build script (`scripts/build.sh`) does this automatically.

---

## Build options

See `meson_options.txt`:

| Option              | Type    | Default | Description                             |
|---------------------|---------|---------|-----------------------------------------|
| `bundle`            | boolean | false   | Build a macOS .app bundle               |
| `portable`          | boolean | false   | Portable install (auto on Windows)      |
| `renderer`          | boolean | false   | Use SDL renderer (auto on macOS)        |
| `use_system_lua`    | boolean | false   | Prefer system Lua over Meson wrap       |
| `bundle_plugins`    | array   | []      | Plugins to bundle at build time         |
| `arch_tuple`        | string  | ""      | Custom architecture tuple               |
| `dirmonitor_backend`| string  | auto    | File watcher backend                    |
