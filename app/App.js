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
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Chat from './Chat';

const STORAGE_KEY = 'rta_api_key';

export default function App() {
  const [apiKey, setApiKey] = useState('');
  const [isReady, setIsReady] = useState(false);
  const [hasKey, setHasKey] = useState(false);

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
    } catch (e) {
      alert('Failed to logout');
    }
  };

  if (!isReady) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" />
      {hasKey ? (
        <Chat apiKey={apiKey} onLogout={handleLogout} />
      ) : (
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.container}
        >
          <LinearGradient
            colors={['#0f172a', '#1e293b', '#0f172a']}
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
                  placeholderTextColor="#64748b"
                  value={apiKey}
                  onChangeText={setApiKey}
                  secureTextEntry
                />
              </View>
            </View>

            <TouchableOpacity activeOpacity={0.8} style={styles.button} onPress={handleSave}>
              <LinearGradient
                colors={['#3b82f6', '#2563eb']}
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
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
    backgroundColor: '#0f172a',
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
    color: '#f8fafc',
    letterSpacing: -4,
  },
  badge: {
    backgroundColor: '#3b82f6',
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
    color: '#94a3b8',
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
    color: '#64748b',
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
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    borderWidth: 1,
    borderColor: '#334155',
    overflow: 'hidden',
  },
  input: {
    width: '100%',
    height: 64,
    paddingHorizontal: 24,
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  button: {
    width: '100%',
    height: 64,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 10,
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
    color: '#3b82f6',
    fontSize: 14,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
  footer: {
    position: 'absolute',
    bottom: 40,
  },
  footerText: {
    color: '#475569',
    fontSize: 12,
    fontWeight: '600',
  },
});


