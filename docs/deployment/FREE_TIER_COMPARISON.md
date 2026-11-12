# Free-Tier Provider Comparison (verified facts only)

Verified: 2026-11-03 by fetching the official pricing pages listed below while
logged-out (HTTP reads — no accounts touched, no signups). Facts under "verified"
come straight from each provider's own page on the fetch date; anything else is
marked UNKNOWN. Restrictions/payments never breached during this evaluation.

> Re-checked 2026-11-12 in
> [`MYFARMAI_CLOUD_PROVIDER_AUDIT.md`](MYFARMAI_CLOUD_PROVIDER_AUDIT.md); the Neon
> and Cloudflare figures below still hold, AWS and GCP are now rejected, R2's free
> tier is newly verified. This file remains the 2026-11-03 record.

## 1. Managed PostgreSQL providers

| Criterion | **Neon** (neon.com/pricing) | **Supabase** (supabase.com/pricing) | **Prisma Postgres** (prisma.io/pricing) |
|---|---|---|---|
| Free plan permanent | ✅ permanent free tier | ✅ Free plan | ✅ "free forever, no time limit" |
| Credit card required | ✅ none on Free | ❔ not stated on page (no-card signups widely used; verify at signup) | ✅ "No credit card required" |
| Projects/Databases | 100 projects per Free account | 2 active projects per Free org | 50 databases |
| Storage per project | 1 GB/project, 20 GB per account | 500 MB database per project | 2 GB included (all databases pooled) |
| Compute | 100 CU-hours/project/month, scale-to-zero after ~5 min idle | Included shared compute | 200k operations/month (each query = 1 operation) |
| Egress/transfer | 5 GB egress/project/month | 5 GB egress | Unlimited data transfer |
| Inactivity pause | ❌ none — suspends only on quota exhaustion | ⚠️ pauses after 1 week of inactivity | Scale-to-zero by design (idle costs nothing) |
| Other Free limits | 10 branches, 1 manual snapshot | Unlimited API requests | 10 pooled + 10 direct connections |

Notes:
- Supabase's 2-project cap and 1-week inactivity pause make it a weaker fit for a
  long-lived single tenant-DB; Neon's "no inactivity pause" claim is the standout.
- Prisma Postgres Free bills by *operations* (200k/month) — a chatty ORM layer
  with N+1 queries could exhaust this; fine for a low-traffic public pilot.
- No database was migrated and no account registered — decision pending owner.

## 2. Frontend / full-stack hosting

| Criterion | **Cloudflare Pages/Workers** | **Netlify** | **Vercel Hobby** |
|---|---|---|---|
| Free plan | Permanent free plan — account live (Google SSO) | ✅ "$0 forever" | ✅ $0/mo |
| Key free limits (verified) | **Pages**: 500 builds/mo (1 at a time), 100 projects, 20k files/site (25 MiB/file), 100 custom domains/project, unlimited preview deploys. **Workers**: 100k requests/day (reset 00:00 UTC, then error 1027), 10 ms CPU/request, 128 MB mem, 50 subrequests/req, 64 MiB bundle, 100 Workers, 5 cron triggers; Pages Functions count toward Workers quota | 300 credit limit/month: production deploy = 15 credits (→ ~20 deploys/mo), bandwidth = 20 credits/GB (→ ~15 GB/mo), 2 credits/10k requests (→ ~1.5 M req/mo), free custom domains + SSL, global CDN | 1M CDN requests/mo, 100 GB Fast Data Transfer/mo, 4h Fluid Active CPU, 1M function invocations, 1 GB Blob, cron jobs included |
| Gotcha | 10 ms CPU/request covers typical SSR (avg 2.2 ms, heavy 10–20 ms); >100 MB uploads rejected on Free domains; **Python not supported in Workers** — fits the Next.js frontend, NOT the FastAPI backend | Credit-based — every deploy consumes quota | ❌ Hobby is explicitly **"for personal, non-commercial use"** — public MyFarmAI with users may violate the Fair Use terms; would need Pro ($20/mo) or owner sign-off |
| Accounts state | ✅ **account created via Google SSO 2026-11-03** (owner-approved; no separate terms screen was shown on the SSO path — recorded honestly). Pages/Workers free quotas still to verify from the dashboard | not inspected (session state unknown) | not inspected |

Note: Netlify does not state non-commercial limits on the pricing page; Vercel
does. For a user-facing product, that distinction matters.

## 3. Backend / compute hosting

