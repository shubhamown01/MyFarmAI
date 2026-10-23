// MyFarm AI Android Theme — Semantic Color Tokens
// Source: docs/frontend/COLOR_SYSTEM.md
// This file mirrors the web CSS variables for cross-platform consistency

// Light theme tokens
export const lightColors = {
  // Surface
  surface: '#FFFFFF',
  surfaceContainer: '#F8FAF5',
  surfaceContainerLow: '#F0F4EF',
  surfaceContainerHigh: '#E7F0E7',
  surfaceContainerHighest: '#DCE5DC',

  // On-surface
  onSurface: '#17211B',
  onSurfaceVariant: '#66736A',
  onSurfaceDisabled: '#9AA39D',

  // Primary
  primary: '#14532D',
  primaryHover: '#166534',
  primaryActive: '#1B5E20',
  primaryContainer: '#E8F5E9',
  onPrimaryContainer: '#17211B',
  onPrimary: '#FFFFFF',

  // Secondary
  secondary: '#4A6F4A',
  secondaryHover: '#3D5A3D',
  secondaryContainer: '#E7F0E7',
  onSecondaryContainer: '#17211B',

  // Tertiary (Info)
  tertiary: '#2563EB',
  tertiaryContainer: '#DBEAFE',
  onTertiaryContainer: '#1E3A8A',

  // Success
  success: '#166534',
  successContainer: '#DCFCE7',
  onSuccessContainer: '#14532D',

  // Warning
  warning: '#F59E0B',
  warningContainer: '#FEF3C7',
  onWarningContainer: '#78350F',

  // Error
  error: '#DC2626',
  errorContainer: '#FEE2E2',
  onErrorContainer: '#7F1D1D',

  // Info
  info: '#2563EB',
  infoContainer: '#DBEAFE',
  onInfoContainer: '#1E3A8A',

  // Outline / Border
  outline: '#DCE5DC',
  outlineVariant: '#C5CDC5',
  outlineStrong: '#9AA39D',

  // Special Purpose
  scrim: 'rgba(0,0,0,0.5)',
  shadow: 'rgba(0,0,0,0.1)',
  backdrop: 'rgba(248,250,245,0.8)',
} as const;

// Dark theme tokens
export const darkColors = {
  // Surface
  surface: '#1E1E1E',
  surfaceContainer: '#2C2C2C',
  surfaceContainerLow: '#252525',
  surfaceContainerHigh: '#333333',
  surfaceContainerHighest: '#3D3D3D',

  // On-surface
  onSurface: '#E8EAE6',
  onSurfaceVariant: '#A0A8A0',
  onSurfaceDisabled: '#707870',

  // Primary
  primary: '#81C784',
  primaryHover: '#66BB6A',
  primaryActive: '#4CAF50',
  primaryContainer: '#1B5E20',
  onPrimaryContainer: '#E8EAE6',
  onPrimary: '#17211B',

  // Secondary
  secondary: '#A5D6A7',
  secondaryHover: '#81C784',
  secondaryContainer: '#2E7D32',
  onSecondaryContainer: '#E8EAE6',

  // Tertiary (Info)
  tertiary: '#60A5FA',
  tertiaryContainer: '#1E3A8A',
  onTertiaryContainer: '#DBEAFE',

  // Success
  success: '#4ADE80',
  successContainer: '#14532D',
  onSuccessContainer: '#DCFCE7',

  // Warning
  warning: '#FBBF24',
  warningContainer: '#78350F',
  onWarningContainer: '#FEF3C7',

  // Error
  error: '#EF4444',
  errorContainer: '#7F1D1D',
  onErrorContainer: '#FEE2E2',

  // Info
  info: '#60A5FA',
  infoContainer: '#1E3A8A',
  onInfoContainer: '#DBEAFE',

  // Outline / Border
  outline: '#3D3D3D',
  outlineVariant: '#4D4D4D',
  outlineStrong: '#707870',

  // Special Purpose
  scrim: 'rgba(0,0,0,0.7)',
  shadow: 'rgba(0,0,0,0.3)',
  backdrop: 'rgba(30,30,30,0.8)',
} as const;

export type ColorTokens = typeof lightColors;
export type ThemeMode = 'light' | 'dark';

// Spacing tokens (4px base unit)
export const spacing = {
  0: 0,
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
} as const;

// Border radius tokens
export const borderRadius = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
} as const;

// Elevation / Shadow tokens
export const elevation = {
  0: { elevation: 0, shadowOpacity: 0 },
  1: {
    elevation: 1,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  2: {
    elevation: 3,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  3: {
    elevation: 6,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
  },
  4: {
    elevation: 8,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
  },
} as const;

// Motion duration tokens (ms)
export const motionDuration = {
  instant: 0,
  quick: 100,
  fast: 150,
  standard: 200,
  medium: 250,
  slow: 300,
  slower: 400,
} as const;

// Typography scale
export const typography = {
  displayLarge: { fontSize: 56, lineHeight: 62, fontWeight: '600' as const },
  displayMedium: { fontSize: 40, lineHeight: 48, fontWeight: '600' as const },
  displaySmall: { fontSize: 32, lineHeight: 40, fontWeight: '600' as const },
  headlineLarge: { fontSize: 24, lineHeight: 32, fontWeight: '600' as const },
  headlineMedium: { fontSize: 20, lineHeight: 28, fontWeight: '500' as const },
  headlineSmall: { fontSize: 18, lineHeight: 24, fontWeight: '500' as const },
  titleLarge: { fontSize: 16, lineHeight: 24, fontWeight: '600' as const },
  titleMedium: { fontSize: 14, lineHeight: 20, fontWeight: '500' as const },
  titleSmall: { fontSize: 13, lineHeight: 18, fontWeight: '500' as const },
  bodyLarge: { fontSize: 16, lineHeight: 24, fontWeight: '400' as const },
  bodyMedium: { fontSize: 14, lineHeight: 20, fontWeight: '400' as const },
  bodySmall: { fontSize: 13, lineHeight: 18, fontWeight: '400' as const },
  labelLarge: { fontSize: 14, lineHeight: 20, fontWeight: '500' as const },
  labelMedium: { fontSize: 13, lineHeight: 18, fontWeight: '500' as const },
  labelSmall: { fontSize: 12, lineHeight: 16, fontWeight: '500' as const },
} as const;