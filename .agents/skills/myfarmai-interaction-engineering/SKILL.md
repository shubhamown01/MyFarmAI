---
name: myfarmai-interaction-engineering
description: Interaction states, motion specifications, accessibility requirements, keyboard behavior, reduced motion, touch targets, and feedback patterns for MyFarm AI across web and Android platforms.
metadata:
  author: myfarmai
  version: "1.0.0"
---

# MyFarm AI Interaction Engineering

## Purpose

This skill defines the complete interaction specification for MyFarm AI: motion/animation standards, component interaction states, accessibility requirements, keyboard navigation, touch targets, voice integration, and feedback patterns. It serves as the implementation reference for `frontend-interaction-engineer` and the audit checklist for `frontend-ux-auditor`.

**Source of truth:** `docs/frontend/INTERACTION_GUIDELINES.md` — this skill mirrors its content for agent consumption.

---

## Motion & Animation Specifications

### Timing Functions (Easing)

| Name | CSS | Reanimated (Android) | Use Case |
|------|-----|----------------------|----------|
| `ease-out-quick` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | `Easing.out(Easing.cubic)` | Button press, hover, micro-interactions |
| `ease-out-standard` | `cubic-bezier(0.0, 0.0, 0.2, 1)` | `Easing.out(Easing.quad)` | Card expand, panel slide, modal enter |
| `ease-in-out` | `cubic-bezier(0.4, 0.0, 0.2, 1)` | `Easing.inOut(Easing.quad)` | Page transitions, major state changes |
| `spring-gentle` | N/A | `withSpring(v, {damping: 20, stiffness: 150})` | Drawer, bottom sheet, pull-to-refresh |
| `spring-bouncy` | N/A | `withSpring(v, {damping: 15, stiffness: 200})` | Success celebrations, playful feedback |

### Duration Scale

| Token | Duration | Use Case |
|-------|----------|----------|
| `motion-instant` | 0ms | Immediate feedback (ripple start) |
| `motion-quick` | 100ms | Button press, checkbox, toggle |
| `motion-fast` | 150ms | Hover, focus, tooltip show |
| `motion-standard` | 200ms | Card expand, dropdown, tab switch |
| `motion-medium` | 250ms | Modal enter, bottom sheet, side panel |
| `motion-slow` | 300ms | Page transition, navigation |
| `motion-slower` | 400ms | Complex orchestrated transitions |

### Reduced Motion Implementation

**Web (CSS):**
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Utility class for conditional animation */
.animate-respectful {
  transition: var(--transition-duration, 200ms) var(--transition-easing, ease-out);
}

@media (prefers-reduced-motion: reduce) {
  .animate-respectful {
    transition-duration: 0.01ms;
  }
}
```

**Android (React Native):**
```tsx
import { AccessibilityInfo } from 'react-native';

export function useReducedMotion(): boolean {
  const [reduceMotion, setReduceMotion] = useState(false);
  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
    const listener = AccessibilityInfo.addEventListener(
      'reduceMotionChanged',
      setReduceMotion
    );
    return () => listener.remove();
  }, []);
  return reduceMotion;
}

