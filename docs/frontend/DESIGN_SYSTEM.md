# MyFarm AI Design System

**Version:** 1.0.0  
**Status:** Foundation Phase - Audit Complete, Design Direction Established  
**Last Updated:** 2026-10-19

---

## Overview

This document establishes the visual design principles, component architecture, and implementation standards for MyFarm AI across web (Next.js 15) and Android (React Native/Expo) platforms.

MyFarm AI is an agricultural AI platform serving farmers, agronomists, and field workers. The design system prioritizes **clarity, restraint, and trustworthiness** — inspired by Apple's design discipline without copying proprietary assets or branding.

---

## Design Principles

### 1. Clarity First
- Every element serves a clear purpose
- No decorative noise or unnecessary visual complexity
- Information hierarchy guides user attention naturally

### 2. Agricultural Context Awareness
- **Sunlight readability**: High contrast ratios, avoid low-contrast gray-on-gray
- **Glove-friendly**: Minimum 48×48dp touch targets (web: 44×44px)
- **Low-end device performance**: Minimal animations, efficient renders
- **Offline-first mental model**: Clear connection status, cached data indicators
- **Multilingual ready**: Hindi/English text rendering, appropriate line heights

### 3. Trustworthy Intelligence
- AI responses clearly attributed with confidence indicators
- No anthropomorphic "personality" — tool, not companion
- Transparent uncertainty acknowledgment
- Source citations for agricultural advice

### 4. Platform Respect
- Web follows Next.js/React conventions, browser standards
- Android follows Material 3 / React Native Paper patterns
- Shared design tokens, platform-appropriate implementations

---

## Color System

See [COLOR_SYSTEM.md](./COLOR_SYSTEM.md) for complete semantic token definitions.

### Primary Palette (Proposed — Pending Audit Reconciliation)

| Token | Light | Dark | Purpose |
|-------|-------|------|---------|
| `primary` | `#14532D` (Forest Green) | `#81C784` | Brand, primary actions, focus rings |
| `surface` | `#FFFFFF` | `#1E1E1E` | Cards, containers, elevated surfaces |
| `surface-variant` | `#F8FAF5` (Warm Background) | `#2C2C2C` | Secondary containers, subtle backgrounds |
| `on-primary` | `#FFFFFF` | `#17211B` | Text on primary backgrounds |
| `on-surface` | `#17211B` (Primary Text) | `#E8EAE6` | Primary text on surfaces |
| `on-surface-variant` | `#66736A` (Secondary Text) | `#A0A8A0` | Secondary text, captions |
| `border` | `#DCE5DC` | `#3D3D3D` | Dividers, input borders, card edges |
| `success` | `#166534` | `#4ADE80` | Success states, positive indicators |
| `warning` | `#F59E0B` (Harvest Amber) | `#FBBF24` | Warnings, attention-needed |
| `error` | `#DC2626` (Error Red) | `#EF4444` | Errors, destructive actions |
| `info` | `#2563EB` (Information Blue) | `#60A5FA` | Informational, neutral actions |

### Current Web Implementation (from `tailwind.config.js`)
```js
primary: {
  50: '#E8F5E9', 100: '#C8E6C9', 200: '#A5D6A7', 300: '#81C784',
  400: '#66BB6A', 500: '#4CAF50', 600: '#43A047', 700: '#388E3C',
  800: '#2E7D32', 900: '#1B5E20'
}
```

**Decision:** The existing Tailwind `primary` scale (Material Green) will be mapped to the new semantic tokens. Forest Green `#14532D` ≈ `primary-800`. The warm background `#F8FAF5` ≈ `primary-50`. This mapping preserves existing components while enabling the new semantic system.

---

## Typography

### Type Scale

| Style | Web (Rem) | Android (SP) | Weight | Line Height | Use Case |
|-------|-----------|--------------|--------|-------------|----------|
| `display-large` | 3.5rem / 56px | 57sp | 600 | 1.1 | Hero headlines |
| `display-medium` | 2.5rem / 40px | 45sp | 600 | 1.2 | Page titles |
| `display-small` | 2rem / 32px | 36sp | 600 | 1.3 | Section headers |
| `headline-large` | 1.5rem / 24px | 24sp | 600 | 1.4 | Card titles, important labels |
| `headline-medium` | 1.25rem / 20px | 20sp | 500 | 1.4 | Sub-section headers |
| `headline-small` | 1.125rem / 18px | 18sp | 500 | 1.5 | Component titles |
| `title-large` | 1rem / 16px | 16sp | 600 | 1.5 | Button labels, form labels |
| `title-medium` | 0.875rem / 14px | 14sp | 500 | 1.5 | Chip labels, small buttons |
| `title-small` | 0.8125rem / 13px | 13sp | 500 | 1.5 | Caption labels |
| `body-large` | 1rem / 16px | 16sp | 400 | 1.6 | Primary body text |
| `body-medium` | 0.875rem / 14px | 14sp | 400 | 1.6 | Secondary body text |
| `body-small` | 0.8125rem / 13px | 12sp | 400 | 1.5 | Captions, helper text |
| `label-large` | 0.875rem / 14px | 14sp | 500 | 1.5 | Input labels |
| `label-medium` | 0.8125rem / 13px | 12sp | 500 | 1.5 | Small labels |
| `label-small` | 0.75rem / 12px | 11sp | 500 | 1.5 | Overline, micro labels |

