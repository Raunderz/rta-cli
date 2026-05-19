import React, { useState } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  FlatList, 
  TouchableOpacity, 
  ScrollView 
} from 'react-native';

const MOCK_FILES = [
  { id: '1', name: 'backend', isDir: true, open: true },
  { id: '2', name: 'main.py', isDir: false, parentId: '1', content: 'import os\n\nprint("Rta Server Running")' },
  { id: '3', name: 'utils.py', isDir: false, parentId: '1', content: 'def clean_text(t):\n    return t.strip()' },
  { id: '4', name: 'frontend', isDir: true, open: false },
  { id: '5', name: 'index.html', isDir: false, parentId: '4', content: '<h1>Rta App</h1>' },
  { id: '6', name: 'package.json', isDir: false, content: '{\n  "name": "rta-project"\n}' },
  { id: '7', name: 'README.md', isDir: false, content: '# Rta Project\n\nRun with container environments.' }
];

export default function Files({ onSelectFile, currentFile }) {
  const [fileList, setFileList] = useState(MOCK_FILES);

  const toggleFolder = (id) => {
    setFileList(prev => prev.map(f => {
      if (f.id === id) {
        return { ...f, open: !f.open };
      }
      return f;
    }));
  };

  const renderItem = ({ item }) => {
    // Hide files in collapsed folders
    if (item.parentId) {
      const parent = fileList.find(f => f.id === item.parentId);
      if (parent && !parent.open) return null;
    }

    const isSelected = currentFile && currentFile.id === item.id;
    const paddingLeft = item.parentId ? 32 : 16;

    return (
      <TouchableOpacity
        style={[
          styles.item, 
          { paddingLeft },
          isSelected && styles.selectedItem
        ]}
        onPress={() => {
          if (item.isDir) {
            toggleFolder(item.id);
          } else {
            onSelectFile(item);
          }
        }}
      >
        <Text style={styles.icon}>
          {item.isDir ? (item.open ? '📂' : '📁') : '📄'}
        </Text>
        <Text style={[
          styles.itemText, 
          item.isDir && styles.dirText,
          isSelected && styles.selectedItemText
        ]}>
          {item.name}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Workspace Explorer</Text>
        <Text style={styles.subtitle}>Rta Local Project</Text>
      </View>
      <FlatList
        data={fileList}
        keyExtractor={item => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f9ff',
  },
  header: {
    padding: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  title: {
    fontSize: 20,
    fontWeight: '900',
    color: '#1f2937',
  },
  subtitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  listContent: {
    paddingVertical: 16,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingRight: 24,
  },
  selectedItem: {
    backgroundColor: '#e0f2fe',
  },
  icon: {
    fontSize: 16,
    marginRight: 10,
  },
  itemText: {
    fontSize: 16,
    color: '#1f2937',
  },
  selectedItemText: {
    color: '#0ea5e9',
    fontWeight: '700',
  },
  dirText: {
    fontWeight: '600',
  },
});
