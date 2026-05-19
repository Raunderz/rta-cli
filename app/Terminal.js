import React, { useState, useRef, useEffect } from 'react';
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

const INITIAL_LOG = [
  'Welcome to Rta Terminal.',
  'Container Status: DISCONNECTED (Local Mock Mode)',
  'Type "help" to see available mock commands.',
  ''
];

export default function Terminal({ files = [] }) {
  const [logs, setLogs] = useState(INITIAL_LOG);
  const [commandInput, setCommandInput] = useState('');
  const scrollViewRef = useRef();

  const handleCommand = () => {
    if (!commandInput.trim()) return;

    const fullCmd = commandInput.trim();
    const parts = fullCmd.split(' ');
    const cmd = parts[0].toLowerCase();
    const arg = parts[1];

    let response = [];
    response.push(`$ ${fullCmd}`);

    switch (cmd) {
      case 'help':
        response.push('Available commands:');
        response.push('  help            - List commands');
        response.push('  ls              - List files in workspace');
        response.push('  cat <file>      - View file contents');
        response.push('  clear           - Clear screen');
        response.push('  python <file>   - Run a Python script');
        break;
      case 'clear':
        setLogs([]);
        setCommandInput('');
        return;
      case 'ls':
        if (files.length === 0) {
          response.push('(empty workspace)');
        } else {
          files.forEach(f => {
            response.push(`${f.isDir ? '📁' : '📄'} ${f.name}`);
          });
        }
        break;
      case 'cat':
        if (!arg) {
          response.push('Error: Specify a filename. Example: cat main.py');
        } else {
          const file = files.find(f => f.name.toLowerCase() === arg.toLowerCase());
          if (file) {
            response.push(file.content || '(empty)');
          } else {
            response.push(`Error: File "${arg}" not found.`);
          }
        }
        break;
      case 'python':
        if (!arg) {
          response.push('Error: Specify a script. Example: python main.py');
        } else {
          const file = files.find(f => f.name.toLowerCase() === arg.toLowerCase());
          if (file) {
            if (arg.endsWith('.py')) {
              response.push('Running python script...');
              response.push('--- stdout ---');
              response.push(file.content ? `Output: Compiled main successfully.\nCaptured: hello!` : 'No output.');
            } else {
              response.push('Error: Not a python script.');
            }
          } else {
            response.push(`Error: Script "${arg}" not found.`);
          }
        }
        break;
      default:
        response.push(`bash: ${cmd}: command not found`);
    }

    response.push('');
    setLogs(prev => [...prev, ...response]);
    setCommandInput('');
  };

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [logs]);

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>bash terminal</Text>
          <Text style={styles.subtitle}>mock-env-active</Text>
        </View>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>LOCAL</Text>
        </View>
      </View>
      
      <ScrollView 
        ref={scrollViewRef} 
        style={styles.logArea}
        contentContainerStyle={styles.logContent}
      >
        {logs.map((log, index) => (
          <Text key={index} style={styles.logText}>
            {log}
          </Text>
        ))}
      </ScrollView>

      <View style={styles.inputArea}>
        <Text style={styles.prompt}>$</Text>
        <TextInput
          style={styles.input}
          value={commandInput}
          onChangeText={setCommandInput}
          onSubmitEditing={handleCommand}
          placeholder="Type command..."
          placeholderTextColor="#94a3b8"
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="done"
        />
      </View>
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
  title: {
    fontSize: 16,
    fontWeight: '800',
    color: '#1f2937',
    textTransform: 'lowercase',
  },
  subtitle: {
    fontSize: 10,
    color: '#6b7280',
    marginTop: 2,
  },
  statusBadge: {
    backgroundColor: '#e0f2fe',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    color: '#0ea5e9',
    fontSize: 10,
    fontWeight: '800',
  },
  logArea: {
    flex: 1,
  },
  logContent: {
    padding: 20,
  },
  logText: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 13,
    lineHeight: 20,
    color: '#1f2937',
  },
  inputArea: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0f2fe',
    backgroundColor: '#f0f9ff',
  },
  prompt: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 14,
    color: '#0ea5e9',
    marginRight: 8,
    fontWeight: '700',
  },
  input: {
    flex: 1,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 14,
    color: '#1f2937',
    padding: 0,
  },
});
