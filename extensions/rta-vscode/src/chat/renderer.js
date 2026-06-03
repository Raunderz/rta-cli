/**
 * Generates the HTML for the chat webview.
 * @param {object} options
 * @param {string} options.cspSource - Content security policy source
 * @param {string} options.nonce - Nonce for inline scripts
 * @returns {string}
 */
function getChatHtml({ cspSource, nonce }) {
  return /*html*/ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'none'; style-src ${cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <title>RTA Chat</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--vscode-font-family, system-ui, sans-serif);
      font-size: var(--vscode-font-size, 13px);
      color: var(--vscode-foreground, #ccc);
      background: var(--vscode-sideBar-background, #1e1e1e);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }

    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .msg {
      padding: 8px 12px;
      border-radius: 6px;
      line-height: 1.5;
      word-wrap: break-word;
      white-space: pre-wrap;
    }

    .msg-user {
      background: var(--vscode-input-background, #3c3c3c);
      border-left: 3px solid var(--vscode-accent-foreground, #007acc);
      align-self: flex-end;
      max-width: 85%;
    }

    .msg-assistant {
      background: var(--vscode-editor-background, #252526);
      border-left: 3px solid var(--vscode-terminal-ansiGreen, #4ec9b0);
      align-self: flex-start;
      max-width: 95%;
    }

    .msg-system {
      background: transparent;
      color: var(--vscode-descriptionForeground, #888);
      font-style: italic;
      text-align: center;
      align-self: center;
      max-width: 80%;
    }

    .msg-tool {
      background: var(--vscode-editor-background, #1a1a2e);
      border-left: 3px solid var(--vscode-terminal-ansiYellow, #dcdcaa);
      font-family: var(--vscode-editor-font-family, monospace);
      font-size: 12px;
    }

    .msg-error {
      background: var(--vscode-input-background, #3c3c3c);
      border-left: 3px solid var(--vscode-terminal-ansiRed, #f44747);
      color: var(--vscode-terminal-ansiRed, #f44747);
    }

    .msg-role {
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      opacity: 0.7;
    }

    pre {
      background: var(--vscode-editor-background, #1e1e1e);
      border: 1px solid var(--vscode-widget-border, #444);
      border-radius: 4px;
      padding: 8px;
      overflow-x: auto;
      margin: 8px 0;
      font-family: var(--vscode-editor-font-family, monospace);
      font-size: 12px;
    }

    code {
      font-family: var(--vscode-editor-font-family, monospace);
      background: var(--vscode-textCodeBlock-background, rgba(127,127,127,0.1));
      padding: 1px 4px;
      border-radius: 3px;
      font-size: 12px;
    }

    pre code { background: none; padding: 0; }

    #input-area {
      padding: 8px 12px;
      border-top: 1px solid var(--vscode-widget-border, #444);
      display: flex;
      gap: 8px;
      background: var(--vscode-input-background, #3c3c3c);
    }

    #input {
      flex: 1;
      background: var(--vscode-input-background, #3c3c3c);
      color: var(--vscode-input-foreground, #ccc);
      border: 1px solid var(--vscode-input-border, #444);
      border-radius: 4px;
      padding: 8px;
      font-family: inherit;
      font-size: inherit;
      resize: none;
      outline: none;
      min-height: 36px;
      max-height: 150px;
    }

    #input:focus { border-color: var(--vscode-focusBorder, #007acc); }

    #send-btn {
      background: var(--vscode-button-background, #0e639c);
      color: var(--vscode-button-foreground, #fff);
      border: none;
      border-radius: 4px;
      padding: 8px 16px;
      cursor: pointer;
      font-family: inherit;
      font-size: 13px;
    }

    #send-btn:hover { background: var(--vscode-button-hoverBackground, #1177bb); }
    #send-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    #context-badge {
      padding: 4px 12px;
      background: var(--vscode-badge-background, #4d4d4d);
      color: var(--vscode-badge-foreground, #fff);
      font-size: 11px;
      display: none;
      align-items: center;
      gap: 6px;
    }

    #context-badge.visible { display: flex; }

    #context-badge .remove {
      cursor: pointer;
      opacity: 0.7;
    }

    #context-badge .remove:hover { opacity: 1; }

    #status {
      padding: 4px 12px;
      font-size: 11px;
      color: var(--vscode-descriptionForeground, #888);
      border-top: 1px solid var(--vscode-widget-border, #333);
    }

    .typing-indicator {
      display: inline-block;
      animation: blink 1s infinite;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
  </style>
</head>
<body>
  <div id="messages"></div>
  <div id="context-badge"><span id="context-text"></span><span class="remove" id="context-clear">x</span></div>
  <div id="input-area">
    <textarea id="input" placeholder="Ask RTA..." rows="1"></textarea>
    <button id="send-btn">Send</button>
  </div>
  <div id="status">Ready</div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();

    const messagesEl = document.getElementById('messages');
    const inputEl = document.getElementById('input');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');
    const contextBadge = document.getElementById('context-badge');
    const contextText = document.getElementById('context-text');
    const contextClear = document.getElementById('context-clear');

    let context = null;

    // Auto-resize textarea
    inputEl.addEventListener('input', () => {
      inputEl.style.height = 'auto';
      inputEl.style.height = Math.min(inputEl.scrollHeight, 150) + 'px';
    });

    // Send on Enter (Shift+Enter for newline)
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    sendBtn.addEventListener('click', sendMessage);

    contextClear.addEventListener('click', () => {
      context = null;
      contextBadge.classList.remove('visible');
    });

    function sendMessage() {
      const text = inputEl.value.trim();
      if (!text) return;

      addMessage('user', text);
      vscode.postMessage({ type: 'send', text, context });
      context = null;
      contextBadge.classList.remove('visible');

      inputEl.value = '';
      inputEl.style.height = 'auto';
      sendBtn.disabled = true;
      statusEl.textContent = 'Thinking...';
    }

    function addMessage(role, content) {
      const div = document.createElement('div');
      div.className = 'msg msg-' + role;
      if (role !== 'system') {
        const roleEl = document.createElement('div');
        roleEl.className = 'msg-role';
        roleEl.textContent = role === 'user' ? 'You' : role === 'assistant' ? 'RTA' : role;
        div.appendChild(roleEl);
      }
      const contentEl = document.createElement('div');
      contentEl.className = 'msg-content';
      contentEl.textContent = content;
      div.appendChild(contentEl);
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return contentEl;
    }

    function updateLastMessage(content) {
      const msgs = messagesEl.querySelectorAll('.msg-assistant');
      if (msgs.length === 0) return;
      const last = msgs[msgs.length - 1];
      const contentEl = last.querySelector('.msg-content');
      if (contentEl) contentEl.textContent = content;
    }

    let currentAssistantContent = '';

    // Handle messages from the extension host
    window.addEventListener('message', (e) => {
      const msg = e.data;
      switch (msg.type) {
        case 'assistant':
          currentAssistantContent += msg.content;
          updateLastMessage(currentAssistantContent);
          messagesEl.scrollTop = messagesEl.scrollHeight;
          break;

        case 'assistant-start':
          currentAssistantContent = '';
          addMessage('assistant', '');
          statusEl.textContent = 'Thinking...';
          break;

        case 'assistant-end':
          sendBtn.disabled = false;
          statusEl.textContent = 'Ready';
          break;

        case 'tool':
          addMessage('tool', msg.content);
          break;

        case 'error':
          addMessage('error', msg.content);
          sendBtn.disabled = false;
          statusEl.textContent = 'Error';
          break;

        case 'status':
          statusEl.textContent = msg.content;
          break;

        case 'context':
          context = msg.context;
          contextText.textContent = msg.label;
          contextBadge.classList.add('visible');
          break;

        case 'clear':
          messagesEl.innerHTML = '';
          break;
      }
    });
  </script>
</body>
</html>`;
}

module.exports = { getChatHtml };
