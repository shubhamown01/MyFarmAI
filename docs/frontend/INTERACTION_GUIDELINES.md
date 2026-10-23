# MyFarm AI Interaction Guidelines

**Version:** 1.0.0  
**Status:** Foundation Phase — Interaction Specifications Defined  
**Last Updated:** 2026-10-19

---

## Overview

This document defines the interaction patterns, motion specifications, accessibility requirements, and feedback mechanisms for MyFarm AI across web and Android platforms.

**Core Principle:** Interactions are purposeful, accessible, and respectful of user context (outdoor, gloves, low connectivity, assistive technologies).

---

## Motion & Animation Specifications

### Timing Functions

| Name | CSS | Reanimated | Use Case |
|------|-----|------------|----------|
| `ease-out-quick` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | `Easing.out(Easing.cubic)` | Button press, hover, micro-interactions |
| `ease-out-standard` | `cubic-bezier(0.0, 0.0, 0.2, 1)` | `Easing.out(Easing.quad)` | Card expand, panel slide, modal enter |
| `ease-in-out` | `cubic-bezier(0.4, 0.0, 0.2, 1)` | `Easing.inOut(Easing.quad)` | Page transitions, major state changes |
| `spring-gentle` | N/A (JS) | `withSpring(value, {damping: 20, stiffness: 150})` | Drawer, bottom sheet, pull-to-refresh |
| `spring-bouncy` | N/A (JS) | `withSpring(value, {damping: 15, stiffness: 200})` | Success celebrations, playful feedback |

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

### Reduced Motion

**Web:**
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
```

**Android:**
```tsx
import { AccessibilityInfo } from 'react-native';

