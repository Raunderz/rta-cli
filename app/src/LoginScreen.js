import React, { useState, useEffect } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  Linking,
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { LinearGradient } from 'expo-linear-gradient';

const STORAGE_KEY = 'rta_api_key';

export default function LoginScreen({ onAuthenticated }) {
  const [apiKey, setApiKey] = useState('');

  const handleSave = async () => {
    if (!apiKey.trim()) {
      alert('Please enter an API key');
      return;
    }
    try {
      await SecureStore.setItemAsync(STORAGE_KEY, apiKey.trim());
      onAuthenticated(apiKey.trim());
    } catch (e) {
      alert('Failed to save key');
    }
  };

  return (
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
  );
}

const styles = {
  container: { flex: 1, backgroundColor: '#f0f9ff' },
  background: { ...StyleSheet.absoluteFillObject },
  inner: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  logoContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  title: { fontSize: 72, fontWeight: '900', color: '#1f2937', letterSpacing: -4 },
  badge: { backgroundColor: '#f59e0b', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6, marginLeft: 8, marginTop: 8 },
  badgeText: { color: '#fff', fontSize: 10, fontWeight: '900' },
  subtitle: { fontSize: 14, color: '#4b5563', fontWeight: '700', marginBottom: 64, textTransform: 'uppercase', letterSpacing: 4 },
  inputContainer: { width: '100%', marginBottom: 32 },
  label: { color: '#6b7280', fontSize: 12, marginBottom: 12, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 1, textAlign: 'center' },
  inputWrapper: { width: '100%', borderRadius: 20, backgroundColor: '#ffffff', borderWidth: 1, borderColor: '#e0f2fe', overflow: 'hidden', shadowColor: '#0ea5e9', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 10, elevation: 2 },
  input: { width: '100%', height: 64, paddingHorizontal: 24, color: '#1f2937', fontSize: 18, textAlign: 'center', fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  button: { width: '100%', height: 64, borderRadius: 20, overflow: 'hidden', shadowColor: '#0ea5e9', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.3, shadowRadius: 15, elevation: 8 },
  gradientButton: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 2 },
  linkButton: { marginTop: 40, padding: 12 },
  linkText: { color: '#0ea5e9', fontSize: 14, fontWeight: '700', textDecorationLine: 'underline' },
  footer: { position: 'absolute', bottom: 40 },
  footerText: { color: '#6b7280', fontSize: 12, fontWeight: '600' },
};
