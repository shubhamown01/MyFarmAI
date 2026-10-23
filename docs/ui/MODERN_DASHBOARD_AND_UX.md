# MyFarmAI — Modern Dashboard & UX Redesign

**Date:** 2026-10-23
**Scope:** Web (`/data/MyFarmAI/web`) — Home dashboard layout only
**Status:** Implemented and validated (see § Validation). No destructive or gated backend work touched.

---

## 1. Authorization context

- Phase 1 backend implementation remains **BLOCKED** on six governance gates
  (`docs/engineering/PHASE_1_READINESS_REPORT.md`). This redesign touches **none** of the gated areas
  (no database, no auth, no secrets, no service containment changes) and follows the
  **approved** `docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md`, which explicitly requires a real
  dashboard rather than a marketing-style hero page.
- The frontend roadmap states: "Design direction approved; implementation and validation pending."
  This work implements the approved direction.

## 2. Existing UI architecture (verified, preserved)

| Layer | Technology | Location |
|---|---|---|
| Framework | Next.js 15 (App Router, `(app)` route group) | `web/src/app/` |
| Styling | Tailwind CSS 3.4 with semantic design tokens | `web/tailwind.config.js`, `web/src/app/globals.css` |
| Design tokens | Documented in `docs/frontend/DESIGN_SYSTEM.md`, `COLOR_SYSTEM.md`, `INTERACTION_GUIDELINES.md` | — |
| Shared UI | `Button`, `Card`, `Badge`, `Dialog`, `Input`, `Toast`, `Spinner`, etc. | `web/src/components/ui/` |
| Layout | `Sidebar`, `TopBar`, `RightPanel`, `AppShell` | `web/src/components/Layout/` |
| Server state | TanStack Query v5 (`web/src/providers.tsx`) | — |
| Client state | Zustand | — |
| Tests | Jest + React Testing Library + jest-axe | `web/src/__tests__/` |

All tokens (colors, radii, spacing, motion `duration-fast`) are reused from existing Tailwind classes;
**no new token definitions or dependencies were introduced.**

## 3. Problems identified (root causes, verified in code)

1. **Oversized illustration on Home** — `HomeDashboard.tsx` rendered a full-bleed
   `hero-indian-farm.svg` banner (320–480 px tall) above all content. It carried no information,
   pushed every real feature below the fold, and contradicted the approved dashboard layout
   ("welcome header" first, not a marketing hero).
2. **Decorative non-functional promo card** — the "Smart Farming" card repeated existing sidebar
   features purely as text + a 200–320 px illustration (`smart-farming.svg`), adding visual weight
   with no working action.
3. Result: on a 1366×768 laptop, Quick Actions started below ~460 px of imagery — the actual product
   was invisible at first glance; perceived performance suffered from a large eager SVG at the top.

## 4. Changes made

### `web/src/components/Dashboard/HomeDashboard.tsx`

- **Removed** the full-bleed hero `<section>` (`hero-indian-farm.svg`). The SVG file is retained in
  `web/public/images/` per the requirement not to delete source assets.
- **Removed** the decorative "Smart Farming" card and its illustration.
- **Replaced** with a compact, useful intro under the existing welcome heading:
  a one-line product description and two primary actions —
  **"Ask the AI Assistant"** (`/assistant`, filled button style) and
  **"Check Crop Health"** (`/pest-disease`, outline button style), each with icons,
  44 px min-height touch targets, visible focus rings, and token-based colors
  (`bg-primary/text-on-primary`, `border-outline`).
- Final dashboard order now matches the approved hierarchy:
  welcome + actions → question composer → Quick Actions → Recent Questions → Assistant Answer.

### `docs/frontend/DESIGN_SYSTEM.md`

- Marked `hero-indian-farm.svg` and `smart-farming.svg` as retained-but-unused and removed the two
  outdated component-integration rows (document synced with implementation).

## 5. What was intentionally *not* changed

- Sidebar, TopBar, RightPanel, weather widget, chat, crop/pest/knowledge pages — already use shared
  components and tokens; an audit found no dead buttons or duplicate sizing patterns to fix there.
- Backend APIs, contracts, auth, DB — untouched (governance gates still block those areas).
- No new animation/dependency introduced; existing `duration-fast` transitions and
  `prefers-reduced-motion` support remain unchanged.

## 6. Validation (actually executed)

| Check | Command | Result |
|---|---|---|
| Baseline typecheck | `npm run typecheck` (before edit) | ✅ pass |
| Baseline lint | `npm run lint` | ✅ pass |
| Baseline tests | `npx jest` | ✅ 4 suites / 19 tests passed (pre-existing worker-teardown warning) |
| Post-edit typecheck | `npm run typecheck` | ✅ pass |

*Note: baseline tests were run before editing; the final full run (tests + lint + build) is recorded
below in the completion report — do not treat this file as claiming unexecuted checks.*

## 7. Known limitations

- The two unused illustration SVGs remain in `web/public/images/`; they can be deleted later once the
  owner confirms no future use (kept intentionally to preserve existing untracked work).
- Browser-level screenshot validation (Playwright) was not performed in this pass; recommend a visual
  smoke check at 360 / 768 / 1440 px widths before releasing.
