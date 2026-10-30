# MyFarm AI — Database Schema Reference

**Version:** 0.1.0
**Date:** 2026-10-28
**Schema source:** Alembic migration `6cd2bffd9881_initial_schema.py` (authoritative)
**Databases:** PostgreSQL 17 (production target), SQLite (tests only)

---

## ER Diagram

```mermaid
erDiagram
    users ||--o{ farms : "owns (owner_id)"
    users ||--o{ farm_members : "joins"
    users ||--o{ conversations : "creates"
    users ||--o{ sessions : "has"
    users ||--o{ refresh_tokens : "has"
    users ||--o{ research_queries : "issues"
    users ||--o{ audit_events : "acts (actor_id, nullable)"
    farms ||--o{ farm_members : "has members"
    farms ||--o{ crop_cycles : "tracks"
    farms ||--o{ conversations : "context (nullable)"
    crops ||--o{ crop_cycles : "grown"
    conversations ||--o{ messages : "contains"
    research_queries ||--o{ research_sources : "retrieves"
    research_queries ||--o{ citations : "cites"
    research_sources ||--o{ citations : "supports"

    users {
        uuid id PK
        varchar email UK
        boolean email_verified
        varchar password_hash
        varchar full_name
        varchar preferred_language
        varchar timezone
        boolean is_active
        enum role "USER|ADMIN"
        timestamptz last_login_at
    }
    farms {
        uuid id PK
        varchar name
        text description
        varchar address
        float latitude
        float longitude
        varchar timezone
        uuid owner_id FK
        boolean is_active
    }
    farm_members {
        uuid id PK
        uuid farm_id FK
        uuid user_id FK
        enum role "OWNER|MEMBER|VIEWER"
        timestamptz joined_at
    }
    crops {
        uuid id PK
        varchar name UK
        varchar scientific_name
        enum category "CEREAL..OTHER"
        text description
        float min_temp_c
        float max_temp_c
        float optimal_rainfall_mm
        int growing_days_min
        int growing_days_max
        boolean is_active
    }
    crop_cycles {
        uuid id PK
        uuid farm_id FK
        uuid crop_id FK
        varchar season_name
        int season_year
        date planting_date
        date expected_harvest_date
        date actual_harvest_date
        float area_hectares
        float area_acres
        enum status "PLANNED..ARCHIVED"
        float expected_yield_kg
        float actual_yield_kg
        varchar yield_unit
        text notes
    }
    conversations {
        uuid id PK
        uuid user_id FK
        uuid farm_id FK "nullable"
        varchar language
        varchar crop
        varchar location
        varchar model_name
        varchar model_version
        boolean is_archived
        int message_count
    }
    messages {
        int id PK "autoincrement"
        uuid conversation_id FK
        enum role "USER|ASSISTANT|SYSTEM"
        text content
        varchar model_name
        varchar model_version
        int token_count
        varchar finish_reason
    }
    sessions {
        uuid id PK
        uuid user_id FK
        varchar session_id_hash UK
        timestamptz expires_at
        varchar ip_address
        varchar user_agent
        text device_info
        boolean is_revoked
        timestamptz revoked_at
        varchar revoked_reason
    }
    refresh_tokens {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        timestamptz expires_at
        varchar parent_token_hash
        boolean is_revoked
        timestamptz revoked_at
        varchar revoked_reason
        varchar ip_address
        varchar user_agent
        text device_info
    }
    research_queries {
        uuid id PK
        uuid user_id FK
        text query_text
        varchar language
        enum status "PENDING..FAILED"
        text answer
        float confidence_score
        varchar model_name
        varchar model_version
        int token_count
        timestamptz started_at
        timestamptz completed_at
        text error_message
    }
    research_sources {
        uuid id PK
        uuid query_id FK
        varchar url
        varchar title
        varchar domain
        varchar publisher
        timestamptz published_at
        text content_text
        varchar content_hash
        varchar extraction_status
        text extraction_error
        int word_count
        varchar license
        boolean attribution_required
        boolean robots_compliant
        float relevance_score
        float credibility_score
    }
    citations {
        uuid id PK
        uuid query_id FK
        uuid source_id FK
        text claim_text
        text source_excerpt
        int position_in_answer
    }
    audit_events {
        uuid id PK
        uuid actor_id FK "nullable, SET NULL"
        varchar actor_type
        enum event_type "LOGIN_SUCCESS..DATA_DELETION_REQUESTED"
        varchar event_category
        uuid subject_id
        varchar subject_type
        text description
        text event_metadata
        varchar ip_address
        varchar user_agent
        varchar request_id
        boolean success
        text error_message
        timestamptz occurred_at
    }
```

---

## Delete Semantics (FK on-delete)

