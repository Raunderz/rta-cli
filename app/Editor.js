import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TextInput, 
  TouchableOpacity, 
  ScrollView, 
  KeyboardAvoidingView, 
  Platform 
} from 'react-native';

export default function Editor({ file, onSave }) {
  const [code, setCode] = useState('');

  useEffect(() => {
    if (file) {
      setCode(file.content || '');
    } else {
      setCode('');
    }
  }, [file]);

  if (!file) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>📝</Text>
        <Text style={styles.emptyText}>No File Open</Text>
        <Text style={styles.emptySubtext}>Select a file in the Files tab to start coding</Text>
      </View>
    );
  }

  // Generate line numbers gutter
  const lineCount = code.split('\n').length || 1;
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'} 
      style={styles.container}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.fileName}>{file.name}</Text>
          <Text style={styles.filePath}>/workspace/{file.name}</Text>
        </View>
        <TouchableOpacity 
          style={styles.saveBtn}
          onPress={() => onSave(file.id, code)}
        >
          <Text style={styles.saveText}>SAVE</Text>
        </TouchableOpacity>
      </View>
      <ScrollView contentContainerStyle={styles.editorArea}>
        <View style={styles.editorInner}>
          <Text style={styles.gutterText}>{lineNumbers}</Text>
          <TextInput
            multiline
            value={code}
            onChangeText={setCode}
            style={styles.textInput}
            autoCapitalize="none"
            autoCorrect={false}
            spellCheck={false}
            placeholder="Start coding here..."
            placeholderTextColor="#94a3b8"
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    height: 70,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    backgroundColor: '#f0f9ff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  fileName: {
    fontSize: 16,
    fontWeight: '800',
    color: '#1f2937',
  },
  filePath: {
    fontSize: 10,
    color: '#6b7280',
    marginTop: 2,
  },
  saveBtn: {
    backgroundColor: '#0ea5e9',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
  },
  saveText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 12,
    letterSpacing: 1,
  },
  editorArea: {
    flexGrow: 1,
  },
  editorInner: {
    flexDirection: 'row',
    paddingVertical: 16,
  },
  gutterText: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 14,
    lineHeight: 22,
    color: '#94a3b8',
    textAlign: 'right',
    paddingHorizontal: 12,
    backgroundColor: '#f0f9ff',
    borderRightWidth: 1,
    borderRightColor: '#e0f2fe',
    minWidth: 40,
  },
  textInput: {
    flex: 1,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 14,
    lineHeight: 22,
    color: '#1f2937',
    paddingHorizontal: 16,
    textAlignVertical: 'top',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f9ff',
    padding: 24,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#1f2937',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 8,
  },
});
