import { useState } from 'react';
import { resolveBackendUrl } from './utils/backend';
import {
  uploadWorkspace,
  downloadWorkspace,
  applyDownload,
  deleteRemovedFiles,
  clearSnapshot,
} from './utils/workspaceSync';

export default function useSession({ apiKey, reloadFiles }) {
  const [session, setSession] = useState({ id: null, status: 'off', ws_url: null });
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [syncStatus, setSyncStatus] = useState('');
  const [conflicts, setConflicts] = useState(null);
  const [pendingDownload, setPendingDownload] = useState(null);

  async function startSession() {
    if (isStartingSession) return;
    setIsStartingSession(true);
    try {
      const backendUrl = await resolveBackendUrl();
      const resp = await fetch(`${backendUrl}/v1/executor/env`, {
        method: 'POST',
        headers: {
          'X-API-KEY': apiKey.trim(),
          'Content-Type': 'application/json',
        },
      });

      if (!resp.ok) {
        const err = await resp.text();
        throw new Error(err || 'Failed to start session');
      }

      const data = await resp.json();
      setSession({ id: data.id, status: 'on', ws_url: data.ws_url });

      try {
        setSyncStatus('Uploading project...');
        await uploadWorkspace(apiKey.trim(), data.id, backendUrl);
        setSyncStatus('');
      } catch (uploadErr) {
        console.error('Workspace upload failed:', uploadErr);
        setSyncStatus('Upload failed');
      }
    } catch (e) {
      alert('Session Error: ' + e.message);
    } finally {
      setIsStartingSession(false);
    }
  }

  async function endSession() {
    if (!session.id) return;
    try {
      const backendUrl = await resolveBackendUrl();

      try {
        setSyncStatus('Downloading project...');
        const result = await downloadWorkspace(apiKey.trim(), session.id, backendUrl);

        if (result.conflicts && result.conflicts.length > 0) {
          setPendingDownload(result);
          setConflicts(result.conflicts);
          setSyncStatus('');
          return;
        }

        await reloadFiles();
        setSyncStatus('');
      } catch (downloadErr) {
        console.error('Workspace download failed:', downloadErr);
        setSyncStatus('Download failed');
      }

      await fetch(`${backendUrl}/v1/executor/env/${session.id}`, {
        method: 'DELETE',
        headers: { 'X-API-KEY': apiKey.trim() },
      });
      setSession({ id: null, status: 'off', ws_url: null });
    } catch (e) {
      console.error('Failed to end session', e);
      setSession({ id: null, status: 'off', ws_url: null });
    }
  }

  async function resolveConflicts({ remotePaths, localPaths }) {
    if (!pendingDownload) return;

    const skipPaths = localPaths;
    await applyDownload(pendingDownload.zip, skipPaths);

    const remoteHashes = {};
    for (const [path, entry] of Object.entries(pendingDownload.zip.files)) {
      if (!entry.dir) remoteHashes[path] = true;
    }
    await deleteRemovedFiles(remoteHashes);
    await clearSnapshot();

    setConflicts(null);
    setPendingDownload(null);
    await reloadFiles();

    const backendUrl = await resolveBackendUrl();
    if (session.id) {
      await fetch(`${backendUrl}/v1/executor/env/${session.id}`, {
        method: 'DELETE',
        headers: { 'X-API-KEY': apiKey.trim() },
      });
      setSession({ id: null, status: 'off', ws_url: null });
    }
  }

  async function cancelConflicts() {
    setConflicts(null);
    setPendingDownload(null);
    setSyncStatus('');

    const backendUrl = await resolveBackendUrl();
    if (session.id) {
      await fetch(`${backendUrl}/v1/executor/env/${session.id}`, {
        method: 'DELETE',
        headers: { 'X-API-KEY': apiKey.trim() },
      });
      setSession({ id: null, status: 'off', ws_url: null });
    }
  }

  return {
    session,
    isStartingSession,
    syncStatus,
    conflicts,
    startSession,
    endSession,
    resolveConflicts,
    cancelConflicts,
  };
}