// Usage in animated values
const duration = reduceMotion ? 0 : 200;
const easing = reduceMotion ? Easing.linear : Easing.out(Easing.quad);
```

---

## Universal Component State Matrix

Every interactive component must implement these states:

| State | Web Selector | Android Prop | Visual Change | Duration |
|-------|--------------|--------------|---------------|----------|
| **Default** | Base | Base | Base appearance | — |
| **Hover** | `hover:*` | N/A | Color shift, subtle scale | 150ms |
| **Focus** | `focus-visible:*` | `accessibilityFocus` | 3px ring, color shift | 100ms |
| **Active/Press** | `active:*` | `onPressIn` | Scale 0.98, color deepen | 100ms |
| **Loading** | `[data-loading]` | `activityIndicator` | Spinner, disabled opacity | — |
| **Disabled** | `disabled:*` | `disabled` | 38% opacity, no pointer | — |
| **Error** | `[data-error]` | `accessibilityState={{invalid: true}}` | Red outline, error text | — |
| **Success** | `[data-success]` | N/A | Green check, subtle pulse | 300ms |

---

## Button Interaction Specification

### Web Implementation

```tsx
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center font-medium transition-all duration-100',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        'disabled:opacity-38 disabled:pointer-events-none',
        'active:scale-[0.98]',
        // Variant styles
        variant === 'primary' && 'bg-primary text-on-primary hover:bg-primary-hover active:bg-primary-active',
        variant === 'secondary' && 'bg-secondary-container text-on-secondary-container hover:bg-secondary-hover',
        variant === 'ghost' && 'bg-transparent hover:bg-surface-container-high text-on-surface',
        variant === 'destructive' && 'bg-error-container text-on-error-container hover:bg-error',
        // Size styles
        size === 'sm' && 'px-3 py-1.5 text-sm rounded-sm min-h-[44px]',
        size === 'md' && 'px-4 py-2 text-base rounded-md min-h-[44px]',
        size === 'lg' && 'px-6 py-3 text-lg rounded-lg min-h-[48px]',
        className
      )}
      disabled={isDisabled}
      aria-busy={loading}
      aria-disabled={isDisabled}
      {...props}
    >
      {loading && <Spinner className="w-4 h-4 mr-2" />}
      {children}
    </button>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );
}
```

### Android Implementation

```tsx
import React, { useState } from 'react';
import { Pressable, Text, StyleSheet, ActivityIndicator, View } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  children: React.ReactNode;
  accessibilityLabel?: string;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  onPress,
  children,
  accessibilityLabel,
}: ButtonProps) {
  const { colors } = useTheme();
  const [pressed, setPressed] = useState(false);
  const isDisabled = disabled || loading;

  const variantColors = {
    primary: { bg: colors.primary, text: colors.onPrimary, hover: colors.primaryHover, active: colors.primaryActive },
    secondary: { bg: colors.secondaryContainer, text: colors.onSecondaryContainer, hover: colors.secondaryHover, active: colors.secondary },
    ghost: { bg: 'transparent', text: colors.onSurface, hover: colors.surfaceContainerHigh, active: colors.surfaceContainerHighest },
    destructive: { bg: colors.errorContainer, text: colors.onErrorContainer, hover: colors.error, active: colors.error },
  }[variant];

  const sizeStyles = {
    sm: { px: 12, py: 6, fontSize: 12, minHeight: 44, borderRadius: 4 },
    md: { px: 16, py: 10, fontSize: 14, minHeight: 48, borderRadius: 8 },
    lg: { px: 24, py: 14, fontSize: 16, minHeight: 56, borderRadius: 12 },
  }[size];

  return (
    <Pressable
      onPress={onPress}
      onPressIn={() => !isDisabled && setPressed(true)}
      onPressOut={() => setPressed(false)}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      android_ripple={{ color: variantColors.text, borderless: false }}
      style={({ pressed: pressablePressed }) => [
        styles.button,
        { backgroundColor: pressablePressed ? variantColors.active : variantColors.bg },
        { paddingHorizontal: sizeStyles.px, paddingVertical: sizeStyles.py, minHeight: sizeStyles.minHeight, borderRadius: sizeStyles.borderRadius },
        isDisabled && styles.buttonDisabled,
      ]}
    >
      <View style={styles.content} accessible={false}>
        {loading ? (
          <ActivityIndicator color={variantColors.text} size="small" style={styles.spinner} />
        ) : (
          <Text style={[styles.text, { color: variantColors.text, fontSize: sizeStyles.fontSize, fontWeight: '600' }]}>
            {children}
          </Text>
        )}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  buttonDisabled: {
    opacity: 0.38,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  text: {
    textAlign: 'center',
  },
  spinner: {
    marginRight: 8,
  },
});
```

---

## Input Field Interaction Specification

### Web Implementation

```tsx
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
}

