"""Tests for the async HTTP transport (httpx mocked with respx, no network)."""
import asyncio

import httpx
import pytest
import respx

from gsc_wrapper.aio.transport import (
    AsyncTransport,
    GSCApiError,
    SITES_URL,
)


@respx.mock
async def test_request_returns_json_and_sends_bearer_token(async_transport):
    route = respx.get(SITES_URL).mock(
        return_value=httpx.Response(200, json={"siteEntry": []})
    )

    data = await async_transport.request("GET", SITES_URL)

    assert data == {"siteEntry": []}
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer fake-access-token"


@respx.mock
async def test_post_forwards_json_body(async_transport):
    route = respx.post(SITES_URL).mock(return_value=httpx.Response(200, json={"ok": 1}))

    await async_transport.request("POST", SITES_URL, json={"a": "b"})

    import json as _json
    assert _json.loads(route.calls.last.request.content) == {"a": "b"}


@respx.mock
async def test_error_response_raises_gsc_api_error(async_transport):
    respx.get(SITES_URL).mock(
        return_value=httpx.Response(
            403, json={"error": {"message": "Insufficient permission"}}
        )
    )

    with pytest.raises(GSCApiError) as excinfo:
        await async_transport.request("GET", SITES_URL)

    assert excinfo.value.status_code == 403
    assert "Insufficient permission" in str(excinfo.value)


@respx.mock
async def test_error_without_json_body_falls_back_to_text(async_transport):
    respx.get(SITES_URL).mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(GSCApiError) as excinfo:
        await async_transport.request("GET", SITES_URL)

    assert excinfo.value.status_code == 500
    assert "boom" in excinfo.value.message


class _RefreshingCreds:
    """Credentials that are invalid until refreshed exactly once."""

    token = None

    def __init__(self):
        self.valid = False
        self.refresh_calls = 0

    def refresh(self, request):
        self.refresh_calls += 1
        self.valid = True
        self.token = "refreshed-token"


@respx.mock
async def test_token_refreshed_when_invalid():
    creds = _RefreshingCreds()
    transport = AsyncTransport(creds, max_rate=1000, time_period=1)
    route = respx.get(SITES_URL).mock(return_value=httpx.Response(200, json={}))

    try:
        await transport.request("GET", SITES_URL)
    finally:
        await transport.aclose()

    assert creds.refresh_calls == 1
    assert route.calls.last.request.headers["authorization"] == "Bearer refreshed-token"


@respx.mock
async def test_concurrent_requests_refresh_token_only_once():
    creds = _RefreshingCreds()
    transport = AsyncTransport(creds, max_rate=1000, time_period=1)
    respx.get(SITES_URL).mock(return_value=httpx.Response(200, json={}))

    try:
        await asyncio.gather(
            *(transport.request("GET", SITES_URL) for _ in range(5))
        )
    finally:
        await transport.aclose()

    # The refresh lock must collapse the stampede into a single refresh.
    assert creds.refresh_calls == 1


async def test_externally_supplied_client_is_not_closed(fake_credentials):
    client = httpx.AsyncClient()
    transport = AsyncTransport(fake_credentials, client=client)

    await transport.aclose()

    assert not client.is_closed
    await client.aclose()
