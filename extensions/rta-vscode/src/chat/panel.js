const vscode = require('vscode');
const { getChatHtml } = require('./renderer');

/**
 * WebviewViewProvider for the RTA chat panel.
 */
class ChatPanel {
  constructor(agent) {
    /** @type {import('../agent').AgentSidecar} */
    this.agent = agent;
    /** @type {import('vscode').WebviewView | null} */
    this.view = null;
    this.disposables = [];
    /** @type {Array<{role: string, content: string}>} */
    this.messages = [];
  }

  /**
   * Register the chat panel provider.
   * @param {import('vscode').ExtensionContext} context
   * @param {import('../agent').AgentSidecar} agent
   * @returns {ChatPanel}
   */
  static register(context, agent) {
    const panel = new ChatPanel(agent);

    const provider = vscode.window.registerWebviewViewProvider('rta.chat', panel, {
      webviewOptions: { retainContextWhenHidden: true },
    });

    context.subscriptions.push(provider);
    panel.disposables.push(provider);
    return panel;
  }

  /**
   * Called when the webview is created.
   * @param {import('vscode').WebviewView} webviewView
   */
  resolveWebviewView(webviewView) {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [],
    };

    const nonce = getNonce();
    webviewView.webview.html = getChatHtml({
      cspSource: webviewView.webview.cspSource,
      nonce,
    });

    // Handle messages from the webview
    webviewView.webview.onDidReceiveMessage(async (msg) => {
      if (msg.type === 'send') {
        await this._handleSend(msg.text, msg.context);
      }
    });

    // Send initial context if there's an active editor
    this._sendEditorContext();
  }

  /**
   * Send a user message to the agent and stream the response.
   * @param {string} text
   * @param {object|null} context
   */
  async _handleSend(text, context) {
    if (!this.view) return;

    // Build the message with optional context
    let fullMessage = text;
    if (context) {
      if (context.type === 'selection') {
        fullMessage = `Here is the selected code from \`${context.file}\` (lines ${context.startLine}-${context.endLine}):\n\`\`\`\n${context.text}\n\`\`\`\n\n${text}`;
      } else if (context.type === 'file') {
        fullMessage = `Here is the file \`${context.file}\`:\n\`\`\`\n${context.text}\n\`\`\`\n\n${text}`;
      }
    }

    this.view.webview.postMessage({ type: 'assistant-start' });
    this.view.webview.postMessage({ type: 'status', content: 'Thinking...' });

    // Track messages for conversation history
    this.messages.push({ role: 'user', content: fullMessage });

    try {
      const workspace = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;

      const assistantText = await this.agent.ask(fullMessage, {
        messages: this.messages,
        workspace,
      }, (event) => {
        if (!this.view) return;

        if (event.type === 'text_chunk') {
          this.view.webview.postMessage({ type: 'assistant', content: event.content });
        } else if (event.type === 'tool_start') {
          this.view.webview.postMessage({
            type: 'tool',
            content: `Executing: ${event.content}`,
          });
        } else if (event.type === 'thought') {
          // Thinking content — could show in a collapsible section
          this.view.webview.postMessage({
            type: 'tool',
            content: `Thinking: ${event.content}`,
          });
        } else if (event.type === 'error') {
          this.view.webview.postMessage({
            type: 'error',
            content: event.content,
          });
        }
      });
    } catch (err) {
      this.view.webview.postMessage({
        type: 'error',
        content: `Agent error: ${err.message}`,
      });
    }

    // Save assistant response to history
    this.messages.push({ role: 'assistant', content: assistantText || '' });
    this.view.webview.postMessage({ type: 'assistant-end' });
  }

  /**
   * Send the current editor selection/file as context to the webview.
   */
  _sendEditorContext() {
    if (!this.view) return;
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.document.getText(editor.selection);
    if (selection) {
      this.view.webview.postMessage({
        type: 'context',
        label: `Selection: ${editor.selection.start.line + 1}-${editor.selection.end.line + 1}`,
        context: {
          type: 'selection',
          file: editor.document.fileName,
          text: selection,
          startLine: editor.selection.start.line + 1,
          endLine: editor.selection.end.line + 1,
        },
      });
    }
  }

  /**
   * Add text to the chat (used by commands like addSelection, addFile).
   * @param {'selection' | 'file'} type
   * @param {object} data
   */
  addContext(type, data) {
    if (!this.view) return;

    if (type === 'selection') {
      this.view.webview.postMessage({
        type: 'context',
        label: `Selection: ${data.startLine}-${data.endLine}`,
        context: {
          type: 'selection',
          file: data.file,
          text: data.text,
          startLine: data.startLine,
          endLine: data.endLine,
        },
      });
    } else if (type === 'file') {
      this.view.webview.postMessage({
        type: 'context',
        label: `File: ${data.file}`,
        context: {
          type: 'file',
          file: data.file,
          text: data.text,
        },
      });
    }
  }

  /**
   * Clear the chat panel.
   */
  clear() {
    this.messages = [];
    if (this.view) {
      this.view.webview.postMessage({ type: 'clear' });
    }
  }

  dispose() {
    this.disposables.forEach((d) => d.dispose());
  }
}

/**
 * Generate a random nonce for CSP.
 * @returns {string}
 */
function getNonce() {
  let text = '';
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return text;
}

module.exports = { ChatPanel };
