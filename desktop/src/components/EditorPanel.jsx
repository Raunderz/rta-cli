import { h } from 'preact';
import { useState } from 'preact/hooks';

export function EditorPanel() {
  const [tabs, setTabs] = useState([
    { id: 1, name: "welcome.txt", content: "Welcome to RTA Desktop\n\nStart by opening a file from the explorer or chat with AI to create/edit files.\n\nThis is a placeholder for Monaco Editor integration." }
  ]);
  const [activeTab, setActiveTab] = useState(1);

  const currentTab = tabs.find(t => t.id === activeTab);

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* Tab Bar */}
      <div className="flex items-center bg-[#252526] border-b border-[#3c3c3c] overflow-x-auto">
        {tabs.map(tab => (
          <div
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-3 py-2 text-sm cursor-pointer border-r border-[#3c3c3c] min-w-[120px] ${
              activeTab === tab.id 
                ? "bg-[#1e1e1e] text-[#ffffff]" 
                : "bg-[#2d2d2d] text-[#969696] hover:bg-[#2a2d2e]"
            }`}
          >
            <span>{tab.name}</span>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                setTabs(tabs.filter(t => t.id !== tab.id));
                if (activeTab === tab.id && tabs.length > 1) {
                  setActiveTab(tabs.find(t => t.id !== tab.id).id);
                }
              }}
              className="text-[#969696] hover:text-[#ffffff] ml-auto"
            >
              ×
            </button>
          </div>
        ))}
        <div className="px-3 py-2 text-[#969696] hover:text-[#ffffff] cursor-pointer">+</div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 relative">
        <textarea
          value={currentTab?.content || ""}
          onInput={(e) => {
            const updated = tabs.map(t => 
              t.id === activeTab ? { ...t, content: e.target.value } : t
            );
            setTabs(updated);
          }}
          className="w-full h-full bg-[#1e1e1e] text-[#d4d4d4] p-4 font-mono text-sm resize-none focus:outline-none"
          spellCheck={false}
        />
        
        {/* Placeholder overlay when no tabs */}
        {!currentTab && (
          <div className="absolute inset-0 flex items-center justify-center text-[#6b6b6b]">
            <p>Open a file to start editing</p>
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between px-3 py-1 bg-[#007acc] text-white text-xs">
        <div className="flex items-center gap-4">
          <span>main.js</span>
          <span>UTF-8</span>
          <span>JavaScript</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Ln 1, Col 1</span>
          <span>Spaces: 2</span>
        </div>
      </div>
    </div>
  );
}