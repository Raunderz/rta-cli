import React from 'react';
import { ActivityIndicator, Platform, Text, View, TouchableOpacity } from 'react-native';

export default function SessionHeader({ session, syncStatus, syncProgress, isStartingSession, onStart, onEnd }) {
  return (
    <View style={styles.header}>
      <View style={styles.info}>
        <View style={[styles.dot, session.status === 'on' ? styles.dotOn : styles.dotOff]} />
        <View style={styles.textCol}>
          <Text style={styles.text}>
            {syncStatus || (session.status === 'on' ? `Cloud: ${session.id}` : 'Local Mode')}
          </Text>
          {syncProgress && (
            <View style={styles.progressRow}>
              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: `${syncProgress.percent || 0}%` }]} />
              </View>
              <Text style={styles.progressText}>{syncProgress.percent || 0}%</Text>
            </View>
          )}
        </View>
      </View>

      <TouchableOpacity
        style={[styles.btn, session.status === 'on' ? styles.btnEnd : styles.btnStart]}
        onPress={session.status === 'on' ? onEnd : onStart}
        disabled={isStartingSession}
      >
        {isStartingSession ? (
          <ActivityIndicator size="small" color="#fff" />
        ) : (
          <Text style={styles.btnText}>
            {session.status === 'on' ? 'END' : 'START CLOUD'}
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = {
  header: {
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  info: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
  dotOn: { backgroundColor: '#10b981' },
  dotOff: { backgroundColor: '#94a3b8' },
  textCol: { flex: 1 },
  text: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  progressRow: { flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 6 },
  progressTrack: { flex: 1, height: 3, backgroundColor: '#e0f2fe', borderRadius: 2 },
  progressFill: { height: 3, backgroundColor: '#0ea5e9', borderRadius: 2 },
  progressText: { fontSize: 9, fontWeight: '700', color: '#0ea5e9', width: 28 },
  btn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  btnStart: { backgroundColor: '#0ea5e9' },
  btnEnd: { backgroundColor: '#f43f5e' },
  btnText: { color: '#fff', fontSize: 10, fontWeight: '900' },
};
