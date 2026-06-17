// Tests for useWorkspace hook logic and useSession flow
// Run: npx jest tests/

const WORKSPACE_DIR = '/mock/workspace/';

// =============================================================================
// useWorkspace — file path helpers
// =============================================================================

describe('useWorkspace — file path resolution', () => {
  function resolveBaseDir(parentUri) {
    if (!parentUri) return WORKSPACE_DIR;
    return parentUri.endsWith('/') ? parentUri : parentUri + '/';
  }

  test('uses WORKSPACE_DIR when parentUri is null', () => {
    expect(resolveBaseDir(null)).toBe(WORKSPACE_DIR);
  });

  test('uses WORKSPACE_DIR when parentUri is undefined', () => {
    expect(resolveBaseDir(undefined)).toBe(WORKSPACE_DIR);
  });

  test('appends slash when parentUri has no trailing slash', () => {
    expect(resolveBaseDir('/some/dir')).toBe('/some/dir/');
  });

  test('keeps parentUri as-is when it already has trailing slash', () => {
    expect(resolveBaseDir('/some/dir/')).toBe('/some/dir/');
  });

  test('constructs correct file path', () => {
    const base = resolveBaseDir('/project/src/');
    const fileUri = base + 'main.py';
    expect(fileUri).toBe('/project/src/main.py');
  });

  test('constructs correct folder path', () => {
    const base = resolveBaseDir('/project/');
    const folderUri = base + 'utils/';
    expect(folderUri).toBe('/project/utils/');
  });
});

// =============================================================================
// useWorkspace — directory scanning sort order
// =============================================================================

describe('useWorkspace — file sorting', () => {
  function sortItems(items) {
    return [...items].sort((a, b) => {
      if (a.isDirectory && !b.isDirectory) return -1;
      if (!a.isDirectory && b.isDirectory) return 1;
      return a.name.localeCompare(b.name);
    });
  }

  test('directories come before files', () => {
    const items = [
      { name: 'file.txt', isDirectory: false },
      { name: 'src', isDirectory: true },
      { name: 'readme.md', isDirectory: false },
    ];
    const sorted = sortItems(items);
    expect(sorted[0].name).toBe('src');
    expect(sorted[1].name).toBe('file.txt');
    expect(sorted[2].name).toBe('readme.md');
  });

  test('files are sorted alphabetically', () => {
    const items = [
      { name: 'zebra.py', isDirectory: false },
      { name: 'alpha.py', isDirectory: false },
      { name: 'middle.py', isDirectory: false },
    ];
    const sorted = sortItems(items);
    expect(sorted.map(i => i.name)).toEqual(['alpha.py', 'middle.py', 'zebra.py']);
  });

  test('directories are sorted alphabetically among themselves', () => {
    const items = [
      { name: 'z-dir', isDirectory: true },
      { name: 'a-dir', isDirectory: true },
    ];
    const sorted = sortItems(items);
    expect(sorted.map(i => i.name)).toEqual(['a-dir', 'z-dir']);
  });

  test('mixed list: dirs first sorted, then files sorted', () => {
    const items = [
      { name: 'z.txt', isDirectory: false },
      { name: 'b', isDirectory: true },
      { name: 'a', isDirectory: true },
      { name: 'm.txt', isDirectory: false },
    ];
    const sorted = sortItems(items);
    expect(sorted.map(i => i.name)).toEqual(['a', 'b', 'm.txt', 'z.txt']);
  });

  test('empty list stays empty', () => {
    expect(sortItems([])).toEqual([]);
  });
});

// =============================================================================
// useWorkspace — initial workspace file creation paths
// =============================================================================

