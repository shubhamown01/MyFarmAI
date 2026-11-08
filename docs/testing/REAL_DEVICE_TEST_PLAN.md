# MyFarmAI — Real Device Test Plan (Android)

Status: checklist defined; **on-device pass pending phone pairing** (see
`ANDROID_TESTING_MASTER_PLAN.md` for the build + adb recipe). Update
`TEST_RESULTS.md` gate F/G as evidence lands.

## Installation
| # | Step | Expected | Result |
|---|---|---|---|
| 1 | `adb install -r app-release.apk` | `Success` | ⬜ |
| 2 | Launch icon `MyFarm AI` | cold start < 5 s, no crash | ⬜ |
| 3 | `adb shell dumpsys package com.myfarmai.android \| grep versionName` | `1.0.0` | ⬜ |

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
| 12 | Voice input button | permission prompt → works | ⬜ |
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

## Stall-risk notes for the tester (already handled elsewhere)
- Manual/user login must be done by the owner (no SMTP yet).
- `adb pair` (wireless) needs the 6-digit code on screen — Android 11+.
- `adb install -r` requires owner approval per-phone (theoretically every
  partner assignable install pop-up).
