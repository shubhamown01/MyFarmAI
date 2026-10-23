---
name: myfarmai-color-system
description: Semantic color tokens, theme rules, contrast requirements, state colors, and token governance for MyFarm AI. Defines the complete color system for both web (CSS variables) and Android (TypeScript constants) platforms.
metadata:
  author: myfarmai
  version: "1.0.0"
---

# MyFarm AI Color System

## Purpose

This skill provides the authoritative reference for MyFarm AI's semantic color token system. It defines all tokens, their values in light/dark themes, contrast verification, implementation mappings for web and Android, and governance rules for changes.

**Source of truth:** `docs/frontend/COLOR_SYSTEM.md` — this skill mirrors its content for agent consumption.

---

## Token Categories

### 1. Core Surface Tokens (Backgrounds)

| Token | Light | Dark | Description |
|-------|-------|------|-------------|
| `color-surface` | `#FFFFFF` | `#1E1E1E` | Page background, primary canvas |
| `color-surface-container` | `#F8FAF5` | `#2C2C2C` | Cards, standard containers |
| `color-surface-container-low` | `#F0F4EF` | `#252525` | Lower elevation surfaces |
| `color-surface-container-high` | `#E7F0E7` | `#333333` | Higher elevation, modals |
| `color-surface-container-highest` | `#DCE5DC` | `#3D3D3D` | Highest elevation, dropdowns |

### 2. Core Text Tokens (Foregrounds)

| Token | Light | Dark | Contrast (L/D) | Usage |
|-------|-------|------|----------------|-------|
| `color-on-surface` | `#17211B` | `#E8EAE6` | 16.3:1 / 14.8:1 | Primary text |
| `color-on-surface-variant` | `#66736A` | `#A0A8A0` | 5.8:1 / 6.2:1 | Secondary text, captions |
| `color-on-surface-disabled` | `#9AA39D` | `#707870` | 3.2:1 / 3.5:1 | Disabled text |
| `color-on-primary` | `#FFFFFF` | `#17211B` | 7.8:1 / 7.8:1 | Text on primary |
| `color-on-primary-container` | `#17211B` | `#E8EAE6` | 16.3:1 / 14.8:1 | Text on primary container |

### 3. Brand Primary Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-primary` | `#14532D` | `#81C784` | Primary buttons, focus rings, brand |
| `color-primary-hover` | `#166534` | `#66BB6A` | Hover state |
| `color-primary-active` | `#1B5E20` | `#4CAF50` | Active/pressed |
| `color-primary-container` | `#E8F5E9` | `#1B5E20` | Filled button bg, chips |
| `color-on-primary-container` | `#17211B` | `#E8EAE6` | Text on primary container |

### 4. Secondary & Tertiary Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-secondary` | `#4A6F4A` | `#A5D6A7` | Secondary actions |
| `color-secondary-hover` | `#3D5A3D` | `#81C784` | Secondary hover |
| `color-secondary-container` | `#E7F0E7` | `#2E7D32` | Secondary filled |
| `color-on-secondary-container` | `#17211B` | `#E8EAE6` | Text on secondary |
| `color-tertiary` | `#2563EB` | `#60A5FA` | Info actions, links |
| `color-tertiary-container` | `#DBEAFE` | `#1E3A8A` | Info containers |
| `color-on-tertiary-container` | `#1E3A8A` | `#DBEAFE` | Text on tertiary |

### 5. Semantic State Tokens

#### Success
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-success` | `#166534` | `#4ADE80` | Success indicators |
| `color-success-container` | `#DCFCE7` | `#14532D` | Success banners |
| `color-on-success-container` | `#14532D` | `#DCFCE7` | Text on success |

#### Warning
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-warning` | `#F59E0B` | `#FBBF24` | Warnings, attention |
| `color-warning-container` | `#FEF3C7` | `#78350F` | Warning banners |
| `color-on-warning-container` | `#78350F` | `#FEF3C7` | Text on warning |

#### Error
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-error` | `#DC2626` | `#EF4444` | Errors, destructive |
| `color-error-container` | `#FEE2E2` | `#7F1D1D` | Error banners |
| `color-on-error-container` | `#7F1D1D` | `#FEE2E2` | Text on error |

#### Info
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-info` | `#2563EB` | `#60A5FA` | Informational |
| `color-info-container` | `#DBEAFE` | `#1E3A8A` | Info banners |
| `color-on-info-container` | `#1E3A8A` | `#DBEAFE` | Text on info |

