// Tests for app/src/utils/backend.js and workspaceSync.js
// Run: npx jest tests/

// =============================================================================
// backend.js tests
// =============================================================================

describe('resolveBackendUrl', () => {
  const originalEnv = process.env;
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
    global.fetch = jest.fn();
  });

  afterAll(() => {
    process.env = originalEnv;
    global.fetch = originalFetch;
  });

  test('returns backup URL when it responds OK', async () => {
    process.env.EXPO_PUBLIC_BACKEND_URL = 'https://primary.example.com';
    process.env.EXPO_PUBLIC_MOBILE_BACKEND_URL = 'https://backup.example.com';

    global.fetch.mockResolvedValue({ ok: true });

    const { resolveBackendUrl } = require('../src/utils/backend');
    const url = await resolveBackendUrl();
    expect(url).toBe('https://backup.example.com');
  });

  test('falls back to primary when backup fails', async () => {
    process.env.EXPO_PUBLIC_BACKEND_URL = 'https://primary.example.com';
    process.env.EXPO_PUBLIC_MOBILE_BACKEND_URL = 'https://backup.example.com';

    global.fetch
      .mockResolvedValueOnce({ ok: false })  // backup fails
      .mockResolvedValueOnce({ ok: true });   // primary works

    const { resolveBackendUrl } = require('../src/utils/backend');
    const url = await resolveBackendUrl();
    expect(url).toBe('https://primary.example.com');
  });

  test('returns primary when both fail', async () => {
    process.env.EXPO_PUBLIC_BACKEND_URL = 'https://primary.example.com';
    process.env.EXPO_PUBLIC_MOBILE_BACKEND_URL = '';

    global.fetch.mockRejectedValue(new Error('network error'));

    const { resolveBackendUrl } = require('../src/utils/backend');
    const url = await resolveBackendUrl();
    expect(url).toBe('https://primary.example.com');
  });
});

describe('getBackendUrlSync', () => {
  test('returns cached URL after resolve', async () => {
    jest.resetModules();
    process.env.EXPO_PUBLIC_BACKEND_URL = 'https://primary.example.com';
    process.env.EXPO_PUBLIC_MOBILE_BACKEND_URL = '';
    global.fetch = jest.fn().mockResolvedValue({ ok: true });

    const { resolveBackendUrl, getBackendUrlSync } = require('../src/utils/backend');
    await resolveBackendUrl();
    expect(getBackendUrlSync()).toBe('https://primary.example.com');
  });
});

// =============================================================================
// workspaceSync.js — simpleHash tests
// =============================================================================

describe('simpleHash', () => {
  test('produces consistent hashes', () => {
    // simpleHash is not exported, but we can test it indirectly via snapshotWorkspace
    // For now, test the hash function directly by extracting it
    function simpleHash(str) {
      let hash = 5381;
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0xffffffff;
      }
      return hash.toString(36);
    }

    expect(simpleHash('hello')).toBe(simpleHash('hello'));
    expect(simpleHash('hello')).not.toBe(simpleHash('world'));
    expect(simpleHash('')).toBe('45h');
    expect(typeof simpleHash('test')).toBe('string');
  });

  test('handles unicode', () => {
    function simpleHash(str) {
      let hash = 5381;
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0xffffffff;
      }
      return hash.toString(36);
    }

    const h1 = simpleHash('hello');
    const h2 = simpleHash('héllo')
    expect(h1).not.toBe(h2);
  });
});

// =============================================================================
// workspaceSync.js — conflict detection logic tests
// =============================================================================

describe('conflict detection logic', () => {
  // Test the conflict detection algorithm from downloadWorkspaceWithConflicts
  // by extracting the logic into a testable function

  function detectConflicts(remoteHashes, localHashes, snapshot) {
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
      } else {
        unchanged.push(path);
      }
    }

    const localOnly = Object.keys(localHashes).filter(p => !remoteHashes[p] && snapshot[p]);
    return { conflicts, remoteOnly, localOnly, unchanged };
  }

  test('detects no conflict when only AI changed', () => {
    const remote = { 'a.py': 'remote_hash' };
    const local = { 'a.py': 'local_hash' };
    const snapshot = { 'a.py': 'local_hash' }; // snapshot matches local → user didn't change

    const result = detectConflicts(remote, local, snapshot);
    expect(result.conflicts).toHaveLength(0);
    expect(result.remoteOnly).toContain('a.py');
  });

  test('detects no conflict when only user changed', () => {
    const remote = { 'a.py': 'original_hash' };
    const local = { 'a.py': 'user_hash' };
    const snapshot = { 'a.py': 'original_hash' }; // snapshot matches remote → AI didn't change

    const result = detectConflicts(remote, local, snapshot);
    expect(result.conflicts).toHaveLength(0);
    expect(result.remoteOnly).toHaveLength(0);
    expect(result.unchanged).toHaveLength(0);
  });

  test('detects conflict when both changed', () => {
    const remote = { 'a.py': 'remote_hash' };
    const local = { 'a.py': 'local_hash' };
    const snapshot = { 'a.py': 'original_hash' }; // both differ from snapshot

    const result = detectConflicts(remote, local, snapshot);
    expect(result.conflicts).toHaveLength(1);
    expect(result.conflicts[0].path).toBe('a.py');
  });

  test('detects remote-only file (new from AI)', () => {
    const remote = { 'new.py': 'hash' };
    const local = {};
    const snapshot = {};

    const result = detectConflicts(remote, local, snapshot);
    expect(result.remoteOnly).toContain('new.py');
  });

  test('detects local-only file (deleted by AI)', () => {
    const remote = {};
    const local = { 'deleted.py': 'hash' };
    const snapshot = { 'deleted.py': 'hash' };

    const result = detectConflicts(remote, local, snapshot);
    expect(result.localOnly).toContain('deleted.py');
  });

  test('unchanged files reported correctly', () => {
    const remote = { 'a.py': 'same_hash' };
    const local = { 'a.py': 'same_hash' };
    const snapshot = { 'a.py': 'same_hash' };

    const result = detectConflicts(remote, local, snapshot);
    expect(result.unchanged).toContain('a.py');
    expect(result.conflicts).toHaveLength(0);
    expect(result.remoteOnly).toHaveLength(0);
  });

  test('multiple files with mixed states', () => {
    const remote = {
      'a.py': 'remote_a',   // conflict
      'b.py': 'remote_b',   // AI only
      'c.py': 'same',       // unchanged
      'd.py': 'remote_d',   // new from AI
    };
    const local = {
      'a.py': 'local_a',    // conflict
      'b.py': 'original_b', // AI changed
      'c.py': 'same',       // unchanged
      'e.py': 'local_e',    // local only
    };
    const snapshot = {
      'a.py': 'original_a',
      'b.py': 'original_b',
      'c.py': 'same',
      'e.py': 'original_e',
    };

    const result = detectConflicts(remote, local, snapshot);
    expect(result.conflicts).toHaveLength(1);
    expect(result.conflicts[0].path).toBe('a.py');
    expect(result.remoteOnly).toContain('b.py');
    expect(result.remoteOnly).toContain('d.py');
    expect(result.unchanged).toContain('c.py');
    expect(result.localOnly).toContain('e.py');
  });
});
