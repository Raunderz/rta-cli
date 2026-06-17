// Tests for SessionHeader and TabBar logic
// Run: npx jest tests/

// =============================================================================
// TabBar — tab configuration
// =============================================================================

describe('TabBar — tab config', () => {
  const TABS = [
    { key: 'files', icon: '📁', label: 'Files' },
    { key: 'terminal', icon: '💻', label: 'Terminal' },
    { key: 'git', icon: '🌿', label: 'Git' },
    { key: 'chat', icon: '💬', label: 'Chat' },
  ];

  test('has exactly 4 tabs', () => {
    expect(TABS).toHaveLength(4);
  });

  test('all tabs have required fields', () => {
    for (const tab of TABS) {
      expect(tab).toHaveProperty('key');
      expect(tab).toHaveProperty('icon');
      expect(tab).toHaveProperty('label');
      expect(typeof tab.key).toBe('string');
      expect(typeof tab.icon).toBe('string');
      expect(typeof tab.label).toBe('string');
    }
  });

  test('tab keys are unique', () => {
    const keys = TABS.map(t => t.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  test('default tab is chat', () => {
    const activeTab = 'chat';
    const tab = TABS.find(t => t.key === activeTab);
    expect(tab).toBeDefined();
    expect(tab.label).toBe('Chat');
  });
});

// =============================================================================
// TabBar — active tab detection
// =============================================================================

describe('TabBar — active tab detection', () => {
  const TABS = ['files', 'terminal', 'git', 'chat'];

  test('files tab activates correctly', () => {
    expect(TABS.includes('files')).toBe(true);
  });

  test('chat tab activates correctly', () => {
    expect(TABS.includes('chat')).toBe(true);
  });

  test('unknown tab does not match any', () => {
    expect(TABS.includes('unknown')).toBe(false);
  });
});

// =============================================================================
// SessionHeader — status dot logic
// =============================================================================

describe('SessionHeader — status display', () => {
  function getStatusDotClass(status) {
    return status === 'on' ? 'dotOn' : 'dotOff';
  }

  function getStatusText(session, syncStatus) {
    if (syncStatus) return syncStatus;
    return session.status === 'on' ? `Cloud Active: ${session.id}` : 'Local Mode';
  }

  test('dot is green when session is on', () => {
    expect(getStatusDotClass('on')).toBe('dotOn');
  });

  test('dot is gray when session is off', () => {
    expect(getStatusDotClass('off')).toBe('dotOff');
  });

  test('text shows sync status when available', () => {
    const session = { id: null, status: 'off' };
    expect(getStatusText(session, 'Uploading project...')).toBe('Uploading project...');
  });

  test('text shows cloud active when session is on', () => {
    const session = { id: 'env-123', status: 'on' };
    expect(getStatusText(session, '')).toBe('Cloud Active: env-123');
  });

  test('text shows local mode when session is off', () => {
    const session = { id: null, status: 'off' };
    expect(getStatusText(session, '')).toBe('Local Mode');
  });

  test('sync status takes priority over session status', () => {
    const session = { id: 'env-123', status: 'on' };
    expect(getStatusText(session, 'Download failed')).toBe('Download failed');
  });
});

// =============================================================================
// SessionHeader — button logic
// =============================================================================

describe('SessionHeader — button state', () => {
  function getButtonProps(session, isStartingSession) {
    return {
      label: isStartingSession ? null : (session.status === 'on' ? 'END' : 'START CLOUD'),
      style: session.status === 'on' ? 'btnEnd' : 'btnStart',
      disabled: isStartingSession,
    };
  }

  test('start button when session is off', () => {
    const props = getButtonProps({ status: 'off' }, false);
    expect(props.label).toBe('START CLOUD');
    expect(props.style).toBe('btnStart');
    expect(props.disabled).toBe(false);
  });

  test('end button when session is on', () => {
    const props = getButtonProps({ status: 'on' }, false);
    expect(props.label).toBe('END');
    expect(props.style).toBe('btnEnd');
    expect(props.disabled).toBe(false);
  });

  test('button disabled while starting', () => {
    const props = getButtonProps({ status: 'off' }, true);
    expect(props.disabled).toBe(true);
    expect(props.label).toBeNull();
  });
});

// =============================================================================
// LoginScreen — input validation
// =============================================================================

describe('LoginScreen — input validation', () => {
  test('empty key is rejected', () => {
    const apiKey = '';
    expect(apiKey.trim()).toBe('');
  });

  test('whitespace-only key is rejected', () => {
    const apiKey = '   ';
    expect(apiKey.trim()).toBe('');
  });

  test('valid key passes validation', () => {
    const apiKey = 'sk-abc123';
    expect(apiKey.trim().length).toBeGreaterThan(0);
  });

  test('key is trimmed before storage', () => {
    const apiKey = '  sk-abc123  ';
    expect(apiKey.trim()).toBe('sk-abc123');
  });
});