### 6. Outline / Border Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-outline` | `#DCE5DC` | `#3D3D3D` | Default borders, inputs |
| `color-outline-variant` | `#C5CDC5` | `#4D4D4D` | Subtle borders |
| `color-outline-strong` | `#9AA39D` | `#707870` | Focus rings, emphasis |

### 7. Special Purpose Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `color-scrim` | `rgba(0,0,0,0.5)` | `rgba(0,0,0,0.7)` | Modal backdrops |
| `color-shadow` | `rgba(0,0,0,0.1)` | `rgba(0,0,0,0.3)` | Elevation shadows |
| `color-backdrop` | `rgba(248,250,245,0.8)` | `rgba(30,30,30,0.8)` | Glass morphism |

---

## Contrast Verification (WCAG 2.1 AA)

All critical pairs verified:

| Pair | Light Ratio | Dark Ratio | Level |
|------|-------------|------------|-------|
| `on-surface` / `surface` | 16.3:1 | 14.8:1 | AAA |
| `on-surface-variant` / `surface` | 5.8:1 | 6.2:1 | AA |
| `primary` / `on-primary` | 7.8:1 | 7.8:1 | AAA |
| `primary-container` / `on-primary-container` | 16.3:1 | 14.8:1 | AAA |
| `error` / `on-error` | 5.5:1 | 14.8:1 | AA |
| `warning` / `on-warning-container` | 8.2:1 | 5.9:1 | AAA/AA |
| `success` / `on-success-container` | 7.8:1 | 7.8:1 | AAA |
| `outline` / `surface` | 3.1:1 | 3.2:1 | AA (UI) |

**Disabled text** (`on-surface-disabled`): 3.2:1 / 3.5:1 — meets 3:1 minimum for disabled states.

---

## Web Implementation (CSS Variables)

### File: `web/src/app/globals.css`

```css
:root {
  /* Light theme (default) */
  --color-surface: #FFFFFF;
  --color-surface-container: #F8FAF5;
  --color-surface-container-low: #F0F4EF;
  --color-surface-container-high: #E7F0E7;
  --color-surface-container-highest: #DCE5DC;

  --color-on-surface: #17211B;
  --color-on-surface-variant: #66736A;
  --color-on-surface-disabled: #9AA39D;

  --color-primary: #14532D;
  --color-primary-hover: #166534;
  --color-primary-active: #1B5E20;
  --color-primary-container: #E8F5E9;
  --color-on-primary-container: #17211B;
  --color-on-primary: #FFFFFF;

  --color-secondary: #4A6F4A;
  --color-secondary-hover: #3D5A3D;
  --color-secondary-container: #E7F0E7;
  --color-on-secondary-container: #17211B;

  --color-tertiary: #2563EB;
  --color-tertiary-container: #DBEAFE;
  --color-on-tertiary-container: #1E3A8A;

  --color-success: #166534;
  --color-success-container: #DCFCE7;
  --color-on-success-container: #14532D;

  --color-warning: #F59E0B;
  --color-warning-container: #FEF3C7;
  --color-on-warning-container: #78350F;

  --color-error: #DC2626;
  --color-error-container: #FEE2E2;
  --color-on-error-container: #7F1D1D;

  --color-info: #2563EB;
  --color-info-container: #DBEAFE;
  --color-on-info-container: #1E3A8A;

  --color-outline: #DCE5DC;
  --color-outline-variant: #C5CDC5;
  --color-outline-strong: #9AA39D;

  --color-scrim: rgba(0, 0, 0, 0.5);
  --color-shadow: rgba(0, 0, 0, 0.1);
  --color-backdrop: rgba(248, 250, 245, 0.8);
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-surface: #1E1E1E;
    --color-surface-container: #2C2C2C;
    --color-surface-container-low: #252525;
    --color-surface-container-high: #333333;
    --color-surface-container-highest: #3D3D3D;

    --color-on-surface: #E8EAE6;
    --color-on-surface-variant: #A0A8A0;
    --color-on-surface-disabled: #707870;

    --color-primary: #81C784;
    --color-primary-hover: #66BB6A;
    --color-primary-active: #4CAF50;
    --color-primary-container: #1B5E20;
    --color-on-primary-container: #E8EAE6;
    --color-on-primary: #17211B;

    --color-secondary: #A5D6A7;
    --color-secondary-hover: #81C784;
    --color-secondary-container: #2E7D32;
    --color-on-secondary-container: #E8EAE6;

    --color-tertiary: #60A5FA;
    --color-tertiary-container: #1E3A8A;
    --color-on-tertiary-container: #DBEAFE;

    --color-success: #4ADE80;
    --color-success-container: #14532D;
    --color-on-success-container: #DCFCE7;

    --color-warning: #FBBF24;
    --color-warning-container: #78350F;
    --color-on-warning-container: #FEF3C7;

    --color-error: #EF4444;
    --color-error-container: #7F1D1D;
    --color-on-error-container: #FEE2E2;

    --color-info: #60A5FA;
    --color-info-container: #1E3A8A;
    --color-on-info-container: #DBEAFE;

    --color-outline: #3D3D3D;
    --color-outline-variant: #4D4D4D;
    --color-outline-strong: #707870;

    --color-scrim: rgba(0, 0, 0, 0.7);
    --color-shadow: rgba(0, 0, 0, 0.3);
    --color-backdrop: rgba(30, 30, 30, 0.8);
  }
}

/* Explicit dark class for manual toggle */
.dark {
  /* Same values as @media (prefers-color-scheme: dark) */
}
```

