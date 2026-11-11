"""SMTP OTP delivery adapter (MFAI-026).

Every test replaces ``smtplib.SMTP`` with a fake: no socket is ever opened.
The cases mirror the release requirements — success, missing configuration,
bad credentials, timeout, server rejection, STARTTLS failure, safe logging,
dev behaviour, and production startup refusal.
"""

import logging
import smtplib

import pytest

from app.core.config import Settings
from app.services import delivery as delivery_mod
from app.services.delivery import (
    DevModeEmailDelivery,
    EmailDeliveryConfigError,
    EmailDeliveryError,
    SmtpEmailDelivery,
    get_email_delivery,
)

CODE = "483920"
DESTINATION = "farmer@example.com"
PASSWORD = "relay-secret-do-not-log"


class FakeSMTP:
    """Records every call; class attributes let a test inject a failure."""

    instances: list["FakeSMTP"] = []
    fail_on: str | None = None
    fail_with: Exception | None = None
    sent: list[object] = []

    def __init__(self, host: str, port: int, timeout: float | None = None) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_called = False
        self.logged_in: tuple[str, str] | None = None
        FakeSMTP.instances.append(self)
        if FakeSMTP.fail_on == "connect":
            assert FakeSMTP.fail_with is not None
            raise FakeSMTP.fail_with

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def starttls(self, context: object | None = None) -> None:
        self.starttls_called = True
        if FakeSMTP.fail_on == "starttls":
            assert FakeSMTP.fail_with is not None
            raise FakeSMTP.fail_with

    def login(self, username: str, password: str) -> None:
        self.logged_in = (username, password)
        if FakeSMTP.fail_on == "login":
            assert FakeSMTP.fail_with is not None
            raise FakeSMTP.fail_with

    def send_message(self, message: object) -> None:
        if FakeSMTP.fail_on == "send":
            assert FakeSMTP.fail_with is not None
            raise FakeSMTP.fail_with
        FakeSMTP.sent.append(message)


@pytest.fixture
def fake_smtp(monkeypatch: pytest.MonkeyPatch) -> type[FakeSMTP]:
    FakeSMTP.instances = []
    FakeSMTP.sent = []
    FakeSMTP.fail_on = None
    FakeSMTP.fail_with = None
    monkeypatch.setattr(delivery_mod.smtplib, "SMTP", FakeSMTP)
    return FakeSMTP


def _adapter(**over: object) -> SmtpEmailDelivery:
    values: dict[str, object] = {
        "host": "smtp.example.com",
        "port": 587,
        "sender": "no-reply@myfarmai.example.com",
        "username": "relay-user",
        "password": PASSWORD,
    }
    values.update(over)
    return SmtpEmailDelivery(**values)  # type: ignore[arg-type]


# -- delivery -----------------------------------------------------------------


async def test_successful_submission(fake_smtp: type[FakeSMTP]) -> None:
    await _adapter().send_otp(DESTINATION, CODE)

    assert len(fake_smtp.sent) == 1
    message = fake_smtp.sent[0]
    assert message["To"] == DESTINATION  # type: ignore[index]
    assert message["From"] == "no-reply@myfarmai.example.com"  # type: ignore[index]
    assert CODE in message.get_content()  # type: ignore[attr-defined]

    instance = fake_smtp.instances[0]
    assert instance.starttls_called is True
    assert instance.logged_in == ("relay-user", PASSWORD)
    assert instance.timeout == 15.0


async def test_no_auth_when_username_blank(fake_smtp: type[FakeSMTP]) -> None:
    await _adapter(username="", password="").send_otp(DESTINATION, CODE)
    assert fake_smtp.instances[0].logged_in is None


async def test_starttls_disabled(fake_smtp: type[FakeSMTP]) -> None:
    await _adapter(starttls=False).send_otp(DESTINATION, CODE)
    assert fake_smtp.instances[0].starttls_called is False


# -- configuration failures ---------------------------------------------------


def test_missing_host_or_sender_raises() -> None:
    with pytest.raises(EmailDeliveryConfigError):
        _adapter(host="")
    with pytest.raises(EmailDeliveryConfigError):
        _adapter(sender="  ")


def test_factory_builds_smtp_adapter(tmp_path) -> None:
    adapter = get_email_delivery(
        Settings(
            email_delivery_mode="smtp",
            smtp_host="smtp.example.com",
            smtp_from="no-reply@myfarmai.example.com",
            smtp_user="relay-user",
            smtp_password=PASSWORD,
            otp_outbox_path=str(tmp_path / "outbox.txt"),
        )
    )
    assert isinstance(adapter, SmtpEmailDelivery)


