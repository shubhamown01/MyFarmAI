# MyFarmAI — Real Device Test Plan (Android)

Status: checklist defined; **on-device pass pending phone pairing** (see
`ANDROID_TESTING_MASTER_PLAN.md` for the build + adb recipe). Update
`TEST_RESULTS.md` gate F/G as evidence lands.

Verified APK (2026-11-11): `android/android/app/build/outputs/apk/release/app-release.apk`
— 67,884,479 bytes, SHA-256 `352020c56819c9349e139204692c4a01ba21ca4a8401a6601f5ef4072192c465`,
signer `CN=MyFarmAI Release`, versionName `1.0.0`. The live download endpoint
(`GET /api/v1/downloads/app-release.apk`) returns this identical binary.

## Prerequisites
| # | Check | Expected |
|---|---|---|
| 0a | `adb devices -l` | one device in `device` state (not `unauthorized`) |
| 0b | USB debugging + RSA fingerprint accepted on phone | yes |
| 0c | Android version | 6.0+ (minSdk 23) |
| 0d | Build-time `EXPO_PUBLIC_API_BASE_URL` | points at the live backend (not the `api.myfarmai.example.com` placeholder) |

## Already verified statically (do not repeat)
The release APK was audited with `apkanalyzer` on 2026-11-11; these need no
device re-check:
- `versionName 1.0.0`, `versionCode 1`, `minSdk 23`, `targetSdk 34`
- not debuggable; cleartext HTTP blocked by default; OTA updates disabled
- only `MainActivity` is exported; all providers/activities are `exported="false"`
- shipped bundle contains the real backend URL (`…catalystappsail.in`), not the
  `api.myfarmai.example.com` placeholder
- auth tokens and conversations live in Keystore-backed `expo-secure-store`
- `allowBackup="true"` and unused `myfarmai://` deep links are known hardening
  items for v1.0.1 (MFAI-018/020) — not device blockers

## Installation
| # | Step | Expected | Result |
|---|---|---|---|
| 1 | `adb install -r app-release.apk` | `Success` | ⬜ |
| 2 | Launch icon `MyFarm AI` | cold start < 5 s, no crash | ⬜ |
| 3 | `adb shell dumpsys package com.myfarmai.android \| grep versionName` | `1.0.0` | ⬜ |
| 3b | `sha256sum` on pulled APK | matches `352020c5…` | ⬜ |

## Authentication
| # | Step | Expected | Result |
|---|---|---|---|
| 4 | Login with tester account | dashboard loads | ⬜ |
| 5 | Wrong password | inline error, no crash | ⬜ |
| 6 | Kill app → reopen | session persists | ⬜ |
| 7 | Settings → Log out | returns to login; relogin works | ⬜ |

## Core features
| # | Step | Expected | Result |
|---|---|---|---|
| 8 | Send chat question | answer with sources; quota shown | ⬜ |
| 9 | 21st chat message in window | friendly quota error | ⬜ |
| 10 | Weather with location | data renders | ⬜ |
| 11 | Crop plans | list renders | ⬜ |
| 12 | Voice input button | permission prompt → works (client-platform STT, not the contained `ai/voice` service) | ⬜ |
| 13 | Camera/image analyze | permission prompt → works | ⬜ |

## Network & resilience
| # | Step | Expected | Result |
|---|---|---|---|
| 14 | Airplane mode ON mid-chat | error banner, no crash | ⬜ |
| 15 | Airplane mode OFF → resend | works again | ⬜ |
| 16 | Wi-Fi ↔ mobile-data switch | session lives through handover | ⬜ |

## Accessibility & UX
| # | Step | Expected | Result |
|---|---|---|---|
| 17 | TalkBack over login | both fields labeled | ⬜ |
| 18 | Font scale 1.3× | no clipped UI | ⬜ |
| 19 | Low-memory device (RAM ≈ 2–3 GB free) | app survives | ⬜ |

## Capture for every failure
`adb logcat -d -s MyFarmAI:V AndroidRuntime:E` + screenshot + step number.

## Results log
| Date | Device / Android | Tester | Pass/Fail counts | Notes |
|---|---|---|---|---|
| — | pending device | — | — | — |

## Stall-risk notes for the tester (already handled elsewhere)
- Manual/user login must be done by the owner (no SMTP yet).
- `adb pair` (wireless) needs the 6-digit code on screen — Android 11+.
- `adb install -r` requires owner approval per-phone (theoretically every
  partner assignable install pop-up).
