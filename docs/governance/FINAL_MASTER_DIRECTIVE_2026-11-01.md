# FINAL MASTER ENGINEERING DIRECTIVE — 2026-11-01 (owner)

> Imported 2026-11-02 per security-review finding Q6 (E3_SELFIE_SECURITY_REVIEW.md): the verbatim directive text was not previously in the repo. This file is the authoritative source for §5 (selfie/liveness) and all other sections. Owner-issued 2026-11-01 via interactive session; recorded verbatim from the owner's message.

## FINAL MASTER ENGINEERING DIRECTIVE
## ZERO-COST ARCHITECTURE · COMPLETE AGRICULTURAL PLATFORM · VERIFIED FARMER ONBOARDING · MAP-BASED LAND REGISTRATION · PUBLIC DEPLOYMENT

**Project:** MyFarmAI — **Repository:** `/data/MyFarmAI` — **Primary host:** Owner's Ubuntu machine
**Platform:** Next.js Web + Expo Android + FastAPI + PostgreSQL + Ollama
**Deployment objective:** Public multi-user agricultural application
**Final objective:** Secure signup, verification, farmer profile creation, land mapping, agricultural personalization and public application access.

---

## 1. PROJECT VISION

Build MyFarmAI as a complete agricultural AI platform for real farmers.

Every farmer must be able to:
1. Register an account.
2. Sign up using Google, Microsoft, email or phone number.
3. Verify their email address or phone number through OTP when using passwordless email/phone registration.
4. Complete the mandatory live selfie verification workflow.
5. Grant location permission to detect their approximate location automatically.
6. Confirm their location on an interactive map.
7. Register their home, garden or agricultural land.
8. Draw the farm boundary on the map.
9. Calculate their farm area automatically.
10. Select their land measurement unit.
11. Specify their farming type and intended crops.
12. Complete their farmer profile.
13. Access the application after successful onboarding.
14. Log in securely in subsequent sessions.

The system must not require farmers to know latitude or longitude.

Product principle: **My Land. My Farm. My Decision.**

## 2. NON-NEGOTIABLE PROJECT POLICIES

- Zero-cost-first. Open-source-first. Self-host-first. Local-AI-first.
- No mandatory paid API. No mandatory expiring free-tier quota.
- No mandatory paid identity provider. No mandatory paid map provider.
- No paid SMS service as a hidden dependency. No unapproved billing activation.
- No data collection without an explained purpose. No background location tracking.
- No public exposure of private farmer information.
- No fake identity-verification success.
- No fabricated farm boundaries or land measurements.
- No fabricated agricultural information.
- Preserve all existing data and project architecture decisions.
- Document every meaningful code change.
- Obtain owner approval before destructive operations and public production release.

Important: No provider can guarantee unlimited free SMS, email delivery, bandwidth, hosting or geocoding. Document provider limits honestly. The application must not depend on those services for all its essential functionality.

## 3. PHASE ROADMAP — FINAL STRUCTURE

- **Phase 0** — Foundation and governance: inspect current state; review phase docs/ADRs; zero-cost policy; license/dependency register; data protection; security/deployment standards; feature acceptance criteria.
- **Phase 1** — Core backend: FastAPI architecture; request validation; versioning; logging/request IDs; error handling; rate limiting; persistence; integration tests.
- **Phase 2** — Database: PostgreSQL architecture/ADRs; normalized farmer/farm data; safe migrations; retention; backups/restoration; private-data protection; PostGIS where appropriate.
- **Phase 3** — Authentication and identity: the complete authentication architecture of Section 4.
- **Phase 4** — AI Gateway: local Ollama; model registry/routing; agricultural AI context; model resource monitoring; image understanding; embeddings; research integrations; voice/translation; graceful fallback; no mandatory paid model API.
- **Phase 5** — Farmer experience: onboarding; dashboard; farm/crop management; location-aware info; weather; crop recommendations; farm-specific AI context; map-based land management; voice; notifications; mobile+web integration.
- **Phase 6** — Production readiness: secure production config; container health checks; monitoring; backup/recovery; resource limits; deployment hardening; logging; incident response; release verification.
- **Phase 7** — Advanced agricultural intelligence: crop planning; irrigation; soil; pest/disease; weather-aware planning; farm economics; market info; land-based crop recommendations; knowledge/research. Only enable predictions when the necessary data and model validation exist.
- **Phase 8** — Zero-cost infrastructure compliance: full cost/license/API-quota/self-hosting/security audits; network assessment; public access design; Ubuntu deployment prep.
- **Phase 9** — Final deployment and public release: deploy web/backend/DB/local AI; public HTTPS ingress; enable registration/login/verification/mapping; external tests; backup restoration; security verification; operational documentation; owner release approval.

