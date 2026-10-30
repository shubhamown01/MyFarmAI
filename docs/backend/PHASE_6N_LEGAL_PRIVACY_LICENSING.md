# Phase 6N — Legal, Privacy & Licensing Inventory

**Date:** 2026-10-31 · **Status:** INVENTORY + DRAFT REQUIREMENTS — **NOT legal advice; flagged items need qualified legal review before public operation.** Deployment jurisdiction assumed: India (per product docs' farmer focus) — confirm.

## 1. License inventory (shipped/runtime components)

| Component | License | Notes |
|---|---|---|
| MyFarmAI backend/web/android code | Owner's choice — **UNDECIDED (Phase 0 gate)** | A LICENSE file decision is still open; until chosen, "all rights reserved" applies by default |
| PostgreSQL | PostgreSQL License (permissive) | No obligations beyond notices |
| FastAPI / Pydantic / SQLAlchemy / httpx | MIT/BSD-style | Notices sufficient |
| Ollama | MIT | Notices |
| qwen3:0.6b, qwen3-vl:2b (runtime models) | Apache-2.0 (verify each model card) | Registry records license strings; commercial use OK per Apache-2.0 — **verify model cards** |
| SearXNG | **AGPL-3.0** | Used as a separate unmodified process over a network: AGPL source obligations apply to *SearXNG itself* (offer its source; you run it unmodified → upstream source satisfies this). Not viral to MyFarmAI code. Owner accepted 2026-10-31; **legal review flagged** |
| Open-Meteo | API terms — **free tier is non-commercial** | Owner accepted non-commercial terms 2026-10-31; if MyFarmAI ever monetizes, upgrade tier or switch provider |
| Next.js / React / React Native / Expo | MIT | Notices |

## 2. Privacy posture (what the system actually does — verified against code)

- **Collected:** email, full name (optional), preferred language; farm name/location text, optional coordinates (for weather); crop records; chat conversations (user + assistant messages); session records; audit events (ID-only descriptions — no coordinates logged).
- **Never collected/logged:** message content is not logged; farm coordinates never in logs/audit; images processed in memory only (never stored); audio never sent to the backend.
- **Cross-user isolation:** deny-by-default at repository/service level (verified by tests + security review).
- **Retention:** interim — conversations/farms retained until deletion or account action; **ADR-015 (retention policy) is owner-pending** — required before public launch.
- **Deletion:** farm deletion exists; user/account deletion flow is NOT implemented (flag: privacy requirement for launch).

## 3. Documents required before public operation (drafts needed)

1. **Privacy policy** — must state: data collected (above), purpose, retention (ADR-015), deletion rights, third parties (Open-Meteo receives coordinates to serve weather; SearXNG receives search queries; Ollama is local-only, no data leaves the host), contact.
2. **Terms of service** — including the critical **AI disclaimer**: responses are AI-generated, may be wrong; **never a substitute for professional agronomist/veterinary advice**; safety rules (no invented doses) are best-effort, not a warranty.
3. **Data retention policy** — blocked on ADR-015.
4. **User consent** — at registration: privacy policy + AI-limitations acknowledgment.
5. **Security contact** — owner email; incident process per PHASE_6I runbooks (no public disclosure without owner authorization).
6. **Android privacy disclosures** — Play Data Safety form + microphone permission rationale (client-side speech only, per ADR-016).

## 4. Flagged for qualified legal review

- AGPL-3.0 network-interaction interpretation for the specific SearXNG deployment shape.
- Open-Meteo non-commercial boundary vs any future monetization.
- India DPDP Act (Digital Personal Data Protection) applicability once operating publicly — consent notices, grievance officer.
- Final license choice for the MyFarmAI codebase itself (Phase 0 gate, owner decision).

**Do not launch publicly until items 1–5 exist and flagged items are reviewed.**
