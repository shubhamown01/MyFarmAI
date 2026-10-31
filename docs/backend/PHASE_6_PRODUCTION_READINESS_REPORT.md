# Report 2 — Phase 6 Production Readiness

**Date:** 2026-10-31 · **Executor:** OpenCode orchestrator (+ independent security-engineer, ai-ml-engineer, android-engineer subagents) · **Baseline commit:** `caa65b2` (chain: `7dafc8a`…`caa65b2`, all owner-approved commits)

## Verdict: PARTIAL — repo-ready; deployment track awaits owner decisions

Every workstream executable **without owner infrastructure decisions** is complete, tested, documented, and committed. No deployment action has been taken (per the no-deploy-without-approval rule). The three gating decisions are listed in §5.

## 1. Delivered in Phase 6 (all committed)

| Workstream | Status | Evidence |
|---|---|---|
| 6A Architecture review | COMPLETE | `PHASE_6A_ARCHITECTURE_REVIEW.md` — current/proposed topology, risk register |
| 6B Environment separation | VERIFIED | Production validator (CORS/DB-path/Ollama-URL/allowed_hosts), secrets hygiene, `.env` gitignored |
| 6C Backend hardening audit | COMPLETE — PASS WITH GAPS | `PHASE_6C_BACKEND_HARDENING_AUDIT.md` — 15 verified-PASS areas, no Critical/High; M2/L1/L2 **fixed with tests** (FCL-064); M1 = owner decision |
| 6D/6L Backup + restore drill | PRE-WORK COMPLETE — DRILL PASSED | `scripts/backup.sh` (UNscheduled) + isolated drill restored **14/14 tables** (FCL-066); activation gate = owner |
| 6E AI inference readiness | COMPLETE — PASS WITH GAPS | `PHASE_6E_AI_INFERENCE_READINESS.md` — chat production-ready; G1 registry bypass **fixed**; **G2 closed with live evidence** |
| 6F Web production build | COMPLETE (build path) | `output: standalone`, build + boot verified locally (200); Dockerfile deferred to hosting decision |
| 6G Android release audit | COMPLETE — PASS WITH GAPS | `PHASE_6G_ANDROID_RELEASE_AUDIT.md` — no keystore material in git; owner-side: keystore, versionCode, prod URL, device QA |
| 6H Monitoring | NOT STARTED | Requires something deployed to monitor |
| 6I Incident runbooks | COMPLETE | 10 runbooks, S1–S4 model |
| 6J CI | COMPLETE | `.github/workflows/ci.yml` — backend/web/android/compose gates; **no deploy jobs by design** |
| 6K Domain/TLS | BLOCKED | Needs hosting target + domain |
| 6M Production acceptance | BLOCKED | Needs all above |
| 6N Legal/privacy/licensing | COMPLETE (inventory) | Launch gated on 5 required documents + qualified legal review (AGPL, Open-Meteo, DPDP, codebase license) |

## 2. Live evidence (real calls, not simulations)

- **Vision:** `POST /api/v1/vision/analyze` → **200** from live `qwen3-vl:2b` (template-compliant observations/uncertainty/referral; no diagnosis). Cold-start 504 documented → warm before serving or `OLLAMA_TIMEOUT_SECONDS≥300`.
- **Research:** live SearXNG loopback container → `GET /api/v1/research` → **200**, verbatim URLs, UTC `retrieved_at`, official gov.in/TNAU domains ranked 1–2.
- **Backup/restore:** one-shot dump (integrity-checked) restored 14/14 tables in an isolated container.

## 3. Regression status (evidence)

- Backend: **192 passed, all checks passed** (`bash scripts/check.sh`) — includes 3 security fixes with tests from 6C.
- Web: build + standalone boot 200 (6F); last full web suite 19/19 (Report 1).
- Android: typecheck + lint PASS (6G audit).
- Known non-blocking: mypy 54 pre-existing errors (gate passes by design); in-memory rate limiter/lockout (single-host OK, revisit at scale-out — SEC-P5-03/6C-I1).

## 4. Honest gaps

1. **No production deployment exists** — nothing is exposed publicly, no TLS, no domain (by design; requires owner decisions).
2. **M1:** weather/resources endpoints are unauthenticated (Medium) — owner decision required before exposure.
3. **6N pre-launch documents** (privacy policy, ToS, retention via ADR-015, consent, security contact) do not exist yet — mandatory before public operation.
4. **ADR-016 (voice) and ADR-015 (retention) remain PROPOSED** — owner acceptance pending.
5. **Swap 100% full** on the host (6E-G7) — ops check before any production AI serving.
6. **Swap-in of the vision cold-start:** deployment requirement documented above.

## 5. Decisions that unblock the remaining track

1. **Hosting target** — this machine (fits: 7 GiB RAM, HDD storage; swap needs attention) or a VPS (~US$5–10/mo).
2. **Domain name** — available and which registrar/DNS.
3. **Nightly pg_dump schedule** — approve → activates `scripts/backup.sh` (6D complete).
4. **M1** — keep weather/resources public or require auth.

With 1–3 answered: 6D activation → 6K domain/TLS (Caddy auto-HTTPS) → 6H monitoring → 6M acceptance → Report 2 re-issue at **READY FOR OWNER RELEASE APPROVAL** (or honest failure).