def test_factory_rejects_unconfigured_smtp() -> None:
    """SMTP mode without a relay must not degrade into a fake success."""
    with pytest.raises(EmailDeliveryConfigError):
        get_email_delivery(
            Settings(
                email_delivery_mode="smtp",
                smtp_host="",
                smtp_from="",
                otp_outbox_path="/tmp/unused-outbox.txt",
            )
        )


def test_production_unknown_mode_raises() -> None:
    with pytest.raises(EmailDeliveryConfigError):
        get_email_delivery(
            Settings(environment="production", email_delivery_mode="sendgrid")
        )


def test_dev_mode_is_unchanged(tmp_path) -> None:
    adapter = get_email_delivery(
        Settings(
            environment="development",
            email_delivery_mode="dev",
            otp_outbox_path=str(tmp_path / "outbox.txt"),
        )
    )
    assert isinstance(adapter, DevModeEmailDelivery)


# -- delivery failures --------------------------------------------------------


async def test_invalid_credentials_raise_delivery_error(fake_smtp: type[FakeSMTP]) -> None:
    fake_smtp.fail_on = "login"
    fake_smtp.fail_with = smtplib.SMTPAuthenticationError(535, b"auth failed")
    with pytest.raises(EmailDeliveryError):
        await _adapter().send_otp(DESTINATION, CODE)


async def test_connection_timeout_raises_delivery_error(fake_smtp: type[FakeSMTP]) -> None:
    fake_smtp.fail_on = "connect"
    fake_smtp.fail_with = TimeoutError("timed out")
    with pytest.raises(EmailDeliveryError):
        await _adapter().send_otp(DESTINATION, CODE)


async def test_server_rejection_raises_delivery_error(fake_smtp: type[FakeSMTP]) -> None:
    fake_smtp.fail_on = "send"
    fake_smtp.fail_with = smtplib.SMTPRecipientsRefused({DESTINATION: (550, b"no such user")})
    with pytest.raises(EmailDeliveryError):
        await _adapter().send_otp(DESTINATION, CODE)


async def test_starttls_failure_raises_delivery_error(fake_smtp: type[FakeSMTP]) -> None:
    fake_smtp.fail_on = "starttls"
    fake_smtp.fail_with = smtplib.SMTPNotSupportedError("STARTTLS not supported")
    with pytest.raises(EmailDeliveryError):
        await _adapter().send_otp(DESTINATION, CODE)


async def test_logging_never_contains_secrets(
    fake_smtp: type[FakeSMTP], caplog: pytest.LogCaptureFixture
) -> None:
    """A relay failure must not put the OTP, password, or address in the log."""
    fake_smtp.fail_on = "login"
    fake_smtp.fail_with = smtplib.SMTPAuthenticationError(535, b"auth failed")
    with caplog.at_level(logging.DEBUG), pytest.raises(EmailDeliveryError):
        await _adapter().send_otp(DESTINATION, CODE)

    assert CODE not in caplog.text
    assert PASSWORD not in caplog.text
    assert DESTINATION not in caplog.text
    assert "SMTPAuthenticationError" in caplog.text


# -- production startup -------------------------------------------------------


def _prod(**over: object) -> Settings:
    base: dict[str, object] = {
        "environment": "production",
        "cors_allowed_origins": "https://farm.example.com",
        "trusted_proxy_cidrs": "10.0.0.0/8",
        "allowed_hosts": "farm.example.com",
        "database_path": "/app/data/app.db",
        "ollama_base_url": "http://ollama.internal:11434",
        "email_delivery_mode": "smtp",
        "smtp_host": "smtp.example.com",
        "smtp_from": "no-reply@myfarmai.example.com",
    }
    base.update(over)
    return Settings(**base)  # type: ignore[arg-type]


def test_production_with_smtp_configured_has_no_email_error() -> None:
    errors = _prod().validate_for_environment()
    assert not [e for e in errors if "email" in e or "smtp" in e]


def test_production_with_dev_delivery_fails_startup() -> None:
    errors = _prod(email_delivery_mode="dev").validate_for_environment()
    assert any("email_delivery_mode" in e for e in errors)


def test_production_with_blank_smtp_host_fails_startup() -> None:
    errors = _prod(smtp_host="").validate_for_environment()
    assert any("smtp_host" in e for e in errors)


def test_development_does_not_require_smtp() -> None:
    errors = Settings(environment="development").validate_for_environment()
    assert not [e for e in errors if "email" in e or "smtp" in e]
