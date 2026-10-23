import { useState, useCallback } from 'react';
import * as Speech from 'expo-speech';

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speak = useCallback(
    (text: string, language = 'hi-IN') => {
      return new Promise<void>((resolve) => {
        if (!Speech) {
          console.warn('expo-speech not available');
          return;
        }

        const utterance = {
          text,
          language,
          pitch: 1.0,
          rate: 0.9,
          onStart: () => setIsSpeaking(true),
          onDone: () => setIsSpeaking(false),
          onError: () => setIsSpeaking(false),
        };

        Speech.speak(utterance);
        resolve();
      });
    }, []);

  const stop = useCallback(() => {
    Speech.stop();
  }, []);

  return { speak, stop, isSpeaking };
}