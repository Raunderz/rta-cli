import { h } from 'preact';
import { ChatPanel } from './ChatPanel.jsx';
import { EditorPanel } from './EditorPanel.jsx';

export function MainLayout() {
  return (
    <div className="min-h-[100dvh] w-screen flex overflow-hidden bg-[#09090b] selection:bg-blue-500/30">
      {/* Left Sidebar - Chat */}
      <div className="w-[380px] min-w-[300px] max-w-[600px] flex-shrink-0 shadow-[4px_0_24px_rgba(0,0,0,0.3)] z-10">
        <ChatPanel />
      </div>

      {/* Resizer */}
      <div className="w-1.5 bg-[#09090b] hover:bg-blue-500/40 cursor-col-resize transition-all duration-300 relative group">
        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-[1px] bg-white/5 group-hover:bg-blue-500/50 transition-colors" />
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 min-w-0 bg-[#09090b]">
        <EditorPanel />
      </div>
    </div>
  );
}