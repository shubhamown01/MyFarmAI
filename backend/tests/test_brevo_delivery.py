"""Brevo HTTP email adapter tests — mocked HTTP, no network."""

import httpx
import pytest

from app.core.config import Settings
from app.services.delivery import (
    BrevoEmailDelivery,
    EmailDeliveryConfigError,
    EmailDeliveryError,
    get_email_delivery,
)

CODE = "483920"
DESTINATION = "farmer@example.com"
API_KEY = "xkeysib-test-secret"


class FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status {self.status_code}",
                request=httpx.Request("POST", "https://api.brevo.com/v3/smtp/email"),
                response=httpx.Response(self.status_code),
            )


class FakeAsyncClient:
    def __init__(self, response: FakeResponse | None = None, exc: Exception | None = None):
        self.response = response or FakeResponse()
        self.exc = exc
        self.posts: list[dict] = []
        self.is_closed = False

    async def post(self, url: str, json: dict | None = None, headers: dict | None = None):
        self.posts.append({"url": url, "json": json, "headers": headers})
        if self.exc:
            raise self.exc
        return self.response

    async def aclose(self) -> None:
        self.is_closed = True


def _adapter(client: FakeAsyncClient) -> BrevoEmailDelivery:
    return BrevoEmailDelivery(api_key=API_KEY, sender="no-reply@myfarmai.test", client=client)


async def test_successful_submission():
    client = FakeAsyncClient()
    await _adapter(client).send_otp(DESTINATION, CODE)

    assert len(client.posts) == 1
    post = client.posts[0]
    assert post["url"] == BrevoEmailDelivery.API_URL
    assert post["headers"]["api-key"] == API_KEY
    assert post["json"]["sender"] == {"email": "no-reply@myfarmai.test"}
    assert post["json"]["to"] == [{"email": DESTINATION}]
    assert CODE in post["json"]["textContent"]


async def test_http_error_raises_delivery_error():
    client = FakeAsyncClient(FakeResponse(400))
    with pytest.raises(EmailDeliveryError):
        await _adapter(client).send_otp(DESTINATION, CODE)


async def test_network_error_raises_delivery_error():
    client = FakeAsyncClient(exc=httpx.ConnectError("refused"))
    with pytest.raises(EmailDeliveryError):
        await _adapter(client).send_otp(DESTINATION, CODE)


def test_missing_configuration_refused():
    with pytest.raises(EmailDeliveryConfigError):
        BrevoEmailDelivery(api_key="", sender="")
    with pytest.raises(EmailDeliveryConfigError):
        BrevoEmailDelivery(api_key=API_KEY, sender="")


async def test_aclose_closes_client():
    client = FakeAsyncClient()
    adapter = _adapter(client)
    await adapter.aclose()
    assert client.is_closed is True


def test_factory_builds_brevo_adapter():
    settings = Settings(
        environment="test",
        email_delivery_mode="brevo",
        brevo_api_key=API_KEY,
        brevo_sender="no-reply@myfarmai.test",
    )
    adapter = get_email_delivery(settings)
    assert isinstance(adapter, BrevoEmailDelivery)
