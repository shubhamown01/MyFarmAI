"""Unit tests for security primitives (P3-02/P3-03)."""

from argon2.exceptions import (
    InvalidHashError as _ArgonInvalidHash,  # noqa: F401  (asserts lib present)
)

from app.core.security import (
    generate_refresh_token,
    generate_session_id,
    hash_password,
    hash_token,
    needs_rehash,
    tokens_match,
    verify_password,
)


class TestPasswordHashing:
    def test_round_trip(self) -> None:
        h = hash_password("correct horse battery staple")
        assert h.startswith("$argon2id$")
        assert verify_password("correct horse battery staple", h) is True

    def test_wrong_password_rejected(self) -> None:
        h = hash_password("secret")
        assert verify_password("wrong", h) is False

    def test_malformed_hash_returns_false(self) -> None:
        # Malformed stored hash → plain login failure, never a 500.
        assert verify_password("x", "not-a-hash") is False

    def test_needs_rehash_on_weak_params(self) -> None:
        # A hash made with lower time_cost must trigger rehash.
        from argon2 import PasswordHasher

        weak = PasswordHasher(memory_cost=8192, time_cost=1, parallelism=1).hash("pw")
        assert needs_rehash(weak) is True
        assert needs_rehash(hash_password("pw")) is False

    def test_timing_within_adr_band(self) -> None:
        import time

        h = hash_password("timing-test")
        start = time.perf_counter()
        verify_password("timing-test", h)
        elapsed = time.perf_counter() - start
        # ADR-008 band ≈100–300 ms; allow 60–400 ms for CI jitter.
        assert 0.06 <= elapsed <= 0.4, f"verify took {elapsed * 1000:.0f} ms"


class TestOpaqueTokens:
    def test_session_ids_unique_and_256bit(self) -> None:
        ids = {generate_session_id() for _ in range(100)}
        assert len(ids) == 100
        # urlsafe(32) → 43 chars base64url (256-bit entropy)
        assert all(len(s) >= 43 for s in ids)

    def test_refresh_tokens_unique(self) -> None:
        assert generate_refresh_token() != generate_refresh_token()

    def test_hash_token_deterministic_and_distinct(self) -> None:
        assert hash_token("abc") == hash_token("abc")
        assert hash_token("abc") != hash_token("abd")
        assert len(hash_token("abc")) == 64  # SHA-256 hex

    def test_tokens_match_constant_time_path(self) -> None:
        tok = generate_session_id()
        assert tokens_match(hash_token(tok), tok) is True
        assert tokens_match(hash_token(tok), "forged") is False