Do not mark a phase complete without test evidence.

## 4. AUTHENTICATION AND SIGNUP SYSTEM

### 4.1 Supported signup methods

**Google** — OAuth 2.0 / OpenID Connect; verified identity claims; validate issuer, audience, signature, nonce and state; secure callback URLs; prevent account takeover during account linking.

**Microsoft** — Microsoft identity platform / OpenID Connect; configured account types; validate issuer, audience, signature, state and nonce; secure account linking.

**Email** — email registration; email OTP verification; OTP expiry; resend cooldown; attempt limits; secure OTP storage; single-use verification; account activation only after successful verification.

**Phone** — international normalization (E.164); SMS OTP; expiry; attempt limits; resend cooldown; abuse protection; secure OTP storage; verified phone status.

SMS provider integration must use a modular adapter. Do not hardcode a paid SMS provider or assume unlimited free SMS. If no approved SMS delivery provider is configured, explain that phone verification is temporarily unavailable. Do not pretend an OTP was delivered. Support provider replacement without rewriting authentication logic.

### 4.2 Authentication lifecycle

Required flow:
1. User chooses registration method.
2. User enters required information or completes OAuth.
3. Verify email/phone ownership where applicable.
4. Create a pending account.
5. Start the required live selfie workflow.
6. Complete liveness verification.
7. Complete farmer and location onboarding.
8. Create or activate the farmer profile.
9. Enable normal login.

For Google/Microsoft registration, do not ask for another email OTP unless there is a specific security or ownership reason.

### 4.3 Login

Support: Google login; Microsoft login; verified email login; verified phone login; secure passwordless or password-based login per the approved authentication design; session expiration; session revocation; secure refresh token rotation; logout from individual devices; account recovery.

Do not make OTP mandatory for every login unless the selected security policy explicitly requires it.

### 4.4 Authentication security

Secure HTTP-only cookies where appropriate; CSRF protection where applicable; secure session management; login attempt limits; OTP brute-force protection; OAuth state and nonce validation; account linking protection; password hashing if passwords are used; audit logging; account deletion and recovery procedures; privacy-aware error responses.

## 5. LIVE SELFIE AND LIVENESS VERIFICATION

A live selfie is a mandatory onboarding step under this product requirement. Implement a dedicated verification workflow.

### 5.1 Camera capture
- Request camera permission only when the user reaches verification.
- Display the purpose of selfie collection.
- Capture a fresh image using the camera.
- Do not silently use an old gallery image as a live capture.
- Validate image format, dimensions and file size.
- Securely transmit the capture. Protect temporary files.

### 5.2 Liveness
Design a liveness challenge system. Possible challenges: blink; turn head left or right; follow a randomized visual instruction; other validated liveness checks.
- Do not claim that a single still photograph proves liveness.
- Do not claim government identity verification.
- Do not use face recognition to identify or infer a person's identity.
- If automated liveness is not reliable enough, use a clearly documented manual-review workflow rather than reporting false verification success.

### 5.3 Privacy and security
- Obtain explicit informed consent. Explain why selfie data is collected.
- Encrypt data in transit and at rest.
- Restrict access to authorized verification components.
- Do not store raw selfie images longer than necessary.
- Define retention and deletion periods.
- Do not reuse selfies for model training.
- Do not use selfies for advertising.
- Do not expose selfie URLs publicly.
- Record verification status and audit events.
- Provide a secure deletion process.

Before production, review applicable Indian privacy and data-protection obligations, including the DPDP framework and any relevant rules in force.