function useReducedMotion() {
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

// Usage
const duration = reduceMotion ? 0 : 200;
```

---

## Component Interaction States

### Universal State Matrix

| State | Web CSS | Android | Visual Change | Duration |
|-------|---------|---------|---------------|----------|
| **Default** | Base | Base | Base appearance | — |
| **Hover** | `hover:*` | N/A | Color shift, subtle scale | 150ms |
| **Focus** | `focus-visible:*` | `accessibilityFocus` | Ring (3px), color shift | 100ms |
| **Active/Press** | `active:*` | `Pressable onPressIn` | Scale 0.98, color deepen | 100ms |
| **Loading** | `data-loading` | `activityIndicator` | Spinner, disabled opacity | — |
| **Disabled** | `disabled:*` | `disabled` | 38% opacity, no pointer | — |
| **Error** | `data-error` | `accessibilityState={{invalid: true}}` | Red outline, error text | — |
| **Success** | `data-success` | N/A | Green check, subtle pulse | 300ms |

### Button Interactions

```tsx
// Web: Semantic button variants with consistent states
<button className={cn(
  "inline-flex items-center justify-center font-medium transition-all duration-100",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
  "disabled:opacity-38 disabled:pointer-events-none",
  "active:scale-[0.98]",
  variants.primary && "bg-primary text-on-primary hover:bg-primary-hover active:bg-primary-active",
  variants.secondary && "bg-secondary-container text-on-secondary-container hover:bg-secondary-hover",
  variants.ghost && "bg-transparent hover:bg-surface-container-high",
  variants.destructive && "bg-error-container text-on-error-container hover:bg-error",
  size.sm && "px-3 py-1.5 text-sm rounded-sm",
  size.md && "px-4 py-2 text-base rounded-md",
  size.lg && "px-6 py-3 text-lg rounded-lg",
)} />

// Android: Pressable with consistent states
<Pressable
  onPress={onPress}
  onPressIn={() => setPressed(true)}
  onPressOut={() => setPressed(false)}
  onLongPress={onLongPress}
  disabled={disabled}
  accessibilityState={{ disabled, busy: loading }}
  android_ripple={{
    color: colors.onSurface,
    borderless: false,
  }}
  style={({ pressed }) => [
    styles.button,
    pressed && styles.buttonPressed,
    disabled && styles.buttonDisabled,
    loading && styles.buttonLoading,
    variantStyles[variant],
  ]}
>
  {loading ? <ActivityIndicator color={colors.onPrimary} size="small" /> : <Text>{children}</Text>}
</Pressable>
```

### Input Field Interactions

```tsx
// Web: Input with full state coverage
<div className="relative">
  <label className="block text-label-large text-on-surface mb-1.5" htmlFor={id}>
    {label}
  </label>
  <input
    id={id}
    type={type}
    className={cn(
      "w-full px-4 py-2.5 rounded-md border transition-colors duration-150",
      "bg-surface text-on-surface placeholder:text-on-surface-disabled",
      "border-outline",
      "hover:border-outline-strong",
      "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
      "disabled:bg-surface-container-low disabled:text-on-surface-disabled disabled:cursor-not-allowed",
      "data-[error]:border-error data-[error]:focus:ring-error",
      error && "border-error focus:ring-error",
    )}
    aria-invalid={error ? 'true' : 'false'}
    aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
    disabled={disabled}
  />
  {error && (
    <p id={`${id}-error`} className="mt-1.5 text-body-small text-error flex items-center gap-1" role="alert">
      <ErrorIcon className="w-4 h-4" /> {error}
    </p>
  )}
  {helperText && !error && (
    <p id={`${id}-helper`} className="mt-1.5 text-body-small text-on-surface-variant">
      {helperText}
    </p>
  )}
</div>

// Android: TextInput with states
<View style={styles.container}>
  <Text style={[styles.label, { color: colors.onSurface }]}>{label}</Text>
  <TextInput
    style={[
      styles.input,
      { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
      focused && { borderColor: colors.primary, borderWidth: 2 },
      error && { borderColor: colors.error, borderWidth: 2 },
      disabled && { backgroundColor: colors.surfaceContainerLow, color: colors.onSurfaceDisabled },
    ]}
    placeholderTextColor={colors.onSurfaceDisabled}
    editable={!disabled}
    onFocus={() => setFocused(true)}
    onBlur={() => setFocused(false)}
    onChangeText={onChangeText}
    value={value}
    accessibilityState={{ invalid: !!error }}
    accessibilityLabel={label}
  />
  {(error || helperText) && (
    <Text
      style={[
        styles.helper,
        { color: error ? colors.error : colors.onSurfaceVariant },
      ]}
      accessibilityLiveRegion="polite"
    >
      {error ? <ErrorIcon /> : null} {error || helperText}
    </Text>
  )}
</View>
```

### Card Interactions

| Interaction | Web | Android |
|-------------|-----|---------|
| **Hover** | `hover:shadow-md hover:-translate-y-0.5` | N/A |
| **Press** | `active:scale-[0.99] active:shadow-sm` | `Pressable` with `android:foreground` ripple |
| **Focus** | `focus-visible:ring-2 focus-visible:ring-primary` | `accessibilityFocus` + outline |
| **Loading** | Skeleton overlay | `Skeleton` component (FlashList) |

---

## Feedback Patterns

### Toast / Snackbar

```tsx
// Web: Toast with semantic colors
<div className={cn(
  "fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl",
  "animate-slide-in-from-right",
  variant === 'success' && "bg-success-container text-on-success-container",
  variant === 'error' && "bg-error-container text-on-error-container",
  variant === 'warning' && "bg-warning-container text-on-warning-container",
  variant === 'info' && "bg-info-container text-on-info-container",
)}>
  <Icon className="w-5 h-5 flex-shrink-0" />
  <p className="text-body-medium">{message}</p>
  <button onClick={dismiss} className="ml-2 p-1 rounded hover:bg-black/10">
    <X className="w-4 h-4" />
  </button>
</div>

// Android: Snackbar via react-native-paper
import { Snackbar } from 'react-native-paper';

<Snackbar
  visible={visible}
  onDismiss={onDismiss}
  action={{ label: 'Dismiss', onPress: onDismiss }}
  duration={duration}
  style={[
    styles.snackbar,
    variant === 'success' && { backgroundColor: colors.successContainer },
    variant === 'error' && { backgroundColor: colors.errorContainer },
    variant === 'warning' && { backgroundColor: colors.warningContainer },
    variant === 'info' && { backgroundColor: colors.infoContainer },
  ]}
  contentStyle={{ color: variantColors[variant].onContainer }}
>
  <Text>{message}</Text>
</Snackbar>
```

### Loading States

| Pattern | Web | Android | Use Case |
|---------|-----|---------|----------|
| **Inline Spinner** | `<Spinner className="w-5 h-5 animate-spin" />` | `<ActivityIndicator size="small" />` | Button, inline actions |
| **Overlay Spinner** | Fixed center, backdrop | `Modal` + `ActivityIndicator` | Full-page operations |
| **Skeleton** | `animate-pulse bg-surface-container-high` | `Skeleton` from `react-native-skeleton-placeholder` | Known structure (lists, cards) |
| **Progress Bar** | `<progress value={pct} max="100" />` | `<ProgressBar progress={pct} />` | Determinate (upload, sync) |
| **Pull to Refresh** | N/A (web) | `RefreshControl` on `ScrollView`/`FlatList` | List refresh |

### Empty States

```tsx
// Web: Consistent empty state pattern
<div className="flex flex-col items-center justify-center p-8 text-center">
  <div className="w-16 h-16 rounded-full bg-surface-container-high flex items-center justify-center mb-4">
    <Icon className="w-8 h-8 text-on-surface-variant" />
  </div>
  <h3 className="text-headline-small text-on-surface mb-1">{title}</h3>
  <p className="text-body-medium text-on-surface-variant max-w-sm mb-6">{description}</p>
  {action && (
    <Button variant="primary" size="md" onClick={action.onClick}>
      {action.label}
    </Button>
  )}
</div>

// Android: Same pattern with Paper components
<View style={styles.emptyContainer}>
  <View style={[styles.emptyIcon, { backgroundColor: colors.surfaceContainerHigh }]}>
    <Icon color={colors.onSurfaceVariant} size={32} />
  </View>
  <Text style={[styles.emptyTitle, { color: colors.onSurface }]}>{title}</Text>
  <Text style={[styles.emptyDescription, { color: colors.onSurfaceVariant }]}>{description}</Text>
  {action && (
    <Button mode="contained" onPress={action.onPress} style={{ marginTop: 16 }}>
      {action.label}
    </Button>
  )}
</View>
```

### Offline / Connectivity Indicators

```tsx
// Web: Persistent offline banner
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

// Android: Top snackbar or persistent banner
<View style={isOffline ? styles.offlineBanner : styles.offlineBannerHidden}>
  <View style={styles.offlineContent}>
    <WifiOff color={colors.onWarningContainer} size={20} />
    <Text style={{ color: colors.onWarningContainer }}>You're offline. Changes will sync when reconnected.</Text>
  </View>
  <Text style={{ color: colors.onWarningContainer }}>{pendingCount} pending</Text>
</View>
```

---

## Voice Interaction Patterns

### Speech Recognition (Input)

| Platform | API | Language | Continuous | Interim Results |
|----------|-----|----------|------------|-----------------|
| Web | `SpeechRecognition` | `hi-IN`, `en-IN` | ✅ | ✅ |
| Android | `expo-speech-recognition` | `hi-IN`, `en-IN` | ✅ | ✅ |

**UI States:**
1. **Idle** — Mic icon, tap to start
2. **Listening** — Pulsing mic, "Listening..." text, live transcript
3. **Processing** — Spinner, "Processing..."
4. **Result** — Transcript shown, confirm/edit/send
5. **Error** — Error message, retry button

```tsx
// Web: Voice button states
<Button
  variant={isListening ? 'destructive' : 'ghost'}
  size="icon"
  onClick={isListening ? stopListening : startListening}
  aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
  aria-pressed={isListening}
>
  {isListening ? (
    <Mic className="w-5 h-5 animate-pulse text-error" />
  ) : (
    <Mic className="w-5 h-5 text-on-surface-variant" />
  )}
</Button>

// Live transcript display
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

| Platform | API | Voices | Rate/Pitch Control |
|----------|-----|--------|-------------------|
| Web | `SpeechSynthesis` | System voices | ✅ |
| Android | `expo-speech` | System TTS engines | ✅ |

**Controls:** Play, Pause, Stop, Rate (0.5x - 2x), Voice selection

```tsx
// Web: TTS controls on AI messages
{message.role === 'assistant' && (
  <div className="flex items-center gap-1 ml-auto">
    <Button
      variant="ghost"
      size="icon"
      onClick={() => speak(message.content)}
      disabled={isSpeaking}
      aria-label={isSpeaking ? 'Stop reading' : 'Read aloud'}
    >
      {isSpeaking ? <Pause className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
    </Button>
  </div>
)}
```

---

## Navigation & Routing Interactions

### Web (Next.js App Router)

- **Client-side transitions:** Next.js `Link` with `prefetch` (default)
- **Loading UI:** `loading.tsx` per route segment
- **Error UI:** `error.tsx` per route segment
- **Back navigation:** Browser back button, preserved scroll position

### Android (Expo Router + React Navigation)

- **Stack navigation:** Native stack animator (iOS/Android defaults)
- **Tab navigation:** Native bottom tabs
- **Gestures:** Swipe back (iOS), back button (Android)
- **Deep linking:** Expo Router automatic

**Transition Customization:**
```tsx
// Stack screen options
<Stack.Screen
  name="Chat"
  component={ChatScreen}
  options={{
    headerStyle: { backgroundColor: colors.primary },
    headerTintColor: colors.onPrimary,
    headerTitleStyle: { fontWeight: '600' },
    // Custom transitions via Reanimated
    transition: 'modal' | 'push' | 'fade',
  }}
/>
```

---

## Touch & Pointer Interactions

### Touch Targets

| Platform | Minimum | Recommended | Implementation |
|----------|---------|-------------|----------------|
| Web | 44×44px | 48×48px | `min-h-[44px] min-w-[44px]` + padding |
| Android | 48×48dp | 56×56dp | `minHeight: 48, minWidth: 48` + padding |

**Never** make interactive elements smaller than minimums. Use padding to expand hit area visually.

### Gesture Patterns

| Gesture | Web | Android | Use Case |
|---------|-----|---------|----------|
| Tap | `onClick` | `Pressable onPress` | Primary action |
| Long Press | `onContextMenu` / hold | `Pressable onLongPress` | Context menus, delete |
| Swipe | Pointer events | `PanGestureHandler` | Dismiss, archive, actions |
| Pull to Refresh | N/A | `RefreshControl` | List refresh |
| Pinch Zoom | Touch events | `PinchGestureHandler` | Images, maps |

### Drag & Drop

**Web:** `@dnd-kit` or native HTML5 Drag and Drop
**Android:** `react-native-gesture-handler` + `react-native-reanimated`

---

## Keyboard Navigation (Web)

### Focus Order
1. Logical tab order following visual layout
2. Skip links for main content
3. Focus trapping in modals/drawers
4. Restore focus on close

### Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Focus chat input | `/` or `Ctrl+K` | Global |
| Send message | `Enter` | Chat input |
| New line | `Shift+Enter` | Chat input |
| Voice input | `Ctrl+Space` | Global |
| Toggle theme | `Ctrl+Shift+L` | Global |
| Open shortcuts help | `?` | Global |

### Focus Indicators

```css
/* Global focus-visible style */
:focus-visible {
  outline: none;
  ring: 2px solid var(--color-primary);
  ring-offset: 2px;
  ring-offset-color: var(--color-surface);
}

/* Custom focus for specific elements */
.button:focus-visible {
  box-shadow: 0 0 0 3px var(--color-primary-container);
}

.input:focus-visible {
  box-shadow: 0 0 0 2px var(--color-primary);
}
```

---

## Screen Reader Support

### Semantic HTML (Web)

```tsx
// Chat messages
<article aria-label={`Message from ${message.role}`}>
  <header className="sr-only">{message.role === 'user' ? 'You' : 'Assistant'}</header>
  <p>{message.content}</p>
  <time dateTime={message.timestamp.toISOString()} className="sr-only">
    {message.timestamp.toLocaleTimeString()}
  </time>
</article>

// Live regions for dynamic content
<div aria-live="polite" aria-atomic="true" className="sr-only">
  {announcement}
</div>

// Form errors
<input aria-invalid="true" aria-describedby="email-error" />
<p id="email-error" role="alert">Invalid email address</p>
```

### Accessibility Props (Android)

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

## Agricultural Context Interactions

### Crop/Field Selection

- **Chip groups** for crop types (single/multi select)
- **Map-based selection** for fields (future)
- **Voice:** "Select wheat crop" → highlights wheat chip

### Weather Data

- **Pull-to-refresh** for latest forecast
- **Swipe** between current/forecast/detail views
- **Voice:** "Read weather" → TTS reads current conditions

### Disease Detection (Future)

- **Camera capture** with overlay guide
- **Gallery selection** with crop filter
- **Progress** during analysis with cancel
- **Results** with confidence, treatment options, local resources

### Advisory Cards

- **Expand/collapse** for details
- **Dismiss** with "Don't show again" option
- **Share** via system share sheet
- **Voice:** Read advisory aloud

---

## Performance Constraints

| Interaction | Max Latency | Strategy |
|-------------|-------------|----------|
| Button press feedback | < 16ms | Optimistic UI, ripple immediate |
| Focus ring | < 50ms | CSS-only, no layout thrash |
| Modal open | < 100ms | Pre-render, animate opacity/transform |
| List scroll | 60fps | Virtualization, `content-visibility` |
| Voice start | < 200ms | Pre-warm recognition, show immediate feedback |
| TTS start | < 500ms | Queue utterance, show playing state |

---

## Testing Checklist

### Automated (CI)
- [ ] `axe-core` / `eslint-plugin-jsx-a11y` (web)
- [ ] `react-native-accessibility` (Android)
- [ ] Reduced motion respected
- [ ] Color contrast ratios (CI script)
- [ ] Focus order (Playwright / Detox)

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

## Related Documents

- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md) — Overall design system
- [COLOR_SYSTEM.md](./COLOR_SYSTEM.md) — Semantic color tokens
- [FRONTEND_AGENTS.md](./FRONTEND_AGENTS.md) — Agent roles and workflow
- `vercel-react-best-practices` skill — React performance rules
- `vercel-react-native-skills` skill — React Native performance rules
- `web-design-guidelines` skill — Web Interface Guidelines compliance

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-19 | Initial interaction specifications |