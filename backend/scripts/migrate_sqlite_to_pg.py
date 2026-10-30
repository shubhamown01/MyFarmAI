"""SQLite (legacy) -> PostgreSQL migration tool for MyFarmAI.

Rehearsal tooling for Phase 2 (P2-23..P2-26). The canonical SQLite database
(`backend/data/app.db`) is opened READ-ONLY; this script never modifies it.

Legacy schema:
    conversations(id TEXT PK, created_at, updated_at, language, crop, location)
    messages(id INTEGER PK, conversation_id FK, role, content, created_at)

Target schema (Alembic 6cd2bffd9881):
    users / conversations / messages with UUID PKs, TIMESTAMPTZ, ownership columns.

Transform rules:
- All legacy conversation ids are UUID strings and are preserved as-is.
- A single `legacy_import` user (nil UUID, is_active=false) owns all migrated
  conversations; no real user is impersonated.
- Legacy naive timestamps (SQLite CURRENT_TIMESTAMP) are interpreted as UTC and
  stored as UTC TIMESTAMPTZ.
- Message roles are upper-cased and validated against {USER, ASSISTANT, SYSTEM}.
- conversations.message_count is recomputed from the messages table.

Usage:
    uv run python scripts/migrate_sqlite_to_pg.py export --db data/app.db --out /tmp/export
    uv run python scripts/migrate_sqlite_to_pg.py load --export /tmp/export --dsn postgresql://...
    uv run python scripts/migrate_sqlite_to_pg.py validate --export /tmp/export --dsn postgresql://...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import timezone
from pathlib import Path
from uuid import UUID

import psycopg

LEGACY_USER_ID = UUID("00000000-0000-0000-0000-000000000000")
LEGACY_USER_EMAIL = "legacy_import@myfarmai.internal"
VALID_ROLES = {"USER", "ASSISTANT", "SYSTEM"}


def _parse_utc(value: str) -> str:
    """Parse a naive legacy timestamp and render it as UTC ISO-8601."""
    from datetime import datetime

    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_export(db: Path, out: Path) -> None:
    """Export legacy tables to JSON and record SHA-256 of source + export."""
    out.mkdir(parents=True, exist_ok=True)
    src_hash = _sha256(db)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        conversations = [
            {
                "id": row[0],
                "created_at": _parse_utc(row[1]),
                "updated_at": _parse_utc(row[2]),
                "language": row[3],
                "crop": row[4],
                "location": row[5],
            }
            for row in con.execute(
                "SELECT id, created_at, updated_at, language, crop, location "
                "FROM conversations ORDER BY id"
            )
        ]
        messages = [
            {
                "id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "created_at": _parse_utc(row[4]),
            }
            for row in con.execute(
                "SELECT id, conversation_id, role, content, created_at "
                "FROM messages ORDER BY id"
            )
        ]
    finally:
        con.close()

    counts_path = out / "counts.json"
    counts = {
        "conversations": len(conversations),
        "messages": len(messages),
        "source_sha256": src_hash,
    }
    counts_path.write_text(json.dumps(counts, indent=2))

    conv_path = out / "conversations.json"
    msg_path = out / "messages.json"
    conv_path.write_text(json.dumps(conversations))
    msg_path.write_text(json.dumps(messages))

    manifest = {
        "source_db": str(db),
        "source_sha256": src_hash,
        "conversations_sha256": _sha256(conv_path),
        "messages_sha256": _sha256(msg_path),
        "conversations": len(conversations),
        "messages": len(messages),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


def _load_export(export: Path) -> tuple[list[dict], list[dict], dict]:
    manifest = json.loads((export / "manifest.json").read_text())
    conversations = json.loads((export / "conversations.json").read_text())
    messages = json.loads((export / "messages.json").read_text())
    # Verify export integrity before touching the database.
    assert _sha256(export / "conversations.json") == manifest["conversations_sha256"], (
        "conversations.json hash mismatch"
    )
    assert _sha256(export / "messages.json") == manifest["messages_sha256"], (
        "messages.json hash mismatch"
    )
    assert len(conversations) == manifest["conversations"]
    assert len(messages) == manifest["messages"]
    return conversations, messages, manifest


def _validate_transform(conversations: list[dict], messages: list[dict]) -> None:
    conv_ids = {c["id"] for c in conversations}
    for c in conversations:
        UUID(c["id"])  # raises if not a UUID
    counts: dict[str, int] = {}
    for m in messages:
        role = m["role"].upper()
        if role not in VALID_ROLES:
            raise ValueError(f"message {m['id']}: invalid role {m['role']!r}")
        m["role"] = role
        if m["conversation_id"] not in conv_ids:
            raise ValueError(f"message {m['id']}: orphan (no conversation {m['conversation_id']})")
        counts[m["conversation_id"]] = counts.get(m["conversation_id"], 0) + 1
    for c in conversations:
        c["user_id"] = str(LEGACY_USER_ID)
        c["farm_id"] = None
        c["model_name"] = None
        c["model_version"] = None
        c["is_archived"] = False
        c["message_count"] = counts.get(c["id"], 0)


def cmd_load(export: Path, dsn: str) -> None:
    """Transform and load into PostgreSQL via COPY inside one transaction."""
    conversations, messages, manifest = _load_export(export)
    _validate_transform(conversations, messages)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            existing = cur.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()
            assert existing is not None
            if existing[0] > 0:
                sys.exit(
                    f"REFUSING to load: target conversations table already has "
                    f"{existing[0]} rows. Load only into an empty/rehearsal database."
                )
        # Single transaction: legacy user + conversations + messages.
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, email_verified, password_hash,
                                   preferred_language, timezone, is_active, role)
                VALUES (%s, %s, false, %s, 'en', 'UTC', false, 'USER')
                ON CONFLICT (id) DO NOTHING
                """,
                (str(LEGACY_USER_ID), LEGACY_USER_EMAIL, "!legacy-import-no-login"),
            )
            buf = []
            for c in conversations:
                buf.append(
                    "\t".join(
                        [
                            c["id"],
                            c["user_id"],
                            "\\N" if c["farm_id"] is None else c["farm_id"],
                            c["language"],
                            c["crop"] or "\\N",
                            c["location"] or "\\N",
                            "\\N",
                            "\\N",
                            "f",
                            str(c["message_count"]),
                            c["created_at"],
                            c["updated_at"],
                        ]
                    )
                )
            with cur.copy(
                "COPY conversations (id, user_id, farm_id, language, crop, location, "
                "model_name, model_version, is_archived, message_count, created_at, updated_at) "
                "FROM STDIN"
            ) as copy:
                copy.write("\n".join(buf) + "\n" if buf else "")
            buf = []
            for m in messages:
                buf.append(
                    "\t".join(
                        [
                            str(m["id"]),
                            m["conversation_id"],
                            m["role"],
                            m["content"].replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r"),
                            "\\N",
                            "\\N",
                            "\\N",
                            "\\N",
                            m["created_at"],
                            m["created_at"],
                        ]
                    )
                )
            with cur.copy(
                "COPY messages (id, conversation_id, role, content, model_name, "
                "model_version, token_count, finish_reason, created_at, updated_at) "
                "FROM STDIN"
            ) as copy:
                copy.write("\n".join(buf) + "\n" if buf else "")
            # COPY with explicit ids does not advance the serial sequence; the
            # next app INSERT would collide. Realign it to the loaded maximum.
            cur.execute(
                "SELECT setval(pg_get_serial_sequence('messages', 'id'), "
                "COALESCE((SELECT MAX(id) FROM messages), 1))"
            )
        conn.commit()
    print(f"Loaded {len(conversations)} conversations, {len(messages)} messages "
          f"(source sha256 {manifest['source_sha256'][:16]}...)")


