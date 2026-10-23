# MyFarmAI — UI/UX Design System

**Document ID:** MYFARMAI-UX-002  
**Version:** 1.0  
**Status:** Proposed System — Owner Review Required  
**Platforms:** Web and Android  
**Related documents:** UI_UX_DESIGN_BRIEF.md, PRD, TRD, APP_FLOW, approved SRS and ADRs

## 1. Purpose

This document proposes shared design tokens, component patterns, interaction states, accessibility rules, and implementation conventions for MyFarmAI.

It is a foundation for consistent design and implementation. Values are proposed defaults, not approved brand decisions. Existing product code and owner-approved design decisions must be inspected before replacing styles or components.

## 2. Design Principles

1. **Clarity:** Make the primary task obvious.
2. **Trust:** Show source provenance and limitations honestly.
3. **Consistency:** Use shared tokens and components.
4. **Accessibility:** Build contrast, keyboard, screen-reader, and touch support into components.
5. **Resilience:** Design for latency, partial results, and failures.
6. **Simplicity:** Prefer a focused agricultural assistant experience over a cluttered dashboard.

## 3. Design Tokens

### 3.1 Color roles

Use semantic roles rather than hard-coding colors inside components. The following palette is illustrative and must be checked for contrast in actual use.

| Token | Proposed value | Usage |
|---|---|---|
| `color.brand.primary` | `#246B45` | Primary actions and brand accents |
| `color.brand.primaryHover` | `#1C5436` | Hover/pressed state where supported |
| `color.brand.primarySoft` | `#E7F2EA` | Subtle selected or informational surfaces |
| `color.text.primary` | `#17231B` | Main text |
| `color.text.secondary` | `#526158` | Secondary text |
| `color.surface.default` | `#FFFFFF` | Main surface |
| `color.surface.subtle` | `#F5F7F5` | Page or section background |
| `color.border.default` | `#D8E0DA` | Borders and separators |
| `color.state.success` | `#247447` | Successful state |
| `color.state.warning` | `#8A5700` | Warning state |
| `color.state.error` | `#B42318` | Error state |
| `color.state.info` | `#175CD3` | Informational state |

Rules:
- Validate text and component contrast against WCAG 2.2 AA.
- Do not use color alone to communicate meaning.
- Dark mode is not defined by this draft; add a complete semantic dark palette before claiming dark-mode support.
- Never use success colors to decorate general recommendations.

### 3.2 Typography

Proposed type stack: system UI fonts for fast loading and good platform integration. A bundled font may be chosen only after licensing, rendering, and performance review.

| Token | Proposed size | Usage |
|---|---:|---|
| `font.size.xs` | 12 px | Metadata and compact labels |
| `font.size.sm` | 14 px | Secondary text |
| `font.size.md` | 16 px | Body text and inputs |
| `font.size.lg` | 18 px | Emphasized body text |
| `font.size.xl` | 22 px | Section headings |
| `font.size.2xl` | 28 px | Screen titles on larger layouts |
| `font.weight.regular` | 400 | Body text |
| `font.weight.medium` | 500 | Controls and emphasis |
| `font.weight.semibold` | 600 | Headings |
| `line.height.body` | 1.5 | Long-form content |
| `line.height.heading` | 1.2 | Headings |

Rules:
- Avoid long passages in all caps.
- Allow text scaling, especially on Android.
- Do not use font size alone to establish the entire hierarchy; use spacing and semantic headings.

### 3.3 Spacing scale

Use a consistent 4 px base scale.

| Token | Value |
|---|---:|
| `space.1` | 4 px |
| `space.2` | 8 px |
| `space.3` | 12 px |
| `space.4` | 16 px |
| `space.5` | 20 px |
| `space.6` | 24 px |
| `space.8` | 32 px |
| `space.10` | 40 px |
| `space.12` | 48 px |
| `space.16` | 64 px |

Use the nearest token instead of introducing arbitrary spacing values without a reason.

### 3.4 Shape, border, and elevation

| Token | Proposed value | Usage |
|---|---:|---|
| `radius.sm` | 6 px | Compact controls |
| `radius.md` | 10 px | Inputs and standard cards |
| `radius.lg` | 16 px | Major content panels |
| `radius.pill` | 999 px | Pill tags only where appropriate |
| `border.width.default` | 1 px | Standard border |
| `shadow.card` | Subtle | Elevation only when it improves hierarchy |

