# Phase 2 — Database Architecture and Migration Readiness

## Objective

Establish an explicit, recoverable data model and decide how PostgreSQL becomes the production system of record without losing existing data.

## Entry conditions
- Phase 1 accepted.
- Canonical data source and data-preservation requirements explicitly decided.
- No migration runs against project data without separate approval.

## Workstreams

### 1. Inventory and data ownership
- Document every database file, configured path, container volume and connection string.
- Compare schemas and metadata of the two reported SQLite databases.
- Do not infer which database is canonical from row counts alone.
- Identify personal/location data and define access, retention and deletion rules.
- Define ownership boundaries for users, farms, conversations and related records.

### 2. Domain model
Design only approved MVP entities, potentially:
- Users and authentication records.
- Farms and farm membership/ownership.
- Crops and crop cycles.
- Conversations and messages.
- Research queries, sources and citations.
- Audit/security events.

For each entity specify keys, relationships, constraints, indexes, timestamps, deletion behavior and retention. Avoid speculative tables without product requirements.

### 3. Persistence layer
- Evaluate SQLAlchemy 2 and the approved sync/async approach.
- Use Alembic for versioned schema changes if approved.
- Keep migrations deterministic and reviewed.
- Document transaction boundaries and concurrency behavior.
- Avoid database-specific assumptions leaking into domain logic.

### 4. PostgreSQL readiness
- Verify chosen PostgreSQL version and deployment support.
- Check differences between SQLite and PostgreSQL semantics.
- Review types, constraints, indexes, case sensitivity, JSON handling, locking, transactions and query behavior.
- Run migrations only against disposable test instances during validation.

### 5. Migration and recovery rehearsal
- Define source snapshot and integrity verification.
- Create a disposable copy of the selected source database.
- Build an idempotent or safely repeatable migration/import procedure.
- Compare row counts, key relationships and representative data invariants.
- Validate application reads/writes against the target database.
- Define cutover, downtime, rollback/forward-fix and recovery steps.
- Do not delete or alter source databases during rehearsal.

### 6. Backup and restore
- Choose backup format, frequency, retention, encryption and storage location.
- Ensure backup storage does not exhaust the SSD.
- Test restore to a separate disposable database.
- Document recovery point and recovery time objectives appropriate to the product.

## Deliverables
- ER diagram and data dictionary.
- Database ownership and retention rules.
- Migration ADR and tested rehearsal plan.
- Versioned migrations.
- Backup/restore runbook and evidence.
- Database integration tests.

## Acceptance criteria
- [ ] Canonical source and data retention are approved.
- [ ] Schema changes are versioned and reviewable.
- [ ] Clean database can be created from migrations.
- [ ] Migration rehearsal preserves expected records and relationships.
- [ ] Cross-user/farm data isolation is tested.
- [ ] Restore from backup is demonstrated.
- [ ] No production data is changed without explicit approval.

## Exit gate
Reviewer accepts the schema, migration evidence, backup/restore evidence and cutover plan.
