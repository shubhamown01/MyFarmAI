# MyFarmAI — Android Test Results (2026-11-08)

Companion: `ANDROID_TESTING_MASTER_PLAN.md` (phases + strategy),
`ANDROID_DEVICE_COMPATIBILITY.md` (device matrix).

Evidence baseline: commits `213fe80`, `0db8281` — typecheck ✅, lint ✅,
jest **16/16 ✅** (API contract, makeId, friendlyChatError),
`npx expo export --platform android` → Hermes bundle **3.9 MB** ✅
(4.6 MB before the 5-dep prune).
On-device runtime verification NOT YET PERFORMED (no SDK/emulator; JDK is
JRE-only): everything below marked "static/unit" explicitly carries that
limitation.

## Defect table

| ID | Severity | Area | Finding | Root cause | Fix | Verified |
|---|---|---|---|---|---|---|
| AND-001 | Critical | Build/bundle | Metro crashed at startup: `Cannot find module react-native-svg-transformer` | `metro.config.js:11` required a package never installed; nothing in src/ uses SVG | Removed transformer block; svg stays an asset ext | unit/static: `expo export` succeeds ✅ |
| AND-002 | Critical | Boot | App rendered nothing on start | `package.json` main = `expo-router/entry`, but the project has no `app/` routes; `src/App.tsx` (react-navigation) was unreachable | `main` → `index.js`, `registerRootComponent(App)` | unit/static (export resolves entry) ✅; runtime boot ⏳ |
| AND-003 | Critical | Build/test infra | No `babel.config.js` — broke jest AND Metro flow stripping | Standard Expo config missing | Added `babel-preset-expo` babel.config.js | jest runs, export runs ✅ |
| AND-004 | High | Export/config | `PluginError: "expo-speech" does not contain a valid config plugin` | `app.json` listed `expo-speech` (ships no plugin) and dead `expo-router` in plugins | Removed both from plugins; `expo-speech ~12.0.2` confirmed correct for SDK 51 via `bundledNativeModules.json` | `expo export` succeeds ✅ |
| AND-005 | High | Runtime/chat | `crypto.randomUUID()` crashes on Hermes (no WebCrypto) — first chat send likely fatal | Hermes lacks browser crypto global | New `src/utils/id.ts` `makeId()` (v4-formatted, non-crypto — IDs are correlation IDs, backend stores `String(100)`); used in ApiClient + useChat | unit: format/uniqueness/length tests ✅; on-device ⏳ |
| AND-006 | High | Test infra | `npm test` failed (`jest: not found`) | Script declared, dependency absent | jest-expo@~51.0.4 + jest@~29.7 devDeps, jest.config.js, first suites | 6/6 pass ✅ |
| AND-007 | High | UX/errors | Chat errors never visible: `useChat.error` set but never rendered; raw `code: message` text | ChatInterface destructured only messages/isLoading/speak | Friendly per-code mapping (offline / session expired / rate limit / quota / AI busy) + dismissible live-region banner | unit: gates green; UI on-device ⏳ |
| AND-008 | High | Offline/history | Conversation cache never wired: `src/storage/conversations.ts` imported nowhere; history lost on restart | Feature was built but never integrated into useChat | Restore-on-mount (most recent thread), persist-after-exchange, 200-message cap per thread (SecureStore ~2 MB ceiling), failures swallowed | unit: gates green; runtime persist/restore ⏳ |
| AND-009 | High | Auth | Refresh token stored but never used; expiry forced full re-login | No refresh flow in client | 401 → exchange refresh token once (`/api/v1/auth/token/refresh`) → rotate both tokens → single retry; clear on failure; `_allowRefresh` guard blocks recursion | static ✅; rotation against real login ⏳ (needs a session) |
| AND-010 | Medium | A11y | Chat screen had zero accessibility props; 44dp targets; emoji-only mic | Omissions | Roles/labels on mic/send/header buttons, `accessibilityState`, 48dp targets | static ✅; TalkBack ⏳ |
| AND-011 | Medium | UX/voice | Every assistant reply auto-spoke (hi-IN) with no off switch | Unconditional `speak()` effect | Header toggle 🔇 Off (default) / 🔊 On; effect gated | static ✅ |
| AND-012 | Medium | Product | Weather hardcoded to Delhi (28.6139, 77.2090); `expo-location` absent although `app.json` declares FINE/COARSE location permissions; chat `weatherContext` always null | Location never implemented despite permission | OPEN — decision needed: add expo-location (≤17.0.1 per bundledNativeModules) or drop the unused permission. NOT changed in this pass | n/a |

## Journey inventory (from Phase B audit)

Present: dashboard sign-in/out, AI chat (voice in/out), crop plans CRUD +
tasks, weather, resources list.
Missing (gap list, not defects of shipped code): onboarding flow,
register/OTP (sign-in only since backend admin-creates users), farm
creation, chat history list UI, settings, dark-mode toggle (theme supports
it), splash handling beyond static image — all consistent with
backend ADR-008 admin-created accounts; onboarding belongs to the web app.

## Test-case ledger (executed)

| # | Case | Result |
|---|---|---|
| T1 | `npm run typecheck` | PASS (clean) |
| T2 | `npm run lint` | PASS (0 errors/0 warnings) |
| T3 | jest: api.ts URL contract (single `/api/v1`, emulator fallback, /health special case) | PASS |
| T4 | jest: makeId format v4 / 1000-call uniqueness / ≤36 chars | PASS |
| T5 | `expo export --platform android` bundle build | PASS (Hermes hbc emitted) |
| T6 | Rate-limit spoof-resistance of the API the app talks to (live staging) | PASS (429 w/ spoofed XFF, 2026-11-07) |
| T7 | Android client↔staging OpenAPI contract (14 endpoints) | PASS (no drift, 2026-11-07) |
| T8 | On-device cold start / chat / voice / refresh rotation | NOT RUN — blocked (no device/SDK) |

## Open items

1. AND-012 location decision (owner).
2. SDK install landed 2026-11-08 (`/data/Android/Sdk`, 458 MB — see
   `ACCOUNT_SETUP_LOG.md`); remaining Phase C gates: a physical device or
   emulator (RAM-blocked), and a JDK for Gradle builds (SSD permission gate).
3. On-device pass: boot, login, chat incl. 429/refresh paths, voice
   permissions, restart persistence.
