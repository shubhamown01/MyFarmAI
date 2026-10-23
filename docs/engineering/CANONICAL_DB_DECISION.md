# MyFarmAI — Canonical SQLite Database Decision

**Document ID:** MYFARMAI-CDB-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Proposed — Owner Decision Required  
**Gate:** G1 (Blocks P1-01, Phase 2)

---

## 1. Executive Summary

**Recommendation:** Designate `backend/data/app.db` as the canonical SQLite database for MyFarmAI.

**Rationale:** This file contains the actively used development dataset (234 conversations, 573 messages, recent activity Oct 21), is the default for local development runs, and represents the current working state of the application. The `data/app.db` file (35 conversations, 74 messages, last modified Oct 19) appears to be a stale Compose deployment artifact.

**Owner Decision Required:** Approve, modify, or reject this recommendation.

---

## 2. Evidence Comparison

| Attribute | `backend/data/app.db` | `data/app.db` |
|-----------|----------------------|---------------|
| **File Size** | 151,552 bytes | 40,960 bytes |
| **Last Modified** | 2026-10-21 14:54:31 | 2026-10-19 11:07:54 |
| **Conversations** | 234 | 35 |
| **Messages** | 573 | 74 |
| **Integrity Check** | `ok` | `ok` |
| **Git Status** | Untracked, **NOT ignored** | Untracked, ignored by `data/*` |
| **Used By** | Local development (running from `backend/`) | Docker Compose bind mount `./data:/app/data` |
| **Recent Activity** | Oct 21 09:24 (today) | Oct 19 05:37 (3 days ago) |
| **Sample Data** | Test conversations with mocked Ollama | Real agricultural Q&A (wheat fertilizer) |

### Recent Conversation Samples

**backend/data/app.db (Latest):**
```
3ecb2837-51a1-49e7-a5ff-3b0a7165ce50 | 2026-10-21 09:24:26 | hi | wheat | Punjab
  → user: "Test"
  → assistant: "Test response from mocked Ollama"

210ebb9c-586c-46ac-916f-6f52974960bf | 2026-10-21 09:24:24 | en | None | None
  → user: "Hello"
```

**data/app.db (Latest):**
```
da0609b8-c065-4947-8d85-2858ce350cde | 2026-10-19 05:37:29 | en | None | None
  → user: "What fertilizer for wheat?"
  → assistant: Detailed wheat fertilizer recommendations (organic vs synthetic)
```

---

## 3. Application Configuration References

### Database Path Resolution Chain

1. **Default Setting** (`backend/app/core/config.py:36-37`):
   ```python
   database_path: str = Field(default="data/app.db")
   ```

2. **Profile Overrides** (`backend/app/core/config_profiles.py`):
   ```python
   DEVELOPMENT:  {"database_path": "data/app.db"}
   TEST:         {"database_path": ":memory:"}
   PRODUCTION:   {"database_path": "/app/data/app.db"}
   ```

3. **Runtime Initialization** (`backend/app/factory.py:79-83`):
   ```python
   await init_db(app_settings.database_path)
   app.state.database_path = app_settings.database_path
   ```

4. **Connection Resolution** (`backend/app/db/connection.py:19-21`):
   ```python
   if request and hasattr(request.app.state, "database_path"):
       return request.app.state.database_path
   return settings.database_path
   ```

### Key Finding
- When running locally from `backend/` directory with default settings, `data/app.db` resolves to `backend/data/app.db` (relative path)
- Docker Compose mounts `./data:/app/data`, so `data/app.db` inside container = host `data/app.db`
- These are **two different physical files** with divergent data

---

## 4. Decision Options

### Option A: `backend/data/app.db` as Canonical (RECOMMENDED)
- **Pros:** Contains 6.7x more conversations, 7.7x more messages, actively used today, represents current development state
- **Cons:** Not git-ignored (risk of accidental commit), not the Compose mount target
- **Actions Required:** 
  - Add `backend/data/` and `**/*.db` to `.gitignore`
  - Update Compose to mount `./backend/data:/app/data` instead of `./data:/app/data`
  - Backup this file for Phase 1 P1-01

### Option B: `data/app.db` as Canonical
- **Pros:** Already git-ignored, Compose mount target
- **Cons:** 35 conversations vs 234, stale (3 days old), loses recent development work
- **Actions Required:** Accept data loss of 199 conversations / 499 messages

### Option C: Start Fresh (No Data Preservation)
- **Pros:** Clean slate, no migration complexity
- **Cons:** Loses all 269 conversations / 647 messages across both files
- **Condition:** Only if owner confirms no data must be preserved

### Option D: Merge Both with Legacy Tag
- **Pros:** Preserves all unique data
- **Cons:** Complex deduplication, no owner mapping for conversations, schema has no user_id
- **Actions Required:** Import both with `legacy_source` tag, deduplicate by conversation ID

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Accidental commit of `backend/data/app.db` | High (not ignored) | Data exposure | **Immediate:** Add to `.gitignore` before any commit |
| Compose uses stale DB | Medium | Inconsistent data | Update Compose mount to point to canonical |
| Data loss if wrong file chosen | High | Irreversible | Owner decision with full evidence |
| Test contamination | Medium | False test results | Tests use `:memory:` profile (already isolated) |

---

## 6. Recommendation

**Select Option A: `backend/data/app.db` as canonical**

**Justification:**
1. **Data volume:** 234 vs 35 conversations (6.7x), 573 vs 74 messages (7.7x)
2. **Recency:** Actively used today vs 3 days stale
3. **Development workflow:** Default for local runs from `backend/`
4. **Content relevance:** Contains current test conversations with mocked Ollama responses

**Required Follow-up Actions (if approved):**
1. Add to `.gitignore`: `backend/data/`, `**/*.db`, `**/*.sqlite*`
2. Update `docker-compose.yml`: change `./data:/app/data` → `./backend/data:/app/data`
3. Execute backup of canonical file per P1-01 procedure
4. Document decision in `DECISION_REGISTER.md` Gate G1

---

## 7. Owner Decision

| Field | Value |
|-------|-------|
| **Decision** | ☐ Approve Option A / ☐ Approve Option B / ☐ Approve Option C / ☐ Approve Option D / ☐ Other: _______ |
| **Rationale** | |
| **Approver** | |
| **Date** | |
| **Signature** | |

---

## 8. Implementation Impact

If Option A approved:
- **P1-01 Backup:** Back up `backend/data/app.db` (canonical) + `data/app.db` (secondary)
- **Compose Change:** `docker-compose.yml` volume mount updated
- **Gitignore:** `backend/data/`, `**/*.db`, `**/*.sqlite*` added
- **Phase 2 Migration:** Export from `backend/data/app.db` as source

**No database modification, migration, or deletion occurs until this decision is recorded.**