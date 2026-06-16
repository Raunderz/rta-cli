# RTA Mobile

React Native (Expo) mobile app for the RTA AI coding platform. Thin client that connects to the Go execution service for cloud coding sessions.

## Features

- **AI Chat** — send prompts to the agent running inside a cloud container
- **Code Editor** — CodeMirror 6 with syntax highlighting (Python, JS, HTML, CSS)
- **Terminal** — xterm.js WebView with WebSocket PTY
- **File Browser** — local file tree with expo-file-system
- **Git** — offline git operations via isomorphic-git (init, status, add, commit, log)
- **Session Sync** — ZIP upload/download for container ↔ mobile file sync
- **Preview Tunnel** — cloudflared URLs for web server preview

## Prerequisites

- [Bun](https://bun.sh) (recommended) or npm
- Expo CLI (`bun install -g expo-cli`)
- Android Studio (for Android) or Xcode (for iOS)
- RTA backend running (for auth + AI)

## Setup

```bash
cd app
bun install
```

## Running

```bash
# Start Expo dev server
bun run start

# Run on Android
bun run android

# Run on iOS
bun run ios

# Run on web (for testing)
bun run web
```

## Project Structure

```
app/
├── src/
│   ├── components/
│   │   ├── Chat.js            # AI chat with streaming
│   │   ├── Editor.js          # CodeMirror 6 editor
│   │   ├── Files.js           # File browser
│   │   ├── Terminal.js        # xterm.js terminal
│   │   ├── GitUI.js           # Git operations (status, commit, log)
│   │   └── ConflictResolver.js # Merge conflict UI
│   ├── utils/
│   │   ├── backend.js         # API client for RTA backend
│   │   └── workspaceSync.js   # ZIP sync with Go executor
│   ├── App.js                 # Root component, session lifecycle
│   └── index.js               # Entry point
├── android/                   # Android native project
├── assets/                    # Icons, splash screens
├── app.json                   # Expo config
├── package.json
└── eas.json                   # EAS Build config
```

## Architecture

```
Mobile App (Expo)
    ↓ HTTP/WebSocket
FastAPI Backend (auth, API keys)
    ↓
Go Executor Service (Docker lifecycle)
    ↓
Docker Container (rta CLI + user code)
```

The app is a thin client. All heavy lifting (AI inference, code execution, container management) happens on the server side.

## Environment

Create a `.env` file:

```
EXPO_PUBLIC_API_URL=https://your-backend-url
```

## Building

### Development Build

```bash
eas build --profile development --platform android
```

### Production Build

```bash
eas build --profile production --platform android
```

## Dependencies

| Package | Purpose |
|---------|---------|
| expo | React Native framework |
| react-native-webview | Terminal xterm.js |
| isomorphic-git | Offline git operations |
| expo-file-system | Local file storage |
| expo-secure-store | Secure credential storage |
| @codemirror/* | Code editor |
| jszip | ZIP sync with container |

## License

MIT
