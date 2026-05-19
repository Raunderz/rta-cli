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
import Chat from './Chat';
import Files from './Files';
import Editor from './Editor';
import Terminal from './Terminal';

const STORAGE_KEY = 'rta_api_key';

export default function App() {
  const [apiKey, setApiKey] = useState('');
  const [isReady, setIsReady] = useState(false);
  const [hasKey, setHasKey] = useState(false);
  
  // Navigation & Tab state
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedFile, setSelectedFile] = useState(null);
  
  // Local project workspace state
  const [files, setFiles] = useState([
    { id: '2', name: 'main.py', isDir: false, parentId: '1', content: 'import os\n\nprint("Rta Server Running")' },
    { id: '3', name: 'utils.py', isDir: false, parentId: '1', content: 'def clean_text(t):\n    return t.strip()' },
    { id: '5', name: 'index.html', isDir: false, parentId: '4', content: '<h1>Rta App</h1>' },
    { id: '6', name: 'package.json', isDir: false, content: '{\n  "name": "rta-project"\n}' },
    { id: '7', name: 'README.md', isDir: false, content: '# Rta Project\n\nRun with container environments.' }
  ]);

  useEffect(() => {
    loadKey();
  }, []);

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
    setActiveTab('editor');
  };

  const handleSaveFile = (id, newContent) => {
    setFiles(prev => prev.map(f => {
      if (f.id === id) {
        return { ...f, content: newContent };
      }
      return f;
    }));
    // Sync active editor state
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
    <SafeAreaProvider>
      <StatusBar barStyle="dark-content" />
      {hasKey ? (
        <MainApp 
          apiKey={apiKey}
          onLogout={handleLogout}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedFile={selectedFile}
          handleSelectFile={handleSelectFile}
          handleSaveFile={handleSaveFile}
          files={files}
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
  files 
}) {
  const insets = useSafeAreaInsets();

  const renderContent = () => {
    switch (activeTab) {
      case 'files':
        return <Files onSelectFile={handleSelectFile} currentFile={selectedFile} />;
      case 'editor':
        return <Editor file={selectedFile} onSave={handleSaveFile} />;
      case 'terminal':
        return <Terminal files={files} />;
      case 'chat':
      default:
        return <Chat apiKey={apiKey} onLogout={onLogout} />;
    }
  };

  return (
    <View style={[styles.appContainer, { paddingTop: insets.top }]}>
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
          onPress={() => setActiveTab('editor')}
        >
          <Text style={[styles.tabIcon, activeTab === 'editor' && styles.activeTabIcon]}>
            📝
          </Text>
          <Text style={[styles.tabLabel, activeTab === 'editor' && styles.activeTabLabel]}>
            Editor
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
});
