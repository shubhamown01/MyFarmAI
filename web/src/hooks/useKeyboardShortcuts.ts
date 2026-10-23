'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  description: string;
  category: 'navigation' | 'chat' | 'voice' | 'global';
  callback: () => void;
  global?: boolean;
  preventDefault?: boolean;
}

interface RegisteredShortcut extends KeyboardShortcut {
  id: string;
}

export function useKeyboardShortcuts() {
  const shortcutsRef = useRef<Map<string, RegisteredShortcut>>(new Map());
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([]);

  const generateId = useCallback((shortcut: KeyboardShortcut): string => {
    const parts = [];
    if (shortcut.ctrlKey) parts.push('ctrl');
    if (shortcut.shiftKey) parts.push('shift');
    if (shortcut.altKey) parts.push('alt');
    if (shortcut.metaKey) parts.push('meta');
    parts.push(shortcut.key.toLowerCase());
    return parts.join('+');
  }, []);

  const matchesShortcut = useCallback((event: KeyboardEvent, shortcut: RegisteredShortcut): boolean => {
    if (event.key.toLowerCase() !== shortcut.key.toLowerCase()) return false;
    if (shortcut.ctrlKey !== undefined && event.ctrlKey !== shortcut.ctrlKey) return false;
    if (shortcut.shiftKey !== undefined && event.shiftKey !== shortcut.shiftKey) return false;
    if (shortcut.altKey !== undefined && event.altKey !== shortcut.altKey) return false;
    if (shortcut.metaKey !== undefined && event.metaKey !== shortcut.metaKey) return false;
    return true;
  }, []);

  const isInputFocused = useCallback((): boolean => {
    const activeElement = document.activeElement;
    if (!activeElement) return false;
    const tagName = activeElement.tagName.toLowerCase();
    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      (activeElement as HTMLElement).isContentEditable
    );
  }, []);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const inputFocused = isInputFocused();

    shortcutsRef.current.forEach((shortcut) => {
      if (!matchesShortcut(event, shortcut)) return;

      const shouldTrigger = shortcut.global || !inputFocused;

      if (shouldTrigger) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault();
        }
        shortcut.callback();
      }
    });
  }, [isInputFocused, matchesShortcut]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  const registerShortcut = useCallback((shortcut: KeyboardShortcut): string => {
    const id = generateId(shortcut);
    const registeredShortcut: RegisteredShortcut = { ...shortcut, id };
    shortcutsRef.current.set(id, registeredShortcut);
    setShortcuts(Array.from(shortcutsRef.current.values()));
    return id;
  }, [generateId]);

  const unregisterShortcut = useCallback((idOrShortcut: string | KeyboardShortcut): void => {
    const id = typeof idOrShortcut === 'string' ? idOrShortcut : generateId(idOrShortcut);
    shortcutsRef.current.delete(id);
    setShortcuts(Array.from(shortcutsRef.current.values()));
  }, [generateId]);

  return {
    registerShortcut,
    unregisterShortcut,
    shortcuts,
  };
}

export function createDefaultShortcuts(callbacks: {
  onFocusChatInput?: () => void;
  onSendMessage?: () => void;
  onNewLine?: () => void;
  onToggleVoiceInput?: () => void;
  onToggleTheme?: () => void;
  onShowHelp?: () => void;
}): KeyboardShortcut[] {
  return [
    {
      key: '/',
      description: 'Focus chat input',
      category: 'navigation',
      callback: callbacks.onFocusChatInput ?? (() => {}),
      global: true,
    },
    {
      key: 'k',
      ctrlKey: true,
      description: 'Focus chat input',
      category: 'navigation',
      callback: callbacks.onFocusChatInput ?? (() => {}),
      global: true,
    },
    {
      key: 'Enter',
      description: 'Send message',
      category: 'chat',
      callback: callbacks.onSendMessage ?? (() => {}),
      global: false,
    },
    {
      key: 'Enter',
      shiftKey: true,
      description: 'New line',
      category: 'chat',
      callback: callbacks.onNewLine ?? (() => {}),
      global: false,
    },
    {
      key: ' ',
      ctrlKey: true,
      description: 'Toggle voice input',
      category: 'voice',
      callback: callbacks.onToggleVoiceInput ?? (() => {}),
      global: true,
    },
    {
      key: 'l',
      ctrlKey: true,
      shiftKey: true,
      description: 'Toggle theme',
      category: 'global',
      callback: callbacks.onToggleTheme ?? (() => {}),
      global: true,
    },
    {
      key: '?',
      description: 'Show shortcuts help',
      category: 'global',
      callback: callbacks.onShowHelp ?? (() => {}),
      global: true,
    },
  ];
}