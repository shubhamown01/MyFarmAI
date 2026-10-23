'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onend: () => void;
  onstart: () => void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

function getSpeechErrorMessage(error: string) {
  switch (error) {
    case 'not-allowed':
    case 'service-not-allowed':
      return 'Microphone access was blocked. Allow microphone access in your browser settings, then try again.';
    case 'audio-capture':
      return 'No microphone was found. Check that a microphone is connected and try again.';
    case 'no-speech':
      return 'No speech was detected. Try again and speak a little closer to the microphone.';
    case 'network':
      return 'Voice input needs a network connection in this browser. Check your connection and try again.';
    case 'aborted':
      return 'Voice input stopped.';
    default:
      return 'Voice input could not start. Type your question instead.';
  }
}

export function useSpeechRecognition(initialLanguage = 'en-IN') {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [language, setLanguageState] = useState(initialLanguage);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isListeningRef = useRef(false);

  useEffect(() => {
    const Recognition =
      typeof window !== 'undefined'
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : undefined;

    if (!Recognition) {
      setIsSupported(false);
      return;
    }

    setIsSupported(true);
    const recognition = new Recognition();
    recognition.lang = language;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript((previous) => `${previous} ${finalTranscript}`.trim());
      }
      setInterimTranscript(interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setError(getSpeechErrorMessage(event.error));
      isListeningRef.current = false;
      setIsListening(false);
      setInterimTranscript('');
    };

    recognition.onend = () => {
      isListeningRef.current = false;
      setIsListening(false);
      setInterimTranscript('');
    };

    recognition.onstart = () => {
      isListeningRef.current = true;
      setIsListening(true);
      setError(null);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.onresult = () => {};
      recognition.onerror = () => {};
      recognition.onend = () => {};
      recognition.onstart = () => {};
      try {
        recognition.abort();
      } catch {
        // The browser may already have stopped recognition.
      }
      recognitionRef.current = null;
    };
  }, [language]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      setError('Voice input is not supported in this browser. Type your question instead.');
      return;
    }
    if (isListeningRef.current) return;

    setTranscript('');
    setInterimTranscript('');
    setError(null);

    try {
      recognitionRef.current.start();
    } catch {
      setError('Voice input could not start. Try again, or type your question instead.');
    }
  }, []);

  const stopListening = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // Ignore stop errors when the browser has already ended the session.
    }
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setError(null);
  }, []);

  const setLanguage = useCallback((lang: string) => {
    setLanguageState(lang);
    if (isListeningRef.current) {
      try {
        recognitionRef.current?.stop();
      } catch {
        // Ignore stop errors when the browser has already ended the session.
      }
    }
  }, []);

  return {
    isListening,
    isSupported,
    transcript,
    interimTranscript,
    language,
    startListening,
    stopListening,
    resetTranscript,
    setLanguage,
    error,
  };
}