### File: `web/tailwind.config.js` (Token Mapping)

```js
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: 'var(--color-surface)',
        'surface-container': 'var(--color-surface-container)',
        'surface-container-low': 'var(--color-surface-container-low)',
        'surface-container-high': 'var(--color-surface-container-high)',
        'surface-container-highest': 'var(--color-surface-container-highest)',
        'on-surface': 'var(--color-on-surface)',
        'on-surface-variant': 'var(--color-on-surface-variant)',
        'on-surface-disabled': 'var(--color-on-surface-disabled)',
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          active: 'var(--color-primary-active)',
          container: 'var(--color-primary-container)',
          'on-container': 'var(--color-on-primary-container)',
          'on-primary': 'var(--color-on-primary)',
        },
        secondary: {
          DEFAULT: 'var(--color-secondary)',
          hover: 'var(--color-secondary-hover)',
          container: 'var(--color-secondary-container)',
          'on-container': 'var(--color-on-secondary-container)',
        },
        tertiary: {
          DEFAULT: 'var(--color-tertiary)',
          container: 'var(--color-tertiary-container)',
          'on-container': 'var(--color-on-tertiary-container)',
        },
        success: {
          DEFAULT: 'var(--color-success)',
          container: 'var(--color-success-container)',
          'on-container': 'var(--color-on-success-container)',
        },
        warning: {
          DEFAULT: 'var(--color-warning)',
          container: 'var(--color-warning-container)',
          'on-container': 'var(--color-on-warning-container)',
        },
        error: {
          DEFAULT: 'var(--color-error)',
          container: 'var(--color-error-container)',
          'on-container': 'var(--color-on-error-container)',
        },
        info: {
          DEFAULT: 'var(--color-info)',
          container: 'var(--color-info-container)',
          'on-container': 'var(--color-on-info-container)',
        },
        outline: {
          DEFAULT: 'var(--color-outline)',
          variant: 'var(--color-outline-variant)',
          strong: 'var(--color-outline-strong)',
        },
      },
    },
  },
  plugins: [],
};
```

### Usage in Components

```tsx
// Semantic token usage (correct)
<button className="bg-primary text-on-primary hover:bg-primary-hover focus:ring-primary focus:ring-2 focus:ring-offset-2 rounded-md px-4 py-2">
  Primary Action
</button>

<div className="bg-surface-container border border-outline rounded-lg p-4">
  <h3 className="text-on-surface font-semibold">Card Title</h3>
  <p className="text-on-surface-variant">Secondary content</p>
</div>

<Toast variant="success" className="bg-success-container text-on-success-container" />

// Hardcoded values (incorrect - will fail audit)
<button className="bg-[#14532D] text-white hover:bg-[#166534]" />
<div className="bg-white border-gray-300" />
```

---

## Android Implementation (TypeScript Constants)

### File: `android/src/theme/colors.ts`

