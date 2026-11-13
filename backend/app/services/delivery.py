"""OTP delivery adapters (E1) — zero-cost, provider-swappable.

Owner approval 2026-11-01: dev-mode email delivery now (OTP to server log /
file, clearly marked, never pretends to send); a real provider is configured
later via ``settings.email_delivery_mode``.

SMS: an ``SmsDelivery`` protocol interface is defined here for later stages
(E1 scope is email only). No zero-cost SMS provider exists, so
``UnavailableSmsDelivery`` explicitly reports unavailability instead of
pretending to deliver (never fake delivery).
"""

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import httpx

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


class EmailDeliveryError(Exception):
    """Real delivery was attempted and failed; the code did not reach the user."""


class EmailDeliveryConfigError(Exception):
    """SMTP mode was selected but the relay is not configured."""


class SmtpEmailDelivery:
    """Real OTP delivery through an SMTP relay (MFAI-026).

    Uses only the standard library: ``smtplib`` blocks, so the send runs in
    a worker thread and the event loop stays free. Failures raise
    :class:`EmailDeliveryError` with a generic message — credentials, the
    OTP, and the full message body never reach the logs.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        username: str = "",
        password: str = "",
        starttls: bool = True,
        timeout: float = 15.0,
    ) -> None:
        if not host.strip() or not sender.strip():
            raise EmailDeliveryConfigError("smtp_host and smtp_from are required")
        self._host = host.strip()
        self._port = port
        self._sender = sender.strip()
        self._username = username
        self._password = password
        self._starttls = starttls
        self._timeout = timeout

    async def send_otp(self, destination: str, code: str) -> None:
        await asyncio.to_thread(self._send, destination, code)

    def _send(self, destination: str, code: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Your MyFarmAI verification code"
        message["From"] = self._sender
        message["To"] = destination
        message.set_content(
            f"Your MyFarmAI verification code is {code}.\n\n"
            "It expires in 10 minutes. If you did not request it, ignore this email."
        )
        try:
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as smtp:
                if self._starttls:
                    smtp.starttls(context=ssl.create_default_context())
                if self._username:
                    smtp.login(self._username, self._password)
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            # Type name only: SMTP responses and tracebacks can echo addresses
            # and server details into platform logs.
            logger.error("SMTP OTP delivery failed (%s)", type(exc).__name__)
            raise EmailDeliveryError("email delivery failed") from exc


class BrevoEmailDelivery:
    """Real OTP delivery through the Brevo HTTP API (MFAI-027).

    Used when the host blocks outbound SMTP (Render free blocks 25/465/587).
    Credentials and the OTP never reach the logs: only the exception type name
    is recorded.
    """

    API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(
        self,
        *,
        api_key: str,
        sender: str,
        timeout: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip() or not sender.strip():
            raise EmailDeliveryConfigError("brevo_api_key and brevo_sender are required")
        self._api_key = api_key.strip()
        self._sender = sender.strip()
        self._timeout = timeout
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout))
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def send_otp(self, destination: str, code: str) -> None:
        payload = {
            "sender": {"email": self._sender},
            "to": [{"email": destination}],
            "subject": "Your MyFarmAI verification code",
            "textContent": (
                f"Your MyFarmAI verification code is {code}.\n\n"
                "It expires in 10 minutes. If you did not request it, ignore this email."
            ),
        }
        headers = {"api-key": self._api_key, "content-type": "application/json"}
        client = await self._get_client()
        try:
            response = await client.post(self.API_URL, json=payload, headers=headers)
            if response.status_code >= 400:
                raise EmailDeliveryError("email delivery failed")
        except httpx.HTTPError as exc:
            logger.error("Brevo OTP delivery failed (%s)", type(exc).__name__)
            raise EmailDeliveryError("email delivery failed") from exc


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

    ``smtp`` builds a real relay adapter and raises when it is unconfigured —
    a missing host must not degrade into "pretend we sent it". Unknown modes
    raise in production and fall back to the dev adapter (with a redacted
    code) everywhere else.
    """
    mode = settings.email_delivery_mode
    environment = getattr(settings, "environment", "")
    if mode == "smtp":
        return SmtpEmailDelivery(
            host=getattr(settings, "smtp_host", ""),
            port=getattr(settings, "smtp_port", 587),
            sender=getattr(settings, "smtp_from", ""),
            username=getattr(settings, "smtp_user", ""),
            password=getattr(settings, "smtp_password", ""),
            starttls=getattr(settings, "smtp_starttls", True),
            timeout=getattr(settings, "smtp_timeout_seconds", 15.0),
        )
    if mode == "brevo":
        return BrevoEmailDelivery(
            api_key=getattr(settings, "brevo_api_key", ""),
            sender=getattr(settings, "brevo_sender", ""),
            timeout=getattr(settings, "smtp_timeout_seconds", 15.0),
        )
    if mode != "dev":
        if environment == "production":
            raise EmailDeliveryConfigError(f"unknown email_delivery_mode '{mode}'")
        logger.error(
            "email_delivery_mode='%s' has no adapter — falling back to dev-mode delivery",
            mode,
        )
    return DevModeEmailDelivery(
        outbox_path=getattr(settings, "otp_outbox_path", None),
        redact_code=environment == "production",
    )
