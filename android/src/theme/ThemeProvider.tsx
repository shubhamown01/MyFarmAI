'use client';

import React, { createContext, useContext, useMemo, useState, useEffect, ReactNode } from 'react';
import { Appearance, ColorSchemeName, StyleSheet } from 'react-native';
import { lightColors, darkColors, ColorTokens, ThemeMode } from './colors';

interface ThemeContextValue {
  colors: ColorTokens;
  mode: ThemeMode;
  systemMode: ColorSchemeName;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>('light');
  const [systemMode, setSystemMode] = useState<ColorSchemeName>('light');

  useEffect(() => {
    const subscription = Appearance.addChangeListener(({ colorScheme }) => {
      setSystemMode(colorScheme);
    });
    setSystemMode(Appearance.getColorScheme());
    return () => subscription.remove();
  }, []);

  const colors = useMemo(() => (mode === 'dark' ? darkColors : lightColors), [mode]);

  const toggleTheme = () => setMode((prev) => (prev === 'light' ? 'dark' : 'light'));
  const setTheme = (newMode: ThemeMode) => setMode(newMode);

  return (
    <ThemeContext.Provider value={{ colors, mode, systemMode, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}

// Helper hook for reduced motion (Android)
export function useReducedMotion(): boolean {
  const [reduceMotion, setReduceMotion] = useState(false);
  useEffect(() => {
    // Note: React Native's AccessibilityInfo.isReduceMotionEnabled() requires native module
    // For now, we'll use a simple state. In production, integrate with AccessibilityInfo.
    const checkReducedMotion = async () => {
      try {
        const { AccessibilityInfo } = await import('react-native');
        const enabled = await AccessibilityInfo.isReduceMotionEnabled();
        setReduceMotion(enabled);
        const listener = AccessibilityInfo.addEventListener(
          'reduceMotionChanged',
          setReduceMotion
        );
        return () => listener.remove();
      } catch {
        // AccessibilityInfo not available
      }
    };
    checkReducedMotion();
  }, []);
  return reduceMotion;
}

// Helper to get motion duration respecting reduced motion
export function useMotionDuration(duration: number): number {
  const reduceMotion = useReducedMotion();
  return reduceMotion ? 0 : duration;
}

// Pre-defined styles using theme tokens (for StyleSheet.create)
export const createThemedStyles = <T extends StyleSheet.NamedStyles<T> | StyleSheet.NamedStyles<any>>(
  styleFactory: (colors: ColorTokens) => T
) => {
  // This is a helper for creating themed styles - actual usage requires useTheme() hook
  // because StyleSheet.create is static. Use inline styles or the useTheme hook in components.
  return styleFactory(lightColors); // Fallback, actual theming done in components
};