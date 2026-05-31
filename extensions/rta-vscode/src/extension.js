const vscode = require('vscode');

function activate(context) {
  console.log('RTA extension activating...');

  const toggleChat = vscode.commands.registerCommand('rta.chat.toggle', () => {
    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
  });

  const addSelection = vscode.commands.registerCommand('rta.chat.addSelection', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const selection = editor.document.getText(editor.selection);
    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
    // TODO: send selection to chat panel
  });

  const addFile = vscode.commands.registerCommand('rta.chat.addFile', async (uri) => {
    const doc = await vscode.workspace.openTextDocument(uri);
    vscode.commands.executeCommand('workbench.view.extension.rta-sidebar');
    // TODO: send file content to chat panel
  });

  const explain = vscode.commands.registerCommand('rta.inline.explain', () => {
    // TODO: select code, send to agent, show explanation in hover/chat
  });

  const edit = vscode.commands.registerCommand('rta.inline.edit', () => {
    // TODO: select code, prompt for change, apply diff
  });

  const fix = vscode.commands.registerCommand('rta.inline.fix', () => {
    // TODO: get diagnostics for active file, send to agent, fix
  });

  const status = vscode.commands.registerCommand('rta.agent.status', () => {
    // TODO: show sidecar status
  });

  context.subscriptions.push(
    toggleChat, addSelection, addFile, explain, edit, fix, status
  );

  console.log('RTA extension activated');
}

function deactivate() {
  console.log('RTA extension deactivated');
}

module.exports = { activate, deactivate };