Mandatory selfie verification must be clearly disclosed before registration. Do not quietly collect biometric information.

If a camera or liveness service fails, keep the account in pending verification state. Provide a documented support or review process; never silently bypass verification.

## 6. AUTOMATIC LOCATION DETECTION

The farmer must not have to understand coordinates.

### 6.1 Browser and Android geolocation
Use platform geolocation APIs. Flow: explain why location is requested; ask permission; request current location; obtain lat/lon; obtain accuracy; resolve approximate city and locality; display on the map; let the farmer correct manually.
Handle: permission granted; denied; location disabled; timeout; low accuracy; browser incompatibility; Android permission denial; approximate location.
Do not continuously track users. Do not collect background location. Do not assume GPS coordinates identify the exact legal property boundary.

### 6.2 Location data
Store only the location information needed for the selected use case. Separate: current device location; home location; farm location; farm boundary; mailing/contact address. Allow multiple farms and a separate home location. Never automatically assume the farmer lives on their farmland.

### 6.3 Address resolution
Use a geocoding adapter. Support: city; district; state; country; locality; postal code (when available); optional street. Use legally permitted data sources. Avoid overloading public geocoding services. Support locally hosted geocoding where practical. If address resolution fails, allow manual entry and map-pin correction. Do not invent a complete postal address from approximate GPS coordinates.

## 7. MAP-BASED FARM AND LAND REGISTRATION

Dedicated interactive farm map. Use Leaflet and OpenStreetMap-compatible data sources, subject to licenses and usage policies. Map provider integration must be replaceable. Do not rely on a public tile service as an unlimited production resource. Evaluate self-hosted tiles if scale requires.

### 7.1 Map onboarding
After automatic location detection: open map centered on detected location; display detected approximate location; search by place/address; manual pin placement; zoom/navigation; boundary drawing; boundary editing; multiple farm registrations; save and revisit boundaries. The farmer must be able to use the map without knowing coordinates.

### 7.2 Land selection modes
A. Home farming (indoor, balcony, terrace, kitchen garden, small outdoor home garden).
B. Small outdoor farming (backyard, small agricultural plot, community/rented area).
C. Agricultural land (small/medium/large farm, multiple fields).
D. Other (greenhouse, polyhouse, nursery, orchard, other specialized).

### 7.3 Boundary selection
Draw polygon; edit; delete; save; multiple plots per farm; multiple farms per farmer. A location pin must not be treated as a measured farm boundary. Support approximate manual area entry, marked as user-reported (not map-measured).

### 7.4 Area calculation
Calculate area from geographic polygon coordinates using an appropriate geodesic calculation or verified geospatial library. Support: m²; km²; hectares; acres; ft²; yd² (where appropriate). Display conversions automatically: 1 ha = 10,000 m²; 1 acre ≈ 4,046.8564224 m²; 1 ha ≈ 2.47105381 acres. Do not calculate polygon area using simple lat/lon degree arithmetic.
Validate polygons: invalid geometry; self-intersection; missing points; zero area; unrealistic dimensions; duplicate vertices; boundary changes.
Display calculated area and let the farmer confirm. Explain that map-measured boundaries are estimates and are not legal land-survey certificates.

### 7.5 Land information
Save: farm name; land type; farm boundary; calculated area; area unit; user-confirmed area; address; city; district; state; country; location accuracy; boundary source; created date; last updated date.

## 8. FARMER PROFILE CREATION

**Personal:** name; verified email; verified phone (if provided); preferred language; profile photograph (subject to verification and privacy policy); account status.
**Location:** home location; farm location; address; city; district; state; country; coordinates with appropriate access controls.
**Farming:** farming type; home/outdoor; land area; area unit; farm plots; soil info (if known); water availability (if known); existing crops; intended crops; growing season; experience; preferences.

Do not force farmers to provide information not required for core onboarding. Use progressive profile completion for optional agricultural details.

**Multiple farm support:** one farmer may own, rent, manage or work on multiple plots. Represent ownership/management relationships explicitly. Do not assume all registered land is legally owned by the account holder.

## 9. DATABASE DESIGN

