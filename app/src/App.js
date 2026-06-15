import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TextInput, 
  TouchableOpacity, 
  KeyboardAvoidingView, 
  Platform,
  Linking,
  ActivityIndicator,
  StatusBar
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import * as FileSystem from 'expo-file-system/legacy';
import Chat from './components/Chat';
import Files from './components/Files';
import Editor from './components/Editor';
import Terminal from './components/Terminal';
import GitUI from './components/GitUI';

const STORAGE_KEY = 'rta_api_key';
const WORKSPACE_DIR = `${FileSystem.documentDirectory}workspace/`;
import { resolveBackendUrl } from './utils/backend';
import { uploadWorkspace, downloadWorkspace, applyDownload, deleteRemovedFiles, clearSnapshot } from './utils/workspaceSync';
import ConflictResolver from './components/ConflictResolver';

export default function App() {
  const [apiKey, setApiKey] = useState('');
  const [isReady, setIsReady] = useState(false);
  const [hasKey, setHasKey] = useState(false);
  
  // Navigation & Tab state
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Session state
  const [session, setSession] = useState({ id: null, status: 'off', ws_url: null });
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [syncStatus, setSyncStatus] = useState('');
  const [conflicts, setConflicts] = useState(null);
  const [pendingDownload, setPendingDownload] = useState(null);

  // Local project workspace state
  const [files, setFiles] = useState([]);

  useEffect(() => {
    loadKey();
  }, []);

  useEffect(() => {
    if (hasKey) {
      initWorkspace();
    }
  }, [hasKey]);

  const loadKey = async () => {
    try {
      const savedKey = await SecureStore.getItemAsync(STORAGE_KEY);
      if (savedKey) {
        setApiKey(savedKey);
        setHasKey(true);
      }
    } catch (e) {
      console.error('Failed to load key', e);
    } finally {
      setIsReady(true);
    }
  };

  const initWorkspace = async () => {
    try {
      const info = await FileSystem.getInfoAsync(WORKSPACE_DIR);
      if (!info.exists) {
        await FileSystem.makeDirectoryAsync(WORKSPACE_DIR, { intermediates: true });
        
        // Create initial default workspace files
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
  };

  const reloadFiles = async () => {
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
  };

  const handleSave = async () => {
    if (!apiKey.trim()) {
      alert('Please enter an API key');
      return;
    }
    try {
      await SecureStore.setItemAsync(STORAGE_KEY, apiKey.trim());
      setHasKey(true);
    } catch (e) {
      alert('Failed to save key');
    }
  };

  const handleLogout = async () => {
    try {
      if (session.status === 'on') {
        await handleEndSession();
      }
      await SecureStore.deleteItemAsync(STORAGE_KEY);
      setApiKey('');
      setHasKey(false);
      setSelectedFile(null);
      setActiveTab('chat');
    } catch (e) {
      alert('Failed to logout');
    }
  };

  const handleSelectFile = (file) => {
    setSelectedFile(file);
    if (!file.isDir) {
      setActiveTab('editor');
    }
  };

  const handleSaveFile = async (id, newContent) => {
    try {
      await FileSystem.writeAsStringAsync(id, newContent);
      setFiles(prev => prev.map(f => {
        if (f.id === id) {
          return { ...f, content: newContent };
        }
        return f;
      }));
      setSelectedFile(prev => prev && prev.id === id ? { ...prev, content: newContent } : prev);
      alert('Saved successfully!');
    } catch (e) {
      alert('Failed to save file');
    }
  };

  const handleCreateFile = async (parentUri, fileName) => {
    try {
      const baseDir = parentUri ? (parentUri.endsWith('/') ? parentUri : parentUri + '/') : WORKSPACE_DIR;
      const targetUri = baseDir + fileName;
      await FileSystem.writeAsStringAsync(targetUri, '');
      await reloadFiles();
    } catch (e) {
      alert('Failed to create file');
    }
  };

  const handleCreateFolder = async (parentUri, folderName) => {
    try {
      const baseDir = parentUri ? (parentUri.endsWith('/') ? parentUri : parentUri + '/') : WORKSPACE_DIR;
      const targetUri = baseDir + folderName + '/';
      await FileSystem.makeDirectoryAsync(targetUri, { intermediates: true });
      await reloadFiles();
    } catch (e) {
      alert('Failed to create folder');
    }
  };

  const handleDeleteItem = async (uri) => {
    try {
      await FileSystem.deleteAsync(uri);
      if (selectedFile && selectedFile.id === uri) {
        setSelectedFile(null);
      }
      await reloadFiles();
    } catch (e) {
      alert('Failed to delete item');
    }
  };

  const handleStartSession = async () => {
    if (isStartingSession) return;
    setIsStartingSession(true);
    try {
      const backendUrl = await resolveBackendUrl();
      const resp = await fetch(`${backendUrl}/v1/executor/env`, {
        method: 'POST',
        headers: {
          'X-API-KEY': apiKey.trim(),
          'Content-Type': 'application/json',
        }
      });
      
      if (!resp.ok) {
        const err = await resp.text();
        throw new Error(err || 'Failed to start session');
      }

      const data = await resp.json();
      setSession({
        id: data.id,
        status: 'on',
        ws_url: data.ws_url
      });

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
  };

  const handleEndSession = async () => {
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
        headers: { 
          'X-API-KEY': apiKey.trim(),
        }
      });
      setSession({ id: null, status: 'off', ws_url: null });
    } catch (e) {
      console.error('Failed to end session', e);
      setSession({ id: null, status: 'off', ws_url: null });
    }
  };

  const handleConflictResolve = async ({ remotePaths, localPaths }) => {
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
  };

  const handleConflictCancel = async () => {
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
  };

  if (!isReady) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#0ea5e9" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="dark-content" />
      {conflicts && (
        <ConflictResolver
          conflicts={conflicts}
          onResolve={handleConflictResolve}
          onCancel={handleConflictCancel}
        />
      )}
      {hasKey ? (
        <MainApp 
          apiKey={apiKey}
          onLogout={handleLogout}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedFile={selectedFile}
          handleSelectFile={handleSelectFile}
          handleSaveFile={handleSaveFile}
          handleCreateFile={handleCreateFile}
          handleCreateFolder={handleCreateFolder}
          handleDeleteItem={handleDeleteItem}
          reloadFiles={reloadFiles}
          files={files}
          session={session}
          syncStatus={syncStatus}
          isStartingSession={isStartingSession}
          onStartSession={handleStartSession}
          onEndSession={handleEndSession}
        />
      ) : (
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.container}
        >
          <LinearGradient
            colors={['#e0f2fe', '#f0f9ff', '#e0f2fe']}
            style={styles.background}
          />
          <View style={styles.inner}>
            <View style={styles.logoContainer}>
              <Text style={styles.title}>Rta</Text>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>BETA</Text>
              </View>
            </View>
            <Text style={styles.subtitle}>Autonomous Agentic IDE</Text>
            
            <View style={styles.inputContainer}>
              <Text style={styles.label}>Developer API Key</Text>
              <View style={styles.inputWrapper}>
                <TextInput
                  style={styles.input}
                  placeholder="Paste your key here"
                  placeholderTextColor="#94a3b8"
                  value={apiKey}
                  onChangeText={setApiKey}
                  secureTextEntry
                />
              </View>
            </View>

            <TouchableOpacity activeOpacity={0.8} style={styles.button} onPress={handleSave}>
              <LinearGradient
                colors={['#0ea5e9', '#0284c7']}
                style={styles.gradientButton}
              >
                <Text style={styles.buttonText}>Authenticate</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.linkButton} 
              onPress={() => Linking.openURL('https://rta-three.vercel.app/auth')}
            >
              <Text style={styles.linkText}>Get API Key from Dashboard</Text>
            </TouchableOpacity>

            <View style={styles.footer}>
              <Text style={styles.footerText}>Secure locally stored credentials</Text>
            </View>
          </View>
        </KeyboardAvoidingView>
      )}
    </SafeAreaProvider>
  );
}