### Font Families

**Web:**
```css
--font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

**Android (Expo):**
```tsx
// Using expo-font with config plugin
fontFamily: {
  regular: 'Inter_400Regular',
  medium: 'Inter_500Medium',
  semiBold: 'Inter_600SemiBold',
  bold: 'Inter_700Bold',
  mono: 'JetBrainsMono_400Regular',
}
```

### Implementation Notes
- **Web**: Use Tailwind's `font-sans` / `font-mono` utilities with CSS variables for font loading
- **Android**: Use `StyleSheet.create` with font family references; avoid inline font objects
- **Fallback**: System fonts load instantly — no flash of unstyled text
- **Multilingual**: Inter supports Devanagari (Hindi) glyphs; test line heights with mixed scripts

---

## Spacing & Layout

### Spacing Scale (4px Base Unit)

| Token | Value | Rem | Use Case |
|-------|-------|-----|----------|
| `space-0` | 0 | 0 | Reset, tight compaction |
| `space-1` | 4px | 0.25rem | Micro gaps, icon-text |
| `space-2` | 8px | 0.5rem | Standard gaps, internal padding |
| `space-3` | 12px | 0.75rem | Medium gaps, form fields |
| `space-4` | 16px | 1rem | Standard padding, card internal |
| `space-5` | 20px | 1.25rem | Large padding |
| `space-6` | 24px | 1.5rem | Section spacing, card gaps |
| `space-8` | 32px | 2rem | Major section breaks |
| `space-10` | 40px | 2.5rem | Page-level spacing |
| `space-12` | 48px | 3rem | Hero sections, large layouts |

### Breakpoints

| Name | Width | Target Devices |
|------|-------|----------------|
| `xs` | < 480px | Small phones |
| `sm` | ≥ 640px | Large phones, small tablets |
| `md` | ≥ 768px | Tablets |
| `lg` | ≥ 1024px | Laptops, desktops |
| `xl` | ≥ 1280px | Large desktops |
| `2xl` | ≥ 1536px | Ultra-wide |

### Container Max-Widths

| Size | Max Width | Use Case |
|------|-----------|----------|
| `container-sm` | 640px | Narrow content, forms |
| `container-md` | 768px | Standard content |
| `container-lg` | 1024px | Wide content, dashboards |
| `container-xl` | 1280px | Full-width layouts |
| `container-full` | 100% | Edge-to-edge backgrounds |

### Border Radius

| Token | Value | Use Case |
|-------|-------|----------|
| `radius-none` | 0 | Sharp corners, tables |
| `radius-sm` | 4px | Small elements, chips, badges |
| `radius-md` | 8px | Buttons, inputs, cards |
| `radius-lg` | 12px | Large cards, modals |
| `radius-xl` | 16px | Hero cards, feature panels |
| `radius-full` | 9999px | Pills, avatars, circular buttons |

### Elevation / Shadows

| Level | Web (Tailwind) | Android (Elevation) | Use Case |
|-------|----------------|---------------------|----------|
| `elev-0` | `shadow-none` | 0dp | Flat surfaces, dividers |
| `elev-1` | `shadow-sm` | 1dp | Cards, input focus |
| `elev-2` | `shadow-md` | 3dp | Elevated cards, dropdowns |
| `elev-3` | `shadow-lg` | 6dp | Modals, bottom sheets |
| `elev-4` | `shadow-xl` | 8dp | Overlays, toasts |

---

## Component Architecture

### Composition Patterns (per `vercel-composition-patterns`)

**Core Principle:** Composition over configuration. Avoid boolean prop proliferation.

#### ✅ Do: Compound Components with Shared Context
```tsx
// Web: ChatInterface with composed parts
<Chat.Provider>
  <Chat.Header />
  <Chat.MessageList />
  <Chat.InputArea>
    <Chat.TextInput />
    <Chat.VoiceButton />
    <Chat.SendButton />
  </Chat.InputArea>
