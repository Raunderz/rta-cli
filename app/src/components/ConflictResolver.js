import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export default function ConflictResolver({ conflicts, onResolve, onCancel }) {
  const [resolutions, setResolutions] = useState(
    conflicts.map(c => ({ path: c.path, choice: 'remote' }))
  );

  const setChoice = (path, choice) => {
    setResolutions(prev => prev.map(r =>
      r.path === path ? { ...r, choice } : r
    ));
  };

  const setAll = (choice) => {
    setResolutions(prev => prev.map(r => ({ ...r, choice })));
  };

  const handleResolve = () => {
    const remotePaths = resolutions.filter(r => r.choice === 'remote').map(r => r.path);
    const localPaths = resolutions.filter(r => r.choice === 'local').map(r => r.path);
    onResolve({ remotePaths, localPaths });
  };

  return (
    <Modal transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>File Conflicts</Text>
            <Text style={styles.subtitle}>
              {conflicts.length} file{conflicts.length > 1 ? 's' : ''} changed both locally and in the cloud
            </Text>
          </View>

          <View style={styles.bulkActions}>
            <TouchableOpacity style={styles.bulkBtn} onPress={() => setAll('remote')}>
              <Text style={styles.bulkBtnText}>ALL CLOUD</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.bulkBtn} onPress={() => setAll('local')}>
              <Text style={styles.bulkBtnText}>ALL LOCAL</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.fileList}>
            {resolutions.map((r, i) => (
              <View key={i} style={styles.fileItem}>
                <Text style={styles.filePath} numberOfLines={1}>{r.path}</Text>
                <View style={styles.choiceRow}>
                  <TouchableOpacity
                    style={[styles.choiceBtn, r.choice === 'local' && styles.choiceLocal]}
                    onPress={() => setChoice(r.path, 'local')}
                  >
                    <Text style={[styles.choiceText, r.choice === 'local' && styles.choiceTextActive]}>
                      LOCAL
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.choiceBtn, r.choice === 'remote' && styles.choiceRemote]}
                    onPress={() => setChoice(r.path, 'remote')}
                  >
                    <Text style={[styles.choiceText, r.choice === 'remote' && styles.choiceTextActive]}>
                      CLOUD
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </ScrollView>

          <View style={styles.footer}>
            <TouchableOpacity style={styles.cancelBtn} onPress={onCancel}>
              <Text style={styles.cancelBtnText}>CANCEL</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.resolveBtn} onPress={handleResolve}>
              <LinearGradient colors={['#0ea5e9', '#0284c7']} style={styles.gradient}>
                <Text style={styles.resolveBtnText}>RESOLVE ({resolutions.length})</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  header: {
    padding: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  title: { fontSize: 20, fontWeight: '900', color: '#1f2937' },
  subtitle: { fontSize: 13, color: '#6b7280', marginTop: 4 },
  bulkActions: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    paddingVertical: 12,
    gap: 8,
  },
  bulkBtn: {
    flex: 1,
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0f2fe',
    alignItems: 'center',
  },
  bulkBtnText: { fontSize: 10, fontWeight: '800', color: '#6b7280' },
  fileList: {
    paddingHorizontal: 24,
    maxHeight: 300,
  },
  fileItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    marginBottom: 8,
  },
  filePath: { fontSize: 13, color: '#1f2937', fontFamily: 'monospace', flex: 1, marginRight: 8 },
  choiceRow: { flexDirection: 'row', gap: 4 },
  choiceBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#e0f2fe',
  },
  choiceLocal: { backgroundColor: '#fef3c7', borderColor: '#f59e0b' },
  choiceRemote: { backgroundColor: '#dbeafe', borderColor: '#3b82f6' },
  choiceText: { fontSize: 9, fontWeight: '800', color: '#94a3b8' },
  choiceTextActive: { color: '#1f2937' },
  footer: {
    flexDirection: 'row',
    padding: 24,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0f2fe',
  },
  cancelBtn: {
    flex: 1,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0f2fe',
    alignItems: 'center',
  },
  cancelBtnText: { fontSize: 12, fontWeight: '800', color: '#6b7280' },
  resolveBtn: { flex: 2, height: 48, borderRadius: 12, overflow: 'hidden' },
  gradient: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  resolveBtnText: { color: '#fff', fontWeight: '900', letterSpacing: 1 },
});
