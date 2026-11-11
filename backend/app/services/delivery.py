"""OTP delivery adapters (E1) — zero-cost, provider-swappable.

Owner approval 2026-11-01: dev-mode email delivery now (OTP to server log /
file, clearly marked, never pretends to send); a real provider is configured
later via ``settings.email_delivery_mode``.

SMS: an ``SmsDelivery`` protocol interface is defined here for later stages
(E1 scope is email only). No zero-cost SMS provider exists, so
``UnavailableSmsDelivery`` explicitly reports unavailability instead of
pretending to deliver (never fake delivery).
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger("myfarmai.delivery")

# Dev-mode outbox (fail-open: only the log line is guaranteed).
_OTP_OUTBOX = Path("/tmp/opencode/dev_otp_outbox.txt")


class EmailDelivery(Protocol):
    """Delivery adapter for email OTP codes."""

    async def send_otp(self, destination: str, code: str) -> None:
        """Deliver ``code`` to ``destination``. Raises on delivery failure."""
        ...


class DevModeEmailDelivery:
    """Dev-mode adapter: logs the OTP and appends it to a local outbox file.

    NEVER actually delivers email — the log line is clearly marked. The
    outbox append is best-effort (read-only filesystem → log-only).
    """

    def __init__(self, outbox_path: Path | None = None, *, redact_code: bool = False) -> None:
        self._outbox = Path(outbox_path) if outbox_path else _OTP_OUTBOX
        # In production the code must never reach the logs: OTP verification can
        # reset a password, so a log reader would get account takeover.
        self._redact_code = redact_code

    async def send_otp(self, destination: str, code: str) -> None:
        if self._redact_code:
            logger.warning(
                "DEV-MODE OTP — NOT ACTUALLY DELIVERED (code redacted in production): "
                "destination=%s",
                destination,
            )
        else:
            logger.warning(
                "DEV-MODE OTP — NOT ACTUALLY DELIVERED: destination=%s code=%s",
                destination,
                code,
            )
        try:
            # The parent directory may not exist (fresh container) — create it
            # instead of silently dropping the code (fail-open hid this once).
            self._outbox.parent.mkdir(parents=True, exist_ok=True)
            with self._outbox.open("a", encoding="utf-8") as f:
                f.write(
                    f"DEV-MODE OTP — NOT ACTUALLY DELIVERED destination={destination} code={code}\n"
                )
        except OSError:
            pass  # fail open: the log line above is authoritative


class SmsDelivery(Protocol):
    """Delivery adapter for SMS OTP codes (reserved for later stages)."""

    async def send_otp(self, destination: str, code: str) -> None:
        """Deliver ``code`` to ``destination``. Raises on delivery failure."""
        ...


class SmsDeliveryUnavailableError(Exception):
    """No approved SMS provider is configured; delivery is impossible."""


class UnavailableSmsDelivery:
    """Explicit 'temporarily unavailable' SMS adapter (owner approval 2026-11-01).

    No zero-cost SMS provider exists; this adapter refuses to deliver rather
    than pretending to. Phone-OTP endpoints (later stages) must map
    SmsDeliveryUnavailableError to a clean error response.
    """

    async def send_otp(self, destination: str, code: str) -> None:
        raise SmsDeliveryUnavailableError("SMS delivery is temporarily unavailable")


def get_email_delivery(settings: "Settings") -> EmailDelivery:
    """Factory: pick the email delivery adapter from settings.

    Unknown modes fall back to dev-mode with a warning (never fail signup
    because of a typo'd mode value).
    """
    mode = settings.email_delivery_mode
    if mode == "dev":
        return DevModeEmailDelivery(
            outbox_path=getattr(settings, "otp_outbox_path", None),
            redact_code=getattr(settings, "environment", "") == "production",
        )
    # No real provider adapter exists yet (MFAI-026). Unknown modes fall back to
    # dev rather than failing signup, but the code is redacted in production.
    logger.error(
        "email_delivery_mode='%s' has no adapter — falling back to dev-mode delivery",
        mode,
    )
    return DevModeEmailDelivery(
        outbox_path=getattr(settings, "otp_outbox_path", None),
        redact_code=getattr(settings, "environment", "") == "production",
    )
