# RTA Desktop Development

## Setup
Project use Nix for environment.

1. **Install Nix** if not present.
2. **Enable Flakes** in Nix config.

## Launch Steps

### 1. Build
Build once or after dependency changes:
```bash
nix develop --command npm install
```

### 2. Run Electron (Desktop)
```bash
nix develop --command npm run start:electron
```

### 3. Run Browser (Web)
```bash
nix develop --command npm run start:browser
```
Access at `http://localhost:3000`

## Troubleshooting
If `electron-rebuild` fail with "Permission denied":
```bash
chmod +x node_modules/@electron/rebuild/lib/cli.js
```
