---
name: myfarmai-apple-inspired-design
description: Visual design principles, layout hierarchy, product identity, responsive behavior, and design quality standards for MyFarm AI. Inspired by Apple's design discipline — clarity, restraint, excellent typography, precise spacing, thoughtful hierarchy, responsive layouts, and polished interactions — without copying proprietary assets or branding.
metadata:
  author: myfarmai
  version: "1.0.0"
---

# MyFarm AI Apple-Inspired Design Principles

## Purpose

This skill codifies the visual design direction for MyFarm AI: a trustworthy, modern, intelligent agricultural product that feels crafted, not templated. It draws inspiration from Apple's design discipline — clarity, restraint, excellent typography, precise spacing, thoughtful hierarchy, responsive layouts, and polished interactions — while establishing a distinct agricultural technology identity.

**Do not copy Apple's branding, logos, proprietary assets, or signature screens.** This is about adopting the *discipline*, not the *identity*.

---

## Core Design Principles

### 1. Clarity Over Cleverness
- Every pixel serves a purpose
- No decorative noise, gradients for decoration, or "delightful" animations that don't communicate state
- Information hierarchy guides the eye naturally — no guessing what's important

### 2. Restraint as Strength
- Generous whitespace is not wasted space — it's breathing room for complex agricultural data
- Limited color palette: one primary, supporting neutrals, semantic state colors only
- Typography scale is deliberate, not exhaustive

### 3. Agricultural Context First
- **Sunlight readability**: Minimum 4.5:1 contrast, 7:1 for critical data
- **Glove-friendly**: 48×48dp minimum touch targets
- **Low-end devices**: No heavy animations, efficient renders, offline-first
- **Multilingual**: Hindi/English line heights, Devanagari glyph support

### 4. Trustworthy Intelligence
- AI responses attributed with confidence indicators
- No fake personality — tool, not companion
- Uncertainty acknowledged visibly
- Sources cited for agricultural advice

---

## Visual Identity

### Color Philosophy: "Agricultural Trust Palette"

| Role | Token | Light | Dark | Rationale |
|------|-------|-------|------|-----------|
| Primary brand | `color-primary` | `#14532D` (Forest Green) | `#81C784` | Growth, trust, earth — not generic "tech blue" |
| Background | `color-surface` | `#FFFFFF` | `#1E1E1E` | Clean canvas, reduces glare |
| Warm neutral | `color-surface-container` | `#F8FAF5` | `#2C2C2C` | Paper-like warmth, not sterile gray |
| Accent | `color-warning` | `#F59E0B` (Harvest Amber) | `#FBBF24` | Seasonal change, attention — not "warning orange" |
| Info | `color-info` | `#2563EB` (Sky Blue) | `#60A5FA` | Water, technology, neutral actions |
| Error | `color-error` | `#DC2626` | `#EF4444` | Soil red — urgent, not alarming |

**Full token definitions:** See `docs/frontend/COLOR_SYSTEM.md`

### Typography: Inter + System Fallbacks

