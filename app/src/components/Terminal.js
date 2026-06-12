import React, { useState, useRef, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Platform,
  TouchableOpacity,
} from 'react-native';
import { WebView } from 'react-native-webview';

const GO_URL = process.env.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_MOBILE_BACKEND_URL || '';

export default function Terminal({ apiKey, session }) {
  const webViewRef = useRef(null);
  const [terminalLogs, setTerminalLogs] = useState([]);

  const wsUrl = session.status === 'on' && GO_URL
    ? `${GO_URL.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:')}/v1/executor/ws/env/${session.id}?api_key=${apiKey}`
    : null;

  const terminalHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <link rel="stylesheet" href="https://unpkg.com/xterm@5.1.0/css/xterm.css" />
  <script src="https://unpkg.com/xterm@5.1.0/lib/xterm.js"><\/script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; width: 100%; overflow: auto; background: #0d1117; }
    .xterm { height: 100%; width: 100%; padding: 8px; }
    .xterm-viewport { overflow: auto !important; }
    .xterm-helper-textarea {
      opacity: 0.01 !important;
      left: 0 !important;
      top: 0 !important;
      width: 100% !important;
      height: 100% !important;
      position: absolute !important;
      z-index: 100 !important;
      outline: none !important;
      resize: none !important;
      border: none !important;
      padding: 0 !important;
      margin: 0 !important;
      pointer-events: auto !important;
    }
  </style>
</head>
<body>
  <div id="terminal-container" style="height:100%;width:100%;"></div>
  <script>
    var log = function(m) {
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'log', message: m }));
    };

    var WS_URL = ${JSON.stringify(wsUrl)};

    var cols = Math.max(100, Math.floor(window.innerWidth / 9.5));
    var rows = Math.max(24, Math.floor(window.innerHeight / 19));

    var term = new Terminal({
      cols: cols,
      rows: rows,
      cursorBlink: true,
      fontSize: 13,
      fontFamily: "'Courier New', monospace",
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        selection: 'rgba(88, 166, 255, 0.2)',
        black: '#484f58',
        red: '#f85149',
        green: '#3fb950',
        yellow: '#d29922',
        blue: '#58a6ff',
        magenta: '#bc8ef9',
        cyan: '#79c0ff',
        white: '#b1bac4',
      },
      scrollback: 5000,
      tabStopWidth: 4,
    });

    term.open(document.getElementById('terminal-container'));

    var ws = null;

    term.onData(function(data) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });

    term.onResize(function(size) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ cols: size.cols, rows: size.rows }));
      }
    });

    function connectShell() {
      log('Connecting: ' + WS_URL);
      ws = new WebSocket(WS_URL);
      window._rta_ws = ws;
      ws.binaryType = 'arraybuffer';

      ws.onopen = function() {
        log('WS Open');
        var ta = document.querySelector('.xterm-helper-textarea');
        if (ta) ta.focus();
        var dims = { cols: term.cols, rows: term.rows };
        ws.send(JSON.stringify(dims));
        setTimeout(function() { ws.send('fastfetch\\n'); }, 1000);
      };

      ws.onmessage = function(event) {
        if (event.data instanceof ArrayBuffer) {
          term.write(new Uint8Array(event.data));
        } else {
          term.write(event.data);
        }
      };

      ws.onerror = function(err) {
        log('WS Error');
        term.write('\\r\\n\\x1b[31m\\u2717 Connection failed\\x1b[0m\\r\\n');
      };

      ws.onclose = function(e) {
        log('WS Closed: ' + e.code);
        window._rta_ws = null;
        term.write('\\r\\n\\x1b[33m\\u26A0 Disconnected (' + e.code + ')\\x1b[0m\\r\\n');
      };
    }

    document.getElementById('terminal-container').addEventListener('touchend', function(e) {
      var ta = document.querySelector('.xterm-helper-textarea');
      if (ta) ta.focus();
    });

    document.getElementById('terminal-container').addEventListener('click', function() {
      var ta = document.querySelector('.xterm-helper-textarea');
      if (ta) ta.focus();
    });

    window.addEventListener('resize', function() {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ cols: term.cols, rows: term.rows }));
      }
    });

    connectShell();

    log('Ready');
    window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'ready' }));
  <\/script>
