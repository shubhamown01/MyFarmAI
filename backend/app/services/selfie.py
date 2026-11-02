"""Selfie liveness-challenge service (E3 wave 1).

Issues randomized two-action liveness challenges and single-use consumes
them on upload. Mirrors the oauth.py state-store pattern: a module-level
in-memory store with TTL pruning — safe for the approved single-process
deployment; a multi-worker/replica deployment must move this to shared
storage (Redis/DB) first.

Challenges are session-bound: consumption verifies the requesting user_id.
Issuing a new challenge invalidates the user's prior unconsumed one.
"""

import secrets
import time
import uuid

CHALLENGE_TTL_SECONDS = 300

ACTIONS: tuple[str, ...] = (
    "turn head left",
    "turn head right",
    "blink twice",
    "smile",
    "raise eyebrows",
    "tilt head",
)

# challenge_id -> (actions, expiry monotonic, user_id)
_challenges: dict[str, tuple[tuple[str, ...], float, uuid.UUID]] = {}
# user_id -> latest unconsumed challenge_id (re-issue invalidates the prior)
_user_latest: dict[uuid.UUID, str] = {}


class ChallengeInvalidError(Exception):
    """Challenge missing, expired, already consumed, or wrong user."""


def _prune_expired() -> None:
    now = time.monotonic()
    for key in [k for k, (_, exp, _) in _challenges.items() if exp <= now]:
        del _challenges[key]


def issue_challenge(user_id: uuid.UUID) -> tuple[str, tuple[str, ...]]:
    """Create a 2-action challenge for ``user_id``, invalidating their prior one."""
    _prune_expired()
    prior = _user_latest.pop(user_id, None)
    if prior is not None:
        _challenges.pop(prior, None)
    actions = tuple(secrets.SystemRandom().sample(ACTIONS, 2))
    challenge_id = secrets.token_urlsafe(32)[:64]
    _challenges[challenge_id] = (actions, time.monotonic() + CHALLENGE_TTL_SECONDS, user_id)
    _user_latest[user_id] = challenge_id
    return challenge_id, actions


def consume_challenge(challenge_id: str, user_id: uuid.UUID) -> tuple[str, ...]:
    """Single-use pop; returns the actions or raises ChallengeInvalidError."""
    entry = _challenges.pop(challenge_id, None)
    if entry is None:
        raise ChallengeInvalidError("unknown or replayed challenge")
    actions, expiry, owner = entry
    if user_id != owner:
        # Wrong user: do not leave the challenge valid for the owner either —
        # a leaked challenge_id has already been observed cross-user.
        _user_latest.pop(owner, None)
        raise ChallengeInvalidError("challenge does not belong to this user")
    if time.monotonic() > expiry:
        raise ChallengeInvalidError("expired challenge")
    return actions
