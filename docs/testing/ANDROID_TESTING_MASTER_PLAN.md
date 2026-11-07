# MyFarmAI — Android Testing Master Plan

Status: **ACTIVE** (created 2026-11-08). Companion docs:
`ANDROID_TEST_RESULTS.md` (defects + evidence), `ANDROID_DEVICE_COMPATIBILITY.md`.

## Goal

MyFarmAI must work as a smartphone-first agricultural AI app on budget,
mid-range and premium Android devices, under real network conditions
(good Wi-Fi, slow mobile data, intermittent connectivity), with Hindi and
English experiences, offline access to saved data, and no silent failure.

## Test environment (actual, 2026-11-08)

| Tooling | State |
|---|---|
| Android SDK (`ANDROID_HOME=/data/Android/Sdk`) | **MISSING** (directory absent) — no adb, no sdkmanager, no emulator |
| JDK | OpenJDK 25 **JRE-only** (no javac) — local `gradle` builds impossible |
| Node / npm | v24.22.1 / 11.19.1 ✅ (Metro/Expo tooling runs) |
| Emulator | **BLOCKED** — no SDK images AND host has ~1.9 GiB free RAM (emulator typically needs 2–4 GiB) |
| Physical device | None connected / none assumed |
| EAS cloud build | Viable path (profiles exist in `eas.json`) — requires owner's Expo account authorization |

Strategy implication: Phase A–B (audit) and static/unit-level testing are
authoritative here; on-device functional testing (Phase C/D) is gated on an
SDK install or a physical device or EAS CI runners.

## Phases

| Phase | Scope | Status |
|---|---|---|
| A Environment discovery | host tooling inventory | DONE 2026-11-08 |
| B Application audit | screens, API, auth, storage, a11y, security | DONE 2026-11-08 (14 findings, see results doc) |
| C Emulator validation | low/mid/high profiles, sequential only | BLOCKED (no SDK, no RAM headroom) |
| D Functional testing | onboarding → chat → farms → weather → voice | PARTIAL (unit/contract level only) |
| E Offline & sync | persistence, restore, freshness | PARTIAL (unit level) |
| F Performance | bundle size, startup, memory | PARTIAL (bundle measured 4.6 MB; startup/memory need a device) |
| G Security audit | tokens, secrets, logging, isolation | PARTIAL (static audit clean; runtime needs device) |
| H Release readiness | build/install/verify artifacts | BLOCKED locally; EAS path proposed |
| I Final report | consolidated findings | see results doc |

## Frameworks

Use the project's own gates first: `npm run typecheck`, `npm run lint`,
`npm test` (jest-expo, added 2026-11-08). Do NOT add Detox/Maestro
unnecessarily — E2E frameworks pay off only once an emulator/device path
exists.

Test placement: `src/**/__tests__/*.test.ts[x]`, pure-logic suites
(config contracts, ID generation, friendly-error mapping). React-rendering
tests are intentionally avoided in the first pass (jest-expo render
mocking adds surface area without a device to verify runtime parity).

## Defect process

Every defect gets: ID, screen/feature, repro steps, expected, actual,
severity, root cause, fix, verification evidence — recorded in
`ANDROID_TEST_RESULTS.md`. IDs: `AND-<number>`.

## Non-goals / safety rules

- Never delete real user data; synthetic accounts only.
- Never upload/record audio without explicit user interaction.
- Never weaken security to make a test pass.
- No large SDK/OS installs without owner approval (HDD-First Policy,
  `/data/Android/Sdk` is the destination if approved).