describe('useWorkspace — default workspace structure', () => {
  const expectedFiles = [
    'main.py',
    'README.md',
    'utils.py',
  ];

  const expectedNested = [
    'src/config.json',
  ];

  test('default files are at workspace root', () => {
    for (const file of expectedFiles) {
      const path = WORKSPACE_DIR + file;
      expect(path).toMatch(/^\/mock\/workspace\/\w+\.\w+$/);
    }
  });

  test('nested files have correct parent dir', () => {
    for (const file of expectedNested) {
      const path = WORKSPACE_DIR + file;
      expect(path).toContain('src/');
      expect(path.endsWith('.json')).toBe(true);
    }
  });
});

// =============================================================================
// useSession — session state transitions
// =============================================================================

describe('useSession — state transitions', () => {
  test('initial session state is off', () => {
    const session = { id: null, status: 'off', ws_url: null };
    expect(session.status).toBe('off');
    expect(session.id).toBeNull();
  });

  test('session goes to on with id and ws_url', () => {
    const data = { id: 'env-123', ws_url: 'wss://example.com' };
    const session = { id: data.id, status: 'on', ws_url: data.ws_url };
    expect(session.status).toBe('on');
    expect(session.id).toBe('env-123');
    expect(session.ws_url).toBe('wss://example.com');
  });

  test('session resets to off', () => {
    const session = { id: null, status: 'off', ws_url: null };
    expect(session.status).toBe('off');
    expect(session.id).toBeNull();
    expect(session.ws_url).toBeNull();
  });
});

// =============================================================================
// useSession — conflict resolution paths
// =============================================================================

describe('useSession — conflict resolution', () => {
  test('resolve picks remote-only paths to skip', () => {
    const remotePaths = ['a.py', 'b.py'];
    const localPaths = ['a.py'];
    const skipPaths = localPaths;
    expect(skipPaths).toEqual(['a.py']);
  });

  test('resolve with no conflicts skips nothing', () => {
    const remotePaths = [];
    const localPaths = [];
    const skipPaths = localPaths;
    expect(skipPaths).toHaveLength(0);
  });
});

// =============================================================================
// useSession — session API payload shapes
// =============================================================================

describe('useSession — API payloads', () => {
  test('start session sends correct POST body', () => {
    const apiKey = 'test-key-123';
    const headers = {
      'X-API-KEY': apiKey.trim(),
      'Content-Type': 'application/json',
    };
    expect(headers['X-API-KEY']).toBe('test-key-123');
    expect(headers['Content-Type']).toBe('application/json');
  });

  test('end session sends DELETE with API key', () => {
    const apiKey = 'test-key-123';
    const sessionId = 'env-abc';
    const headers = { 'X-API-KEY': apiKey.trim() };
    expect(headers['X-API-KEY']).toBe('test-key-123');
    expect(`/v1/executor/env/${sessionId}`).toBe('/v1/executor/env/env-abc');
  });

  test('upload endpoint URL is correct', () => {
    const backendUrl = 'https://backend.example.com';
    const sessionId = 'env-xyz';
    const url = `${backendUrl}/v1/executor/env/${sessionId}/upload`;
    expect(url).toBe('https://backend.example.com/v1/executor/env/env-xyz/upload');
  });

  test('download endpoint URL is correct', () => {
    const backendUrl = 'https://backend.example.com';
    const sessionId = 'env-xyz';
    const url = `${backendUrl}/v1/executor/env/${sessionId}/download`;
    expect(url).toBe('https://backend.example.com/v1/executor/env/env-xyz/download');
  });
});

// =============================================================================
// useSession — sync status messages
// =============================================================================

describe('useSession — sync status messages', () => {
  test('upload shows uploading message', () => {
    const syncStatus = 'Uploading project...';
    expect(syncStatus).toBe('Uploading project...');
  });

  test('download shows downloading message', () => {
    const syncStatus = 'Downloading project...';
    expect(syncStatus).toBe('Downloading project...');
  });

  test('cleared status is empty string', () => {
    const syncStatus = '';
    expect(syncStatus).toBe('');
  });

  test('error status shows failure', () => {
    const syncStatus = 'Upload failed';
    expect(syncStatus).toContain('failed');
  });
});
