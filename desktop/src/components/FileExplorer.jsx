import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { open } from '@tauri-apps/plugin-dialog';
import { readDir, mkdir, writeTextFile } from '@tauri-apps/plugin-fs';

const isTauri = () => typeof window !== 'undefined' && typeof window.__TAURI__ !== 'undefined';

const buildBrowserTree = (files) => {
  const root = [];

  const findChild = (children, name) => children.find((node) => node.name === name);

  files.forEach((file) => {
    const relativePath = file.webkitRelativePath || file.name;
    const parts = relativePath.split('/');
    let currentChildren = root;
    let currentPath = '';

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      let node = findChild(currentChildren, part);
      const isFile = index === parts.length - 1;

      if (!node) {
        node = {
          name: part,
          path: currentPath,
          isDir: !isFile,
          expanded: false,
          children: isFile ? null : [],
          file: isFile ? file : undefined,
        };
        currentChildren.push(node);
      }

      if (!isFile) {
        currentChildren = node.children;
      }
    });
  });

  return root;
};

export function FileExplorer({ onFileSelect }) {
  const [workspace, setWorkspace] = useState(null);
  const [files, setFiles] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (workspace && isTauri()) {
      loadFiles(workspace);
    }
  }, [workspace]);

  const loadFiles = async (path) => {
    try {
      const entries = await readDir(path, { recursive: false });
      const fileTree = entries.map((entry) => ({
        ...entry,
        children: entry.children ? [] : null,
        expanded: false,
      }));
      setFiles(fileTree);
    } catch (err) {
      console.error('Failed to load files', err);
    }
  };

  const loadChildren = async (file) => {
    if (file.children && file.children.length === 0) {
      try {
        const entries = await readDir(file.path, { recursive: false });
        file.children = entries.map((entry) => ({
          ...entry,
          children: entry.children ? [] : null,
          expanded: false,
        }));
      } catch (err) {
        console.error('Failed to load children', err);
      }
    }
  };

  const handleBrowserFiles = (event) => {
    const selectedFiles = Array.from(event.target.files || []);
    if (!selectedFiles.length) return;

    // Extract the workspace folder name from the first file's relative path
    // If using webkitdirectory, extract the root folder name
    const firstFile = selectedFiles[0];
    const relativePath = firstFile.webkitRelativePath || firstFile.name;
    const parts = relativePath.split('/');
    const workspaceName = parts.length > 1 ? parts[0] : 'Browser workspace';

    setWorkspace(workspaceName);
    setFiles(buildBrowserTree(selectedFiles));
  };

  const selectWorkspace = async () => {
    if (isTauri()) {
      try {
        const selected = await open({ directory: true });
        if (selected) {
          setWorkspace(selected);
          setSelectedNode(null);
        }
      } catch (err) {
        console.warn('Tauri dialog cancelled or failed', err);
      }
    } else {
      alert('Workspace selection requires the Tauri desktop app. Use Create File/Folder to build a workspace manually.');
    }
  };

  const getParentPath = () => {
    if (!selectedNode) {
      return workspace && workspace !== 'Browser workspace' ? workspace : '';
    }

    const isDir = selectedNode.isDir ?? selectedNode.children !== null;
    if (isDir) {
      return selectedNode.path;
    }

    const parts = selectedNode.path.split('/');
    return parts.slice(0, -1).join('/');
  };

  const insertNode = (entries, targetPath, node) => {
    if (!targetPath) {
      entries.push(node);
      return true;
    }

    const segments = targetPath.split('/');
    let current = { children: entries };

    for (const segment of segments) {
      const child = current.children?.find((item) => item.name === segment && (item.isDir ?? item.children !== null));
      if (!child) {
        return false;
      }
      if (!child.children) child.children = [];
      current = child;
    }

    current.children.push(node);
    return true;
  };

  const createNewFolder = async () => {
    const folderName = prompt('Folder name');
    if (!folderName) return;

    const parentPath = getParentPath();
    const destination = parentPath || (workspace !== 'Browser workspace' ? workspace : '');

    if (isTauri()) {
      try {
        await mkdir(`${destination}/${folderName}`, { recursive: true });
        await loadFiles(workspace);
      } catch (err) {
        console.error('Failed to create folder', err);
      }
      return;
    }

    const newFolder = {
      name: folderName,
      path: destination ? `${destination}/${folderName}` : folderName,
      isDir: true,
      expanded: true,
      children: [],
    };
    setFiles((current) => {
      const updated = [...current];
      if (!insertNode(updated, destination, newFolder)) {
        updated.push(newFolder);
      }
      return updated;
    });
  };

  const createNewFile = async () => {
    const fileName = prompt('File name');
    if (!fileName) return;

    const parentPath = getParentPath();
    const destination = parentPath || (workspace !== 'Browser workspace' ? workspace : '');

    if (isTauri()) {
      try {
        await writeTextFile(`${destination}/${fileName}`, '');
        await loadFiles(workspace);
      } catch (err) {
        console.error('Failed to create file', err);
      }
      return;
    }

    const newFile = {
      name: fileName,
      path: destination ? `${destination}/${fileName}` : fileName,
      isDir: false,
      expanded: false,
      children: null,
      file: new File([''], fileName, { type: 'text/plain' }),
    };
    setFiles((current) => {
      const updated = [...current];
      if (!insertNode(updated, destination, newFile)) {
        updated.push(newFile);
      }
      return updated;
    });
  };

  const handleFileClick = async (file) => {
    const isDir = file.isDir ?? file.children !== null;
    setSelectedNode(file);

    if (isDir) {
      if (!file.expanded) {
        await loadChildren(file);
      }
      file.expanded = !file.expanded;
      setFiles([...files]);
    } else {
      onFileSelect(file);
    }
  };

  const renderFile = (file, level = 0) => {
    const isDir = file.isDir ?? file.children !== null;
    const isSelected = selectedNode?.path === file.path;

    return (
      <div key={file.path}>
        <div
          className={`flex items-center justify-between px-3 py-1.5 rounded-md transition-colors ${isSelected ? 'bg-white/10' : 'hover:bg-white/10'}`}
          style={{ paddingLeft: `${level * 16 + 12}px` }}
          onClick={() => handleFileClick(file)}
        >
          <div className="flex items-center gap-2 text-sm text-slate-200">
            {isDir ? <span className="text-slate-400">📁</span> : <span className="text-slate-500">📄</span>}
            <span>{file.name}</span>
          </div>
          {isDir && <span className="text-slate-500 text-xs">{file.expanded ? '–' : '+'}</span>}
        </div>
        {isDir && file.expanded && file.children?.map((child) => renderFile(child, level + 1))}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-[#0c0c0e] border-r border-white/10">
      <div className="px-4 py-3 border-b border-white/10 bg-[#161616]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Explorer</p>
            <p className="text-sm text-slate-200 truncate max-w-[220px]">{workspace || 'No workspace selected'}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={selectWorkspace}
              className="inline-flex items-center gap-2 text-xs text-slate-300 hover:text-white px-3 py-1 rounded-md bg-white/5 hover:bg-white/10 transition"
            >
              <span>📂</span>
              Open folder
            </button>
            <button
              onClick={createNewFile}
              className="inline-flex items-center gap-1 text-xs text-slate-300 hover:text-white px-3 py-1 rounded-md bg-white/5 hover:bg-white/10 transition"
            >
              <span>+</span>
              File
            </button>
            <button
              onClick={createNewFolder}
              className="inline-flex items-center gap-1 text-xs text-slate-300 hover:text-white px-3 py-1 rounded-md bg-white/5 hover:bg-white/10 transition"
            >
              <span>+</span>
              Folder
            </button>
          </div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          webkitdirectory="true"
          directory="true"
          multiple
          className="hidden"
          onChange={handleBrowserFiles}
        />
      </div>
      <div className="flex-1 overflow-y-auto px-1 py-2 space-y-1">
        {files.map((file) => renderFile(file))}
      </div>
    </div>
  );
}