export function Input({
  label,
  error,
  helperText,
  leadingIcon,
  trailingIcon,
  id,
  className,
  disabled,
  required,
  ...props
}: InputProps) {
  const inputId = id || `input-${useId()}`;
  const errorId = error ? `${inputId}-error` : undefined;
  const helperId = helperText && !error ? `${inputId}-helper` : undefined;

  return (
    <div className="relative w-full">
      <label
        htmlFor={inputId}
        className={cn(
          'block text-label-large text-on-surface mb-1.5',
          required && 'after:content-["*"] after:ml-0.5 after:text-error'
        )}
      >
        {label}
      </label>
      <div className="relative">
        {leadingIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-on-surface-variant">
            {leadingIcon}
          </div>
        )}
        <input
          id={inputId}
          className={cn(
            'w-full px-4 py-2.5 rounded-md border transition-colors duration-150',
            'bg-surface text-on-surface placeholder:text-on-surface-disabled',
            'border-outline',
            'hover:border-outline-strong',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary',
            'disabled:bg-surface-container-low disabled:text-on-surface-disabled disabled:cursor-not-allowed',
            leadingIcon && 'pl-10',
            trailingIcon && 'pr-10',
            error && 'border-error focus:ring-error focus:border-error',
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={cn(errorId, helperId)}
          aria-required={required}
          disabled={disabled}
          {...props}
        />
        {trailingIcon && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-on-surface-variant">
            {trailingIcon}
          </div>
        )}
      </div>
      {error && (
        <p id={errorId} className="mt-1.5 text-body-small text-error flex items-center gap-1" role="alert" aria-live="assertive">
          <ErrorCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={helperId} className="mt-1.5 text-body-small text-on-surface-variant" aria-live="polite">
          {helperText}
        </p>
      )}
    </div>
  );
}
```

### Android Implementation

```tsx
import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';

interface InputProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  placeholder?: string;
  accessibilityLabel?: string;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'numeric' | 'email-address';
}

export function Input({
  label,
  value,
  onChangeText,
  error,
  helperText,
  disabled = false,
  placeholder,
  accessibilityLabel,
  secureTextEntry = false,
  keyboardType = 'default',
}: InputProps) {
  const { colors } = useTheme();
  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: colors.onSurface }]}>{label}</Text>
      <TextInput
        style={[
          styles.input,
          {
            backgroundColor: colors.surface,
            color: colors.onSurface,
            borderColor: error ? colors.error : focused ? colors.primary : colors.outline,
            borderWidth: error || focused ? 2 : 1,
          },
          disabled && { backgroundColor: colors.surfaceContainerLow, color: colors.onSurfaceDisabled },
        ]}
        placeholder={placeholder}
        placeholderTextColor={colors.onSurfaceDisabled}
        value={value}
        onChangeText={onChangeText}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        editable={!disabled}
        secureTextEntry={secureTextEntry}
        keyboardType={keyboardType}
        accessibilityLabel={accessibilityLabel || label}
        accessibilityHint={helperText}
        accessibilityState={{ invalid: !!error }}
        accessibilityLiveRegion={error ? 'assertive' : 'polite'}
      />
      {(error || helperText) && (
        <Text
          style={[
            styles.helper,
            { color: error ? colors.error : colors.onSurfaceVariant },
          ]}
          accessibilityLiveRegion={error ? 'assertive' : 'polite'}
        >
          {error ? '⚠ ' : ''} {error || helperText}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 6 },
  label: { fontSize: 14, fontWeight: '500' },
  input: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    fontSize: 16,
    minHeight: 48,
  },
  helper: { fontSize: 12, marginTop: 4 },
});
```

---

## Card Interaction Specification

### States

| Interaction | Web | Android |
|-------------|-----|---------|
| **Hover** | `hover:shadow-md hover:-translate-y-0.5` | N/A |
| **Press** | `active:scale-[0.99] active:shadow-sm` | `Pressable` with `android:foreground` ripple |
| **Focus** | `focus-visible:ring-2 focus-visible:ring-primary` | `accessibilityFocus` + outline |
| **Loading** | Skeleton overlay | `Skeleton` component |

### Web Card Component

```tsx
interface CardProps {
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  interactive?: boolean;
  onPress?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function Card({ variant = 'default', interactive = false, onPress, children, className }: CardProps) {
  const variantClasses = {
    default: 'bg-surface-container shadow-sm',
    elevated: 'bg-surface-container-high shadow-md',
    outlined: 'bg-surface border border-outline shadow-none',
    filled: 'bg-surface-container-highest shadow-none',
  }[variant];

  const interactiveClasses = interactive
    ? 'transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 active:scale-[0.99] active:shadow-sm cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2'
    : '';

  const Component = interactive && onPress ? 'button' : 'div';

  return (
    <Component
      className={cn(
        'rounded-xl',
        variantClasses,
        interactiveClasses,
        className
      )}
      onClick={onPress}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
    >
      {children}
    </Component>
  );
}
```

### Android Card Component

```tsx
import { Pressable, View, StyleSheet } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';

interface CardProps {
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  interactive?: boolean;
  onPress?: () => void;
  children: React.ReactNode;
  style?: ViewStyle;
}

export function Card({ variant = 'default', interactive = false, onPress, children, style }: CardProps) {
  const { colors } = useTheme();

  const variantStyles = {
    default: { backgroundColor: colors.surfaceContainer, ...styles.elevation1 },
    elevated: { backgroundColor: colors.surfaceContainerHigh, ...styles.elevation2 },
    outlined: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.outline, ...styles.elevation0 },
    filled: { backgroundColor: colors.surfaceContainerHighest, ...styles.elevation0 },
  }[variant];