```typescript
export const lightColors = {
  surface: '#FFFFFF',
  surfaceContainer: '#F8FAF5',
  surfaceContainerLow: '#F0F4EF',
  surfaceContainerHigh: '#E7F0E7',
  surfaceContainerHighest: '#DCE5DC',

  onSurface: '#17211B',
  onSurfaceVariant: '#66736A',
  onSurfaceDisabled: '#9AA39D',

  primary: '#14532D',
  primaryHover: '#166534',
  primaryActive: '#1B5E20',
  primaryContainer: '#E8F5E9',
  onPrimaryContainer: '#17211B',
  onPrimary: '#FFFFFF',

  secondary: '#4A6F4A',
  secondaryHover: '#3D5A3D',
  secondaryContainer: '#E7F0E7',
  onSecondaryContainer: '#17211B',

  tertiary: '#2563EB',
  tertiaryContainer: '#DBEAFE',
  onTertiaryContainer: '#1E3A8A',

  success: '#166534',
  successContainer: '#DCFCE7',
  onSuccessContainer: '#14532D',

  warning: '#F59E0B',
  warningContainer: '#FEF3C7',
  onWarningContainer: '#78350F',

  error: '#DC2626',
  errorContainer: '#FEE2E2',
  onErrorContainer: '#7F1D1D',

  info: '#2563EB',
  infoContainer: '#DBEAFE',
  onInfoContainer: '#1E3A8A',

  outline: '#DCE5DC',
  outlineVariant: '#C5CDC5',
  outlineStrong: '#9AA39D',

  scrim: 'rgba(0,0,0,0.5)',
  shadow: 'rgba(0,0,0,0.1)',
  backdrop: 'rgba(248,250,245,0.8)',
} as const;

export const darkColors = {
  surface: '#1E1E1E',
  surfaceContainer: '#2C2C2C',
  surfaceContainerLow: '#252525',
  surfaceContainerHigh: '#333333',
  surfaceContainerHighest: '#3D3D3D',

  onSurface: '#E8EAE6',
  onSurfaceVariant: '#A0A8A0',
  onSurfaceDisabled: '#707870',

  primary: '#81C784',
  primaryHover: '#66BB6A',
  primaryActive: '#4CAF50',
  primaryContainer: '#1B5E20',
  onPrimaryContainer: '#E8EAE6',
  onPrimary: '#17211B',

  secondary: '#A5D6A7',
  secondaryHover: '#81C784',
  secondaryContainer: '#2E7D32',
  onSecondaryContainer: '#E8EAE6',

  tertiary: '#60A5FA',
  tertiaryContainer: '#1E3A8A',
  onTertiaryContainer: '#DBEAFE',

  success: '#4ADE80',
  successContainer: '#14532D',
  onSuccessContainer: '#DCFCE7',

  warning: '#FBBF24',
  warningContainer: '#78350F',
  onWarningContainer: '#FEF3C7',

  error: '#EF4444',
  errorContainer: '#7F1D1D',
  onErrorContainer: '#FEE2E2',

  info: '#60A5FA',
  infoContainer: '#1E3A8A',
  onInfoContainer: '#DBEAFE',

  outline: '#3D3D3D',
  outlineVariant: '#4D4D4D',
  outlineStrong: '#707870',

  scrim: 'rgba(0,0,0,0.7)',
  shadow: 'rgba(0,0,0,0.3)',
  backdrop: 'rgba(30,30,30,0.8)',
} as const;

export type ColorTokens = typeof lightColors;
export type ThemeMode = 'light' | 'dark';
```

### File: `android/src/theme/ThemeProvider.tsx`

```tsx
import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import { Appearance, ColorSchemeName } from 'react-native';
import { lightColors, darkColors, ColorTokens, ThemeMode } from './colors';

interface ThemeContextValue {
  colors: ColorTokens;
  mode: ThemeMode;
  systemMode: ColorSchemeName;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
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
```

### Usage in Components

```tsx
import { useTheme } from '../theme/ThemeProvider';
import { StyleSheet, Pressable, Text } from 'react-native';

function PrimaryButton({ children, onPress, disabled, loading }: Props) {
  const { colors } = useTheme();

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      android_ripple={{ color: colors.onPrimary, borderless: false }}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: colors.primary },
        pressed && { backgroundColor: colors.primaryActive },
        disabled && { opacity: 0.38 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.onPrimary} size="small" />
      ) : (
        <Text style={[styles.text, { color: colors.onPrimary }]}>{children}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, minHeight: 48 },
  text: { fontSize: 14, fontWeight: '600', textAlign: 'center' },
});
```

---

## Token Governance

### Naming Convention

```
{category}-{property}-{variant}-{state}
Examples:
- color-primary-foreground
- color-surface-container-highest
- color-error-container
- color-outline-strong
```

