"""Password hashing (Argon2id) and opaque token primitives (ADR-008).

Argon2id parameters are tuned on the target host (7 GiB RAM) to land in the
≈100–300 ms verification band required by ADR-008. Measured 2026-10-28:
m=131072/t=3/p=4 → ~114 ms per verify. Re-verify if host hardware changes.
"""

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# memory_cost KiB, time_cost, parallelism — see module docstring for timing.
_argon2 = PasswordHasher(memory_cost=131072, time_cost=3, parallelism=4)


class InvalidPasswordHashError(ValueError):
    """Raised when a stored hash is malformed."""


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return _argon2.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password; returns False on mismatch or malformed hash.

    A malformed stored hash must surface as a plain login failure (the
    caller records it and raises InvalidCredentialsError) — never a 500.
    """
    try:
        return _argon2.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when stored hash params are weaker than current policy."""
    return _argon2.check_needs_rehash(password_hash)


def generate_session_id() -> str:
    """Generate an opaque web session ID (256-bit)."""
    return secrets.token_urlsafe(32)


def generate_refresh_token() -> str:
    """Generate an opaque Android refresh token (256-bit)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """SHA-256 hex digest of an opaque token — the only stored form (ADR-008)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(stored_hash: str, presented_token: str) -> bool:
    """Constant-time token comparison against the stored hash."""
    return hmac.compare_digest(stored_hash, hash_token(presented_token))
