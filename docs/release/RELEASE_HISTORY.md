# Release History

## v1.0.0 — first stable public release

- **Date:** 2026-11-10 (published)
- **Tag:** `v1.0.0` — created 2026-11-10T16:53:56Z, release is public (`isDraft: false`),
  assets: `app-release.apk` (67,884,479 B, SHA-256
  `352020c56819c9349e139204692c4a01ba21ca4a8401a6601f5ef4072192c465`),
  `app-release.apk.sha256`, `v1.0.0.sha256`. Anonymous download verified.
  The pre-publication RC build (`631112be…e112`, 67,884,524 B) was replaced by
  the version-fix rebuild before publication; its hash is retained in
  `V1.0.0_RELEASE_CHECKLIST.md` as history and is not the shipped artifact.
- **Application ID:** `com.myfarmai.android`
- **versionName / versionCode:** `1.0.0` / `1`
- **Backend deployment:** `prod-c63d3963-v2` (version-fix + signed APK; live-verified)

### Highlights
- Auth: email-OTP registration/login, opaque session cookies (Argon2id, refresh rotation) — first version published publicly.
- Farmer profile, farms/land plots, crop plans, weather (Open-Meteo), research (SearXNG, AGPL-3.0 reviewed).
- AI chat (Qwen via per-user quota-gated cloud metadata; only production HTTPS API exposed — local Ollama never public).
- Public APK download from the backend route and (after publication) GitHub Releases (`/releases`).
- Feedback (bug/feature/question/praise) — anonymous submission, optional reply email; schema live in Neon prod (migration `f4b2c3d4e5a7_fb_feedback1`).
- Update-check endpoint (`GET /api/v1/app-updates/latest`) for the Android in-app "Check for updates" flow.
- Security: ENVIRONMENT=production, ALLOWED_HOSTS/CORS/Secure-cookie, `TRUSTED_PROXY_CIDRS`, rate limits, CSRF middleware.

### Known limitations
- Google Play publication not done (owner decision; Play registration fee is NOT ₹0).
- OTP delivery for new-user registration currently requires dev-mode SMTP gating (test accounts); real SMTP pending owner's decision.
- On-device (F/G real-phone) verification pending owner phone pairing as of v1.0.0 RC-1.
- Full pg_dump backup automation pending; documented manual procedure only.

See `../testing/TEST_RESULTS.md` for per-gate evidence.