```css
/* Web: CSS variables in globals.css */
--font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

```tsx
// Android: Expo config plugin for native fonts
fontFamily: {
  regular: 'Inter_400Regular',
  medium: 'Inter_500Medium',
  semiBold: 'Inter_600SemiBold',
  bold: 'Inter_700Bold',
  mono: 'JetBrainsMono_400Regular',
}
```

**Type scale:** 14 sizes from `display-large` (56px/57sp) to `label-small` (12px/11sp). See `DESIGN_SYSTEM.md` for complete table.

**Why Inter:** Excellent Devanagari support, variable font for performance, neutral but distinctive, widely available.

### Spacing: 4px Base Unit, Semantic Tokens

| Token | Value | Use Case |
|-------|-------|----------|
| `space-1` | 4px | Icon-text gaps |
| `space-2` | 8px | Standard internal padding |
| `space-3` | 12px | Form field gaps |
| `space-4` | 16px | Card padding, standard gap |
| `space-6` | 24px | Section spacing |
| `space-8` | 32px | Major breaks |
| `space-12` | 48px | Hero sections |

**Never use magic numbers.** Always reference spacing tokens.

### Border Radius: Consistent Scale

| Token | Value | Use Case |
|-------|-------|----------|
| `radius-sm` | 4px | Chips, badges, small inputs |
| `radius-md` | 8px | Buttons, standard inputs, cards |
| `radius-lg` | 12px | Large cards, modals |
| `radius-xl` | 16px | Hero panels, feature cards |
| `radius-full` | 9999px | Pills, avatars, FAB |

### Elevation: 5 Levels Only

| Level | Web | Android | Use Case |
|-------|-----|---------|----------|
| 0 | `shadow-none` | 0dp | Flat, dividers |
| 1 | `shadow-sm` | 1dp | Cards, input focus |
| 2 | `shadow-md` | 3dp | Elevated cards, dropdowns |
| 3 | `shadow-lg` | 6dp | Modals, bottom sheets |
| 4 | `shadow-xl` | 8dp | Overlays, toasts |

---

## Layout Principles

### Container System

```css
/* Web: Max-width containers */
.container-sm   { max-width: 640px; }   /* Forms, narrow content */
.container-md   { max-width: 768px; }   /* Standard content */
.container-lg   { max-width: 1024px; }  /* Dashboards */
.container-xl   { max-width: 1280px; }  /* Wide layouts */
.container-full { max-width: 100%; }    /* Edge-to-edge backgrounds */
```

### Grid & Flexbox

- **Web**: CSS Grid for 2D layouts, Flexbox for 1D
- **Android**: `Flexbox` (RN) / `ConstraintLayout` (native) — avoid absolute positioning
- **Gutters**: `space-4` (16px) minimum, `space-6` (24px) comfortable

### Responsive Breakpoints

| Name | Width | Web Columns | Android |
|------|-------|-------------|---------|
| `xs` | < 480px | 4 | Phone portrait |
| `sm` | ≥ 640px | 8 | Phone landscape / small tablet |
| `md` | ≥ 768px | 12 | Tablet portrait |
| `lg` | ≥ 1024px | 12 | Tablet landscape / desktop |
| `xl` | ≥ 1280px | 12 | Desktop |
| `2xl` | ≥ 1536px | 12 | Ultra-wide |

**Mobile-first:** Base styles for `xs`, enhance at `sm`, `md`, `lg`, `xl`.

---

## Component Design Standards

### Buttons

**Variants (Explicit, not boolean props):**
```tsx
// Good: Explicit variants
<Button.Primary size="md" />
<Button.Secondary size="lg" />
<Button.Ghost size="sm" />
<Button.Destructive />
<Button.Loading />

// Bad: Boolean prop explosion
<Button variant="primary" size="md" loading={false} disabled={false} />
```

**States (all variants):**
| State | Visual |
|-------|--------|
| Default | Base style |
| Hover (web) | `primary-hover` background, subtle scale |
| Focus | 3px ring `primary-container`, offset 2px |
| Active | `primary-active` background, scale 0.98 |
| Loading | Spinner, `disabled` opacity, `aria-busy` |
| Disabled | 38% opacity, no pointer events |

**Minimum sizes:** 44×44px (web), 48×48dp (Android)

### Inputs

**Structure:**
```
Label (required)
├── Input field
│   ├── Leading icon (optional)
│   ├── Text value
│   └── Trailing icon/action (optional)
├── Helper text (optional)
└── Error text (when invalid)
```

**States:**
| State | Border | Ring | Text |
|-------|--------|------|------|
| Default | `outline` | — | `on-surface` |
| Hover | `outline-strong` | — | — |
| Focus | `primary` | 2px `primary` | — |
| Error | `error` | 2px `error` | `error` + error message |
| Disabled | `outline-variant` | — | `on-surface-disabled` |

### Cards

**Anatomy:**
```
Card (elev-1)
├── Header (optional)
│   ├── Title (headline-small)
│   ├── Subtitle (body-small)
│   └── Action (icon button)
├── Content (body-medium)
│   ├── Primary data (display-small)
│   └── Secondary data (body-small)
└── Footer (optional)
    ├── Actions (button group)
    └── Metadata (caption)
