import { useState, useEffect } from 'react';
import * as FileSystem from 'expo-file-system/legacy';

const WORKSPACE_DIR = `${FileSystem.documentDirectory}workspace/`;

export default function useWorkspace() {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    initWorkspace();
  }, []);

  async function initWorkspace() {
    try {
      const info = await FileSystem.getInfoAsync(WORKSPACE_DIR);
      if (!info.exists) {
        await FileSystem.makeDirectoryAsync(WORKSPACE_DIR, { intermediates: true });
        await FileSystem.writeAsStringAsync(WORKSPACE_DIR + 'main.py', 'import os\n\nprint("Hello from Rta!")\n');
        await FileSystem.writeAsStringAsync(WORKSPACE_DIR + 'README.md', '# Rta Workspace\n\nThis is a real local project stored on your device.\n');
        await FileSystem.writeAsStringAsync(WORKSPACE_DIR + 'utils.py', 'def add(a, b):\n    return a + b\n');
        const srcDir = WORKSPACE_DIR + 'src/';
        await FileSystem.makeDirectoryAsync(srcDir, { intermediates: true });
        await FileSystem.writeAsStringAsync(srcDir + 'config.json', '{\n  "version": "1.0.0"\n}\n');
      }
      await reloadFiles();
    } catch (e) {
      console.error('Failed to initialize workspace directory', e);
    }
  }

  async function reloadFiles() {
    try {
      const scanDir = async (path, parentId = null) => {
        const items = await FileSystem.readDirectoryAsync(path);
        let list = [];

        const infoPromises = items.map(async (name) => {
          const itemUri = path + name;
          const info = await FileSystem.getInfoAsync(itemUri);
          return { name, uri: itemUri, isDirectory: info.isDirectory };
        });

        const resolvedItems = await Promise.all(infoPromises);
        resolvedItems.sort((a, b) => {
          if (a.isDirectory && !b.isDirectory) return -1;
          if (!a.isDirectory && b.isDirectory) return 1;
          return a.name.localeCompare(b.name);
        });

        for (const item of resolvedItems) {
          if (item.isDirectory) {
            const id = item.uri;
            list.push({ id, name: item.name, isDir: true, parentId });
            const children = await scanDir(item.uri + '/', id);
            list = [...list, ...children];
          } else {
            const content = await FileSystem.readAsStringAsync(item.uri);
            list.push({ id: item.uri, name: item.name, isDir: false, parentId, content });
          }
        }
        return list;
      };

      const workspaceFiles = await scanDir(WORKSPACE_DIR);
      setFiles(workspaceFiles);
    } catch (e) {
      console.error('Failed to scan workspace directory', e);
    }
  }

  async function saveFile(id, newContent) {
    try {
      await FileSystem.writeAsStringAsync(id, newContent);
      setFiles(prev => prev.map(f => f.id === id ? { ...f, content: newContent } : f));
      alert('Saved successfully!');
    } catch (e) {
      alert('Failed to save file');
    }
  }

  async function createFile(parentUri, fileName) {
    try {
      const baseDir = parentUri ? (parentUri.endsWith('/') ? parentUri : parentUri + '/') : WORKSPACE_DIR;
      await FileSystem.writeAsStringAsync(baseDir + fileName, '');
      await reloadFiles();
    } catch (e) {
      alert('Failed to create file');
    }
  }

  async function createFolder(parentUri, folderName) {
    try {
      const baseDir = parentUri ? (parentUri.endsWith('/') ? parentUri : parentUri + '/') : WORKSPACE_DIR;
      await FileSystem.makeDirectoryAsync(baseDir + folderName + '/', { intermediates: true });
      await reloadFiles();
    } catch (e) {
      alert('Failed to create folder');
    }
  }

  async function deleteItem(uri) {
    try {
      await FileSystem.deleteAsync(uri);
      await reloadFiles();
    } catch (e) {
      alert('Failed to delete item');
    }
  }

  return { files, reloadFiles, saveFile, createFile, createFolder, deleteItem };
}