Prefer borders and spacing over multiple heavy shadows. Avoid excessive rounded containers that make long answers difficult to scan.

### 3.5 Layout and breakpoints

Proposed web breakpoints:

- Small: below 640 px.
- Medium: 640–1023 px.
- Large: 1024 px and above.

These are initial design tokens, not a guarantee that every screen will use identical breakpoints. Test actual content at narrow widths and intermediate sizes.

## 4. Component Specifications

### 4.1 Button

Variants:
- Primary: main action.
- Secondary: lower-priority action.
- Tertiary/ghost: lightweight action.
- Destructive: irreversible or dangerous action, with confirmation where applicable.

States:
- Default.
- Hover where supported.
- Focus-visible.
- Pressed.
- Disabled.
- Loading.

Requirements:
- Accessible name.
- Clear focus indicator.
- Do not allow repeated submission while a non-repeatable action is pending.
- Avoid icon-only buttons unless the icon has an accessible name and is recognizable.

### 4.2 Text input and question composer

Requirements:
- Persistent label or equivalent accessible name.
- Helpful placeholder, not placeholder-only labeling.
- Clear validation message.
- Character or length guidance when needed.
- Visible focus state.
- Disabled and loading states.
- Preserve user input after recoverable network errors where safe.

The main agricultural question composer should be prominent without overwhelming the answer or research content.

### 4.3 Cards and content panels

Use cards only when they group related content meaningfully. Keep borders and elevation restrained. Do not place every paragraph in its own card.

### 4.4 Answer content

The answer component should support:
- Headings and paragraphs.
- Lists and other safe formatted content.
- Limitations or uncertainty notes where relevant.
- Source references.
- Partial-result state.
- Copy/share actions only if approved and implemented safely.

Do not imply that all claims are externally verified if the response includes model-generated synthesis.

### 4.5 Source item

Display available information:
- Source title.
- Domain or publisher.
- Publication date only when known.
- Retrieval status where useful.
- Link to the actual source.

Requirements:
- Use the real retrieved URL.
- Open links safely according to platform conventions.
- Do not invent source ratings or dates.
- Mark unavailable sources as unavailable rather than presenting them as verified.

### 4.6 Alert and inline status

Variants:
- Informational.
- Success.
- Warning.
- Error.
- Partial result.

Every status must include text or an accessible label; color alone is insufficient. Errors should explain what happened and, when appropriate, what the user can do next.

### 4.7 Loading and progress

- Use a progress indicator for operations that take noticeable time.
- Avoid claiming exact completion percentages unless measurable.
- Keep the user informed for AI and research operations.
- Support cancellation only if the underlying operation actually supports it.

### 4.8 Dialog and confirmation

Use dialogs sparingly. Destructive or security-sensitive actions require clear explanation of impact and explicit confirmation. Never use a confirmation dialog as a substitute for server-side authorization.

### 4.9 Navigation

- Keep primary destinations limited and clear.
- Provide visible active state.
- Support keyboard navigation on web.
- Respect Android back navigation.
- Avoid hiding core functions behind unfamiliar icons.

## 5. Application States

Every asynchronous feature must define applicable states.

| State | UI behavior |
|---|---|
| Idle | Ready for user input |
| Loading | Explain the operation in progress |
| Success | Show the returned result |
| Empty | Explain that no usable result is available |
| Partial | Show available results and explain limitations |
| Error | Show a safe, actionable message |
| Offline | Indicate connectivity or service unavailability |
| Disabled | Explain why an action cannot currently be used where useful |

Do not show success styling for partial results or failures.

## 6. Interaction and Motion

- Use motion to explain state changes, not as decoration.
- Respect reduced-motion preferences where supported.
- Keep transitions brief and non-blocking.
- Avoid auto-playing media or continuous animation.
- Ensure loading indicators do not block necessary navigation unless the operation requires it.
- Keep interactions usable with keyboard, touch, and assistive technology.

## 7. Accessibility Standard

Target WCAG 2.2 AA for web where applicable, with platform accessibility conventions for Android.