  const Content = interactive ? Pressable : View;

  return (
    <Content
      onPress={onPress}
      style={[
        styles.card,
        variantStyles,
        interactive && styles.interactive,
        style,
      ]}
      accessibilityRole={interactive ? 'button' : undefined}
      android_ripple={interactive ? { color: colors.onSurface, borderless: true } : undefined}
    >
      {children}
    </Content>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 12, overflow: 'hidden' },
  interactive: { /* ripple handled by Pressable */ },
  elevation0: { elevation: 0, shadowOpacity: 0 },
  elevation1: { elevation: 1, shadowColor: colors.shadow, shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 2 },
  elevation2: { elevation: 3, shadowColor: colors.shadow, shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.15, shadowRadius: 4 },
});
```

---

## Feedback Patterns

### Toast / Snackbar

**Web:**
```tsx
interface ToastProps {
  variant: 'success' | 'error' | 'warning' | 'info';
  message: string;
  action?: { label: string; onClick: () => void };
  onDismiss: () => void;
}

export function Toast({ variant, message, action, onDismiss }: ToastProps) {
  const variantStyles = {
    success: 'bg-success-container text-on-success-container',
    error: 'bg-error-container text-on-error-container',
    warning: 'bg-warning-container text-on-warning-container',
    info: 'bg-info-container text-on-info-container',
  }[variant];

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  }[variant];

  return (
    <div
      className={cn(
        'fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl',
        'animate-slide-in-from-right',
        variantStyles
      )}
      role="alert"
      aria-live="polite"
    >
      {icons}
      <p className="text-body-medium">{message}</p>
      {action && (
        <Button variant="ghost" size="sm" onClick={action.onClick} className="ml-2">
          {action.label}
        </Button>
      )}
      <Button variant="ghost" size="icon" onClick={onDismiss} aria-label="Dismiss">
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
}
```

**Android:**
```tsx
import { Snackbar } from 'react-native-paper';

interface SnackbarProps {
  visible: boolean;
  variant: 'success' | 'error' | 'warning' | 'info';
  message: string;
  action?: { label: string; onPress: () => void };
  onDismiss: () => void;
  duration?: number;
}

