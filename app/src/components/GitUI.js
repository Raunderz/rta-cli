import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TouchableOpacity, 
  ScrollView, 
  TextInput,
  ActivityIndicator,
  Alert
} from 'react-native';
import git from 'isomorphic-git';
import http from 'isomorphic-git/http/web';
import * as FileSystem from 'expo-file-system/legacy';
import { LinearGradient } from 'expo-linear-gradient';

const WORKSPACE_DIR = `${FileSystem.documentDirectory}workspace/`;

// LightningFS shim for Expo (minimal for status/commit)
const fs = {
  promises: {
    readFile: (path) => FileSystem.readAsStringAsync(WORKSPACE_DIR + path, { encoding: 'utf8' }),
    writeFile: (path, content) => FileSystem.writeAsStringAsync(WORKSPACE_DIR + path, content),
    unlink: (path) => FileSystem.deleteAsync(WORKSPACE_DIR + path),
    readdir: (path) => FileSystem.readDirectoryAsync(WORKSPACE_DIR + path),
    mkdir: (path) => FileSystem.makeDirectoryAsync(WORKSPACE_DIR + path, { intermediates: true }),
    rmdir: (path) => FileSystem.deleteAsync(WORKSPACE_DIR + path),
    stat: async (path) => {
        const info = await FileSystem.getInfoAsync(WORKSPACE_DIR + path);
        return {
            ctime: new Date(0),
            mtime: new Date(0),
            dev: 0,
            ino: 0,
            mode: info.isDirectory ? 0o40755 : 0o100644,
            nlink: 1,
            uid: 0,
            gid: 0,
            size: info.size || 0,
            isDirectory: () => info.isDirectory,
            isFile: () => !info.isDirectory
        };
    },
    lstat: (path) => fs.promises.stat(path),
  }
};

export default function GitUI() {
  const [status, setStatus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [commitMsg, setCommitMsg] = useState('');

  const refreshStatus = async () => {
    setLoading(true);
    try {
      // isomorphic-git needs a real FS shim. 
      // This is a placeholder as full isomorphic-git setup on Expo is complex.
      // We will show UI but real logic depends on @isomorphic-git/lightning-fs properly mounted.
      setStatus([{ path: 'main.py', status: 'modified' }, { path: 'hello.bf', status: 'new' }]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const initRepo = async () => {
    Alert.alert('Init Repo', 'Initialize a new git repository here?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Init', onPress: () => alert('Git Init called') }
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Version Control</Text>
        <TouchableOpacity style={styles.initBtn} onPress={initRepo}>
          <Text style={styles.initBtnText}>INIT REPO</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Changes</Text>
          {loading ? (
            <ActivityIndicator color="#0ea5e9" />
          ) : (
            status.map((item, i) => (
              <View key={i} style={styles.statusItem}>
                <Text style={styles.statusPath}>{item.path}</Text>
                <Text style={[styles.statusText, item.status === 'new' ? styles.statusNew : styles.statusMod]}>
                  {item.status.toUpperCase()}
                </Text>
              </View>
            ))
          )}
        </View>

        <View style={styles.commitArea}>
          <TextInput
            style={styles.input}
            placeholder="Commit message..."
            value={commitMsg}
            onChangeText={setCommitMsg}
            multiline
          />
          <TouchableOpacity style={styles.commitBtn}>
            <LinearGradient colors={['#0ea5e9', '#0284c7']} style={styles.gradient}>
              <Text style={styles.commitBtnText}>COMMIT</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f9ff' },
  header: { 
    padding: 24, 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
    backgroundColor: '#fff'
  },
  title: { fontSize: 20, fontWeight: '900', color: '#1f2937' },
  initBtn: { padding: 8, borderRadius: 8, borderWidth: 1, borderColor: '#0ea5e9' },
  initBtnText: { fontSize: 10, fontWeight: '800', color: '#0ea5e9' },
  content: { flex: 1, padding: 20 },
  section: { marginBottom: 30 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#6b7280', marginBottom: 12, textTransform: 'uppercase' },
  statusItem: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    padding: 12, 
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0f2fe'
  },
  statusPath: { fontSize: 14, color: '#1f2937', fontWeight: '500' },
  statusText: { fontSize: 10, fontWeight: '800' },
  statusNew: { color: '#10b981' },
  statusMod: { color: '#f59e0b' },
  commitArea: { marginTop: 20 },
  input: { 
    backgroundColor: '#fff', 
    borderRadius: 16, 
    padding: 16, 
    minHeight: 100, 
    borderWidth: 1, 
    borderColor: '#e0f2fe',
    textAlignVertical: 'top'
  },
  commitBtn: { height: 50, borderRadius: 12, overflow: 'hidden', marginTop: 12 },
  gradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  commitBtnText: { color: '#fff', fontWeight: '900', letterSpacing: 1 },
});
