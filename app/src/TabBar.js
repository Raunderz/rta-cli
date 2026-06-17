import React from 'react';
import { Text, View, TouchableOpacity } from 'react-native';

const TABS = [
  { key: 'files', icon: '📁', label: 'Files' },
  { key: 'terminal', icon: '💻', label: 'Terminal' },
  { key: 'git', icon: '🌿', label: 'Git' },
  { key: 'chat', icon: '💬', label: 'Chat' },
];

export default function TabBar({ activeTab, onSelectTab, paddingBottom }) {
  return (
    <View style={[styles.bar, { paddingBottom: Math.max(paddingBottom, 8) }]}>
      {TABS.map(tab => (
        <TouchableOpacity
          key={tab.key}
          style={styles.item}
          onPress={() => onSelectTab(tab.key)}
        >
          <Text style={[styles.icon, activeTab === tab.key && styles.iconActive]}>
            {tab.icon}
          </Text>
          <Text style={[styles.label, activeTab === tab.key && styles.labelActive]}>
            {tab.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = {
  bar: {
    height: 64,
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e0f2fe',
  },
  item: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  icon: { fontSize: 20, color: '#94a3b8' },
  iconActive: { color: '#0ea5e9' },
  label: { fontSize: 10, color: '#6b7280', fontWeight: '600', marginTop: 2 },
  labelActive: { color: '#0ea5e9', fontWeight: '800' },
};