Review existing database architecture and ADRs before changing schemas. Design entities/relationships for: users; authentication_accounts; email_verifications; phone_verifications; sessions; selfie_verifications; verification_events; farmer_profiles; home_locations; farms; farm_plots; farm_boundaries; farm_area_measurements; crops; farm_crop_plans; consent_records; audit_logs.
Use PostGIS where appropriate. Proper constraints and indexes. Protect sensitive fields. Migrations with rollback strategies. Never destroy existing records during schema updates. Avoid unnecessary duplication of location and identity information.

## 10. AGRICULTURAL AI PERSONALIZATION

The farmer's profile and land information should influence agricultural assistance: suggest crops appropriate to location/season; consider available land area; distinguish terrace farming from large-field agriculture; calculate seed/fertilizer quantities only from validated recommendations; consider irrigation and soil; present weather-aware suggestions when reliable data exists; practical plans for small gardens; scalable plans for large farms.
Never make recommendations solely from land area. Account for crop, climate, soil, season, water, local agricultural guidance and uncertainty. The AI must distinguish confirmed information from assumptions.

## 11. PHASE 4 — AI AND MODEL REQUIREMENTS

Use local Ollama as the default AI inference engine. Inspect actual installed models before selecting defaults. Evaluate: hardware memory; CPU/GPU; model size; latency; quality; license; storage. Avoid loading large models simultaneously on constrained hardware. Cloud models may only be optional adapters and must not become essential dependencies.

## 12. PHASE 5 — FARMER APPLICATION EXPERIENCE

Implement: signup and login; verification workflow; farmer dashboard; profile management; map and farm management; crop planning; weather information; agricultural chat; image assistance; voice assistance; research and citations; notifications; farm-specific history. Web and Android must use consistent backend APIs. Provide clear onboarding progress indicators. Allow the user to resume an incomplete onboarding process securely.

## 13. PHASE 6 — SECURITY AND PRODUCTION READINESS

Implement and verify: authentication security; authorization; tenant isolation; data encryption; secret management; rate limiting; input validation; file upload protection; secure session handling; OAuth security; OTP abuse protection; liveness verification protection; location privacy; audit logging; database security; API security; container security; backup protection.
Every farmer must only access their own private records unless a properly authorized sharing feature exists. Test cross-account access attempts.

## 14. PHASE 7 — ADVANCED AGRICULTURAL INTELLIGENCE

Connect the verified farmer and farm context to: crop planning; irrigation planning; soil information; pest and disease assistance; weather-aware advice; market information; farm economics; yield estimation when sufficient data exists; seasonal recommendations. Never invent market prices, weather conditions or agricultural data. Document dataset sources, freshness and reliability.

## 15. PHASE 8 — ZERO-COST COMPLIANCE

Audit every dependency: authentication; OAuth; email; SMS; maps; geocoding; weather; AI; search; voice; translation; storage; monitoring; hosting; DNS; HTTPS; CI/CD.
Classify: CORE-SELF-HOSTED; OPTIONAL-OPEN-SOURCE; OPTIONAL-FREE-EXTERNAL; PAID-PROHIBITED; LICENSE-RESTRICTED; REQUIRES-OWNER-APPROVAL.
For each service document: cost; usage limits; license; data processing; failure mode; replacement strategy; whether billing information is required. No mandatory paid provider may remain in the essential application path.

## 16. PHASE 9 — FINAL DEPLOYMENT

Primary deployment: owner's Ubuntu machine. Target services: Docker Engine; Docker Compose; Next.js; FastAPI; PostgreSQL; Ollama; Caddy; monitoring; local backup system; approved public HTTPS ingress.

**Public access:** evaluate Cloudflare Quick Tunnel for initial public access. Do not claim it is a permanent domain or uptime guarantee. Do not open unnecessary router ports. Do not expose PostgreSQL, Ollama, Docker API or administration endpoints. Verify public signup and login from a separate network.

**Multi-user operation:** test multiple concurrent registrations; multiple active sessions; data isolation; rate limits; concurrent farm creation; database load; AI inference capacity; storage growth; recovery. Do not promise unlimited concurrent users on a single Ubuntu machine. Measure actual resource capacity and document supported deployment scale.

