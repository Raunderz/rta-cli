---
slug: mobile-terminal-keyboard
title: "The Mobile Terminal Keyboard Odyssey"
date: "May 28, 2026"
readTime: "6 min read"
excerpt: "Getting Android to show a keyboard inside a WebView terminal took longer than building the entire backend. Here is the full saga."
tags: ["Mobile", "Android", "Terminal", "WebView"]
---

# The Mobile Terminal Keyboard Odyssey

This is the story of how something as simple as a keyboard almost broke us.

We built a cloud terminal — bash inside a Docker container, streamed over WebSocket, rendered in a React Native WebView with xterm.js. The container orchestration runs on a [Go-based backend](https://schallten.github.io/container-provider/) (basic version is open source). The desktop version works on the first try. The mobile version took four full rewrites and a descent into the deepest corners of Android WebView.

Here is everything that went wrong and how we fixed it.

## Act 1: It Does Not Connect

The first problem was the easiest. The WebSocket URL was wrong.

We have a backend that manages the Docker containers and a proxy layer in front of it. The WebSocket URL our app was constructing didn't match the proxy's routing — it pointed at the wrong path. The proxy itself also had a routing bug where it forwarded connections to the wrong upstream endpoint.

Fix: align the URL path in the app with the proxy's routes, and fix the proxy's upstream path.

Result: WebSocket connects. Terminal displays output. We can see neofetch running on a phone. Victory lap? Not yet. We cannot type a single character.

## Act 2: The TextInput Trap

The obvious approach: put a \`TextInput\` overlay on top of the WebView, capture keystrokes, and forward them to the WebSocket.

\`\`\`jsx
<TextInput
  style={{ position: 'absolute', left: 0, top: 0, width: 1, height: 1, opacity: 0.01 }}
  onChangeText={(text) => ws.send(text)}
/>
\`\`\`

The cursor bleeds through the transparent overlay. You set \`color: transparent\` — the cursor is still there, a blinking vertical line floating on top of your terminal emulator. Set \`caretHidden={true}\` — gone. But now the input itself is unreliable. Sometimes keystrokes arrive, sometimes they disappear into the void. The \`TextInput\` overlay has a mind of its own.

We tried everything: \`pointerEvents\