import { useState, useRef, useCallback, useEffect } from 'react';
import * as Speech from 'expo-speech-recognition';

export function useSpeechRecognition(language = 'hi-IN') {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const initializeRecognition = async () => {
      const available = await Speech.isAvailableAsync();
      if (!available) {
        console.warn('Speech recognition not available');
        return;
      }

      const SpeechRecognition = Speech;
      const recognition = new SpeechRecognition();

      recognition.lang = language;
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setTranscript((prev) => prev + ' ' + finalTranscript);
        }
      };

      recognitionRef.current = recognition;
    };

    initializeRecognition();

    return () => {
      recognitionRef.current?.stop();
    };
  }, [language]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      setTranscript('');
      recognitionRef.current.start();
    }
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
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