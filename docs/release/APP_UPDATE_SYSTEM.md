# MyFarmAI App Update System

**Status:** Implemented (v1.0.0, 2026-11-09)

## Design

The Android app performs a **non-intrusive update check** on launch and in the
settings screen. It never silently downloads or installs anything.

Flow:
1. Read the **installed version** (`BuildConfig.VERSION_NAME` / `expo-application`).
2. Fetch release metadata over **HTTPS** from the official backend endpoint
   `GET /api/v1/app-updates/latest` (stable public API, unauthenticated).
   Fallback source (configurable): the GitHub Releases API for
   `github.com/shubhamown01/MyFarmAI` (`releases/latest` asset metadata).
3. Compare installed vs latest using MAJOR.MINOR.PATCH.
4. Classify per the metadata:
   - `optional` — update available, user may continue using the app.
   - `recommended` — nag badge + one-time dialog on opening a relevant screen.
   - `critical` — blocking dialog once per version install; user can always
     choose "Review" then continue (the app remains usable offline/AI-without-update).
   - `minimum_supported_version` — if installed < this value, features that
     need newer server contracts show a clear "please update" screen (app
     still opens). No forced kill.
5. Show **latest version + release notes** (from the metadata body).
6. Button **"Open download page"** opens the official GitHub Releases URL in
   the system browser (never an in-app silent download).
7. User hand-installs: Android will ask to allow installing from the browser
   (Chrome) — "Install unknown apps" permission. Documented in release notes.
8. After update, re-open shows the new version in the About screen, and the
   update dialog disappears.

## Failure modes

- The check **never blocks app startup**: network errors, GitHub/backend
  downtime, or a malformed metadata response result in "no update check made"
  (silent). The app fully works without it.
- Response is validated against a version-pattern and cached max-age
  (metadata ignored if stale or impossible, e.g. clearly a downgrade).
- Rollback communication: release notes may include a "rollback" section and a
  pointer to `docs/release/ROLLBACK_PROCEDURE.md` (kept for reference by the
  support/operator side).

## Backend endpoint contract (implemented)

`GET /api/v1/app-updates/latest`

```json
{
  "latest_version": "1.0.0",
  "minimum_supported_version": "0.9.0",
  "severity": "optional|recommended|critical",
  "release_notes_url": "https://github.com/shubhamown01/MyFarmAI/releases/v1.0.0",
  "download_url": "https://github.com/shubhamown01/MyFarmAI/releases/latest",
  "published_at": "2026-11-09T…"
}
```

(Values are served from the backend's release configuration; if no metadata
is configured, the endpoint returns the current backend release version with
`severity: "optional"`.)

## Where implemented

- Backend: `backend/app/api/v1/app_updates.py`, service `app/services/app_updates.py`
  (reads `VERSION`, `docs/release/RELEASE_HISTORY.md` not required at runtime).
- Android: `update` module (`android/app/src/main/java/.../update/`),
  registered from `App` when the app is foregrounded and from the Settings
  screen "Check for updates" button.

## Privacy

The update check sends no user data — only a plain GET. No telemetry identifiers
are transmitted.
