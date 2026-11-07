# Licensing Decision Records — Open-Meteo & SearXNG

Status: **Decision record — OWNER-APPROVED 2026-11-03** (both D-1 and D-2
marked APPROVED-conditional by the owner in the approval gate of this date).

## D-1 Open-Meteo free API (weather data)

Status: **APPROVED by owner 2026-11-03** (conditional).

**Facts** (official Terms page, open-meteo.com/en/terms, fetched 2026-11-03):
- Free/Open-Access API: **non-commercial use only**, CC-BY 4.0 attribution.
- Hard limits: 10,000 calls/day, 5,000/h, 600/min (300,000/mo).
- "Non-commercial use" defined by the terms as referencing the Creative
  Commons NonCommercial interpretation. Official qualifying examples:
  *private or non-profit websites or apps that do not have subscriptions or
  advertising*; voluntary tip-jar donations ARE permitted. Disqualifying:
  subscriptions or displayed advertisements, commercial products/promotions.
- Commercial use requires a paid plan (API Standard/Professional).

**MyFarmAI's usage**: backend `app/core/config.py` default
`https://api.open-meteo.com/v1/forecast` — weather advisory for the farmer's
own farms.

**Decision proposed**: Continue using Open-Meteo's free tier **only while**
MyFarmAI remains free with no subscriptions and no advertising (₹0 policy
already forbids monetization). Record CC-BY 4.0 attribution in the
production UI's data-source notice. Trigger: if the owner ever monetizes the
app (subscription/ads), the Open-Meteo API plan becomes a cost line and
alternatives (e.g., self-hosted WMO data, national met services' open APIs)
must be evaluated BEFORE launch. Limits headroom at first are enormous
(weather simply does not need 10k calls/day at our scale).

**Consequence if approved**: Phase-0 "Open-Meteo non-commercial licensing"
gate CLOSED (conditional: no monetization + attribution). Add an
attribution line "Weather data by Open-Meteo (CC-BY 4.0)" to the frontend
weather UI before any public exposure.
**→Executed 2026-11-03**: the attribution note with a linked
open-meteo.com URL is rendered in both weather surfaces
(`web/src/components/Dashboard/FarmIntelligence.tsx` Weather card and
`web/src/components/Weather/WeatherCard.tsx`); all web gates green on the
change (typecheck, 40/40 jest tests, lint, build).

## D-2 SearXNG (AGPL-3.0) self-hosted search

Status: **APPROVED by owner 2026-11-03** (conditional).

**Facts** (verified in repo, 2026-11-03):
- Phase-0 finding "hardcoded SearXNG secret" is **already remediated**:
  commit `97f913e` externalized the secret to the environment; current
  `infra/searxng/config/settings.yml` reads `${SEARXNG_SECRET}`.
- Usage: `backend/app/services/research.py` calls the self-hosted SearXNG
  over HTTP (`searxng_base_url` config). Backend is **unmodified** upstream
  SearXNG (no source changes), runs in this project's own infra.

**AGPL-3.0 obligations (unmodified deployment)**:
1. Running SearXNG publicly: the AGPL network-use clause (§13) requires
   offering the running version's source code to its network users. Since
   the deployment is unmodified, providing a link to the exact upstream
   SearXNG commit/tag satisfies this — record the deployed tag in
   `infra/searxng/VERSION.md` (to create) at deploy time.
2. If we ever modify SearXNG configs only (settings.yml counts as config,
   not source), the source-offering duty does not attach to configs, but
   the honest default remains: document the exact upstream version.
3. Internal-only use (backend service on a private/loopback network, not
   user-facing) carries no additional user-facing beyond-preserving duty.

**Decision proposed**: Permit SearXNG via these conditions:
- SearXNG stays **internal** (reachable by the backend only), never
  exposed directly to public internet traffic through a public host.
- If that ever changes, record the upstream tag and add the source link to
  the public-facing notice before exposing.
- Keep the secret in environment injection (already done).

**Consequence if approved**: Phase-0 "SearXNG AGPL-3.0" gate CLOSED
(conditional). The two §5 items in `PRODUCTION_SECURITY_CHECKLIST.md`
(SearXNG review, Open-Meteo decision) can then be checked with this
document as evidence.

## Overall

Both gates **CLOSED-conditional by owner approval, 2026-11-03**: no spend, no
code change, and the conditions align with existing ₹0 + internal-first
architecture. Outstanding execution items: the Open-Meteo attribution line
in the frontend weather UI (go-live), and the `infra/searxng/VERSION.md`
upstream-tag note (only if SearXNG is ever exposed publicly).
