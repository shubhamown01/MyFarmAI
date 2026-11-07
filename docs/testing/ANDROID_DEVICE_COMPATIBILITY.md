# MyFarmAI — Android Device Compatibility

Status: WORKING DOCUMENT (2026-11-08). Runtime claims require on-device
verification (blocked — see `ANDROID_TESTING_MASTER_PLAN.md`). This doc
states what the **build configuration supports** and what must be verified.

## Build/compute identity

- React Native **0.74.0**, Hermes engine (JS bytecode) — the Hermes
  assumption has real consequences we fixed: no WebCrypto (`makeId()` util
  replaces `crypto.randomUUID()`).
- Expo SDK 51, **old architecture** (SDK 51 default; no `newArchEnabled`).
- Managed workflow (no native `android/` dir) — permissions come from
  `app.json` only.
- Package id `com.myfarmai.android`; EAS profiles: development (dev
  client), preview (APK), production (AAB).

## Device matrix plan (to execute when a device/emulator path exists)

| Profile | RAM tier | Emulator AVD equivalent | Focus |
|---|---|---|---|
| Low-end | 2–3 GB | medium 720p x86-64 phone skin, `hw.ramSize=2048` | Cold start, chat memory, image-heavy resources list, thermal |
| Mid-range | 4–6 GB | Pixel-mid 1080p skin, `hw.ramSize=4096` | Default journey, voice, map/large lists |
| High-end | 8 GB+ | modern skin, `hw.ramSize=8192` | Everything incl. long conversations, background/foreground cycles |

Sequential only — the host has ~7 GiB total RAM and cannot run multiple
emulators (and currently has none; ~1.9 GiB free makes even one AVD
marginal).

## OS coverage targets

- Android **8.0 (API 26)** floor candidate — Expo SDK 51 supports minSdk 23;
  confirm the real floor via device testing on the oldest available device.
- Target SDK comes from Expo SDK 51 toolchain (API 34); Play-policy check
  happens at release time.

## Known config-level compatibility notes

| Note | Impact | Source |
|---|---|---|
| Hermes lacks WebCrypto | Fixed via `makeId()`; do not reintroduce `crypto.randomUUID()` | AND-005 |
| SecureStore key/value ceiling ~2 MB per value | Conversation cap 200 msgs/thread (AND-008) | AND-008 |
| `ACCESS_FINE_LOCATION`/`COARSE_LOCATION` declared but unused | Over-requested permission — trim or implement (AND-012) | audit |
| Speech STT locale hi-IN default, no UI language switch | Hindi-first farmers OK; English users get Hindi voice prompts — selection is a gap (documented, audit Medium) | audit |
| Production API base URL is a build-time env (`EXPO_PUBLIC_API_BASE_URL`) | Staging URL works via env override; production URL pending domain decision D2 (Go-Live Runbook §1) | `EXPO_PUBLIC_API_BASE_URL` inlining behavior |

## Screen-factors to verify on device (checklist)

- [ ] Small display (~4.7"): dashboard cards, chat input row, crop planning tables
- [ ] Large text / font-scale 1.3–1.5: no clipped labels
- [ ] One-handed reach: primary actions in bottom half (chat input is bottom-anchored ✅)
- [ ] Portrait primary; landscape sanity for chat/resources
- [ ] Gesture vs 3-button nav: SafeAreaView correctness
- [ ] Dark mode: theme supports it, toggle missing (documented gap)
- [ ] Offline screens: status machine shows "offline" + retry (data-freshness timestamps still to verify)
