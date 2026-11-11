"""Create or promote a MyFarmAI administrator.

The first administrator cannot be created through the API: public
registration produces ordinary pending users, and only an administrator can
approve them. This script is the owner-operated bootstrap and recovery path.

Safety properties:
- the password is read from a hidden prompt or stdin, never from argv (argv
  lands in shell history and process listings);
- nothing is printed except the account id and email — no password, no hash;
- an existing account is promoted, not duplicated, which is also the
  recovery path when the only administrator loses access;
- the account is created ``active`` because an administrator must not be
  blocked by the verification gate it operates.

Usage (from ``backend/``):
    .venv/bin/python scripts/create_admin.py --email owner@example.com
    .venv/bin/python scripts/create_admin.py --email owner@example.com --full-name "Owner"

Password rules mirror the API (8–128 characters).
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.models.user import User, UserRole  # noqa: E402
from app.db.session import db_manager  # noqa: E402

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def _read_password() -> str:
    if sys.stdin.isatty():
        first = getpass.getpass("New administrator password: ")
        second = getpass.getpass("Repeat password: ")
        if first != second:
            raise SystemExit("Passwords do not match.")
        return first
    # Non-interactive: exactly one line on stdin, e.g. from a secret manager.
    return sys.stdin.readline().rstrip("\n")


async def _create_or_promote(email: str, password: str, full_name: str | None) -> tuple[User, bool]:
    from sqlalchemy import select

    async with db_manager.session() as session:
        user = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        created = user is None
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
                verification_status="active",
                email_verified=True,
            )
            session.add(user)
        else:
            user.password_hash = hash_password(password)
            user.role = UserRole.ADMIN
            user.is_active = True
            user.verification_status = "active"
            if full_name:
                user.full_name = full_name
        await session.flush()
        return user, created


async def main() -> int:
    parser = argparse.ArgumentParser(description="Create or promote a MyFarmAI administrator.")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--full-name", default=None, help="Optional display name")
    args = parser.parse_args()

    email = args.email.strip().lower()
    if "@" not in email:
        print("Refusing: that does not look like an email address.", file=sys.stderr)
        return 2

    password = _read_password()
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        print(
            f"Refusing: password must be {MIN_PASSWORD_LENGTH}–{MAX_PASSWORD_LENGTH} characters.",
            file=sys.stderr,
        )
        return 2

    db_manager.initialize()
    try:
        user, created = await _create_or_promote(email, password, args.full_name)
    finally:
        await db_manager.close()

    print(f"{'Created' if created else 'Promoted'} administrator: {user.email} (id={user.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
