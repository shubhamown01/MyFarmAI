'use client';

import { useCallback, useEffect, useState } from 'react';

export interface RecentQuestion {
  id: string;
  text: string;
  createdAt: string;
}

const RECENT_STORAGE_KEY = 'myfarmai_recent_questions_v1';
const RECENT_EVENT = 'myfarmai:recent-questions-change';
const MAX_RECENT_QUESTIONS = 8;

function createId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function isRecentQuestion(value: unknown): value is RecentQuestion {
  if (!value || typeof value !== 'object') return false;
  const item = value as Partial<RecentQuestion>;
  return typeof item.id === 'string' && typeof item.text === 'string' && typeof item.createdAt === 'string';
}

function readStoredQuestions(): RecentQuestion[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(RECENT_STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isRecentQuestion).slice(0, MAX_RECENT_QUESTIONS);
  } catch {
    return [];
  }
}

/**
 * Maintains a small, local question history until the backend exposes a
 * conversation-history endpoint. Storage is versioned and capped so it stays
 * useful without growing unbounded.
 */
export function useRecentQuestions() {
  const [questions, setQuestions] = useState<RecentQuestion[]>([]);

  useEffect(() => {
    const sync = () => setQuestions(readStoredQuestions());
    sync();

    window.addEventListener(RECENT_EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(RECENT_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  const addQuestion = useCallback((text: string) => {
    const clean = text.trim().slice(0, 500);
    if (!clean) return;

    const existing = readStoredQuestions();
    const next: RecentQuestion[] = [
      { id: createId(), text: clean, createdAt: new Date().toISOString() },
      ...existing.filter((item) => item.text.toLowerCase() !== clean.toLowerCase()),
    ].slice(0, MAX_RECENT_QUESTIONS);

    window.localStorage.setItem(RECENT_STORAGE_KEY, JSON.stringify(next));
    setQuestions(next);
    window.dispatchEvent(new Event(RECENT_EVENT));
  }, []);

  const clearQuestions = useCallback(() => {
    window.localStorage.removeItem(RECENT_STORAGE_KEY);
    setQuestions([]);
    window.dispatchEvent(new Event(RECENT_EVENT));
  }, []);

  return { questions, addQuestion, clearQuestions };
}