export function AppSnackbar({ visible, variant, message, action, onDismiss, duration = 4000 }: SnackbarProps) {
  const { colors } = useTheme();

  const variantColors = {
    success: { bg: colors.successContainer, text: colors.onSuccessContainer },
    error: { bg: colors.errorContainer, text: colors.onErrorContainer },
    warning: { bg: colors.warningContainer, text: colors.onWarningContainer },
    info: { bg: colors.infoContainer, text: colors.onInfoContainer },
  }[variant];

  return (
    <Snackbar
      visible={visible}
      onDismiss={onDismiss}
      action={action ? { label: action.label, onPress: action.onPress } : undefined}
      duration={duration}
      style={[{ backgroundColor: variantColors.bg }, styles.snackbar]}
      contentStyle={{ color: variantColors.text }}
    >
      <Text>{message}</Text>
    </Snackbar>
  );
}
```

### Loading States

| Pattern | Web | Android | Use Case |
|---------|-----|---------|----------|
| **Inline Spinner** | `<Spinner className="w-5 h-5 animate-spin" />` | `<ActivityIndicator size="small" />` | Button, inline actions |
| **Overlay Spinner** | Fixed center, `backdrop` | `Modal` + `ActivityIndicator` | Full-page operations |
| **Skeleton** | `animate-pulse bg-surface-container-high` | `Skeleton` from library | Known structure (lists, cards) |
| **Progress Bar** | `<progress value={pct} max="100" className="w-full h-2" />` | `<ProgressBar progress={pct} />` | Determinate (upload, sync) |
| **Pull to Refresh** | N/A | `RefreshControl` on `FlatList` | List refresh |

### Empty States

```tsx
// Web
<div className="flex flex-col items-center justify-center p-8 text-center">
  <div className="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center mb-4">
    <Icon className="w-8 h-8 text-on-surface-variant" />
  </div>
  <h3 className="text-headline-small text-on-surface mb-1">{title}</h3>
  <p className="text-body-medium text-on-surface-variant max-w-sm mb-6">{description}</p>
  {action && <Button variant="primary" size="md" onClick={action.onClick}>{action.label}</Button>}
</div>

// Android
<View style={styles.emptyContainer}>
  <View style={[styles.emptyIcon, { backgroundColor: colors.surfaceContainerHigh }]}>
    <Icon color={colors.onSurfaceVariant} size={32} />
  </View>
  <Text style={[styles.emptyTitle, { color: colors.onSurface }]}>{title}</Text>
  <Text style={[styles.emptyDescription, { color: colors.onSurfaceVariant }]}>{description}</Text>
  {action && <Button mode="contained" onPress={action.onPress} style={{ marginTop: 16 }}>{action.label}</Button>}
</View>
```

### Offline / Connectivity Indicators

```tsx
// Web: Persistent banner
{isOffline && (
  <div className="fixed top-0 left-0 right-0 z-40 bg-warning-container border-b border-warning px-4 py-2 animate-slide-down">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center gap-2 text-on-warning-container">
        <WifiOff className="w-5 h-5" />
        <span className="text-body-medium">You're offline. Changes will sync when reconnected.</span>
      </div>
      <span className="text-body-small text-on-warning-container/80">{pendingCount} pending</span>
    </div>
  </div>
)}

// Android: Top banner
<Animated.View style={[styles.offlineBanner, { opacity: isOffline ? 1 : 0 }]}>
  <View style={styles.offlineContent}>
    <WifiOff color={colors.onWarningContainer} size={20} />
    <Text style={{ color: colors.onWarningContainer }}>You're offline. Changes will sync when reconnected.</Text>
  </View>
  <Text style={{ color: colors.onWarningContainer }}>{pendingCount} pending</Text>
</Animated.View>
```

---

## Voice Interaction Patterns

### Speech Recognition (Input)

| Platform | API | Languages | Continuous | Interim |
|----------|-----|-----------|------------|---------|
| Web | `SpeechRecognition` | `hi-IN`, `en-IN` | ✅ | ✅ |
| Android | `expo-speech-recognition` | `hi-IN`, `en-IN` | ✅ | ✅ |

**UI States:**
1. **Idle** — Mic icon, tap to start
2. **Listening** — Pulsing mic, "Listening...", live transcript
3. **Processing** — Spinner, "Processing..."
4. **Result** — Transcript shown, confirm/edit/send
5. **Error** — Error message, retry button

```tsx
// Web: Voice button with states
<Button
  variant={isListening ? 'destructive' : 'ghost'}
  size="icon"
  onClick={isListening ? stopListening : startListening}
  aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
  aria-pressed={isListening}
>
  {isListening ? <Mic className="w-5 h-5 animate-pulse text-error" /> : <Mic className="w-5 h-5 text-on-surface-variant" />}
</Button>

