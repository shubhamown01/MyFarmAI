# MyFarmAI Versioning Policy

**Status:** Adopted (v1.0.0 preparation, 2026-11-09) · **Applies to:** Android app, web dashboard, backend

## Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR** — breaking change: incompatible API, data model, or installation boundary (e.g. a breaking schema change with no auto-migration, or a new application ID).
- **MINOR** — backward-compatible feature: new screens/endpoints, new settings, additive API fields.
- **PATCH** — bug fix or security fix with no functional surface change intended for users.
- Pre-release suffixes (`-rc.1`, `-beta.1`) may mark release candidates; a tag without a suffix is a stable release.

## Single source of truth

`/data/MyFarmAI/VERSION` (plain text, one line, e.g. `1.0.0`) is authoritative for
the application version. All release tooling reads it.

## Synchronized manifests

Every release must have identical `MAJOR.MINOR.PATCH` across:

| Surface | File | Field |
|---|---|---|
| Android (Expo) | `android/app.json` | `expo.version` (versionName) |
| Android (native) | `android/android/app/build.gradle` | `versionName`, `versionCode` (monotonic int) |
| Web | `web/package.json` | `version` |
| Backend | `backend/pyproject.toml` | `project.version` |
| Git | `CHANGELOG.md` entry | version heading |
| Git | tag `v<MAJOR>.<MINOR>.<PATCH>` | tag name |

## Rules

1. **versionCode** is a monotonically increasing integer. Start at `1` for
   `versionName "1.0.0"`. Suggested mapping: `MAJOR*10000 + MINOR*100 + PATCH`
   (so `1.1.0` → `10100`); a resigned re-upload of the same version must
   increment versionCode even when versionName is unchanged.
2. The Android **application ID stays `com.myfarmai.android`** for all
   `1.x` releases. Changing it breaks upgrade-in-place for existing installs
   (new app next to the old one) — MAJOR decision, owner approval required.
3. Release tag names always carry the `v` prefix (`v1.0.0`).
4. No stable tag is created before: release gates pass, owner approval, and
   (for publication) the signed artifacts are checksum-verified.
5. A release commit chain runs: bump manifests → run gates → tag → build →
   verify signature/checksum → publish. Tag content is immutable; a bad tag is
   deleted only if nothing was published from it, otherwise the fix ships as a
   new PATCH.