```

**Variants:**
- `default` — Standard elevation, `surface-container`
- `elevated` — `elev-2`, `surface-container-high`
- `outlined` — No elevation, `outline` border, `surface`
- `filled` — No elevation, `surface-container-highest` background

### Navigation

**Web:** Single-page sections with anchor links + sticky header
**Android:** Native stack navigator + bottom tabs (3-5 destinations)

**Header:**
- Height: 56px (web), 56dp (Android)
- Background: `primary` / `surface` with `backdrop` blur
- Title: `headline-medium`, `on-primary` / `on-surface`
- Actions: Icon buttons, `icon` size 24×24

---

## Motion Philosophy

### Principles

1. **Motion communicates** — Every transition explains a state change
2. **Fast and subtle** — 150-250ms micro, 300-400ms macro
3. **Respect reduced motion** — `prefers-reduced-motion` / system setting
4. **No motion-only meaning** — Always paired with visual/text change

### Standard Durations

| Interaction | Duration | Easing |
|-------------|----------|--------|
| Button press | 100ms | ease-out |
| Hover/focus | 150ms | ease-out |
| Card expand | 200ms | ease-out |
| Modal enter | 250ms | ease-out |
| Page transition | 300ms | ease-in-out |

**Full specs:** See `docs/frontend/INTERACTION_GUIDELINES.md`

---

## Accessibility as Default

### Non-Negotiables

- [ ] 4.5:1 text contrast (7:1 for < 18px)
- [ ] 3:1 UI element contrast
- [ ] Visible focus indicators (3px ring, not outline)
- [ ] Keyboard accessible (web) / Switch Access (Android)
- [ ] Screen reader labels on all interactive elements
- [ ] Touch targets ≥ 44×44px / 48×48dp
- [ ] Reduced motion respected
- [ ] Text scales to 200% without horizontal scroll
- [ ] No color-only meaning (always icon + text)

### Agricultural Specific

- High contrast mode for direct sunlight (future)
- Voice-first: all actions accessible via speech
- Offline indicators: icon + text, not color alone
- Error messages: plain language, actionable, localized

---

## Platform Adaptation

| Principle | Web (Next.js) | Android (Expo/RN) |
|-----------|---------------|-------------------|
| **Tokens** | CSS variables | TypeScript constants |
| **Theming** | `prefers-color-scheme` + `.dark` class | `Appearance` + `ThemeProvider` |
| **Components** | Compound components + context | Compound components + context |
| **Animation** | CSS transitions / Framer Motion | Reanimated 3 (GPU-only) |
| **Icons** | Lucide React | Lucide React Native |
| **Fonts** | `font-sans` / `font-mono` utilities | StyleSheet + config plugin |
| **Touch** | Pointer events + `:hover` | Pressable + Gesture Handler |

---

## Quality Checklist (Per Component)

### Visual
- [ ] Uses semantic color tokens (no hardcoded hex)
- [ ] Uses spacing tokens (no magic numbers)
- [ ] Uses type scale (no arbitrary font-size)
- [ ] Uses radius tokens
- [ ] Uses elevation tokens
- [ ] Dark mode works via CSS variables / theme context

### Interaction
- [ ] All 5 states implemented (default, hover/focus, active, loading, disabled)
- [ ] Focus visible and keyboard accessible (web)
- [ ] Screen reader labels + roles
- [ ] Touch targets meet minimums
- [ ] Reduced motion respected
- [ ] Loading/error/empty/offline states covered

### Code
- [ ] TypeScript strict, no `any`
- [ ] Compound component pattern (no boolean props)
- [ ] Explicit variants for different configurations
- [ ] State lifted to provider, not trapped in component
- [ ] Memoized appropriately (React.memo, useMemo, useCallback)
- [ ] No inline component definitions

---

## Anti-Patterns (Explicitly Forbidden)

| Anti-Pattern | Why | Alternative |
|--------------|-----|-------------|
| Boolean prop proliferation | Exponential states, unmaintainable | Explicit variants + composition |
| Hardcoded colors/spacing | Theming impossible, inconsistency | Semantic tokens only |
| Inline styles for layout | No design system enforcement | Tailwind / StyleSheet with tokens |
| `forwardRef` everywhere (React 19) | Unnecessary complexity | `ref` as prop, `use()` for context |
| `&&` for conditional rendering | Falsy value bugs | Ternary or early return |
| Inline object/styles in render | New reference every render | StyleSheet.create / hoisted constants |
| Animation on layout properties | Jank, not GPU-accelerated | Transform + opacity only |
| Color-only status | Inaccessible | Icon + text + color |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-19 | Forest Green `#14532D` as primary | Agricultural trust, distinct from tech blues, maps to existing `primary-800` |
| 2026-10-19 | Warm background `#F8FAF5` | Reduces glare vs pure white, paper-like, maps to existing `primary-50` |
| 2026-10-19 | Inter font family | Devanagari support, variable font, neutral |
| 2026-10-19 | 4px spacing base | Standard, divisible, works with 8px grid |
| 2026-10-19 | 5 elevation levels | Sufficient depth, no shadow fatigue |
| 2026-10-19 | Explicit variant components | Composition over configuration, per Vercel patterns |

---

## References

- `docs/frontend/DESIGN_SYSTEM.md` — Complete design system overview
- `docs/frontend/COLOR_SYSTEM.md` — Semantic color tokens
- `docs/frontend/INTERACTION_GUIDELINES.md` — Motion and interaction specs
- `vercel-composition-patterns` skill — Component architecture rules
- `vercel-react-best-practices` skill — React performance rules
- `vercel-react-native-skills` skill — React Native performance rules
- `web-design-guidelines` skill — Web Interface Guidelines compliance

---

## Usage in Agent Workflow

**frontend-design-architect** uses this skill for:
- Architecture audits
- Design specification reviews
- Component API design decisions
- Tradeoff analyses

**frontend-ui-engineer** uses this skill for:
- Visual implementation verification
- Token usage compliance
- Component pattern adherence

**frontend-interaction-engineer** uses this skill for:
- Motion specification implementation
- Interaction state completeness
- Accessibility verification

**frontend-ux-auditor** uses this skill for:
- Visual consistency audits
- Design principle compliance checks
- Anti-pattern detection