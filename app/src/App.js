import React, { useState } from 'react';
import { ActivityIndicator, Platform, Text, View } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';

import LoginScreen from './LoginScreen';
import SessionHeader from './SessionHeader';
import TabBar from './TabBar';
import Chat from './components/Chat';
import Files from './components/Files';
import Editor from './components/Editor';
import Terminal from './components/Terminal';
import GitUI from './components/GitUI';
import ConflictResolver from './components/ConflictResolver';
import ErrorBoundary from './components/ErrorBoundary';
import useWorkspace from './useWorkspace';
import useSession from './useSession';

const STORAGE_KEY = 'rta_api_key';

export default function App() {
  const [isReady, setIsReady] = useState(false);
  const [hasKey, setHasKey] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedFile, setSelectedFile] = useState(null);

  const workspace = useWorkspace();
  const sessionHook = useSession({ apiKey, reloadFiles: workspace.reloadFiles });

  React.useEffect(() => {
    SecureStore.getItemAsync(STORAGE_KEY).then(key => {
      if (key) {
        setApiKey(key);
        setHasKey(true);
      }
      setIsReady(true);
    });
  }, []);

  const handleLogout = async () => {
    try {
      if (sessionHook.session.status === 'on') {
        await sessionHook.endSession();
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
    await workspace.saveFile(id, newContent);
    setSelectedFile(prev => prev && prev.id === id ? { ...prev, content: newContent } : prev);
  };

  if (!isReady) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#0ea5e9" />
      </View>
    );
  }

  return (
    <ErrorBoundary>
      <SafeAreaProvider>
        {sessionHook.conflicts && (
          <ConflictResolver
            conflicts={sessionHook.conflicts}
            onResolve={sessionHook.resolveConflicts}
            onCancel={sessionHook.cancelConflicts}
          />
        )}
        {hasKey ? (
          <MainApp
            apiKey={apiKey}
            onLogout={handleLogout}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            selectedFile={selectedFile}
            onSelectFile={handleSelectFile}
            onSaveFile={handleSaveFile}
            onCreateFile={workspace.createFile}
            onCreateFolder={workspace.createFolder}
            onDeleteItem={workspace.deleteItem}
            reloadFiles={workspace.reloadFiles}
            files={workspace.files}
            session={sessionHook.session}
            syncStatus={sessionHook.syncStatus}
            syncProgress={sessionHook.syncProgress}
            isStartingSession={sessionHook.isStartingSession}
            onStartSession={sessionHook.startSession}
            onEndSession={sessionHook.endSession}
          />
        ) : (
          <LoginScreen onAuthenticated={(key) => { setApiKey(key); setHasKey(true); }} />
        )}
      </SafeAreaProvider>
    </ErrorBoundary>
  );
}

function MainApp({
  apiKey, onLogout, activeTab, setActiveTab,
  selectedFile, onSelectFile, onSaveFile,
  onCreateFile, onCreateFolder, onDeleteItem, reloadFiles,
  files, session, syncStatus, syncProgress, isStartingSession,
  onStartSession, onEndSession,
}) {
  const insets = useSafeAreaInsets();

  const renderContent = () => {
    switch (activeTab) {
      case 'files':
        return (
          <Files
            filesList={files}
            onSelectFile={onSelectFile}
            currentFile={selectedFile}
            onCreateFile={onCreateFile}
            onCreateFolder={onCreateFolder}
            onDeleteItem={onDeleteItem}
            onRefresh={reloadFiles}
          />
        );
      case 'editor':
        return <Editor file={selectedFile} onSave={onSaveFile} />;
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
      <SessionHeader
        session={session}
        syncStatus={syncStatus}
        isStartingSession={isStartingSession}
        onStart={onStartSession}
        onEnd={onEndSession}
      />
      <View style={styles.mainContent}>
        {renderContent()}
      </View>
      <TabBar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        paddingBottom={insets.bottom}
      />
    </View>
  );
}

const styles = {
  centered: { flex: 1, backgroundColor: '#f0f9ff', justifyContent: 'center', alignItems: 'center' },
  appContainer: { flex: 1, backgroundColor: '#f0f9ff' },
  mainContent: { flex: 1 },
};
