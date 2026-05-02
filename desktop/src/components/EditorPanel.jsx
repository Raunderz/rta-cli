import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import Editor from '@monaco-editor/react';
import { readTextFile, writeTextFile } from '@tauri-apps/plugin-fs';

const getLanguage = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const langMap = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    py: 'python',
    json: 'json',
    md: 'markdown',
    html: 'html',
    css: 'css',
    // add more
  };
  return langMap[ext] || 'plaintext';
};

export function EditorPanel({ selectedFile }) {
  const [openFiles, setOpenFiles] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  const [content, setContent] = useState('');

  useEffect(() => {
    if (selectedFile && !selectedFile.isDir) {
      const existing = openFiles.find((f) => f.path === selectedFile.path);
      if (!existing) {
        setOpenFiles((prev) => [...prev, selectedFile]);
      }
      setActiveFile(selectedFile);
      loadFile(selectedFile);
    }
  }, [selectedFile]);

  const loadFile = async (file) => {
    if (!file) return;

    try {
      if (file.file) {
        const text = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = () => reject(reader.error);
          reader.readAsText(file.file);
        });
        setContent(text);
      } else {
        const text = await readTextFile(file.path);
        setContent(text);
      }
    } catch (err) {
      console.error('Failed to load file', err);
      setContent('');
    }
  };

  const saveFile = async () => {
    if (!activeFile) return;

    try {
      if (activeFile.file) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = activeFile.name;
        a.click();
        URL.revokeObjectURL(url);
        alert('Downloaded file content. Save is only available in the Tauri desktop app.');
        return;
      }

      await writeTextFile(activeFile.path, content);
      alert('File saved');
    } catch (err) {
      console.error('Failed to save file', err);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveFile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeFile, content]);

  const closeTab = (file) => {
    setOpenFiles(prev => prev.filter(f => f !== file));
    if (activeFile === file) {
      setActiveFile(null);
      setContent('');
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#09090b]">
      {/* Tab Bar */}
      <div className="flex bg-[#141417] border-b border-white/10">
        {openFiles.map((file) => (
          <div
            key={file.path || file.name}
            className={`px-4 py-2 cursor-pointer border-r border-white/10 ${
              activeFile === file ? 'bg-[#09090b]' : 'hover:bg-white/10'
            }`}
            onClick={() => {
              setActiveFile(file);
              loadFile(file);
            }}
          >
            <span className="text-sm text-white">{file.name}</span>
            <button
              className="ml-2 text-gray-400 hover:text-white"
              onClick={(e) => {
                e.stopPropagation();
                closeTab(file);
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      {/* Editor */}
      <div className="flex-1">
        {activeFile ? (
          <Editor
            height="100%"
            language={getLanguage(activeFile.name)}
            value={content}
            onChange={setContent}
            theme="vs-dark"
          />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            Select a file to edit
          </div>
        )}
      </div>
    </div>
  );
}