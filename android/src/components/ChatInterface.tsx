import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { useChat } from '../hooks/useChat';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { ChatMessage } from '../types/chat';
import { useTheme } from '../theme';

interface ChatInterfaceProps {
  weatherContext?: { latitude: number; longitude: number } | null;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  weatherContext,
}) => {
  const [input, setInput] = useState('');
  const {
    messages,
    isLoading,
    error,
    clearError,
    sendMessage,
    clearConversation,
  } = useChat();
  const { isListening, transcript, startListening, stopListening } =
    useSpeechRecognition('hi-IN');
  const { speak } = useSpeechSynthesis();
  const { colors } = useTheme();
  const [ttsEnabled, setTtsEnabled] = useState(false);

  const lastMessage = messages[messages.length - 1];
  useEffect(() => {
    if (ttsEnabled && lastMessage?.role === 'assistant') {
      speak(lastMessage.content, 'hi-IN');
    }
  }, [lastMessage, ttsEnabled, speak]);

  const handleSubmit = () => {
    if (input.trim()) {
      sendMessage(input, {
        language: 'hi',
        crop: undefined,
        location: weatherContext
          ? `${weatherContext.latitude},${weatherContext.longitude}`
          : undefined,
      });
      setInput('');
    }
  };

  const handleVoiceInput = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleSendTranscript = () => {
    if (transcript.trim()) {
      sendMessage(transcript.trim(), {
        language: 'hi',
        crop: undefined,
        location: weatherContext
          ? `${weatherContext.latitude},${weatherContext.longitude}`
          : undefined,
      });
    }
  };

  const renderMessage = ({ item }: { item: ChatMessage }) => (
    <View
      style={[
        styles.messageContainer,
        item.role === 'user' ? styles.userMessage : styles.assistantMessage,
      ]}
    >
      <View style={[styles.messageBubble, { backgroundColor: item.role === 'user' ? colors.primary : colors.surfaceContainerHigh }]}>
        <Text style={[styles.messageText, { color: item.role === 'user' ? colors.onPrimary : colors.onSurface }]}>{item.content}</Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.surface }]}>
      <View style={[styles.header, { backgroundColor: colors.primary }]}>
        <Text style={styles.headerTitle}>MyFarm AI</Text>
        <TouchableOpacity
          onPress={() => setTtsEnabled((v) => !v)}
          accessibilityRole="button"
          accessibilityLabel={
            ttsEnabled ? 'Disable spoken replies' : 'Enable spoken replies'
          }
          accessibilityState={{ selected: ttsEnabled }}
        >
          <Text style={styles.headerAction}>{ttsEnabled ? '🔊 On' : '🔇 Off'}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => Alert.alert('Clear conversation?', '', [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Clear', style: 'destructive', onPress: clearConversation },
        ])}>
          <Text style={styles.headerAction}>Clear</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={[styles.listContent, messages.length === 0 && styles.emptyListContent]}
        inverted={messages.length > 0}
        ListEmptyComponent={
          <View style={styles.welcomeContainer}>
            <Text style={[styles.welcomeTitle, { color: colors.primary }]}>Welcome to MyFarm AI</Text>
            <Text style={[styles.welcomeText, { color: colors.onSurfaceVariant }]}>
              Ask me anything about farming — crops, weather, soil, pests, or government schemes.
            </Text>
          </View>
        }
      />

      {isLoading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.onSurfaceVariant }]}>Thinking...</Text>
        </View>
      )}

      {error && (
        <TouchableOpacity
          style={[styles.errorBanner, { backgroundColor: colors.errorContainer }]}
          onPress={clearError}
          accessibilityRole="button"
          accessibilityLabel={`Chat error: ${error}. Tap to dismiss.`}
          accessibilityLiveRegion="polite"
        >
          <Text style={[styles.errorText, { color: colors.onErrorContainer }]}>
            {error}
          </Text>
        </TouchableOpacity>
      )}

      <View style={[styles.inputContainer, { backgroundColor: colors.surfaceContainer, borderTopColor: colors.outline }]}>
        <View style={styles.inputRow}>
          <View style={[styles.inputWrapper, { backgroundColor: colors.surfaceContainerLow }]}>
            <TextInput
              style={[styles.input, { color: colors.onSurface }]}
              value={input}
              onChangeText={setInput}
              placeholder="Ask about crops, weather, soil..."
              placeholderTextColor={colors.onSurfaceDisabled}
              multiline
              maxLength={2000}
              onSubmitEditing={handleSubmit}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={[
                styles.voiceButton,
                { backgroundColor: isListening ? colors.primaryActive : colors.primaryContainer },
              ]}
              onPress={handleVoiceInput}
              disabled={isLoading}
              accessibilityRole="button"
              accessibilityLabel={
                isListening ? 'Stop voice input' : 'Start voice input'
              }
              accessibilityState={{ selected: isListening }}
            >
              <Text style={[styles.voiceButtonText, { color: isListening ? colors.onPrimary : colors.onPrimaryContainer }]}>
                {isListening ? '●' : '🎤'}
              </Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[
              styles.sendButton,
              isLoading || !input.trim() ? styles.sendButtonDisabled : null,
              { backgroundColor: isLoading || !input.trim() ? colors.outlineVariant : colors.primary },
            ]}
            onPress={handleSubmit}
            disabled={isLoading || !input.trim()}
            accessibilityRole="button"
            accessibilityLabel="Send message"
          >
            <Text style={[styles.sendButtonText, { color: colors.onPrimary }]}>Send</Text>
          </TouchableOpacity>
        </View>

        {isListening && (
          <View style={[styles.transcriptContainer, { backgroundColor: colors.primaryContainer }]}>
            <Text style={[styles.transcriptLabel, { color: colors.onPrimaryContainer }]}>Listening...</Text>
            <Text style={[styles.transcriptText, { color: colors.onPrimaryContainer }]}>{transcript}</Text>
            <View style={styles.transcriptActions}>
              <TouchableOpacity
                style={[styles.transcriptButton, { backgroundColor: colors.primary }]}
                onPress={handleSendTranscript}
              >
                <Text style={[styles.transcriptButtonText, { color: colors.onPrimary }]}>Send</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.transcriptButton, styles.transcriptButtonSecondary, { backgroundColor: colors.outline }]}
                onPress={stopListening}
              >
                <Text style={[styles.transcriptButtonText, { color: colors.onSurface }]}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '600',
  },
  headerAction: {
    color: '#FFFFFF',
    fontSize: 16,
  },
  listContent: {
    padding: 16,
    paddingBottom: 100,
  },
  emptyListContent: {
    flexGrow: 1,
  },
  messageContainer: {
    marginBottom: 12,
    maxWidth: '85%',
  },
  userMessage: {
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    alignSelf: 'flex-start',
  },
  messageBubble: {
    padding: 12,
    borderRadius: 16,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
  },
  errorBanner: {
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 8,
  },
  errorText: {
    fontSize: 14,
    lineHeight: 20,
  },
  inputContainer: {
    padding: 16,
    borderTopWidth: 1,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  input: {
    flex: 1,
    fontSize: 16,
    maxHeight: 120,
    paddingVertical: 4,
  },
  voiceButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  voiceButtonText: {
    fontSize: 20,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {},
  sendButtonText: {
    fontSize: 18,
    fontWeight: '600',
  },
  transcriptContainer: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  transcriptLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  transcriptText: {
    fontSize: 14,
    marginBottom: 8,
  },
  transcriptActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
  },
  transcriptButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  transcriptButtonSecondary: {},
  transcriptButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  welcomeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 12,
  },
  welcomeText: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
  },
});

export default ChatInterface;