// Live transcript overlay
{isListening && transcript && (
  <div className="fixed bottom-24 left-4 right-4 md:left-auto md:w-96 z-50 bg-surface-container-high border border-outline rounded-lg p-4 shadow-xl animate-slide-up">
    <p className="text-body-medium text-on-surface">{transcript}</p>
    <div className="flex gap-2 mt-3">
      <Button variant="primary" size="sm" onClick={confirmTranscript}>Send</Button>
      <Button variant="ghost" size="sm" onClick={clearTranscript}>Cancel</Button>
    </div>
  </div>
)}
```

### Speech Synthesis (Output)

| Platform | API | Voices | Rate/Pitch |
|----------|-----|--------|------------|
| Web | `SpeechSynthesis` | System | ✅ |
| Android | `expo-speech` | System TTS | ✅ |

**Controls:** Play, Pause, Stop, Rate (0.5x–2x), Voice selection

```tsx
// TTS controls on AI messages
{message.role === 'assistant' && (
  <Button
    variant="ghost"
    size="icon"
    onClick={() => isSpeaking ? stopSpeaking() : speak(message.content)}
    disabled={isSpeaking && !canPause}
    aria-label={isSpeaking ? 'Stop reading' : 'Read aloud'}
    aria-pressed={isSpeaking}
  >
    {isSpeaking ? <Pause className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
  </Button>
)}
```

---

## Keyboard Navigation (Web)

### Focus Order Rules
1. Logical tab order following visual layout (left→right, top→bottom)
2. Skip link as first focusable element: `<a href="#main" className="sr-only focus:not-sr-only">Skip to main content</a>`
3. Focus trapping in modals/drawers (Tab cycles within, Esc closes)
4. Restore focus to trigger element on modal/drawer close

### Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Focus chat input | `/` or `Ctrl+K` | Global |
| Send message | `Enter` | Chat input |
| New line | `Shift+Enter` | Chat input |
| Voice input | `Ctrl+Space` | Global |
| Toggle theme | `Ctrl+Shift+L` | Global |
| Shortcuts help | `?` | Global |

### Focus Indicators (CSS)

```css
/* Global focus-visible */
:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--color-primary);
  border-radius: inherit;
}

/* Button focus */
.button:focus-visible {
  box-shadow: 0 0 0 3px var(--color-primary-container);
}

/* Input focus */
.input:focus-visible {
  box-shadow: 0 0 0 2px var(--color-primary);
}

/* Card focus (interactive) */
.card-interactive:focus-visible {
  box-shadow: 0 0 0 3px var(--color-primary), 0 4px 6px -1px var(--color-shadow);
}
```

---

## Screen Reader Support

### Web (Semantic HTML + ARIA)

```tsx
// Chat messages with proper semantics
<article aria-label={`Message from ${message.role}`}>
  <header className="sr-only">{message.role === 'user' ? 'You' : 'Assistant'}</header>
  <p>{message.content}</p>
  <time dateTime={message.timestamp.toISOString()} className="sr-only">
    {message.timestamp.toLocaleTimeString()}
  </time>
</article>

// Live region for announcements
<div aria-live="polite" aria-atomic="true" className="sr-only" id="announcer">
  {announcement}
</div>

// Form error association
<input aria-invalid="true" aria-describedby="email-error" />
<p id="email-error" role="alert">Invalid email address</p>

// Button with loading state
<button aria-busy={loading} aria-disabled={disabled} disabled={disabled}>
  {loading ? <Spinner /> : 'Submit'}
</button>
```

### Android (AccessibilityProps)

```tsx
// Chat message
<View
  accessibilityRole="article"
  accessibilityLabel={`Message from ${message.role === 'user' ? 'you' : 'assistant'}`}
  accessibilityLiveRegion="polite"
>
  <Text>{message.content}</Text>
</View>

// Button
<Pressable
  accessibilityRole="button"
  accessibilityLabel={label}
  accessibilityState={{ disabled, busy: loading, selected }}
  accessibilityHint={hint}
>
  <Text>{label}</Text>
</Pressable>

// Input
<TextInput
  accessibilityLabel={label}
  accessibilityHint={helperText}
  accessibilityState={{ invalid: !!error }}
  accessibilityLiveRegion={error ? 'assertive' : 'polite'}
