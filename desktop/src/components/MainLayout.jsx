import { h } from 'preact';
import { ChatPanel } from './ChatPanel.jsx';
import { EditorPanel } from './EditorPanel.jsx';

export function MainLayout() {
  return (
    <div className="h-screen w-screen flex overflow-hidden">
      {/* Left Sidebar - Chat */}
      <div className="w-[350px] min-w-[280px] max-w-[500px] flex-shrink-0">
        <ChatPanel />
      </div>

      {/* Resizer */}
      <div className="w-1 bg-[#3c3c3c] hover:bg-[#007acc] cursor-col-resize transition-colors" />

      {/* Main Editor Area */}
      <div className="flex-1 min-w-0">
        <EditorPanel />
      </div>
    </div>
  );
}