| Relationship | On delete | Rationale |
|--------------|-----------|-----------|
| user → conversations | CASCADE | User deletion removes their chat history (privacy) |
| user → farms (owner) | CASCADE | Owner deletion removes owned farms |
| user → farm_members | CASCADE | Membership ends with the user |
| user → sessions / refresh_tokens | CASCADE | Auth state dies with the user |
| user → research_queries | CASCADE | Research history dies with the user |
| user → audit_events (actor) | SET NULL | Audit trail survives the actor (compliance) |
| conversation → messages | CASCADE | Messages cannot outlive their conversation |
| farm → conversations | SET NULL | Conversations survive farm deletion, lose farm context |
| farm → crop_cycles | CASCADE | Cycles are farm-scoped |
| crop → crop_cycles | RESTRICT | Prevent deleting a crop in active use |
| research_query → sources / citations | CASCADE | Provenance is query-scoped |
| research_source → citations | CASCADE | Citations die with their source |

---

## Data Dictionary — Core Tables

### users
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, default `gen_random_uuid()` | |
| email | varchar(255) | NOT NULL, UNIQUE (indexed) | Login identifier |
| email_verified | boolean | NOT NULL | |
| password_hash | varchar(255) | NOT NULL | Argon2id (Phase 3) |
| full_name | varchar(255) | nullable | |
| preferred_language | varchar(10) | NOT NULL | ISO 639-1, e.g. `en`, `hi` |
| timezone | varchar(50) | NOT NULL | IANA name, e.g. `Asia/Kolkata` |
| is_active | boolean | NOT NULL | Soft-disable flag |
| role | varchar enum | NOT NULL | `USER` \| `ADMIN` (native_enum=false) |
| last_login_at | timestamptz | nullable | |
| created_at / updated_at | timestamptz | NOT NULL, default `now()` | |

Indexes: `ix_users_email` (unique), `ix_users_email_active`, `ix_users_role`.

### conversations
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | NOT NULL, FK → users ON DELETE CASCADE | Owner |
| farm_id | UUID | nullable, FK → farms ON DELETE SET NULL | Optional farm context |
| language | varchar(10) | NOT NULL | `en` \| `hi` observed |
| crop | varchar(100) | nullable | Crop context for the chat |
| location | varchar(200) | nullable | Location context |
| model_name / model_version | varchar(100) | nullable | Model metadata |
| is_archived | boolean | NOT NULL | |
| message_count | int | NOT NULL | Denormalized; kept consistent by service layer |
| created_at / updated_at | timestamptz | NOT NULL | |

Indexes: `ix_conversations_user_id`, `ix_conversations_user_updated`, `ix_conversations_user_farm`, `ix_conversations_farm_id`, `ix_conversations_farm_updated`.

### messages
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | int | PK, autoincrement | Integer PK by design (ordered append log) |
| conversation_id | UUID | NOT NULL, FK → conversations ON DELETE CASCADE | |
| role | varchar enum | NOT NULL | `USER` \| `ASSISTANT` \| `SYSTEM` |
| content | text | NOT NULL | |
| model_name / model_version | varchar(100) | nullable | Populated for ASSISTANT rows |
| token_count | int | nullable | |
| finish_reason | varchar(50) | nullable | e.g. `stop`, `length` |
| created_at / updated_at | timestamptz | NOT NULL | |

Indexes: `ix_messages_conversation_id`, `ix_messages_conversation_created`.

---

## Migration Transform Rules (SQLite legacy → PostgreSQL)

Recorded for the Phase 2 rehearsal (P2-24); implemented in
`backend/scripts/migrate_sqlite_to_pg.py`:

1. **Source:** canonical `backend/data/app.db`, opened read-only; SHA-256 recorded in the export manifest.
2. **Ownership:** all legacy conversations are assigned to a single `legacy_import` user — nil UUID `00000000-0000-0000-0000-000000000000`, email `legacy_import@myfarmai.internal`, `is_active=false`, unusable password hash. No real user is impersonated.
3. **IDs:** legacy conversation IDs are already UUID v4 strings and are preserved as-is; message integer IDs are preserved.
4. **Timestamps:** legacy SQLite timestamps are naive (`CURRENT_TIMESTAMP` = UTC). They are parsed as UTC and stored as `TIMESTAMPTZ` at UTC.
5. **Roles:** legacy lowercase `user`/`assistant` are upper-cased and validated against `{USER, ASSISTANT, SYSTEM}`.
6. **Derived data:** `conversations.message_count` is recomputed from messages during transform.
7. **Load:** single transaction; `COPY ... FROM STDIN`; refuses to run if the target `conversations` table is non-empty.
8. **Validation:** row counts, per-conversation message counts, orphan check, `message_count` column consistency, role domain check (P2-26).

---

*Schema reference reflects Alembic migration `6cd2bffd9881` as of 2026-10-28.*