</Chat.Provider>
```

#### ✅ Do: Explicit Variants
```tsx
// Instead of <Button variant="primary" size="large" loading={true} />
// Use explicit components:
<Button.Primary size="lg" />
<Button.Secondary size="md" />
<Button.Ghost size="sm" />
<Button.Destructive />
<Button.Loading />
```

#### ❌ Don't: Boolean Prop Explosion
```tsx
// Bad: exponential state combinations
<ChatInterface
  showHeader={true}
  showVoice={true}
  showAttachments={false}
  isLoading={false}
  isThread={false}
  isEditing={false}
  isForwarding={false}
/>
```

### Component Inventory (Current Web)

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| `ChatInterface` | `web/src/components/Chat/ChatInterface.tsx` | ✅ Implemented | Uses `useChat`, `useSpeechRecognition`, `useSpeechSynthesis` |
| `WeatherCard` | `web/src/components/Weather/WeatherCard.tsx` | ✅ Implemented | Uses `useWeather`, weather codes from utils |
| `ResourcesList` | `web/src/components/Resources/ResourcesList.tsx` | ✅ Implemented | Category filtering, TanStack Query |
| `Providers` | `web/src/providers.tsx` | ✅ Implemented | TanStack Query provider |

### Component Inventory (Current Android)

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| `ChatInterface` | `android/src/components/ChatInterface.tsx` | ✅ Implemented | React Native Paper + expo-speech |
| `WeatherCard` | `android/src/components/WeatherCard.tsx` | ✅ Implemented | Same weather codes |
| `ResourcesList` | `android/src/components/ResourcesList.tsx` | ✅ Implemented | React Native Paper cards |

### Shared Component Contracts

Both platforms implement equivalent features with platform-appropriate patterns:

| Feature | Web Pattern | Android Pattern |
|---------|-------------|-----------------|
| Chat messages | Flexbox + `self-end`/`self-start` | `FlatList` + `ListRenderItem` |
| Voice input | Web Speech API (browser) | `expo-speech-recognition` |
| Voice output | Web SpeechSynthesis API | `expo-speech` |
| Weather display | CSS Grid + Lucide icons | React Native Paper + Lucide React Native |
| Resources | TanStack Query + anchor links | TanStack Query + `Linking.openURL` |
| Navigation | Single-page sections | React Navigation Stack |

---

## Motion & Interactions

See [INTERACTION_GUIDELINES.md](./INTERACTION_GUIDELINES.md) for complete interaction specifications.

### Core Principles
1. **Purposeful only** — Every transition communicates state change
2. **Subtle & fast** — 150-250ms for micro-interactions, 300-400ms for page transitions
3. **Reduced motion** — Respect `prefers-reduced-motion` (web) / system setting (Android)
4. **Accessible** — Focus visible, keyboard navigable, no motion-only meaning

### Standard Transitions

| Interaction | Duration | Easing | Web CSS | Android |
|-------------|----------|--------|---------|---------|
| Button press | 100ms | `ease-out` | `transition-transform duration-100` | `withTiming(0.95, {duration: 100})` |
| Hover/focus | 150ms | `ease-out` | `transition-colors duration-150` | N/A (touch) |
| Card expand | 200ms | `ease-out` | `transition-all duration-200` | `withTiming({height}, {duration: 200})` |
| Modal enter | 250ms | `ease-out` | `transition-opacity duration-250` | `withTiming(1, {duration: 250})` |
| Page transition | 300ms | `ease-in-out` | Next.js `transition` | `Stack.Navigator` animation |

### Loading States
- **Skeleton screens** for known structure (weather cards, resource lists)
- **Spinner** for indeterminate actions (chat send, voice processing)
- **Progress** for determinate operations (file upload, sync)

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance (Minimum)

| Requirement | Web | Android |
|-------------|-----|---------|
| Color contrast (text) | 4.5:1 normal, 3:1 large | 4.5:1 normal, 3:1 large |
| Color contrast (UI) | 3:1 | 3:1 |
| Focus visible | `focus-visible` ring | `focusable` + `accessibilityFocus` |
| Keyboard navigation | Tab order, skip links | N/A (but switch control) |
| Screen reader | Semantic HTML, ARIA labels | `accessibilityLabel`, `accessibilityRole` |
| Touch target | 44×44px minimum | 48×48dp minimum |
| Reduced motion | `@media (prefers-reduced-motion)` | System setting listener |
| Text scaling | `rem` units, respect zoom | `sp` units, respect system font scale |

### Agricultural-Specific Considerations
- **High contrast mode**: Alternative palette for direct sunlight
- **Voice-first**: All interactive elements accessible via speech input
- **Offline indicators**: Non-color-dependent (icon + text)
- **Error messages**: Plain language, actionable, localized

---

## Platform-Specific Guidelines

### Web (Next.js 15 + React 18 + Tailwind CSS 3.4)

**Stack:**
- Next.js 15 App Router, Server Components by default
- React 18 with concurrent features
- Tailwind CSS 3.4 with CSS variables for theming
- TanStack Query v5 for server state
- Zustand for client state
- Lucide React for icons
- `clsx` + `tailwind-merge` for class composition

**Performance Rules (per `vercel-react-best-practices`):**
- Eliminate waterfalls: parallel fetches, Suspense boundaries
- Bundle optimization: direct imports, dynamic imports for heavy components
- Server-side: React.cache(), parallel data fetching, minimize serialization
- Client-side: SWR deduplication, memoization, `startTransition`
- Rendering: `content-visibility`, hoist static JSX, avoid inline components

**File Structure:**
```
web/src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page (chat + weather + resources)
│   └── globals.css        # Tailwind + CSS variables
├── components/
│   ├── Chat/              # Chat feature components
│   ├── Weather/           # Weather feature components
│   └── Resources/         # Resources feature components
├── hooks/                 # Custom React hooks
├── lib/
│   ├── api/               # API client + types
│   └── utils.ts           # cn(), weather codes
└── providers.tsx          # QueryClientProvider
```

### Android (Expo 51 + React Native 0.74 + React Native Paper)

**Stack:**
- Expo Router v3 for file-based routing
- React Native Paper v5 (Material 3 components)
- React Native Reanimated 3 for animations
- Expo Speech / Speech Recognition for voice
- Expo SecureStore for local persistence
- Zustand for client state
- Lucide React Native for icons

**Performance Rules (per `vercel-react-native-skills`):**
- Lists: FlashList for virtualization, memoize items, stabilize callbacks
- Animations: GPU-only properties (transform, opacity), `useDerivedValue`
- Navigation: Native stack/tabs over JS navigators
- Images: `expo-image` for optimization
- Styling: StyleSheet.create or Nativewind, avoid inline objects
- Fonts: Config plugin for native loading

**File Structure:**
```
android/src/
├── app/                   # Expo Router pages (if using)
├── components/            # Shared components
├── hooks/                 # Custom hooks (useChat, useWeather, etc.)
├── lib/api/               # API client + types
├── storage/               # SecureStore persistence
├── config/                # API config, constants
├── types/                 # TypeScript types
└── utils/                 # Weather codes, helpers
```

---

## Design Token Governance

### Token Naming Convention
```
{category}-{property}-{variant}-{state}
Examples:
- color-primary-foreground
- color-surface-container-highest
- spacing-md
- radius-lg
- shadow-elev-2
- motion-duration-200
```

### Token Sources
1. **Figma/Design Tools** → Source of truth for designers
2. **Tailwind Config** → Web implementation (CSS variables)
3. **StyleSheet/Theme** → Android implementation (TypeScript constants)
4. **Documentation** → This design system

### Change Process
1. Propose token change in design review
2. Update source of truth (Figma/design tokens)
3. Update web implementation (tailwind.config.js + CSS variables)
4. Update Android implementation (theme constants)
5. Audit affected components
6. Document in CHANGELOG.md

---

## Current State Assessment (Audit Results)

### ✅ Already Implemented
- Next.js 15 with App Router, TypeScript, Tailwind CSS
- React Native/Expo with Paper, Reanimated, Router
- TanStack Query v5 for server state on both platforms
- Zustand for client state on both platforms
- API client with typed endpoints, error handling
- Chat, Weather, Resources features on both platforms
- Voice input/output hooks on both platforms
- Component structure with domain-based organization
- Lucide icons on both platforms
- ESLint, TypeScript, Jest configured

### ⚠️ Gaps Identified
| Gap | Priority | Effort |
|-----|----------|--------|
| No design token system (CSS variables / theme constants) | HIGH | Medium |
| No dark mode implementation | HIGH | Medium |
| No shared component library / Storybook | MEDIUM | High |
| Inconsistent spacing/radius/elevation usage | MEDIUM | Low |
| No accessibility audit / automated testing | HIGH | Medium |
| No interaction/motion specifications | MEDIUM | Low |
| Android uses Paper theming, web uses Tailwind — no token bridge | HIGH | Medium |
| No design token documentation for developers | MEDIUM | Low |

### 🔄 Decisions Made During Audit

| Decision | Rationale |
|----------|-----------|
| Map existing Tailwind `primary` scale to semantic tokens | Preserves existing components, gradual migration |
| Use CSS variables for web theming | Native browser theming, no build step, works with Tailwind |
| Use TypeScript constants for Android theming | Type-safe, works with StyleSheet, no runtime overhead |
| Keep Paper theming on Android, align tokens | Paper is established, tokens bridge the gap |
| Defer full component library to post-foundation | Foundation must stabilize first |

---

## Next Steps (Post-Foundation)

1. **Implement Design Tokens** — CSS variables (web) + TypeScript constants (Android)
2. **Add Dark Mode** — CSS `prefers-color-scheme` + system listener (Android)
3. **Create Base Components** — Button, Input, Card, Badge, Dialog with variants
4. **Accessibility Audit** — axe-core (web), AccessibilityInfo (Android)
5. **Interaction Specs** — Document all component states and transitions
6. **Pilot Feature** — Implement one feature using new system (e.g., enhanced Chat)
7. **Storybook Setup** — Component documentation and visual regression

---

## Agricultural Images

A cohesive collection of optimized agricultural images lives under `web/public/images/`:

| Category | File | Format | Notes |
|----------|------|--------|-------|
| Purchased-brief Hero (farm landscape) | `images/hero-indian-farm.svg` | SVG | Retained in repo, no longer used on Home (see Modern Dashboard, 2026-10-23) |
| Crop guidance | `images/crop-guidance.svg` | SVG | Healthy close-up crop growth |
| Plant disease | `images/plant-disease.svg` | SVG | Leaves with distinguishable symptoms |
| Pest identification | `images/pest-identification.svg` | SVG | Macro pests on crops |
| Weather & irrigation | `images/weather-irrigation.svg` | SVG | Farmland, irrigation, water management |
| Unused | `images/smart-farming.svg` | SVG | Retained in repo, no longer used on Home (see Modern Dashboard, 2026-10-23) |
| Knowledge & community | `images/knowledge-community.svg` | SVG | Farmer collaboration |
| Empty states | `images/empty-states/*.svg` | SVG | Crops, disease, pest, weather, community, search |
| Thumbnails | `images/thumbnails/thumb-*.svg` | SVG | Smaller variants for lists and cards |

All images use `viewBox`, `role="img"`, and `aria-label` for accessibility, and are drawn in the green/cream/earthy design-system palette (Forest Green `#14532D`, Warm Background `#F8FAF5`, Harvest Amber `#F59E0B`, earth browns). They are lightweight, scalable, and carry no licensing or attribution burden.

**Generation method:** No image-generation provider is configured (OmniRoute has no image API; the local GPU is a 2 GB MX250 unsuitable for image-generation models, and no paid service will be activated). Per the documented fallback, polished SVG illustrations were created locally instead of AI-generated photographs. Files are served statically by Next.js from `public/`, referenceable as `/images/<file>`.

### Component integration

| Component | Image | Placement | Alt text |
|-----------|-------|-----------|----------|
| Crops page | `images/crop-guidance.svg` | Above the unavailability card | Close-up photography of healthy crop growth and agricultural practices |
| Pest & Disease page | `images/plant-disease.svg` | Top grid, first cell | Crop leaves showing distinguishable plant disease symptoms |
| Pest & Disease page | `images/pest-identification.svg` | Top grid, second cell | Macro photography of common agricultural pests on crops |
| Weather page | `images/weather-irrigation.svg` | Above the weather header | Farmland under realistic weather conditions with irrigation systems and water management |
| Knowledge page | `images/knowledge-community.svg` | Above the Knowledge Library heading | Authentic Indian farming activities, farmer collaboration, and crop management |
| Community page | `images/empty-states/empty-community.svg` | Above the unavailability card | Farmer collaboration and community discussion |
| ResourcesList empty state | `images/empty-states/empty-search.svg` | Centered in the empty category card | No resources found |

Informative illustrations carry descriptive `alt` text. Images that serve purely as visual support beside existing heading text are kept descriptive but concise. All image tags include explicit `width`/`height` to reserve layout space and avoid cumulative layout shift.

- `vercel-react-best-practices` skill — React/Next.js performance rules
- `vercel-react-native-skills` skill — React Native/Expo performance rules
- `vercel-composition-patterns` skill — Component architecture patterns
- `web-design-guidelines` skill — Web Interface Guidelines compliance

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-19 | Initial foundation document from audit |
| 1.1.0 | 2026-10-21 | Integrated agricultural SVG illustrations into homepage hero, Smart Farming, Crops, Pest & Disease, Weather, Knowledge, Community pages and ResourcesList empty state |