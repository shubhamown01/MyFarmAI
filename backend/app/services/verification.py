"""Email-OTP verification service (E1 — passwordless registration).

Flow: a request creates a pending (inactive, unverified) User up front and
delivers a 6-digit code via the configured delivery adapter; successful
verification consumes the code, activates the user, and establishes a
session through the SAME AuthService session-creation path as password
login (web HttpOnly cookie).

Privacy-aware: every response is identical whether or not the email was
known — callers must surface a generic "if the address is valid, a code was
sent" message.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.models.identity import AuthenticationAccount, ContactVerification
from app.db.models.user import User
from app.services.auth import AuthService
from app.services.delivery import EmailDelivery

OTP_TTL_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_LENGTH = 6


class OTPInvalidError(Exception):
    """No pending verification, wrong code, or code already consumed."""


class OTPExpiredError(Exception):
    """The pending verification code has expired."""


class OTPMaxAttemptsError(Exception):
    """Too many wrong codes for the pending verification."""


class OTPResendCooldownError(Exception):
    """A code was requested too recently (resend cooldown)."""


class VerificationService:
    """Passwordless email signup/verification (E1)."""

    def __init__(self, session: AsyncSession, settings: Settings, delivery: EmailDelivery):
        self._session = session
        self._settings = settings
        self._delivery = delivery
        self._auth = AuthService(session, settings)

    # -- request ------------------------------------------------------------

    async def request_email_otp(self, email: str) -> None:
        """Issue an OTP for ``email`` (creating a pending user if unknown).

        Never reveals whether the email existed — callers return a generic
        200 either way. Raises OTPResendCooldownError within the cooldown.
        """
        email = email.strip().lower()
        now = datetime.now(UTC)

        # Resend cooldown on the latest row for this destination.
        latest = (
            await self._session.execute(
                select(ContactVerification)
                .where(ContactVerification.channel == "email")
                .where(ContactVerification.destination == email)
                .order_by(ContactVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest is not None:
            created = latest.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if now - created < timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS):
                raise OTPResendCooldownError("code recently requested")

        user = (
            await self._session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user is None:
            # Pending user: inactive + unverified, unusable random password.
            user = User(
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                is_active=False,
                email_verified=False,
            )
            self._session.add(user)
            await self._session.flush()

        account = (
            await self._session.execute(
                select(AuthenticationAccount)
                .where(AuthenticationAccount.provider == "email_otp")
                .where(AuthenticationAccount.provider_account_id == email)
            )
        ).scalar_one_or_none()
        if account is None:
            self._session.add(
                AuthenticationAccount(
                    user_id=user.id, provider="email_otp", provider_account_id=email
                )
            )

        code = f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"
        self._session.add(
            ContactVerification(
                user_id=user.id,
                channel="email",
                destination=email,
                code_hash=hash_password(code),
                expires_at=now + timedelta(minutes=OTP_TTL_MINUTES),
            )
        )
        await self._session.flush()
        await self._delivery.send_otp(email, code)

    # -- verify ---------------------------------------------------------------

    async def verify_email_otp(
        self,
        email: str,
        code: str,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str]:
        """Verify ``code``; on success activate the user and open a session.

        Returns (user, session_id) — the web cookie session, established via
        the existing AuthService login path. Single-use: the row is consumed
        on success. Raises OTPInvalidError / OTPExpiredError /
        OTPMaxAttemptsError.
        """
        email = email.strip().lower()
        now = datetime.now(UTC)

        row = (
            await self._session.execute(
                select(ContactVerification)
                .where(ContactVerification.destination == email)
                .where(ContactVerification.channel == "email")
                .where(ContactVerification.consumed_at.is_(None))
                .order_by(ContactVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            raise OTPInvalidError("no pending verification")
        if row.attempts >= row.max_attempts:
            raise OTPMaxAttemptsError("too many attempts")

        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires <= now:
            raise OTPExpiredError("code expired")

        if not verify_password(code, row.code_hash):
            row.attempts += 1
            # Commit before raising: the DI session rolls back on exceptions,
            # which would lose the increment and defeat brute-force limiting.
            await self._session.commit()
            if row.attempts >= row.max_attempts:
                raise OTPMaxAttemptsError("too many attempts")
            raise OTPInvalidError("wrong code")

        # Success: consume the code, activate the user, open a session.
        row.consumed_at = now
        user = await self._session.get(User, row.user_id)
        assert user is not None  # FK guarantees the row exists
        user.email_verified = True
        user.is_active = True
        session_id, _ = await self._auth._establish_session(
            user, client_ip=client_ip, user_agent=user_agent, android=False
        )
        return user, session_id
