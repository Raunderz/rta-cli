import React from 'react';
import { ActivityIndicator, Platform, Text, View, TouchableOpacity } from 'react-native';

export default function SessionHeader({ session, syncStatus, isStartingSession, onStart, onEnd }) {
  return (
    <View style={styles.header}>
      <View style={styles.info}>
        <View style={[styles.dot, session.status === 'on' ? styles.dotOn : styles.dotOff]} />
        <Text style={styles.text}>
          {syncStatus || (session.status === 'on' ? `Cloud Active: ${session.id}` : 'Local Mode')}
        </Text>
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
  info: { flexDirection: 'row', alignItems: 'center' },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
  dotOn: { backgroundColor: '#10b981' },
  dotOff: { backgroundColor: '#94a3b8' },
  text: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  btn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  btnStart: { backgroundColor: '#0ea5e9' },
  btnEnd: { backgroundColor: '#f43f5e' },
  btnText: { color: '#fff', fontSize: 10, fontWeight: '900' },
};
