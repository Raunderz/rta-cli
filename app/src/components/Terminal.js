import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Platform,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { WebView } from 'react-native-webview';

const GO_URL = process.env.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_MOBILE_BACKEND_URL || '';

const CTRL_KEYS = [
  { label: 'a', code: '\x01' },
  { label: 'b', code: '\x02' },
  { label: 'c', code: '\x03' },
  { label: 'd', code: '\x04' },
  { label: 'e', code: '\x05' },
  { label: 'f', code: '\x06' },
  { label: 'g', code: '\x07' },
  { label: 'h', code: '\x08' },
  { label: 'i', code: '\x09' },
  { label: 'j', code: '\x0a' },
  { label: 'k', code: '\x0b' },
  { label: 'l', code: '\x0c' },
  { label: 'm', code: '\x0d' },
  { label: 'n', code: '\x0e' },
  { label: 'o', code: '\x0f' },
  { label: 'p', code: '\x10' },
  { label: 'q', code: '\x11' },
  { label: 'r', code: '\x12' },
  { label: 's', code: '\x13' },
  { label: 't', code: '\x14' },
  { label: 'u', code: '\x15' },
  { label: 'v', code: '\x16' },
  { label: 'w', code: '\x17' },
  { label: 'x', code: '\x18' },
  { label: 'y', code: '\x19' },
  { label: 'z', code: '\x1a' },
];

function getCtrlCode(char) {
  const lower = char.toLowerCase();
  const found = CTRL_KEYS.find(k => k.label === lower);
  return found ? found.code : null;
}

