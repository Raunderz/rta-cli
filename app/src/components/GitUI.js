import React, { useState, useEffect, useCallback } from 'react';
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
import * as FileSystem from 'expo-file-system/legacy';
import { LinearGradient } from 'expo-linear-gradient';

const WORKSPACE_DIR = `${FileSystem.documentDirectory}workspace/`;

const fs = {
  promises: {
    readFile: async (path, opts) => {
      const uri = WORKSPACE_DIR + path;
      if (opts && opts.encoding === 'utf8') {
        return FileSystem.readAsStringAsync(uri, { encoding: 'utf8' });
      }
      const base64 = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
      return Uint8Array.from(atob(base64), c => c.charCodeAt(0));
    },
    writeFile: (path, content) => {
      const data = typeof content === 'string' ? content : btoa(String.fromCharCode(...content));
      const encoding = typeof content === 'string' ? 'utf8' : FileSystem.EncodingType.Base64;
      return FileSystem.writeAsStringAsync(WORKSPACE_DIR + path, data, { encoding });
    },
    unlink: (path) => FileSystem.deleteAsync(WORKSPACE_DIR + path),
    readdir: async (path) => {
      const items = await FileSystem.readDirectoryAsync(WORKSPACE_DIR + path);
      return items;
    },
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
        isFile: () => !info.isDirectory,
        isSymbolicLink: () => false,
      };
    },
    lstat: async (path) => fs.promises.stat(path),
    readlink: async (path) => { throw new Error('readlink not supported'); },
    symlink: async (target, path) => { throw new Error('symlink not supported'); },
  }
};

const GIT_DIR = '.git';

async function isGitRepo() {
  try {
    await FileSystem.getInfoAsync(WORKSPACE_DIR + GIT_DIR);
    return true;
  } catch {
    return false;
  }
}

