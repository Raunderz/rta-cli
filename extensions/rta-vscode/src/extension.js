const vscode = require('vscode');
const { AgentSidecar } = require('./agent');
const { ChatPanel } = require('./chat/panel');

/** @type {AgentSidecar | null} */
let agent = null;
/** @type {ChatPanel | null} */
let chatPanel = null;

async function activate(context) {
  console.log('RTA extension activating...');

  // 1. Create the agent (calls backend directly, no binary needed)
  agent = new AgentSidecar();

  // Load API key from settings
  const apiKey = vscode.workspace.getConfiguration('rta').get('apiKey');
  if (apiKey) {
    agent.setApiKey(apiKey);
  } else {
    vscode.window.showWarningMessage(
      'RTA: No API key configured. Set rta.apiKey in settings or run: rta login'
    );
  }

  // 2. Register the chat webview
  chatPanel = ChatPanel.register(context, agent);

  // 3. Register commands
  const toggleChat = vscode.commands.registerCommand('rta.chat.toggle', () => {
    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
  });

  const addSelection = vscode.commands.registerCommand('rta.chat.addSelection', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.document.getText(editor.selection);
    if (!selection) {
      vscode.window.showWarningMessage('RTA: No selection to add.');
      return;
    }

    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
    chatPanel.addContext('selection', {
      file: editor.document.fileName,
      text: selection,
      startLine: editor.selection.start.line + 1,
      endLine: editor.selection.end.line + 1,
    });
  });

  const addFile = vscode.commands.registerCommand('rta.chat.addFile', async (uri) => {
    try {
      const doc = await vscode.workspace.openTextDocument(uri);
      const text = doc.getText();
      vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
      chatPanel.addContext('file', {
        file: doc.fileName,
        text,
      });
    } catch (err) {
      vscode.window.showErrorMessage(`RTA: Could not read file: ${err.message}`);
    }
  });

  const explain = vscode.commands.registerCommand('rta.inline.explain', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.document.getText(editor.selection);
    if (!selection) {
      vscode.window.showWarningMessage('RTA: Select code to explain.');
      return;
    }

    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
    chatPanel.addContext('selection', {
      file: editor.document.fileName,
      text: selection,
      startLine: editor.selection.start.line + 1,
      endLine: editor.selection.end.line + 1,
    });

    // Auto-send an explain request
    await chatPanel._handleSend('Explain this code', {
      type: 'selection',
      file: editor.document.fileName,
      text: selection,
      startLine: editor.selection.start.line + 1,
      endLine: editor.selection.end.line + 1,
    });
  });

  const edit = vscode.commands.registerCommand('rta.inline.edit', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.document.getText(editor.selection);
    if (!selection) {
      vscode.window.showWarningMessage('RTA: Select code to edit.');
      return;
    }

    const instruction = await vscode.window.showInputBox({
      prompt: 'How should RTA modify this code?',
      placeHolder: 'e.g., add error handling, optimize for performance',
    });

    if (!instruction) return;

    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
    await chatPanel._handleSend(
      `Edit this code: ${instruction}`,
      {
        type: 'selection',
        file: editor.document.fileName,
        text: selection,
        startLine: editor.selection.start.line + 1,
        endLine: editor.selection.end.line + 1,
      }
    );
  });

  const fix = vscode.commands.registerCommand('rta.inline.fix', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);
    if (diagnostics.length === 0) {
      vscode.window.showInformationMessage('RTA: No diagnostics found.');
      return;
    }

    const diagText = diagnostics
      .map((d) => `Line ${d.range.start.line + 1}: [${vscode.DiagnosticSeverity[d.severity]}] ${d.message}`)
      .join('\n');

    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
    await chatPanel._handleSend(
      `Fix these diagnostics:\n\`\`\`\n${diagText}\n\`\`\``,
      { type: 'file', file: editor.document.fileName, text: editor.document.getText() }
    );
  });

  const status = vscode.commands.registerCommand('rta.agent.status', () => {
    const alive = agent && agent.isAlive();
    const msg = alive ? 'RTA agent is running' : 'RTA agent is not running';
    vscode.window.showInformationMessage(msg);
  });

  context.subscriptions.push(
    toggleChat, addSelection, addFile, explain, edit, fix, status
  );

  // 4. Listen for active editor changes to update context
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor(() => {
      if (chatPanel) chatPanel._sendEditorContext();
    })
  );

  console.log('RTA extension activated');
}

function deactivate() {
  if (agent) {
    agent.stop();
    agent = null;
  }
}

module.exports = { activate, deactivate };