## 17. FINAL END-TO-END ACCEPTANCE TESTS

**Authentication:** Google signup/login; Microsoft signup/login; email OTP signup; phone OTP signup (when an approved SMS provider is configured); invalid OTP rejection; expired OTP rejection; resend cooldown; login after successful verification; session expiration; logout; account recovery; account linking security.
**Selfie:** camera permission; live capture; liveness challenge; invalid capture rejection; verification status; secure storage; retention and deletion; failure and manual-review handling.
**Location:** GPS permission; location detection; city/locality resolution; denied permission; manual map pin; incorrect location correction; home vs farm location.
**Map and land:** polygon drawing; editing; validation; area calculation; acre/hectare/m² conversion; multiple farms; multiple plots; home garden registration; manual area entry; save and reload boundaries.
**Farmer profile:** verified account; verified contact; verification status; farm information; location information; farming preferences; profile update; data isolation.
**Agricultural application:** AI chat; weather; crop management; crop recommendations; image assistance; research; voice; dashboard; web integration; Android integration.
**Deployment:** production builds; service health checks; HTTPS; public access; restart recovery; database persistence; backup restoration; monitoring; security verification.

## 18. DOCUMENTATION DELIVERABLES

Update existing documentation instead of creating unnecessary duplicates. Produce or update:
1. `MYFARMAI_FINAL_PHASE_STATUS.md`
2. `MYFARMAI_ZERO_COST_COMPLIANCE_REPORT.md`
3. `MYFARMAI_FINAL_SECURITY_AUDIT.md`
4. `MYFARMAI_FINAL_TEST_REPORT.md`
5. `MYFARMAI_DEPLOYMENT_GUIDE.md`
6. `MYFARMAI_BACKUP_RECOVERY_GUIDE.md`
7. `MYFARMAI_OPERATIONS_HANDOVER.md`
8. `MYFARMAI_AUTHENTICATION_DESIGN.md`
9. `MYFARMAI_FARMER_ONBOARDING_DESIGN.md`
10. `MYFARMAI_MAP_AND_LAND_REGISTRATION.md`
11. `MYFARMAI_PRIVACY_AND_DATA_RETENTION.md`
12. Updated roadmap.
13. Updated architecture diagrams.
14. Updated API documentation.

## 19. EXECUTION RULES

First inspect the repository. Then produce: current phase status; missing features; technical blockers; dependency and cost audit; security findings; owner approvals required; execution plan.
Execute only verified, unblocked tasks. Preserve existing working code and data. Do not bypass security checks. Do not fabricate tests. Do not publish production without explicit owner approval. Do not silently substitute an unsupported service for a required provider.
If SMS, OAuth, email, map tiles, geocoding or liveness needs external configuration, document the exact setup requirement and continue implementing all independent work. Do not stop after generating documentation. Implement, test and verify the actual features.

## 20. FINAL RELEASE CLASSIFICATION

Use these exact classifications:
1. DEPLOYMENT NOT READY
2. LOCAL DEPLOYMENT VERIFIED
3. PUBLIC DEMO DEPLOYMENT VERIFIED
4. PRODUCTION RELEASE READY — OWNER APPROVAL REQUIRED
5. PRODUCTION RELEASE APPROVED

Only assign a classification supported by evidence. Final report must include: actual status of Phases 0–9; files changed; tests and results; security findings; authentication provider status; OTP provider status; selfie and liveness verification status; location permission and map status; farm measurement accuracy tests; database and AI status; deployment status; public URL if verified; backup restoration evidence; resource usage; cost and license compliance; known limitations; remaining blockers; required owner approvals.

**FINAL OBJECTIVE:** Deliver MyFarmAI as a secure, public, multi-user agricultural platform where farmers can register, verify their account, complete live selfie verification, automatically detect their location with permission, map their home or agricultural land, measure their plots, create a personalized farmer profile and use the agricultural application. Essential services must be self-hosted wherever practical, and the platform must not require paid APIs or expiring free-tier quotas for its core functionality. The final release must be tested, documented, recoverable and approved by the project owner.