</body>
</html>`;

  const onMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'log') {
        setTerminalLogs(prev => [data.message, ...prev.slice(0, 5)]);
      }
    } catch(e) {}
  }, []);

  const sendJS = useCallback((code) => {
    webViewRef.current?.injectJavaScript(
      '(function(){try{' + code + '}catch(e){}})();void(0);'
    );
  }, []);

  const reconnect = useCallback(() => {
    if (wsUrl) {
      webViewRef.current?.reload();
    }
  }, [wsUrl]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>bash terminal</Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            {session.status === 'on' ? (terminalLogs[0] || 'active') : 'offline'}
          </Text>
        </View>
        <View style={styles.actions}>
          {session.status === 'on' && (
            <TouchableOpacity style={styles.actionBtn} onPress={reconnect}>
              <Text style={styles.actionBtnText}>RETRY</Text>
            </TouchableOpacity>
          )}
          <View style={[styles.statusBadge, session.status === 'on' ? styles.badgeOn : styles.badgeOff]}>
            <Text style={[styles.statusText, session.status === 'on' ? styles.statusTextOn : styles.statusTextOff]}>
              {session.status === 'on' ? 'CLOUD' : 'LOCAL'}
            </Text>
          </View>
        </View>
      </View>

      {session.status === 'off' ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>💻</Text>
          <Text style={styles.emptyTitle}>Terminal Offline</Text>
          <Text style={styles.emptyText}>Start a Cloud Session to access the shell.</Text>
        </View>
      ) : (
        <View style={styles.terminalArea}>
          <WebView
            ref={webViewRef}
            originWhitelist={['*']}
            source={{ html: terminalHtml }}
            onMessage={onMessage}
            style={styles.webview}
            scrollEnabled={false}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            allowsInlineMediaPlayback={true}
            keyboardDisplayRequiresUserAction={false}
          />

          <View style={styles.accessoryBar}>
            {[
              { label: 'TAB', code: "'\\t'" },
              { label: '^C', code: "'\\x03'" },
              { label: '^D', code: "'\\x04'" },
              { label: 'ESC', code: "'\\x1b'" },
              { label: '▲', code: "'\\x1b[A'" },
              { label: '▼', code: "'\\x1b[B'" },
              { label: '◀', code: "'\\x1b[D'" },
              { label: '▶', code: "'\\x1b[C'" },
            ].map(({ label, code }) => (
              <TouchableOpacity
                key={label}
                style={styles.accBtn}
                onPress={() => {
                  sendJS('var w=document.querySelector(".xterm-helper-textarea");if(w){w.focus();}if(window._rta_ws&&window._rta_ws.readyState===1){window._rta_ws.send(' + code + ');}');
                }}
              >
                <Text style={styles.accBtnText}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117' },
  header: {
    height: 60,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    backgroundColor: '#161b22',
    borderBottomWidth: 1,
    borderBottomColor: '#30363d',
  },
  title: { fontSize: 14, fontWeight: '900', color: '#fff', textTransform: 'lowercase' },
  subtitle: { fontSize: 10, color: '#8b949e', marginTop: 2, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  actionBtn: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6, backgroundColor: '#238636' },
  actionBtnText: { color: '#fff', fontSize: 9, fontWeight: '800' },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4 },
  badgeOn: { backgroundColor: 'rgba(16, 185, 129, 0.1)', borderWidth: 1, borderColor: '#10b981' },
  badgeOff: { backgroundColor: 'rgba(148, 163, 184, 0.1)', borderWidth: 1, borderColor: '#94a3b8' },
  statusText: { fontSize: 9, fontWeight: '900' },
  statusTextOn: { color: '#10b981' },
  statusTextOff: { color: '#94a3b8' },
  webview: { flex: 1, backgroundColor: '#0d1117' },
  terminalArea: { flex: 1 },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyIcon: { fontSize: 48, marginBottom: 16, opacity: 0.5 },
  emptyTitle: { fontSize: 18, fontWeight: '800', color: '#fff', marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#8b949e', textAlign: 'center' },
});
