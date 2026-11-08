# MyFarmAI — Public Tester Guide

For external testers. **Prerequisite**: an account created by the project
owner, OR self-registration once OTP email is configured (currently blocked
— ask the owner for credentials).

## What you get

- **Web**: open `https://myfarmai-web-zwpytbwu.onslate.in/landing` on any
  phone or laptop browser. Log in, explore the dashboard, weather, crops,
  assistant chat.
- **Android**: download
  `https://myfarmai-backend-50047414881.development.catalystappsail.in/api/v1/downloads/app-release.apk`
  (65 MB, arm64 devices), allow install from that file, log in with the
  account credentials. The APK points at the same staging backend.

## Login
Use the credentials the owner shared (test account). Change nothing there
— multiple testers share staging accounts; do not delete seeded data.

## Testing checklist (what to poke at, ~30 min)
1. Land on `/landing` → links work, legal pages open.
2. Log in → dashboard loads; sidebar works on narrow screens.
3. Ask the assistant a question → expect an answer within ~60 s (cloud AI
   quota: 20 questions/rolling 10 h; the app shows remaining quota).
4. `/weather` (device location or enter a place) → data loads.
5. `/crops` → crop plans.
6. Settings → profile edit; Log out lands you on `/auth/login`.
7. Kill the web tab, reopen → login persists (session cookie).
8. Android: turn airplane mode on/off → app shows an error banner; sends
   fail while offline; recovers after reconnect.
9. Android: force-stop and reopen → conversation history restores.

## Known limitations in this build (do not report as bugs)
- New-user self-registration is temporarily disabled (email OTP path
  waiting on a real mail provider) — get an account from the owner.
- Feedback form not yet built — send bug reports with a screenshot and the
  phone/OS version to the project owner (WhatsApp/email used for tester
  coordination).
- Privacy policy and terms are marked DRAFT — fine for a test build.

## Data hygiene
Use synthetic data only (made-up farm names, sample crops). Don't put real
personal details into your profile beyond the minimum email/password.

## Support
Copy the short request-ID shown in error banners (if any) into your bug
report — it lets the owner find the exact server-side trace instantly.