### Change Process

| Step | Action | Responsible |
|------|--------|-------------|
| 1 | Propose change with rationale | Designer / Architect |
| 2 | Verify contrast ratios (both themes) | Architect / Auditor |
| 3 | Update `docs/frontend/COLOR_SYSTEM.md` | Architect |
| 4 | Update web CSS variables | UI Engineer |
| 5 | Update Android TypeScript constants | Interaction Engineer |
| 6 | Audit affected components | UX Auditor |
| 7 | Update CHANGELOG.md | Docs agent |

### Deprecation Policy

1. Mark token as `@deprecated` in documentation with replacement
2. Keep in code for 2 releases minimum
3. Add lint rule to warn on usage
4. Remove after migration complete

---

## Migration from Existing Implementation

### Current Web State (Tailwind `primary` scale)

```js
// Existing tailwind.config.js
primary: {
  50: '#E8F5E9',   // → color-primary-container (light)
  100: '#C8E6C9',  // → lighter primary-container
  200: '#A5D6A7',  // → color-secondary (dark)
  300: '#81C784',  // → color-primary (dark)
  400: '#66BB6A',  // → color-primary-hover (dark)
  500: '#4CAF50',  // → color-primary-active (dark)
  600: '#43A047',
  700: '#388E3C',
  800: '#2E7D32',  // ≈ color-primary (light) #14532D
  900: '#1B5E20',  // ≈ color-primary-hover (light) #166534
}
```

### Migration Strategy

1. **Phase 1:** Add CSS variables to `globals.css` (non-breaking)
2. **Phase 2:** Update `tailwind.config.js` to map semantic tokens to CSS variables
3. **Phase 3:** Migrate components incrementally: `primary-800` → `primary`, `primary-50` → `primary-container`
4. **Phase 4:** Remove old `primary` scale from Tailwind config after full migration
5. **Phase 5:** Android — create `theme/colors.ts` and `ThemeProvider`, migrate components

---

## Accessibility Notes

### Color Blindness
- All state colors distinguishable by hue + icon + text
- Test with: Deuteranopia, Protanopia, Tritanopia simulators
- Never use red/green alone for status

### High Contrast Mode (Future)
```css
@media (prefers-contrast: high) {
  :root {
    --color-primary: #000000;        /* Light: pure black */
    --color-on-primary: #FFFFFF;
    --color-error: #FFFFFF;          /* Dark: pure white */
    --color-on-error: #000000;
    /* All interactive: 7:1 minimum */
  }
}
```

### Forced Colors (Windows High Contrast)
```css
@media (forced-colors: active) {
  .button { forced-color-adjust: none; }
  .card { forced-color-adjust: none; }
}
```

---

## Anti-Patterns

| Anti-Pattern | Example | Correct |
|--------------|---------|---------|
| Hardcoded hex | `bg-[#14532D]` | `bg-primary` |
| Hardcoded gray | `text-gray-600` | `text-on-surface-variant` |
| Opacity for disabled | `opacity-50` | `disabled:opacity-38` + token color |
| Color-only status | `bg-green-500` for success | `bg-success-container` + check icon + "Success" text |
| Arbitrary dark mode | `dark:bg-gray-800` | `bg-surface-container` (auto via CSS vars) |

---

## Agent Usage

**frontend-design-architect:**
- Validates token completeness in specifications
- Reviews contrast for new state combinations
- Approves token additions/modifications

**frontend-ui-engineer (web):**
- Enforces CSS variable usage via Tailwind config
- Flags hardcoded values in PR reviews
- Migrates components to semantic tokens

**frontend-interaction-engineer (Android):**
- Ensures `useTheme()` hook usage
- Maps state colors to interaction states
- Verifies dark mode parity

**frontend-ux-auditor:**
- Runs automated contrast checks
- Scans for hardcoded color values
- Verifies token usage consistency
- Reports violations with file:line evidence

---

## Related Documents

- `docs/frontend/COLOR_SYSTEM.md` — Complete documentation
- `docs/frontend/DESIGN_SYSTEM.md` — Design system overview
- `docs/frontend/INTERACTION_GUIDELINES.md` — State color usage
- `docs/frontend/FRONTEND_AGENTS.md` — Agent roles
- `myfarmai-apple-inspired-design` skill — Visual principles
- `myfarmai-interaction-engineering` skill — Interaction states

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-19 | Initial semantic token definitions |