export default function Terminal({ apiKey, session }) {
  const webViewRef = useRef(null);
  const inputRef = useRef(null);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [ctrlActive, setCtrlActive] = useState(false);

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
    .xterm-helper-textarea { display: none !important; }
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

    window._rta_send = function(data) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    };

    function connectShell() {
      log('Connecting: ' + WS_URL);
      ws = new WebSocket(WS_URL);
      window._rta_ws = ws;
      ws.binaryType = 'arraybuffer';

      ws.onopen = function() {
        log('WS Open');
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

  const sendToTerminal = useCallback((text) => {
    webViewRef.current?.injectJavaScript(
      'window._rta_send(' + JSON.stringify(text) + ');void(0);'
    );
  }, []);

  const handleKeyButton = useCallback((char) => {
    if (ctrlActive) {
      const ctrlCode = getCtrlCode(char);
      if (ctrlCode) {
        sendToTerminal(ctrlCode);
      } else {
        sendToTerminal(char);
      }
      setCtrlActive(false);
    } else {
      sendToTerminal(char);
    }
  }, [ctrlActive, sendToTerminal]);

  const handleSpecialKey = useCallback((seq) => {
    if (ctrlActive) {
      const first = seq.charAt(0);
      const ctrlCode = getCtrlCode(first);
      if (ctrlCode) {
        sendToTerminal(ctrlCode);
      } else {
        sendToTerminal(seq);
      }
      setCtrlActive(false);
    } else {
      sendToTerminal(seq);
    }
  }, [ctrlActive, sendToTerminal]);

  const toggleCtrl = useCallback(() => {
    setCtrlActive(prev => !prev);
  }, []);

  const reconnect = useCallback(() => {
    if (wsUrl) {
      webViewRef.current?.reload();
    }
  }, [wsUrl]);

  const handleInputChange = useCallback((text) => {
    if (text.length > 0) {
      handleKeyButton(text);
      inputRef.current?.clear();
    }
  }, [handleKeyButton]);

  const handleKeyPress = useCallback((e) => {
    const { key } = e.nativeEvent;
    let seq = null;

    switch (key) {
      case 'Backspace': seq = '\x7f'; break;
      case 'Enter': seq = '\r'; break;
      case 'Tab': seq = '\t'; break;
      case 'Escape': seq = '\x1b'; break;
      case 'ArrowUp': seq = '\x1b[A'; break;
      case 'ArrowDown': seq = '\x1b[B'; break;
      case 'ArrowLeft': seq = '\x1b[D'; break;
      case 'ArrowRight': seq = '\x1b[C'; break;
      case 'Home': seq = '\x1b[H'; break;
      case 'End': seq = '\x1b[F'; break;
      case 'Delete': seq = '\x1b[3~'; break;
    }

    if (seq) {
      handleSpecialKey(seq);
    }
  }, [handleSpecialKey]);

  useEffect(() => {
    if (session.status === 'on' && inputRef.current) {
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [session.status]);

  useEffect(() => {
    if (ctrlActive) {
      const timer = setTimeout(() => setCtrlActive(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [ctrlActive]);

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

          <TextInput
            ref={inputRef}
            style={styles.nativeInput}
            onChangeText={handleInputChange}
            onKeyPress={handleKeyPress}
            autoFocus={session.status === 'on'}
            showSoftInputOnFocus={true}
            blurOnSubmit={false}
            autoCorrect={false}
            autoCapitalize="none"
            autoComplete="off"
            spellCheck={false}
            selectionColor="transparent"
          />

          {/* Row 1: Special keys + Ctrl */}
          <View style={styles.keyRow}>
            <TouchableOpacity
              style={[styles.keyBtn, styles.escKey]}
              onPress={() => handleSpecialKey('\x1b')}
            >
              <Text style={styles.keyBtnText}>ESC</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.keyBtn, ctrlActive ? styles.ctrlKeyActive : styles.ctrlKey]}
              onPress={toggleCtrl}
            >
              <Text style={[styles.keyBtnText, ctrlActive && styles.ctrlKeyTextActive]}>CTRL</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.keyBtn, styles.tabKey]}
              onPress={() => handleSpecialKey('\t')}
            >
              <Text style={styles.keyBtnText}>TAB</Text>
            </TouchableOpacity>

            {['|', '/', '~', '-', ':', '@', '#', '!'].map((char) => (
              <TouchableOpacity
                key={char}
                style={styles.keyBtn}
                onPress={() => handleKeyButton(char)}
              >
                <Text style={styles.keyBtnText}>{char}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Row 2: Arrows + Home/End */}
          <View style={styles.keyRow}>
            <TouchableOpacity
              style={[styles.keyBtn, styles.navKey]}
              onPress={() => handleSpecialKey('\x1b[H')}
            >
              <Text style={styles.keyBtnText}>HOME</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.keyBtn}
              onPress={() => handleSpecialKey('\x1b[D')}
            >
              <Text style={styles.keyBtnText}>&lt;</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.keyBtn}
              onPress={() => handleSpecialKey('\x1b[A')}
            >
              <Text style={styles.keyBtnText}>^</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.keyBtn}
              onPress={() => handleSpecialKey('\x1b[B')}
            >
              <Text style={styles.keyBtnText}>v</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.keyBtn}
              onPress={() => handleSpecialKey('\x1b[C')}
            >
              <Text style={styles.keyBtnText}>&gt;</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.keyBtn, styles.navKey]}
              onPress={() => handleSpecialKey('\x1b[F')}
            >
              <Text style={styles.keyBtnText}>END</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.keyBtn, styles.wideKey]}
              onPress={() => handleKeyButton(' ')}
            >
              <Text style={styles.keyBtnText}>SPACE</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.keyBtn, styles.backKey]}
              onPress={() => handleSpecialKey('\x7f')}
            >
              <Text style={styles.keyBtnText}>DEL</Text>
            </TouchableOpacity>
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
  nativeInput: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: 1,
    height: 1,
    opacity: 0.01,
    zIndex: -1,
  },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyIcon: { fontSize: 48, marginBottom: 16, opacity: 0.5 },
  emptyTitle: { fontSize: 18, fontWeight: '800', color: '#fff', marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#8b949e', textAlign: 'center' },
  keyRow: {
    flexDirection: 'row',
    backgroundColor: '#161b22',
    borderTopWidth: 1,
    borderTopColor: '#30363d',
    paddingHorizontal: 4,
    paddingVertical: 4,
    gap: 3,
  },
  keyBtn: {
    flex: 1,
    height: 36,
    backgroundColor: '#21262d',
    borderRadius: 5,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#30363d',
  },
  keyBtnText: {
    color: '#c9d1d9',
    fontSize: 11,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  escKey: {
    flex: 1.2,
    backgroundColor: '#1f2937',
  },
  ctrlKey: {
    flex: 1.2,
    backgroundColor: '#1f2937',
  },
  ctrlKeyActive: {
    flex: 1.2,
    backgroundColor: '#0ea5e9',
    borderColor: '#38bdf8',
  },
  ctrlKeyTextActive: {
    color: '#fff',
  },
  tabKey: {
    flex: 1.2,
    backgroundColor: '#1f2937',
  },
  navKey: {
    flex: 1.3,
  },
  wideKey: {
    flex: 3,
  },
  backKey: {
    flex: 1.3,
    backgroundColor: '#1f2937',
  },
});
