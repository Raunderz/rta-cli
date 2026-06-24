import { useState, useEffect, useRef, useCallback } from 'react';
import { resolveBackendUrl } from './utils/backend';
import {
  uploadWorkspace,
  downloadWorkspace,
  applyDownload,
  deleteRemovedFiles,
  clearSnapshot,
} from './utils/workspaceSync';

const AUTO_SAVE_INTERVAL = 120000; // 2 minutes

export default function useSession({ apiKey, reloadFiles }) {
  const [session, setSession] = useState({ id: null, status: 'off', ws_url: null });
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [syncStatus, setSyncStatus] = useState('');
  const [syncProgress, setSyncProgress] = useState(null); // null | { phase, percent }
  const [conflicts, setConflicts] = useState(null);
  const [pendingDownload, setPendingDownload] = useState(null);
  const autoSaveRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => { mountedRef.current = false; };
  }, []);

  // Session recovery: check for existing session on mount
  useEffect(() => {
    if (!apiKey) return;
    (async () => {
      try {
        const backendUrl = await resolveBackendUrl();
        const resp = await fetch(`${backendUrl}/v1/executor/envs`, {
          headers: { 'X-API-KEY': apiKey.trim() },
        });
        if (resp.ok) {
          const envs = await resp.json();
          if (envs && envs.length > 0) {
            const env = envs[0];
            if (mountedRef.current) {
              setSession({ id: env.id, status: 'on', ws_url: `/ws/env/${env.id}` });
            }
          }
        }
      } catch (e) {
        // Silent — session recovery is best-effort
      }
    })();
  }, [apiKey]);

  // Auto-save: periodically upload workspace while session is active
  const autoSave = useCallback(async () => {
    if (!session.id || session.status !== 'on' || !apiKey) return;
    try {
      const backendUrl = await resolveBackendUrl();
      await uploadWorkspace(apiKey.trim(), session.id, backendUrl);
    } catch (e) {
      console.warn('Auto-save failed:', e.message);
    }
  }, [session.id, session.status, apiKey]);

  useEffect(() => {
    if (session.status === 'on' && session.id) {
      autoSaveRef.current = setInterval(autoSave, AUTO_SAVE_INTERVAL);
    }
    return () => {
      if (autoSaveRef.current) clearInterval(autoSaveRef.current);
    };
  }, [session.status, session.id, autoSave]);

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
        setSyncProgress({ phase: 'upload', percent: 0 });
        await uploadWorkspace(apiKey.trim(), data.id, backendUrl);
        setSyncProgress({ phase: 'upload', percent: 100 });
        setSyncStatus('');
        setSyncProgress(null);
      } catch (uploadErr) {
        console.error('Workspace upload failed:', uploadErr);
        setSyncStatus('Upload failed');
        setSyncProgress(null);
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
        setSyncProgress({ phase: 'download', percent: 0 });
        const result = await downloadWorkspace(apiKey.trim(), session.id, backendUrl);
        setSyncProgress({ phase: 'download', percent: 100 });

        if (result.conflicts && result.conflicts.length > 0) {
          setPendingDownload(result);
          setConflicts(result.conflicts);
          setSyncStatus('');
          setSyncProgress(null);
          return;
        }

        await reloadFiles();
        setSyncStatus('');
        setSyncProgress(null);
      } catch (downloadErr) {
        console.error('Workspace download failed:', downloadErr);
        setSyncStatus('Download failed');
        setSyncProgress(null);
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
    setSyncProgress(null);
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
    setSyncProgress(null);

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
    syncProgress,
    conflicts,
    startSession,
    endSession,
    resolveConflicts,
    cancelConflicts,
  };
}
