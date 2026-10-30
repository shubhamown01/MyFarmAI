import { useState, useCallback, useEffect } from 'react';
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from 'expo-speech-recognition';

export function useSpeechRecognition(language = 'hi-IN') {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');

  useEffect(() => {
    if (!ExpoSpeechRecognitionModule.isRecognitionAvailable()) {
      console.warn('Speech recognition not available');
    }
    ExpoSpeechRecognitionModule.requestPermissionsAsync().catch(() => {
      console.warn('Speech recognition permission request failed');
    });
  }, []);

  useSpeechRecognitionEvent('start', () => setIsListening(true));
  useSpeechRecognitionEvent('end', () => setIsListening(false));
  useSpeechRecognitionEvent('error', (event: { error?: string }) => {
    console.warn('Speech recognition error:', event?.error);
    setIsListening(false);
  });
  useSpeechRecognitionEvent('result', (event: { results?: { transcript?: string }[] }) => {
    const text = event.results?.[0]?.transcript;
    if (text) {
      setTranscript((prev) => (prev ? `${prev} ${text}` : text));
    }
  });

  const startListening = useCallback(() => {
    if (!ExpoSpeechRecognitionModule.isRecognitionAvailable()) return;
    setTranscript('');
    ExpoSpeechRecognitionModule.start({
      lang: language,
      interimResults: true,
      continuous: false,
    });
  }, [language]);

  const stopListening = useCallback(() => {
    ExpoSpeechRecognitionModule.stop();
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
  }, []);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    resetTranscript,
  };
}
