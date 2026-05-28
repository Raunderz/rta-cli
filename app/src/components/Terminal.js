import React, { useState, useEffect, useRef } from 'react';
import { 
  StyleSheet, 
  View, 
  Text, 
  Platform,
  TouchableOpacity,
  KeyboardAvoidingView
} from 'react-native';
import { WebView } from 'react-native-webview';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://divisive-herbs-jolly.ngrok-free.dev';

export default function Terminal({ session }) {
  const webViewRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState([]);

  const wsUrl = session.status === 'on' 
    ? BACKEND_URL.replace('http', 'ws') + `/v1/executor/ws/ws/env/${session.id}`
    : null;

  // The entire terminal UI lives inside the WebView HTML.
  // xterm.js handles its own input via an internal textarea.
  // We use click/touchend to call term.focus() which opens the keyboard.
  // keyboardDisplayRequiresUserAction={false} on the WebView allows this.
  const terminalHtml = `<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
  <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"><\/script>
  <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"><\/script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; width: 100%; overflow: hidden; background: #000; }
    body { display: flex; flex-direction: column; }
    #terminal-wrap { flex: 1; width: 100%; overflow: hidden; }
    #accessory-bar {
      height: 44px; min-height: 44px;
      background: #1e293b; border-top: 1px solid #334155;
      display: flex; flex-direction: row; align-items: center;
      overflow-x: auto; -webkit-overflow-scrolling: touch;
      white-space: nowrap; padding: 0 6px; gap: 6px;
    }
    #accessory-bar::-webkit-scrollbar { display: none; }
    .acc-btn {
      display: inline-flex; justify-content: center; align-items: center;
      padding: 5px 10px; border-radius: 4px;
      background: #0f172a; border: 1px solid #334155;
      color: #94a3b8; font-size: 11px; font-weight: bold; font-family: monospace;
      -webkit-user-select: none; user-select: none;
      -webkit-tap-highlight-color: transparent;
    }
    .acc-btn:active { background: #334155; }
  </style>
</head>
<body>
  <div id="terminal-wrap"></div>
  <div id="accessory-bar">
    <button class="acc-btn" id="btn-esc">ESC</button>
    <button class="acc-btn" id="btn-tab">TAB</button>
    <button class="acc-btn" id="btn-ctrlc">^C</button>
    <button class="acc-btn" id="btn-ctrld">^D</button>
    <button class="acc-btn" id="btn-up">▲</button>
    <button class="acc-btn" id="btn-down">▼</button>
    <button class="acc-btn" id="btn-left">◀</button>
    <button class="acc-btn" id="btn-right">▶</button>
  </div>

  <script>
    var log = function(m) {
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'log', message: m }));
    };

    var socket = null;

    var term = new Terminal({
      cursorBlink: true,
      fontSize: 13,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: { background: '#000000', foreground: '#ffffff', cursor: '#0ea5e9' },
      allowProposedApi: true
    });

    var fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    term.open(document.getElementById('terminal-wrap'));

    try { fitAddon.fit(); } catch(e) {}
    setTimeout(function() { try { fitAddon.fit(); } catch(e) {} }, 300);

    // xterm.js natively captures keystrokes via its internal textarea.
    // term.onData fires for every key the user types.
    term.onData(function(data) {
      log('In: ' + data.length);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(data);
      }
    });

    // Focus the terminal on tap. Using click satisfies mobile WebKit's
    // user-gesture requirement for opening the keyboard.
    document.getElementById('terminal-wrap').addEventListener('click', function() {
      term.focus();
    });
    // touchend fallback for Android WebViews
    document.getElementById('terminal-wrap').addEventListener('touchend', function(e) {
      e.preventDefault();
      term.focus();
    });

    function connect(url) {
      log('Conn: ' + url);
      if (socket) { try { socket.close(); } catch(e){} }
      term.reset();
      term.write('\\r\\n\\x1b[1;34m\\u26A1 Connecting to Rta Cloud...\\x1b[0m\\r\\n');

      socket = new WebSocket(url);
      socket.binaryType = 'arraybuffer';

      socket.onopen = function() {
        log('WS Open');
        term.write('\\x1b[1;32m\\u2713 Connected.\\x1b[0m\\r\\n');
        socket.send(JSON.stringify({ cols: term.cols, rows: term.rows }));
        setTimeout(function() { socket.send('neofetch\\n'); }, 1000);
        term.focus();
      };

      socket.onmessage = function(ev) {
        if (typeof ev.data === 'string') {
          term.write(ev.data);
        } else {
          term.write(new Uint8Array(ev.data));
        }
      };

      socket.onclose = function(e) {
        log('WS Closed: ' + e.code);
        term.write('\\r\\n\\x1b[1;31m\\uD83D\\uDED1 Disconnected (' + e.code + ')\\x1b[0m\\r\\n');
      };

      socket.onerror = function() { log('WS Error'); };
    }

    // Accessory bar: send control character then refocus terminal
    function sendAndFocus(data) {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(data);
      }
      term.focus();
    }

    document.getElementById('btn-esc').addEventListener('click', function(){ sendAndFocus('\\x1b'); });
    document.getElementById('btn-tab').addEventListener('click', function(){ sendAndFocus('\\t'); });
    document.getElementById('btn-ctrlc').addEventListener('click', function(){ sendAndFocus('\\x03'); });
    document.getElementById('btn-ctrld').addEventListener('click', function(){ sendAndFocus('\\x04'); });
    document.getElementById('btn-up').addEventListener('click', function(){ sendAndFocus('\\x1b[A'); });
    document.getElementById('btn-down').addEventListener('click', function(){ sendAndFocus('\\x1b[B'); });
    document.getElementById('btn-left').addEventListener('click', function(){ sendAndFocus('\\x1b[D'); });
    document.getElementById('btn-right').addEventListener('click', function(){ sendAndFocus('\\x1b[C'); });

    window.addEventListener('resize', function() {
      try { fitAddon.fit(); } catch(e) {}
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ cols: term.cols, rows: term.rows }));
      }
    });

    window.addEventListener('message', function(event) {
      try {
        var data = JSON.parse(event.data);
        if (data.type === 'connect') { connect(data.url); }
        if (data.type === 'focus') { term.focus(); }
      } catch(e) {}
    });

    log('Ready');
    window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'ready' }));
  <\/script>
</body>
</html>`;

  useEffect(() => {
    if (isLoaded && wsUrl) {
      webViewRef.current.postMessage(JSON.stringify({ type: 'connect', url: wsUrl }));
    }
  }, [wsUrl, isLoaded]);

  const onMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'ready') setIsLoaded(true);
      if (data.type === 'log') {
        setTerminalLogs(prev => [data.message, ...prev.slice(0, 5)]);
      }
    } catch(e) {}
  };

  const forceFocus = () => {
    webViewRef.current?.postMessage(JSON.stringify({ type: 'focus' }));
  };

  const reconnect = () => {
    if (wsUrl) {
      webViewRef.current.postMessage(JSON.stringify({ type: 'connect', url: wsUrl }));
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>bash terminal</Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            {session.status === 'on' ? (terminalLogs[0] || 'active') : 'offline'}
          </Text>
        </View>
        <View style={styles.actions}>
          {session.status === 'on' && (
            <>
              <TouchableOpacity style={styles.actionBtn} onPress={reconnect}>
                <Text style={styles.actionBtnText}>RETRY</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.actionBtn} onPress={forceFocus}>
                <Text style={styles.actionBtnText}>KEYBOARD</Text>
              </TouchableOpacity>
            </>
          )}
          <View style={[styles.statusBadge, session.status === 'on' ? styles.badgeOn : styles.badgeOff]}>
            <Text style={[styles.statusText, session.status === 'on' ? styles.statusTextOn : styles.statusTextOff]}>
              {session.status === 'on' ? 'CLOUD' : 'LOCAL'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.terminalContainer}>
        {session.status === 'off' ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>💻</Text>
            <Text style={styles.emptyTitle}>Terminal Offline</Text>
            <Text style={styles.emptyText}>Start a Cloud Session to access the shell.</Text>
          </View>
        ) : (
          <WebView
            ref={webViewRef}
            originWhitelist={['*']}
            source={{ html: terminalHtml }}
            onMessage={onMessage}
            style={styles.webview}
            scrollEnabled={false}
            keyboardDisplayRequiresUserAction={false}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            allowsInlineMediaPlayback={true}
          />
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  header: {
    height: 60,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    backgroundColor: '#111',
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  title: { fontSize: 14, fontWeight: '900', color: '#fff', textTransform: 'lowercase' },
  subtitle: { fontSize: 10, color: '#666', marginTop: 2, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  actionBtn: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6, backgroundColor: '#334155' },
  actionBtnText: { color: '#cbd5e1', fontSize: 9, fontWeight: '800' },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  badgeOn: { backgroundColor: 'rgba(16, 185, 129, 0.1)', borderWidth: 1, borderColor: '#10b981' },
  badgeOff: { backgroundColor: 'rgba(148, 163, 184, 0.1)', borderWidth: 1, borderColor: '#94a3b8' },
  statusText: { fontSize: 9, fontWeight: '900' },
  statusTextOn: { color: '#10b981' },
  statusTextOff: { color: '#94a3b8' },
  terminalContainer: { flex: 1 },
  webview: { flex: 1, backgroundColor: '#000' },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyIcon: { fontSize: 48, marginBottom: 16, opacity: 0.5 },
  emptyTitle: { fontSize: 18, fontWeight: '800', color: '#fff', marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#666', textAlign: 'center' },
});