/>
```

---

## Touch & Pointer Interactions

### Touch Targets (Minimum)

| Platform | Minimum | Recommended | Implementation |
|----------|---------|-------------|----------------|
| Web | 44×44px | 48×48px | `min-h-[44px] min-w-[44px]` + padding |
| Android | 48×48dp | 56×56dp | `minHeight: 48, minWidth: 48` + padding |

**Never** make interactive elements smaller. Use padding to expand hit area visually.

### Gesture Patterns

| Gesture | Web | Android | Use Case |
|---------|-----|---------|----------|
| Tap | `onClick` | `Pressable onPress` | Primary action |
| Long Press | `onContextMenu` / hold | `Pressable onLongPress` | Context menus, delete |
| Swipe | Pointer events | `PanGestureHandler` | Dismiss, archive, actions |
| Pull to Refresh | N/A | `RefreshControl` | List refresh |
| Pinch Zoom | Touch events | `PinchGestureHandler` | Images, maps |

---

## Performance Constraints

| Interaction | Max Latency | Strategy |
|-------------|-------------|----------|
| Button press feedback | < 16ms | Optimistic UI, ripple immediate |
| Focus ring | < 50ms | CSS-only, no layout thrash |
| Modal open | < 100ms | Pre-render, animate opacity/transform |
| List scroll | 60fps | Virtualization, `content-visibility` |
| Voice start | < 200ms | Pre-warm recognition, immediate feedback |
| TTS start | < 500ms | Queue utterance, show playing state |

---

## Testing Checklist

### Automated (CI)
- [ ] `axe-core` / `eslint-plugin-jsx-a11y` (web)
- [ ] `react-native-accessibility` (Android)
- [ ] Reduced motion respected (both)
- [ ] Color contrast ratios (CI script)
- [ ] Focus order (Playwright web / Detox Android)

### Manual
- [ ] Keyboard-only navigation (web)
- [ ] Switch Control / VoiceOver (iOS)
- [ ] TalkBack / Switch Access (Android)
- [ ] High contrast mode (OS level)
- [ ] 200% browser zoom
- [ ] System font size max
- [ ] Outdoor sunlight simulation
- [ ] Glove interaction (physical test)

---

## Agent Usage

**frontend-interaction-engineer:**
- Implements all interaction states per specification
- Builds motion using approved durations/easings
- Ensures keyboard accessibility (web) and TalkBack (Android)
- Integrates voice input/output
- Implements feedback patterns (toast, loading, empty, offline)

**frontend-ui-engineer (web):**
- Implements button/input/card states per this spec
- Uses CSS transitions, not JS animation libraries where possible
- Respects `prefers-reduced-motion`

**frontend-ux-auditor:**
- Verifies all 7 states implemented per component
- Checks focus visibility and keyboard flow
- Runs automated accessibility scans
- Tests reduced motion compliance
- Validates touch target sizes
- Confirms voice interaction flows work

---

## Anti-Patterns

| Anti-Pattern | Why | Correct |
|--------------|-----|---------|
| Missing focus state | Inaccessible keyboard nav | Always `focus-visible` ring |
| Color-only loading | Screen readers miss it | `aria-busy` + spinner + text |
| No reduced motion | Vestibular disorders | `@media (prefers-reduced-motion)` |
| Inline styles for animation | New function every render | CSS transitions / hoisted Reanimated |
| Layout animation (width/height) | Jank, not GPU | Transform + opacity only |
| `&&` for conditional rendering | Falsy 0 renders nothing | Ternary `{condition ? <Component /> : null}` |
| No error announcement | Screen reader misses errors | `role="alert"` + `aria-live="assertive"` |

---

## Related Documents

- `docs/frontend/INTERACTION_GUIDELINES.md` — Complete specifications
- `docs/frontend/DESIGN_SYSTEM.md` — Design system overview
- `docs/frontend/COLOR_SYSTEM.md` — State color tokens
- `docs/frontend/FRONTEND_AGENTS.md` — Agent roles
- `vercel-react-best-practices` skill — Re-render optimization rules
- `vercel-react-native-skills` skill — List performance, animations
- `vercel-composition-patterns` skill — State lifting patterns
- `web-design-guidelines` skill — Accessibility compliance

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-19 | Initial interaction specifications |