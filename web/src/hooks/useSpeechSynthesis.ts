'use client';

import { useState, useCallback, useEffect, useRef } from 'react';

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentText, setCurrentText] = useState<string | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRateState] = useState(1);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    const populateVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      if (availableVoices.length > 0) {
        setVoices(availableVoices);
        if (!selectedVoice) {
          const defaultVoice = availableVoices.find(v => v.default) || availableVoices[0];
          setSelectedVoice(defaultVoice);
        }
      }
    };

    populateVoices();

    const handleVoicesChanged = () => {
      populateVoices();
    };

    window.speechSynthesis.onvoiceschanged = handleVoicesChanged;

    return () => {
      isMountedRef.current = false;
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [selectedVoice]);

  const speak = useCallback(
    (text: string, options?: { language?: string; rate?: number; voice?: SpeechSynthesisVoice }) => {
      if (!('speechSynthesis' in window)) return;

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = options?.language || selectedVoice?.lang || 'en-US';
      utterance.rate = options?.rate ?? rate;
      utterance.pitch = 1;
      utterance.voice = options?.voice || selectedVoice || null;

      utterance.onstart = () => {
        if (isMountedRef.current) {
          setIsSpeaking(true);
          setIsPaused(false);
          setCurrentText(text);
        }
      };
      utterance.onend = () => {
        if (isMountedRef.current) {
          setIsSpeaking(false);
          setIsPaused(false);
          setCurrentText(null);
        }
      };
      utterance.onerror = () => {
        if (isMountedRef.current) {
          setIsSpeaking(false);
          setIsPaused(false);
          setCurrentText(null);
        }
      };
      utterance.onpause = () => {
        if (isMountedRef.current) {
          setIsPaused(true);
        }
      };
      utterance.onresume = () => {
        if (isMountedRef.current) {
          setIsPaused(false);
        }
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    }, [selectedVoice, rate]);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    if (isMountedRef.current) {
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentText(null);
    }
  }, []);

  const pause = useCallback(() => {
    window.speechSynthesis.pause();
  }, []);

  const resume = useCallback(() => {
    window.speechSynthesis.resume();
  }, []);

  const setRate = useCallback((newRate: number) => {
    const clampedRate = Math.max(0.5, Math.min(2, newRate));
    setRateState(clampedRate);
    if (utteranceRef.current && isSpeaking && !isPaused) {
      utteranceRef.current.rate = clampedRate;
    }
  }, [isSpeaking, isPaused]);

  const setVoice = useCallback((voice: SpeechSynthesisVoice) => {
    setSelectedVoice(voice);
  }, []);

  return {
    speak,
    stop,
    pause,
    resume,
    setRate,
    setVoice,
    voices,
    isSpeaking,
    isPaused,
    currentText,
  };
}