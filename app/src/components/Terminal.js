import React, { useState, useEffect, useRef } from 'react';
import { 
  StyleSheet, 
  View, 
  Text, 
  Platform,
  TouchableOpacity
} from 'react-native';
import { WebView } from 'react-native-webview';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://divisive-herbs-jolly.ngrok-free.dev';

export default function Terminal({ session }) {
  const webViewRef = useRef(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState([]);

  const wsUrl = session.status === 'on' 
    ? BACKEND_URL.replace('http', 'ws') + `/v1/executor/ws/env/${session.id}`
    : null;

  const terminalHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
        <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
        <style>
          body { margin: 0; background: #000; overflow: hidden; height: 100vh; width: 100vw; }
          #terminal { height: 100%; width: 100%; }
        </style>
      </head>
      <body>
        <div id="terminal"></div>
        <script>
          const log = (m) => window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'log', message: m }));
          
          const term = new Terminal({
            cursorBlink: true,
            fontSize: 13,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            theme: { background: '#000000', foreground: '#ffffff', cursor: '#0ea5e9' },
            allowProposedApi: true
          });
          const fitAddon = new FitAddon.FitAddon();
          term.loadAddon(fitAddon);
          term.open(document.getElementById('terminal'));
          
          setTimeout(() => {
            fitAddon.fit();
            term.focus();
          }, 500);

          let socket;
          
          function connect(url) {
            log('Conn...');
            if (socket) socket.close();
            term.reset();
            term.write('\\r\\n\\x1b[1;34m⚡ Rta Cloud...\\x1b[0m\\r\\n');
            
            socket = new WebSocket(url);
            socket.binaryType = 'arraybuffer'; // Crucial for Go BinaryMessage

            socket.onopen = () => {
              log('Open');
              term.write('\\x1b[1;32m✓ Connected.\\x1b[0m\\r\\n');
              const dims = JSON.stringify({ cols: term.cols, rows: term.rows });
              socket.send(dims);
              
              // Run neofetch
              setTimeout(() => {
                socket.send('neofetch\\n');
              }, 1000);
            };

            socket.onmessage = (ev) => {
              log('Data: ' + (ev.data.byteLength || ev.data.length));
              if (typeof ev.data === 'string') {
                term.write(ev.data);
              } else {
                term.write(new Uint8Array(ev.data));
              }
            };

            socket.onclose = (e) => {
              log('Closed ' + e.code);
              term.write('\\r\\n\\x1b[1;31m🛑 Off (' + e.code + ')\\x1b[0m\\r\\n');
            };

            socket.onerror = (err) => {
              log('Error');
            };
          }

          term.onData(data => {
            log('In: ' + data.length);
            if (socket && socket.readyState === WebSocket.OPEN) {
              socket.send(data);
            }
          });

          document.body.addEventListener('touchstart', () => {
            term.focus();
          });

          window.addEventListener('resize', () => {
            fitAddon.fit();
            if (socket && socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ cols: term.cols, rows: term.rows }));
            }
          });
          
          window.addEventListener('message', (event) => {
            try {
              const data = JSON.parse(event.data);
              if (data.type === 'connect') connect(data.url);
              if (data.type === 'focus') term.focus();
            } catch(e) {}
          });

          log('Ready');
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'ready' }));
        </script>
      </body>
    </html>
  `;

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
          />
        )}
      </View>
    </View>
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
