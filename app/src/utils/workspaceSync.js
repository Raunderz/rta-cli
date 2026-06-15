import * as FileSystem from 'expo-file-system/legacy';
import JSZip from 'jszip';

const WORKSPACE_DIR = `${FileSystem.documentDirectory}workspace/`;

const EXCLUDE_DIRS = ['.venv', 'node_modules', '__pycache__', '.git', '.expo'];

function simpleHash(str) {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0xffffffff;
  }
  return hash.toString(36);
}

async function collectFiles(dir, baseDir = dir) {
  const items = await FileSystem.readDirectoryAsync(dir);
  const files = [];

  for (const name of items) {
    if (EXCLUDE_DIRS.includes(name)) continue;

    const uri = dir + name;
    const info = await FileSystem.getInfoAsync(uri);

    if (info.isDirectory) {
      const children = await collectFiles(uri + '/', baseDir);
      files.push(...children);
    } else {
      const relativePath = uri.slice(baseDir.length);
      const content = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
      files.push({ path: relativePath, content });
    }
  }

  return files;
}

export async function snapshotWorkspace() {
  const files = await collectFiles(WORKSPACE_DIR);
  const snapshot = {};
  for (const file of files) {
    snapshot[file.path] = simpleHash(file.content);
  }
  try {
    await FileSystem.writeAsStringAsync(
      FileSystem.documentDirectory + 'workspace_snapshot.json',
      JSON.stringify(snapshot)
    );
  } catch (e) {
    console.error('Failed to save snapshot:', e);
  }
  return snapshot;
}

export async function loadSnapshot() {
  try {
    const uri = FileSystem.documentDirectory + 'workspace_snapshot.json';
    const info = await FileSystem.getInfoAsync(uri);
    if (!info.exists) return {};
    const json = await FileSystem.readAsStringAsync(uri);
    return JSON.parse(json);
  } catch {
    return {};
  }
}

export async function clearSnapshot() {
  try {
    const uri = FileSystem.documentDirectory + 'workspace_snapshot.json';
    const info = await FileSystem.getInfoAsync(uri);
    if (info.exists) {
      await FileSystem.deleteAsync(uri);
    }
  } catch {}
}

async function hashZipFiles(zip) {
  const hashes = {};
  for (const [path, entry] of Object.entries(zip.files)) {
    if (entry.dir) continue;
    const content = await entry.async('base64');
    hashes[path] = simpleHash(content);
  }
  return hashes;
}

export async function downloadWorkspaceWithConflicts(apiKey, sessionId, backendUrl) {
  const snapshot = await loadSnapshot();

  const resp = await fetch(`${backendUrl}/v1/executor/env/${sessionId}/download`, {
    method: 'GET',
    headers: { 'X-API-KEY': apiKey },
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || 'Failed to download workspace');
  }

  const arrayBuffer = await resp.arrayBuffer();
  const zip = await JSZip.loadAsync(arrayBuffer);
  const remoteHashes = await hashZipFiles(zip);

  const localFiles = await collectFiles(WORKSPACE_DIR);
  const localHashes = {};
  for (const f of localFiles) {
    localHashes[f.path] = simpleHash(f.content);
  }

  const conflicts = [];
  const remoteOnly = [];
  const unchanged = [];

  for (const [path, remoteHash] of Object.entries(remoteHashes)) {
    const localHash = localHashes[path];
    const snapshotHash = snapshot[path];

    if (!localHash) {
      remoteOnly.push(path);
    } else if (localHash !== remoteHash) {
      const userChanged = snapshotHash !== localHash;
      const aiChanged = snapshotHash !== remoteHash;

      if (userChanged && aiChanged) {
        conflicts.push({ path, localHash, remoteHash, snapshotHash });
      } else if (aiChanged) {
        remoteOnly.push(path);
      }
      // else: user changed but AI didn't → keep local (do nothing)
    } else {
      unchanged.push(path);
    }
  }

  const localOnly = Object.keys(localHashes).filter(p => !remoteHashes[p] && snapshot[p]);

  return { zip, conflicts, remoteOnly, localOnly, unchanged, remoteHashes };
}

export async function applyDownload(zip, skipPaths = []) {
  for (const [path, zipEntry] of Object.entries(zip.files)) {
    if (zipEntry.dir) continue;
    if (skipPaths.includes(path)) continue;

    const content = await zipEntry.async('base64');
    const fileUri = WORKSPACE_DIR + path;

    const parts = path.split('/');
    if (parts.length > 1) {
      const dirPath = WORKSPACE_DIR + parts.slice(0, -1).join('/') + '/';
      await FileSystem.makeDirectoryAsync(dirPath, { intermediates: true });
    }

    await FileSystem.writeAsStringAsync(fileUri, content, { encoding: FileSystem.EncodingType.Base64 });
  }
}

export async function deleteRemovedFiles(remoteHashes) {
  const localFiles = await collectFiles(WORKSPACE_DIR);
  for (const file of localFiles) {
    if (!(file.path in remoteHashes)) {
      await FileSystem.deleteAsync(WORKSPACE_DIR + file.path);
    }
  }
}

export async function uploadWorkspace(apiKey, sessionId, backendUrl) {
  await snapshotWorkspace();

  const files = await collectFiles(WORKSPACE_DIR);

  const zip = new JSZip();
  for (const file of files) {
    zip.file(file.path, file.content, { base64: true });
  }

  const zipBlob = await zip.generateAsync({ type: 'uint8array', compression: 'DEFLATED' });

  const formData = new FormData();
  const zipFile = new Blob([zipBlob], { type: 'application/zip' });
  formData.append('workspace', zipFile, 'workspace.zip');

  const resp = await fetch(`${backendUrl}/v1/executor/env/${sessionId}/upload`, {
    method: 'POST',
    headers: { 'X-API-KEY': apiKey },
    body: formData,
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || 'Failed to upload workspace');
  }

  return true;
}

export async function downloadWorkspace(apiKey, sessionId, backendUrl) {
  const result = await downloadWorkspaceWithConflicts(apiKey, sessionId, backendUrl);

  if (result.conflicts.length > 0) {
    return result;
  }

  await applyDownload(result.zip);
  await deleteRemovedFiles(result.remoteHashes);
  await clearSnapshot();

  return { ...result, applied: true };
}
