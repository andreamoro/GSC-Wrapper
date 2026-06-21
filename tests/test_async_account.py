"""Tests for AsyncAccount / AsyncWebProperty (httpx mocked, no network)."""
import httpx
import pytest
import respx

import gsc_wrapper
from gsc_wrapper.aio import AsyncAccount, AsyncInspectURL, AsyncQuery
from gsc_wrapper.aio.account import AsyncWebProperty
from gsc_wrapper.aio.transport import SITES_URL


def test_requires_credentials():
    with pytest.raises(ValueError):
        AsyncAccount(None)


def test_exposed_at_top_level():
    assert gsc_wrapper.AsyncAccount is AsyncAccount


@respx.mock
async def test_webproperties_fetches_and_caches(async_account, raw_properties):
    route = respx.get(SITES_URL).mock(
        return_value=httpx.Response(200, json={"siteEntry": raw_properties})
    )

    properties = await async_account.webproperties()

    assert [p.url for p in properties] == [r["siteUrl"] for r in raw_properties]
    assert all(isinstance(p, AsyncWebProperty) for p in properties)

    # Second call is served from cache: the API is hit exactly once.
    await async_account.webproperties()
    assert route.call_count == 1


async def test_webproperty_by_url_and_index(async_account_loaded):
    by_url = await async_account_loaded.webproperty("https://www.test2.com/")
    assert by_url.url == "https://www.test2.com/"

    by_index = await async_account_loaded.webproperty(0)
    assert by_index.url == "https://www.test1.com/"

    missing = await async_account_loaded.webproperty("https://nope.com/")
    assert missing is None


async def test_async_context_manager_closes_transport(async_account):
    async with async_account as acct:
        assert acct is async_account
    assert async_account.transport._client.is_closed


def test_webproperty_query_and_inspect_builders(async_site):
    assert isinstance(async_site.query, AsyncQuery)
    assert isinstance(async_site.inspect, AsyncInspectURL)
    # Each access returns a fresh, independent builder.
    assert async_site.query is not async_site.query


def test_repr_uses_client_id(async_account):
    assert "AsyncAccount" in repr(async_account)
