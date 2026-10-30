import { useState, useCallback } from 'react';
import * as Speech from 'expo-speech';

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speak = useCallback(
    (text: string, language = 'hi-IN') => {
      return new Promise<void>((resolve) => {
        Speech.speak(text, {
          language,
          pitch: 1.0,
          rate: 0.9,
          onStart: () => setIsSpeaking(true),
          onDone: () => {
            setIsSpeaking(false);
            resolve();
          },
          onStopped: () => {
            setIsSpeaking(false);
            resolve();
          },
          onError: () => {
            setIsSpeaking(false);
            resolve();
          },
        });
      });
    },
    []
  );

  const stop = useCallback(() => {
    Speech.stop();
  }, []);

  return { speak, stop, isSpeaking };
}