function MainApp({ 
  apiKey, 
  onLogout, 
  activeTab, 
  setActiveTab, 
  selectedFile, 
  handleSelectFile, 
  handleSaveFile, 
  handleCreateFile,
  handleCreateFolder,
  handleDeleteItem,
  reloadFiles,
  files,
  session,
  syncStatus,
  isStartingSession,
  onStartSession,
  onEndSession
}) {
  const insets = useSafeAreaInsets();

  const renderContent = () => {
    switch (activeTab) {
      case 'files':
        return (
          <Files 
            filesList={files}
            onSelectFile={handleSelectFile}
            currentFile={selectedFile}
            onCreateFile={handleCreateFile}
            onCreateFolder={handleCreateFolder}
            onDeleteItem={handleDeleteItem}
            onRefresh={reloadFiles}
          />
        );
      case 'editor':
        return <Editor file={selectedFile} onSave={handleSaveFile} />;
      case 'terminal':
        return <Terminal apiKey={apiKey} files={files} session={session} />;
      case 'git':
        return <GitUI />;
      case 'chat':
      default:
        return <Chat apiKey={apiKey} session={session} onLogout={onLogout} />;
    }
  };

  return (
    <View style={[styles.appContainer, { paddingTop: insets.top }]}>
      {/* Session Header */}
      <View style={styles.sessionHeader}>
        <View style={styles.sessionInfo}>
          <View style={[styles.statusDot, session.status === 'on' ? styles.statusDotOn : styles.statusDotOff]} />
          <Text style={styles.sessionText}>
            {syncStatus || (session.status === 'on' ? `Cloud Active: ${session.id}` : 'Local Mode')}
          </Text>
        </View>
        
        <TouchableOpacity 
          style={[styles.sessionBtn, session.status === 'on' ? styles.sessionBtnEnd : styles.sessionBtnStart]} 
          onPress={session.status === 'on' ? onEndSession : onStartSession}
          disabled={isStartingSession}
        >
          {isStartingSession ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.sessionBtnText}>
              {session.status === 'on' ? 'END' : 'START CLOUD'}
            </Text>
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.mainContent}>
        {renderContent()}
      </View>
      
      {/* Bottom Tab Bar */}
      <View style={[styles.tabBar, { paddingBottom: Math.max(insets.bottom, 8) }]}>
        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => setActiveTab('files')}
        >
          <Text style={[styles.tabIcon, activeTab === 'files' && styles.activeTabIcon]}>
            📁
          </Text>
          <Text style={[styles.tabLabel, activeTab === 'files' && styles.activeTabLabel]}>
            Files
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => setActiveTab('terminal')}
        >
          <Text style={[styles.tabIcon, activeTab === 'terminal' && styles.activeTabIcon]}>
            💻
          </Text>
          <Text style={[styles.tabLabel, activeTab === 'terminal' && styles.activeTabLabel]}>
            Terminal
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => setActiveTab('git')}
        >
          <Text style={[styles.tabIcon, activeTab === 'git' && styles.activeTabIcon]}>
            🌿
          </Text>
          <Text style={[styles.tabLabel, activeTab === 'git' && styles.activeTabLabel]}>
            Git
          </Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => setActiveTab('chat')}
        >
          <Text style={[styles.tabIcon, activeTab === 'chat' && styles.activeTabIcon]}>
            💬
          </Text>
          <Text style={[styles.tabLabel, activeTab === 'chat' && styles.activeTabLabel]}>
            Chat
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f9ff',
  },
  appContainer: {
    flex: 1,
    backgroundColor: '#f0f9ff',
  },
  mainContent: {
    flex: 1,
  },
  background: {
    ...StyleSheet.absoluteFillObject,
  },
  inner: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  centered: {
    flex: 1,
    backgroundColor: '#f0f9ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 72,
    fontWeight: '900',
    color: '#1f2937',
    letterSpacing: -4,
  },
  badge: {
    backgroundColor: '#f59e0b',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginLeft: 8,
    marginTop: 8,
  },
  badgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '900',
  },
  subtitle: {
    fontSize: 14,
    color: '#4b5563',
    fontWeight: '700',
    marginBottom: 64,
    textTransform: 'uppercase',
    letterSpacing: 4,
  },
  inputContainer: {
    width: '100%',
    marginBottom: 32,
  },
  label: {
    color: '#6b7280',
    fontSize: 12,
    marginBottom: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
    textAlign: 'center',
  },
  inputWrapper: {
    width: '100%',
    borderRadius: 20,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e0f2fe',
    overflow: 'hidden',
    shadowColor: '#0ea5e9',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  input: {
    width: '100%',
    height: 64,
    paddingHorizontal: 24,
    color: '#1f2937',
    fontSize: 18,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  button: {
    width: '100%',
    height: 64,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#0ea5e9',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 15,
    elevation: 8,
  },
  gradientButton: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '900',
    textTransform: 'uppercase',
    letterSpacing: 2,
  },
  linkButton: {
    marginTop: 40,
    padding: 12,
  },
  linkText: {
    color: '#0ea5e9',
    fontSize: 14,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  footer: {
    position: 'absolute',
    bottom: 40,
  },
  footerText: {
    color: '#6b7280',
    fontSize: 12,
    fontWeight: '600',
  },
  tabBar: {
    height: 64,
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e0f2fe',
  },
  tabItem: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  tabIcon: {
    fontSize: 20,
    color: '#94a3b8',
  },
  activeTabIcon: {
    color: '#0ea5e9',
  },
  tabLabel: {
    fontSize: 10,
    color: '#6b7280',
    fontWeight: '600',
    marginTop: 2,
  },
  activeTabLabel: {
    color: '#0ea5e9',
    fontWeight: '800',
  },
  sessionHeader: {
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  sessionInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusDotOn: {
    backgroundColor: '#10b981',
  },
  statusDotOff: {
    backgroundColor: '#94a3b8',
  },
  sessionText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  sessionBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  sessionBtnStart: {
    backgroundColor: '#0ea5e9',
  },
  sessionBtnEnd: {
    backgroundColor: '#f43f5e',
  },
  sessionBtnText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '900',
  },
});