Requirements:
- Sufficient text and non-text contrast.
- Logical heading hierarchy.
- Keyboard operability and visible focus on web.
- Accessible names for controls.
- Screen-reader announcements for important asynchronous status changes.
- Form labels and actionable validation.
- Text scaling and zoom support.
- Touch targets meeting platform guidance.
- No reliance on color, sound, or motion alone.
- Accessible link text and source descriptions.

Run automated accessibility checks and manual keyboard/screen-reader review. Automated checks alone do not establish conformance.

## 8. Responsive Rules

### Web
- Use fluid content widths and a readable maximum line length.
- Collapse multi-column layouts when content becomes cramped.
- Keep answer text readable at narrow widths.
- Ensure source URLs do not overflow the viewport.
- Do not rely on hover-only interactions.

### Android
- Respect system bars, safe areas, and the software keyboard.
- Support device text scaling.
- Use platform-appropriate navigation and secure storage.
- Handle orientation and narrow-screen constraints where supported.

## 9. Content Design and Localization

- Prefer plain, concise language.
- Avoid unsupported claims such as “100% accurate” or “guaranteed yield.”
- Use consistent names for AI answers, research, sources, errors, and partial results.
- Plan for localization, including longer translated strings and locale-appropriate date formats.
- Do not imply a language is supported until the client, backend, and model behavior have been tested for it.

The final supported language list is an owner decision.

## 10. Proposed Design Token JSON

This is a starter token file proposal. Reconcile it with existing design tokens and the actual build tooling before adding it to the repository.

```json
{
  "color": {
    "brand": {
      "primary": "#246B45",
      "primaryHover": "#1C5436",
      "primarySoft": "#E7F2EA"
    },
    "text": {
      "primary": "#17231B",
      "secondary": "#526158"
    },
    "surface": {
      "default": "#FFFFFF",
      "subtle": "#F5F7F5"
    },
    "border": {
      "default": "#D8E0DA"
    },
    "state": {
      "success": "#247447",
      "warning": "#8A5700",
      "error": "#B42318",
      "info": "#175CD3"
    }
  },
  "spacing": {
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "12": "48px",
    "16": "64px"
  },
  "radius": {
    "sm": "6px",
    "md": "10px",
    "lg": "16px",
    "pill": "999px"
  },
  "typography": {
    "xs": "12px",
    "sm": "14px",
    "md": "16px",
    "lg": "18px",
    "xl": "22px",
    "2xl": "28px"
  }
}
```

## 11. Implementation Guidance

- Inspect existing UI components and CSS/theme conventions first.
- Reuse the current framework's supported token mechanism.
- Avoid duplicate component libraries.
- Keep design tokens separate from feature-specific business logic.
- Ensure shared terminology and API states align with the flow documents.
- Test components in real screen contexts, not only isolated previews.
- Update documentation whenever a component's contract or behavior changes.

## 12. Design QA Checklist

Before accepting a screen:
- [ ] Primary action is clear.
- [ ] Visual hierarchy is consistent.
- [ ] Text and controls meet contrast requirements.
- [ ] Keyboard focus and screen-reader labels are usable.
- [ ] Loading, empty, partial, and error states are covered.
- [ ] Long answers and long source titles wrap correctly.
- [ ] Narrow web and Android layouts are checked.
- [ ] User input is preserved after recoverable failures where safe.
- [ ] No fabricated sources, unsupported accuracy claims, or misleading status indicators.
- [ ] Design matches the approved user flow.
- [ ] Components use shared tokens.
- [ ] Known issues and unverified behavior are documented.

## 13. Open Decisions

- Final logo and brand identity.
- Approved primary and semantic colors.
- Typography and font licensing.
- Dark-mode support.
- Supported languages.
- Final breakpoints and target devices.
- Authentication scope.
- Whether history and saved results are in MVP.
- Whether source opening, copying, and sharing are supported.
- Existing component library and design-token conventions.

## 14. Acceptance Criteria

The design system is ready for implementation when:
- Token names and values are reviewed.
- Core components and states are specified.
- Accessibility requirements are testable.
- Responsive rules are documented.
- Components align with approved application flows.
- Existing code conventions have been reviewed.
- Brand and scope decisions are recorded.
- Design QA is completed against representative screens.

**Status:** Proposed System — Owner Review Required.
