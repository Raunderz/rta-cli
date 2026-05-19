import React, { useRef, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  KeyboardAvoidingView, 
  Platform 
} from 'react-native';
import { WebView } from 'react-native-webview';

export default function Editor({ file, onSave }) {
  const webViewRef = useRef(null);

  useEffect(() => {
    if (file && webViewRef.current) {
      // Inject code when the file changes
      const escapedContent = JSON.stringify(file.content || '');
      const escapedName = JSON.stringify(file.name || '');
      
      const js = `
        if (window.setCodeMirrorContent) {
          window.setCodeMirrorContent(${escapedContent}, ${escapedName});
        }
        true;
      `;
      webViewRef.current.injectJavaScript(js);
    }
  }, [file]);

  if (!file) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>📝</Text>
        <Text style={styles.emptyText}>No File Open</Text>
        <Text style={styles.emptySubtext}>Select a file in the Files tab to start coding</Text>
      </View>
    );
  }

  // Handle message from WebView (save or auto-change sync)
  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'save' || data.type === 'change') {
        onSave(file.id, data.content);
      }
    } catch (e) {
      console.warn('Failed to parse message from Editor WebView', e);
    }
  };

  const requestSave = () => {
    if (webViewRef.current) {
      webViewRef.current.injectJavaScript(`
        if (window.triggerSave) {
          window.triggerSave();
        }
        true;
      `);
    }
  };

  // HTML content featuring CodeMirror 6 loaded from esm.sh
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
      <style>
        html, body {
          margin: 0;
          padding: 0;
          height: 100%;
          background-color: #ffffff;
          overflow: hidden;
        }
        #editor {
          height: 100%;
          width: 100%;
        }
        /* Custom scrollbars */
        ::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        ::-webkit-scrollbar-thumb {
          background-color: #cbd5e1;
          border-radius: 3px;
        }
      </style>
    </head>
    <body>
      <div id="editor"></div>

      <script type="module">
        import { EditorView, basicSetup } from 'https://esm.sh/codemirror';
        import { EditorState } from 'https://esm.sh/@codemirror/state';
        import { keymap } from 'https://esm.sh/@codemirror/view';
        import { indentWithTab } from 'https://esm.sh/@codemirror/commands';
        
        // Languages
        import { javascript } from 'https://esm.sh/@codemirror/lang-javascript';
        import { python } from 'https://esm.sh/@codemirror/lang-python';
        import { html } from 'https://esm.sh/@codemirror/lang-html';
        import { css } from 'https://esm.sh/@codemirror/lang-css';

        let editor = null;
        let currentFilename = '';

        // Clean light Sky & Horizon theme configuration
        const skyTheme = EditorView.theme({
          "&": {
            height: "100%",
            fontSize: "14px",
            fontFamily: "monospace",
            backgroundColor: "#ffffff",
            color: "#1f2937"
          },
          ".cm-content": {
            caretColor: "#0ea5e9"
          },
          ".cm-cursor, .cm-dropCursor": {
            borderLeftColor: "#0ea5e9"
          },
          "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection": {
            backgroundColor: "#e0f2fe !important"
          },
          ".cm-gutters": {
            backgroundColor: "#f0f9ff",
            color: "#94a3b8",
            borderRight: "1px solid #e0f2fe",
            minWidth: "40px"
          },
          ".cm-activeLine": {
            backgroundColor: "#f8fafc"
          },
          ".cm-activeLineGutter": {
            backgroundColor: "#e0f2fe",
            color: "#0ea5e9"
          }
        }, { dark: false });

        function getLanguageExtension(filename) {
          const ext = filename.split('.').pop().toLowerCase();
          if (ext === 'js' || ext === 'jsx' || ext === 'ts' || ext === 'tsx' || ext === 'json') {
            return javascript();
          }
          if (ext === 'py') {
            return python();
          }
          if (ext === 'html') {
            return html();
          }
          if (ext === 'css') {
            return css();
          }
          return [];
        }

        window.setCodeMirrorContent = function(content, filename) {
          currentFilename = filename;
          
          if (editor) {
            // Update existing editor
            editor.setState(EditorState.create({
              doc: content,
              extensions: [
                basicSetup,
                keymap.of([indentWithTab]),
                getLanguageExtension(filename),
                skyTheme,
                EditorView.updateListener.of((v) => {
                  if (v.docChanged) {
                    window.ReactNativeWebView.postMessage(JSON.stringify({
                      type: 'change',
                      content: v.state.doc.toString()
                    }));
                  }
                })
              ]
            }));
          } else {
            // Initialize editor
            editor = new EditorView({
              state: EditorState.create({
                doc: content,
                extensions: [
                  basicSetup,
                  keymap.of([indentWithTab]),
                  getLanguageExtension(filename),
                  skyTheme,
                  EditorView.updateListener.of((v) => {
                    if (v.docChanged) {
                      window.ReactNativeWebView.postMessage(JSON.stringify({
                        type: 'change',
                        content: v.state.doc.toString()
                      }));
                    }
                  })
                ]
              }),
              parent: document.getElementById('editor')
            });
          }
        };

        window.triggerSave = function() {
          if (editor) {
            window.ReactNativeWebView.postMessage(JSON.stringify({
              type: 'save',
              content: editor.state.doc.toString()
            }));
          }
        };

        // Notify app we are ready to receive data
        window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'ready' }));
      </script>
    </body>
    </html>
  `;

  // Inject script when loading completes
  const onWebViewLoad = () => {
    const escapedContent = JSON.stringify(file.content || '');
    const escapedName = JSON.stringify(file.name || '');
    const js = `
      if (window.setCodeMirrorContent) {
        window.setCodeMirrorContent(${escapedContent}, ${escapedName});
      }
      true;
    `;
    webViewRef.current.injectJavaScript(js);
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      style={styles.container}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.fileName}>{file.name}</Text>
          <Text style={styles.filePath}>/workspace/{file.name}</Text>
        </View>
        <TouchableOpacity 
          style={styles.saveBtn}
          onPress={requestSave}
        >
          <Text style={styles.saveText}>SAVE</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.editorArea}>
        <WebView
          ref={webViewRef}
          source={{ html: htmlContent }}
          onMessage={handleMessage}
          onLoadEnd={onWebViewLoad}
          originWhitelist={['*']}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          style={styles.webview}
          keyboardDisplayRequiresUserAction={false}
          hideKeyboardAccessoryView={true}
        />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    height: 70,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    backgroundColor: '#f0f9ff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  fileName: {
    fontSize: 16,
    fontWeight: '800',
    color: '#1f2937',
  },
  filePath: {
    fontSize: 10,
    color: '#6b7280',
    marginTop: 2,
  },
  saveBtn: {
    backgroundColor: '#0ea5e9',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
  },
  saveText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 12,
    letterSpacing: 1,
  },
  editorArea: {
    flex: 1,
  },
  webview: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f9ff',
    padding: 24,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#1f2937',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
  },
});
