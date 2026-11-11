# MyFarmAI — Public Download Page

**Document ID:** MYFARMAI-REL-015
**Version:** 1.0
**Date:** 2026-11-11
**Page source:** `web/src/app/download/page.tsx`

## 1. Purpose

One canonical page that an ordinary visitor can use to reach the web app and the
official Android build, verify what they downloaded, and find support and legal
information.

## 2. Canonical URLs

| Item | URL | Live status 2026-11-11 |
|---|---|---|
| Canonical download page | `https://myfarmai-web-zwpytbwu.onslate.in/download` | **NOT LIVE** — route exists in the repo only; the deployed bundle predates it |
| Interim public entry point | `https://myfarmai-web-zwpytbwu.onslate.in/landing` | **LIVE**, HTTP 200 |
| Web app (sign-in) | `https://myfarmai-web-zwpytbwu.onslate.in/auth/login` | LIVE, HTTP 200 |
| Direct APK | `https://github.com/shubhamown01/MyFarmAI/releases/download/v1.0.0/app-release.apk` | **LIVE**, HTTP 200, 67,884,479 B, SHA-256 verified |
| Release page | `https://github.com/shubhamown01/MyFarmAI/releases/tag/v1.0.0` | LIVE |
| Support | `https://github.com/shubhamown01/MyFarmAI/issues` | LIVE |

`/download` is written to be fully static — no API call, no auth — so it keeps working
when the backend or the AI provider is unavailable. That is deliberate: a download page
must not depend on the service it distributes.

## 3. Required content and where it comes from

| Requirement | Implementation |
|---|---|
| Product name and branding | Header with the MyFarm AI wordmark and seedling mark |
| Short description | One-sentence product summary under the heading |
| Web app launch link | `/auth/login` |
| Android APK download link | Direct GitHub release asset URL |
| Current version and release date | `1.0.0`, 10 November 2026 |
| APK SHA-256 checksum | `352020c56819c9349e139204692c4a01ba21ca4a8401a6601f5ef4072192c465` |
| Supported Android requirements | Android 6.0 (API 23) or newer; package `com.myfarmai.android` |
| Installation instructions | Four numbered steps, including the unknown-sources path |
| Release notes and known limitations | "Known limitations" section, see §5 |
| Privacy policy and terms links | `/legal/privacy`, `/legal/terms` |
| Support / feedback contact | GitHub Issues |
| Update instructions | "install the newer APK over the existing app — your data is preserved" |

## 4. Checksum publication

The checksum is embedded as a constant in the page. It must be updated in the same
commit that changes the APK. The value was re-verified on 2026-11-11 by downloading the
public asset and hashing it:

```
352020c56819c9349e139204692c4a01ba21ca4a8401a6601f5ef4072192c465  app-release.apk
67884479 bytes
```

The value matches `docs/release/v1.0.0.sha256` and the GitHub asset digest. It does **not**
match the older `631112be…` figure still quoted in parts of
`docs/release/V1.0.0_RELEASE_CHECKLIST.md`; that section has been corrected.

## 5. What the page deliberately does not claim

The page states the current limitations instead of advertising blocked features:

- Self-registration needs emailed verification codes, and email delivery is not enabled
  on the hosted deployment.
- The hosted deployment runs with the local AI model disabled, so the assistant and
  research report themselves unavailable.
- No Play Store listing; sideload only.
- No push notifications.
- No in-app update checker yet.

This is intentional. A download page that advertises features the deployment cannot
serve is worse than one that is honest about them.

## 6. Verification

| Check | Result |
|---|---|
| Page renders without a backend | By construction — no fetch, no auth, no dynamic import |
| Route builds | `npm run build` — route present in the build output |
| Typecheck / lint | clean |
| Live reachability | **NOT TESTED** — the route is not deployed (no deployment path from this host) |

## 7. Owner action required

Deploy the current `phase-01-foundation` tree to the Slate app from an authenticated
machine, then re-check `/download`. Until then the interim entry point is `/landing`,
which links to this page and to the GitHub release.