def cmd_validate(export: Path, dsn: str) -> None:
    """Compare target row counts and per-conversation counts against the export."""
    conversations, messages, _manifest = _load_export(export)
    expected_conv = len(conversations)
    expected_msg = len(messages)
    per_conv: dict[str, int] = {}
    for m in messages:
        per_conv[m["conversation_id"]] = per_conv.get(m["conversation_id"], 0) + 1

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            (n_users,) = cur.execute(
                "SELECT COUNT(*) FROM users WHERE id = %s", (str(LEGACY_USER_ID),)
            ).fetchone()
            (n_conv,) = cur.execute("SELECT COUNT(*) FROM conversations").fetchone()
            (n_msg,) = cur.execute("SELECT COUNT(*) FROM messages").fetchone()
            (orphans,) = cur.execute(
                "SELECT COUNT(*) FROM messages m LEFT JOIN conversations c "
                "ON m.conversation_id = c.id WHERE c.id IS NULL"
            ).fetchone()
            (bad_counts,) = cur.execute(
                """
                SELECT COUNT(*) FROM conversations c
                WHERE c.message_count <> (
                    SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id
                )
                """
            ).fetchone()
            (bad_roles,) = cur.execute(
                "SELECT COUNT(*) FROM messages WHERE role NOT IN ('USER','ASSISTANT','SYSTEM')"
            ).fetchone()
            per_conv_db = dict(
                cur.execute(
                    "SELECT conversation_id::text, COUNT(*) FROM messages GROUP BY conversation_id"
                ).fetchall()
            )

    checks = {
        "legacy_user_present": n_users == 1,
        "conversation_count": n_conv == expected_conv,
        "message_count": n_msg == expected_msg,
        "no_orphan_messages": orphans == 0,
        "message_count_column_consistent": bad_counts == 0,
        "roles_valid": bad_roles == 0,
        "per_conversation_counts_match": per_conv_db == per_conv,
    }
    print(f"users(legacy)={n_users} conversations={n_conv} (expect {expected_conv}) "
          f"messages={n_msg} (expect {expected_msg}) orphans={orphans} "
          f"bad_message_count={bad_counts} bad_roles={bad_roles}")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not all(checks.values()):
        sys.exit(1)
    print("VALIDATION PASSED")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("export", help="Export legacy SQLite to JSON (read-only)")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)

    p = sub.add_parser("load", help="Transform + COPY into PostgreSQL (one transaction)")
    p.add_argument("--export", type=Path, required=True)
    p.add_argument("--dsn", required=True)

    p = sub.add_parser("validate", help="Validate PostgreSQL contents against export")
    p.add_argument("--export", type=Path, required=True)
    p.add_argument("--dsn", required=True)

    args = parser.parse_args()
    if args.command == "export":
        cmd_export(args.db, args.out)
    elif args.command == "load":
        cmd_load(args.export, args.dsn)
    else:
        cmd_validate(args.export, args.dsn)


if __name__ == "__main__":
    main()
