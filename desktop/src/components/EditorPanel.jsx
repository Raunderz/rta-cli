import { h } from 'preact';
import { useState } from 'preact/hooks';

const CloseIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const PlusIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

export function EditorPanel() {
  const [tabs, setTabs] = useState([
    { id: 1, name: "welcome.txt", content: "Welcome to RTA Desktop\n\nStart by opening a file from the explorer or chat with AI to create/edit files.\n\nThis is a placeholder for Monaco Editor integration." }
  ]);
  const [activeTab, setActiveTab] = useState(1);

  const currentTab = tabs.find(t => t.id === activeTab);

  return (
    <div className="h-full flex flex-col bg-[#09090b]">
      {/* Tab Bar */}
      <div className="flex items-center bg-[#141417] border-b border-white/10 overflow-x-auto scrollbar-none">
        {tabs.map(tab => (
          <div
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-3 px-4 py-2.5 text-[13px] cursor-pointer border-r border-white/5 min-w-[140px] transition-all relative group ${
              activeTab === tab.id 
                ? "bg-[#09090b] text-zinc-100" 
                : "text-zinc-400 hover:text-zinc-200 hover:bg-[#1c1c21]"
            }`}
          >
            {activeTab === tab.id && (
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
            )}
            <span className="truncate max-w-[100px] font-medium">{tab.name}</span>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                const newTabs = tabs.filter(t => t.id !== tab.id);
                setTabs(newTabs);
                if (activeTab === tab.id && newTabs.length > 0) {
                  setActiveTab(newTabs[0].id);
                }
              }}
              className={`ml-auto p-1 rounded-md transition-all ${
                activeTab === tab.id 
                  ? "text-zinc-400 hover:text-white hover:bg-zinc-800" 
                  : "text-zinc-600 group-hover:text-zinc-300 group-hover:hover:bg-zinc-700"
              }`}
            >
              <CloseIcon />
            </button>
          </div>
        ))}
        <button className="p-3 text-zinc-400 hover:text-zinc-100 transition-colors">
          <PlusIcon />
        </button>
      </div>

      {/* Editor Area */}
      <div className="flex-1 relative bg-[#09090b]">
        <textarea
          value={currentTab?.content || ""}
          onInput={(e) => {
            const updated = tabs.map(t => 
              t.id === activeTab ? { ...t, content: e.target.value } : t
            );
            setTabs(updated);
          }}
          className="w-full h-full bg-transparent text-zinc-200 p-6 font-mono text-[13px] leading-relaxed resize-none focus:outline-none scrollbar-thin selection:bg-blue-500/30"
          spellCheck={false}
          placeholder="// Your code here..."
        />
        
        {!currentTab && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 space-y-4">
            <div className="w-16 h-16 bg-zinc-900/50 rounded-3xl flex items-center justify-center border border-white/10 animate-pulse">
              <PlusIcon />
            </div>
            <p className="text-sm font-medium">No active files</p>
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#141417] border-t border-white/10 text-zinc-400 text-[11px] font-medium tracking-wide">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-1.5 text-zinc-300 hover:text-white cursor-pointer transition-colors">
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
            <span className="uppercase tracking-wider">Connected</span>
          </div>
          <span className="hover:text-zinc-200 cursor-pointer transition-colors">UTF-8</span>
          <span className="hover:text-zinc-200 cursor-pointer transition-colors">JavaScript</span>
        </div>
        <div className="flex items-center gap-6">
          <span className="hover:text-zinc-200 cursor-pointer transition-colors">Ln 1, Col 1</span>
          <span className="hover:text-zinc-200 cursor-pointer transition-colors">Spaces: 2</span>
        </div>
      </div>
    </div>
  );
}