export default function GitUI() {
  const [repoExists, setRepoExists] = useState(false);
  const [status, setStatus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [commitMsg, setCommitMsg] = useState('');
  const [committing, setCommitting] = useState(false);
  const [log, setLog] = useState([]);
  const [branch, setBranch] = useState('');

  useEffect(() => {
    checkRepo();
  }, []);

  const checkRepo = async () => {
    const exists = await isGitRepo();
    setRepoExists(exists);
    if (exists) {
      await refreshStatus();
      await loadLog();
      await loadBranch();
    }
  };

  const loadBranch = async () => {
    try {
      const b = await git.currentBranch({ fs, dir: '' });
      setBranch(b || 'HEAD');
    } catch {}
  };

  const loadLog = async () => {
    try {
      const commits = await git.log({ fs, dir: '', depth: 10 });
      setLog(commits);
    } catch {
      setLog([]);
    }
  };

  const refreshStatus = async () => {
    setLoading(true);
    try {
      const statusMatrix = await git.statusMatrix({ fs, dir: '' });
      const files = statusMatrix
        .map(([filepath, HEAD, workingDir, stage]) => {
          let status = 'unchanged';
          if (HEAD === 0 && workingDir === 1 && stage === 0) status = 'new';
          else if (HEAD === 1 && workingDir === 0 && stage === 1) status = 'deleted';
          else if (HEAD === 1 && workingDir === 1 && stage === 0) status = 'modified';
          else if (HEAD === 1 && workingDir === 1 && stage === 1 && HEAD !== workingDir) status = 'modified';
          else if (HEAD === 0 && workingDir === 1 && stage === 1) status = 'staged';
          return { path: filepath, status, HEAD, workingDir, stage };
        })
        .filter(f => f.status !== 'unchanged');
      setStatus(files);
    } catch (e) {
      console.error('git status error:', e);
      setStatus([]);
    } finally {
      setLoading(false);
    }
  };

  const initRepo = async () => {
    Alert.alert('Init Repo', 'Initialize a new git repository in workspace?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Init', onPress: async () => {
          try {
            await git.init({ fs, dir: '' });
            setRepoExists(true);
            await refreshStatus();
            await loadBranch();
          } catch (e) {
            Alert.alert('Error', 'Failed to init repo: ' + e.message);
          }
        }
      }
    ]);
  };

  const stageFile = async (filepath) => {
    try {
      await git.add({ fs, dir: '', filepath });
      await refreshStatus();
    } catch (e) {
      console.error('git add error:', e);
    }
  };

  const unstageFile = async (filepath) => {
    try {
      await git.resetIndex({ fs, dir: '', filepath });
      await refreshStatus();
    } catch (e) {
      console.error('git reset error:', e);
    }
  };

  const stageAll = async () => {
    try {
      for (const file of status) {
        if (file.status !== 'deleted') {
          await git.add({ fs, dir: '', filepath: file.path });
        }
      }
      await refreshStatus();
    } catch (e) {
      console.error('git add all error:', e);
    }
  };

  const commit = async () => {
    if (!commitMsg.trim()) {
      Alert.alert('Error', 'Enter a commit message');
      return;
    }
    setCommitting(true);
    try {
      const sha = await git.commit({
        fs,
        dir: '',
        message: commitMsg.trim(),
        author: { name: 'Rta Mobile', email: 'rta@mobile.app', timestamp: Math.floor(Date.now() / 1000), timezoneOffset: 0 },
      });
      setCommitMsg('');
      await refreshStatus();
      await loadLog();
      Alert.alert('Committed', `Created commit ${sha.slice(0, 7)}`);
    } catch (e) {
      Alert.alert('Commit Failed', e.message);
    } finally {
      setCommitting(false);
    }
  };

  const formatDate = (timestamp) => {
    const d = new Date(timestamp * 1000);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (!repoExists) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>Version Control</Text>
        </View>
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>🌿</Text>
          <Text style={styles.emptyTitle}>No Git Repository</Text>
          <Text style={styles.emptyText}>Initialize a repo to track changes.</Text>
          <TouchableOpacity style={styles.initBtnLarge} onPress={initRepo}>
            <LinearGradient colors={['#10b981', '#059669']} style={styles.gradient}>
              <Text style={styles.initBtnLargeText}>INIT REPO</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>Version Control</Text>
          <Text style={styles.branch}>{branch}</Text>
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.refreshBtn} onPress={refreshStatus}>
            <Text style={styles.refreshBtnText}>REFRESH</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.stageAllBtn} onPress={stageAll}>
            <Text style={styles.stageAllBtnText}>STAGE ALL</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView style={styles.content}>
        {status.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Changes ({status.length})</Text>
            {status.map((item, i) => (
              <View key={i} style={styles.statusItem}>
                <Text style={styles.statusPath} numberOfLines={1}>{item.path}</Text>
                <View style={styles.statusActions}>
                  <Text style={[styles.statusBadge, getStatusStyle(item.status)]}>
                    {item.status.toUpperCase()}
                  </Text>
                  {item.stage === 0 ? (
                    <TouchableOpacity onPress={() => stageFile(item.path)}>
                      <Text style={styles.stageBtn}>+</Text>
                    </TouchableOpacity>
                  ) : (
                    <TouchableOpacity onPress={() => unstageFile(item.path)}>
                      <Text style={styles.unstageBtn}>-</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}

        {status.length === 0 && !loading && (
          <View style={styles.cleanState}>
            <Text style={styles.cleanIcon}>✓</Text>
            <Text style={styles.cleanText}>Working tree clean</Text>
          </View>
        )}

        {loading && <ActivityIndicator color="#0ea5e9" style={{ marginVertical: 20 }} />}

        <View style={styles.commitArea}>
          <TextInput
            style={styles.input}
            placeholder="Commit message..."
            value={commitMsg}
            onChangeText={setCommitMsg}
            multiline
          />
          <TouchableOpacity
            style={[styles.commitBtn, (!commitMsg.trim() || committing) && styles.disabledBtn]}
            onPress={commit}
            disabled={!commitMsg.trim() || committing}
          >
            <LinearGradient colors={['#0ea5e9', '#0284c7']} style={styles.gradient}>
              {committing ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.commitBtnText}>COMMIT</Text>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {log.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Recent Commits</Text>
            {log.map((commit, i) => (
              <View key={i} style={styles.commitItem}>
                <Text style={styles.commitHash}>{commit.oid.slice(0, 7)}</Text>
                <Text style={styles.commitMsg} numberOfLines={2}>{commit.commit.message}</Text>
                <Text style={styles.commitDate}>{formatDate(commit.commit.author.timestamp)}</Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function getStatusStyle(status) {
  switch (status) {
    case 'new': return { color: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)' };
    case 'modified': return { color: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)' };
    case 'deleted': return { color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)' };
    case 'staged': return { color: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.1)' };
    default: return { color: '#6b7280', backgroundColor: 'rgba(107, 114, 128, 0.1)' };
  }
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
  branch: { fontSize: 10, color: '#6b7280', fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', marginTop: 2 },
  headerActions: { flexDirection: 'row', gap: 8 },
  refreshBtn: { padding: 8, borderRadius: 8, borderWidth: 1, borderColor: '#e0f2fe' },
  refreshBtnText: { fontSize: 10, fontWeight: '800', color: '#6b7280' },
  stageAllBtn: { padding: 8, borderRadius: 8, borderWidth: 1, borderColor: '#0ea5e9' },
  stageAllBtnText: { fontSize: 10, fontWeight: '800', color: '#0ea5e9' },
  content: { flex: 1, padding: 20 },
  section: { marginBottom: 30 },
  sectionTitle: { fontSize: 12, fontWeight: '800', color: '#6b7280', marginBottom: 12, textTransform: 'uppercase' },
  statusItem: { 
    flexDirection: 'row', 
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12, 
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0f2fe'
  },
  statusPath: { fontSize: 14, color: '#1f2937', fontWeight: '500', flex: 1, marginRight: 8 },
  statusActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusBadge: { fontSize: 9, fontWeight: '800', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, overflow: 'hidden' },
  stageBtn: { fontSize: 16, fontWeight: '900', color: '#10b981', paddingHorizontal: 4 },
  unstageBtn: { fontSize: 16, fontWeight: '900', color: '#ef4444', paddingHorizontal: 4 },
  cleanState: { alignItems: 'center', paddingVertical: 40 },
  cleanIcon: { fontSize: 32, color: '#10b981', marginBottom: 8 },
  cleanText: { fontSize: 14, color: '#6b7280', fontWeight: '600' },
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
  disabledBtn: { opacity: 0.5 },
  gradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  commitBtnText: { color: '#fff', fontWeight: '900', letterSpacing: 1 },
  commitItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e0f2fe'
  },
  commitHash: { fontSize: 12, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', color: '#0ea5e9', fontWeight: '700' },
  commitMsg: { fontSize: 14, color: '#1f2937', marginTop: 4, lineHeight: 20 },
  commitDate: { fontSize: 10, color: '#94a3b8', marginTop: 4 },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
  emptyIcon: { fontSize: 48, marginBottom: 16, opacity: 0.5 },
  emptyTitle: { fontSize: 18, fontWeight: '800', color: '#1f2937', marginBottom: 8 },
  emptyText: { fontSize: 14, color: '#6b7280', textAlign: 'center', marginBottom: 24 },
  initBtnLarge: { width: 200, height: 50, borderRadius: 12, overflow: 'hidden' },
  initBtnLargeText: { color: '#fff', fontWeight: '900', letterSpacing: 1 },
});
