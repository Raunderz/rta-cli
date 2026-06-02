import React, { useState, useRef, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StatusBar
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://rta-tb0k.onrender.com';

export default function Chat({ apiKey, session, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const scrollViewRef = useRef();

  const sendMessage = async () => {
    if (!inputText.trim() || isStreaming) return;
    
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    const userMessage = { role: 'user', content: inputText };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputText('');
    setIsStreaming(true);

    const assistantMessage = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      const isCloud = session && session.status === 'on' && session.id;
      const chatUrl = isCloud 
        ? `${BACKEND_URL}/v1/executor/env/chat/${session.id}`
        : `${BACKEND_URL}/v1/chat`;

      const xhr = new XMLHttpRequest();
      xhr.open('POST', chatUrl);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('X-API-KEY', apiKey);
      xhr.setRequestHeader('X-Device-ID', 'mobile-app');
      xhr.setRequestHeader('X-CLI-Version', '2.0.0');


      let lastProcessedLength = 0;

      xhr.onreadystatechange = () => {
        if (xhr.readyState === 3 || xhr.readyState === 4) {
          const newData = xhr.responseText.substring(lastProcessedLength);
          lastProcessedLength = xhr.responseText.length;

          if (isCloud) {
            // Executor chat returns raw text stream, not SSE JSON
            setMessages(prev => {
              const last = prev[prev.length - 1];
              const updated = { ...last, content: last.content + newData };
              return [...prev.slice(0, -1), updated];
            });
          } else {
            const lines = newData.split('\n');
            lines.forEach(line => {
              if (line.startsWith('data: ')) {
                const jsonStr = line.replace('data: ', '').trim();
                if (jsonStr === '[DONE]') return;
                
                try {
                  const data = JSON.parse(jsonStr);
                  if (data.type === 'text') {
                    setMessages(prev => {
                      const last = prev[prev.length - 1];
                      const updated = { ...last, content: last.content + data.content };
                      return [...prev.slice(0, -1), updated];
                    });
                  }
                } catch (e) {
                  // Ignore parse errors
                }
              }
            });
          }
        }

        if (xhr.readyState === 4) {
          setIsStreaming(false);
        }
      };

      xhr.onerror = () => {
        setIsStreaming(false);
        alert('Network error');
      };

      if (isCloud) {
        // Go executor expects simple prompt JSON
        xhr.send(JSON.stringify({ prompt: inputText }));
      } else {
        xhr.send(JSON.stringify({
          messages: newMessages,
          model: 'auto',
          provider: 'auto',
          stream: true,
          session_id: sessionId,
          turn_index: newMessages.length
        }));
      }

    } catch (error) {
      console.error(error);
      setIsStreaming(false);
    }
  };

  useEffect(() => {
    if (!isStreaming && messages.length > 0 && messages[messages.length-1].role === 'assistant') {
      if (messages[messages.length-1].content.length > 0) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    }
  }, [isStreaming]);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <LinearGradient
        colors={['#f0f9ff', '#e0f2fe']}
        style={styles.header}
      >
        <View style={styles.headerInner}>
          <View>
            <Text style={styles.headerTitle}>Rta</Text>
            <Text style={[styles.headerStatus, { color: isStreaming ? '#f59e0b' : '#0d9488' }]}>
              {isStreaming ? 'Thinking...' : 'Ready'}
            </Text>
          </View>
          <TouchableOpacity onPress={onLogout} style={styles.logoutBtn}>
            <Text style={styles.logoutText}>EXIT</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView
        style={styles.chatContainer}
        contentContainerStyle={styles.chatContent}
        ref={scrollViewRef}
        onContentSizeChange={() => scrollViewRef.current.scrollToEnd({ animated: true })}
      >
        {messages.length === 0 && (
          <View style={styles.emptyContainer}>
            <LinearGradient
              colors={['#e0f2fe', 'transparent']}
              style={styles.emptyGradient}
            />
            <Text style={styles.emptyText}>Rta is ready to help</Text>
            <Text style={styles.emptySubtext}>Ask anything about your code</Text>
          </View>
        )}
        {messages.map((msg, index) => (
          <View
            key={index}
            style={[
              styles.messageBubble,
              msg.role === 'user' ? styles.userBubble : styles.assistantBubble
            ]}
          >
            {msg.role === 'user' ? (
              <LinearGradient
                colors={['#0ea5e9', '#0284c7']}
                style={styles.bubbleGradient}
              >
                <Text style={styles.userText}>{msg.content}</Text>
              </LinearGradient>
            ) : (
              <Text style={styles.assistantText}>{msg.content || (isStreaming && index === messages.length - 1 ? '...' : '')}</Text>
            )}
          </View>
        ))}
      </ScrollView>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
      >
        <View style={styles.inputArea}>
          <View style={styles.inputWrapper}>
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Message Rta..."
              placeholderTextColor="#94a3b8"
              multiline
            />
            <TouchableOpacity
              style={[styles.sendButton, (!inputText.trim() || isStreaming) && styles.disabledButton]}
              onPress={sendMessage}
              disabled={!inputText.trim() || isStreaming}
            >
              <LinearGradient
                colors={['#f59e0b', '#d97706']}
                style={styles.sendGradient}
              >
                <Text style={styles.sendButtonText}>↑</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f9ff',
  },
  header: {
    borderBottomWidth: 1,
    borderBottomColor: '#e0f2fe',
  },
  headerInner: {
    height: 70,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  headerTitle: {
    color: '#1f2937',
    fontSize: 24,
    fontWeight: '900',
    letterSpacing: -1,
  },
  headerStatus: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  logoutBtn: {
    backgroundColor: 'rgba(31, 41, 55, 0.05)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(31, 41, 55, 0.1)',
  },
  logoutText: {
    color: '#4b5563',
    fontWeight: '800',
    fontSize: 10,
  },
  chatContainer: {
    flex: 1,
  },
  chatContent: {
    padding: 20,
    paddingBottom: 40,
  },
  emptyContainer: {
    flex: 1,
    marginTop: 60,
    alignItems: 'center',
  },
  emptyGradient: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 20,
  },
  emptyText: {
    color: '#1f2937',
    fontSize: 20,
    fontWeight: '800',
  },
  emptySubtext: {
    color: '#4b5563',
    fontSize: 14,
    marginTop: 8,
  },
  messageBubble: {
    marginBottom: 20,
    maxWidth: '85%',
  },
  userBubble: {
    alignSelf: 'flex-end',
    borderRadius: 24,
    borderBottomRightRadius: 4,
    overflow: 'hidden',
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#ffffff',
    borderRadius: 24,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#e0f2fe',
    padding: 16,
    shadowColor: '#0ea5e9',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.02,
    shadowRadius: 5,
    elevation: 1,
  },
  bubbleGradient: {
    padding: 16,
  },
  userText: {
    color: '#fff',
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '500',
  },
  assistantText: {
    color: '#1f2937',
    fontSize: 16,
    lineHeight: 24,
  },
  inputArea: {
    padding: 16,
    backgroundColor: '#f0f9ff',
    borderTopWidth: 1,
    borderTopColor: '#e0f2fe',
  },
  inputWrapper: {
    flexDirection: 'row',
    backgroundColor: '#ffffff',
    borderRadius: 28,
    padding: 4,
    paddingLeft: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0f2fe',
    shadowColor: '#0ea5e9',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.03,
    shadowRadius: 10,
    elevation: 2,
  },
  textInput: {
    flex: 1,
    color: '#1f2937',
    fontSize: 16,
    maxHeight: 120,
    paddingVertical: 10,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    overflow: 'hidden',
  },
  sendGradient: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  disabledButton: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
});