| Provider | Verified facts | Fit for FastAPI backend |
|---|---|---|
| **Koyeb** (koyeb.com/pricing) | Cheapest plan is **Pro $29/mo** — no free compute plan on the pricing page. Free catalog: "Free 5h" Postgres tier (0.25 vCPU/1 GB/1 GB storage, 4h/day-style) and signup credits are not shown on the page. Announced acquisition by Mistral AI (blog link on page). | ❌ as-is: paid only, BLOCKED under ₹0 policy. Postgres "Free 5h" exists but 1 GB capped storage and limited compute make it a poor production fit. |
| **Prisma Compute** (prisma.io/pricing) | Free tier includes app hosting: 1M requests/mo, 360 GB-hours memory, 4 active vCPU-hours, 10 GB outbound bandwidth, scale-to-zero, no card. | ⚠️ TypeScript app hosting ("Prisma Compute is TypeScript app hosting") — a Python/FastAPI backend does not appear supported on the Free compute tier. Not a FastAPI candidate. |
| **Hugging Face Spaces** (huggingface.co/pricing) | CPU Basic free Space (2 vCPU/16 GB RAM — no persistent disk guarantee), ZeroGPU free with quota, community GPU grants for side projects. | ⚠️ demo-oriented; short sleeps/restarts on free hardware. Candidate only for AI demos, not for the authenticated backend. |
| **Zoho Catalyst + AppSail** (official pages deep-fetched 2026-11-03: students page, `docs.catalyst.zoho.com` deployment-and-billing + free-tier pages) | **Backend IS feasible here — AppSail runs Python** (managed Flask/Django/etc. runtimes **and custom runtimes as OCI images** — our existing FastAPI Docker image deploys as a custom runtime). No card to sign up for the free tier (official FAQ). Free tier (monthly, forever, no expiry): **AppSail 900 GB-minutes** (≈ **~60 h/month** of a 256 MB instance 24⁄7-style — NOT enough for a continuous backend), Functions 25k GB-seconds, Web Client Hosting 300k requests + 500 MB CDN (frontend fits), API Gateway 100k requests, Data Store 2 GB, Mail **100 emails/month**. **$250 one-time credits from the general signup require adding a card → BLOCKED under ₹0 policy** (docs: "The $250 credit you receive after setting up your payment method is valid for 6 months"). **Student program**: free for non-commercial student projects (support-team review; extends/link $250 usage), owner does the identity/academic verification personally — this is the only ₹0 path to app-tier usage above free limits. Exceeding free tier without a card ⇒ $5-minimum bill stays unpaid ⇒ account suspends (financially safe degradation — no auto-charge without a payment method). | ⚠️ PARTIAL FIT — frontend+Catalyst free tier fits; continuous FastAPI backend fits ONLY via the student program after owner verification; otherwise backend stays on the local CPU (E6). Postgres NOT in Zoho's stack (Data Store ≠ SQL; we pair Catalyst compute with **Neon** Postgres). |
| **UppCoder** (portal.uppcoder.com) | Not publicly documented on a fetchable pricing page; portal requires login. | ❔ UNKNOWN — low priority unless the owner confirms it. |

## 4. Verdict snapshot (proposal only — not approved)

Provisional zero-cost architecture if owner approves:
1. **Database**: Neon free (100 CU-hrs, no card, no inactivity pause) — pending owner
   approval; optional Prisma Postgres as an overflow/second project.
2. **Frontend**: Cloudflare Pages (needs account + ToS gate) — fallback Netlify free
   (300 credits ≈ 15 GB/mo transfer + 20 deploys) — Vercel Hobby only if owner accepts
   the non-commercial clause risk (not recommended for public farmer users).
3. **Backend**: ⚠️ no verified no-card Python FastAPI free host in this table. Until
   a no-card Python host is verified, the backend stays on local/sandbox infra
   (blocker E6 refuse-public) or requires further investigation (Koyeb signup
   credits are not verifiable from the pricing page alone).
4. **AI**: local-first (Ollama on device/host) + cloud-AI quota enforcement per
   directive §10; HF Spaces only for optional public demos.

## 5. Sources & dates

- neon.com/pricing — fetched 2026-11-03
- supabase.com/pricing — fetched 2026-11-03
- prisma.io/pricing — fetched 2026-11-03
- koyeb.com/pricing — fetched 2026-11-03
- netlify.com/pricing — fetched 2026-11-03 (first attempt failed, retry succeeded)
- vercel.com/pricing — fetched 2026-11-03
- huggingface.co/pricing — fetched 2026-11-03
- catalyst.zoho.com/students/ — fetched 2026-11-03 (FAQ answers collapsed in fetch); **re-verified live 2026-11-04 with full FAQ**: $250 usage over 6 months at no cost, no subscription, no credit card, **no verification form** (student status = sign in + create project); on hitting the $250 threshold the app is *stopped*, never auto-charged (extensions via Support). catalyst.zoho.com/free-tier/ fetched 2026-11-04: free tier "Card required: None", renews "Monthly, Forever, no expiry"; ⚠️ projects exceeding free limits incur a **₹300/month minimum bill per project** — keep usage in free tier, delete unused projects. Console verified 2026-11-04: org `60094539808`, Project-Rainfall (`90779000000015001`) created; no payment plan selected.
- developers.cloudflare.com/pages/platform/limits/ and /workers/platform/limits/ — fetched 2026-11-03 (account now live, Google SSO)
