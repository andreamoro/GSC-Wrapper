"""Shared pytest fixtures.

The whole suite runs fully offline: no Google credentials, no network.
An ``Account`` is built with empty (``None``) credentials, exactly the way the
manual ``standalone_sync.py`` script builds its fake object, and the
web-property list is
injected directly so ``Account.__getitem__`` never calls the live API.
"""
import sys
from pathlib import Path

import pytest

# Make the package importable when the suite is run from a checkout that has
# not been installed (e.g. a bare CI clone before `pip install -e .`).
sys.path.insert(0, str(Path(__file__).parent.parent))

import gsc_wrapper  # noqa: E402


FAKE_CREDENTIALS = {
    "token": None,
    "refresh_token": None,
    "client_id": None,
    "client_secret": None,
    "token_uri": gsc_wrapper.GOOGLE_TOKEN_URI,
    "scopes": "https://www.googleapis.com/auth/webmasters.readonly",
}

RAW_PROPERTIES = [
    {"siteUrl": "https://www.test1.com/", "permissionLevel": "siteOwner"},
    {"siteUrl": "https://www.test2.com/", "permissionLevel": "siteFullUser"},
    {"siteUrl": "sc-domain:test3.com", "permissionLevel": "siteOwner"},
]


@pytest.fixture
def account():
    """An ``Account`` with a pre-populated, offline web-property list."""
    acct = gsc_wrapper.Account(FAKE_CREDENTIALS)
    acct._webproperties = [
        gsc_wrapper.WebProperty(raw, acct) for raw in RAW_PROPERTIES
    ]
    return acct


@pytest.fixture
def site(account):
    """The first web property of the fake account."""
    return account["https://www.test1.com/"]


@pytest.fixture
def query(site):
    return gsc_wrapper.Query(site)


@pytest.fixture
def inspect(site):
    return gsc_wrapper.InspectURL(site)


# --- async fixtures --------------------------------------------------------
# The async suite is equally offline: a fake, always-valid credentials object
# means the transport never tries to refresh a token, and ``respx`` (used in
# the tests themselves) intercepts the httpx calls so the live API is untouched.

from gsc_wrapper.aio import AsyncAccount  # noqa: E402
from gsc_wrapper.aio.account import AsyncWebProperty  # noqa: E402
from gsc_wrapper.aio.transport import AsyncTransport  # noqa: E402


class FakeCredentials:
    """A minimal stand-in for a ``google-auth`` credentials object.

    It reports itself as always valid and hands out a fixed token, so the
    transport never performs a (network-bound) refresh.
    """

    valid = True
    token = "fake-access-token"
    client_id = "fake-client-id"

    def refresh(self, request):  # pragma: no cover - never called when valid
        raise AssertionError("refresh() must not be called in offline tests")


@pytest.fixture
def fake_credentials():
    return FakeCredentials()


@pytest.fixture
def raw_properties():
    """The raw web-property payloads, as the sites API would return them."""
    return RAW_PROPERTIES


@pytest.fixture
def async_transport(fake_credentials):
    """An ``AsyncTransport`` with a generous rate limit for fast tests."""
    return AsyncTransport(fake_credentials, max_rate=1000, time_period=1)


@pytest.fixture
def async_account(async_transport):
    """An ``AsyncAccount`` backed by the offline transport."""
    return AsyncAccount(FAKE_CREDENTIALS, transport=async_transport)


@pytest.fixture
def async_account_loaded(async_account):
    """An ``AsyncAccount`` with a pre-populated web-property list."""
    async_account._webproperties = [
        AsyncWebProperty(raw, async_account) for raw in RAW_PROPERTIES
    ]
    return async_account


@pytest.fixture
def async_site(async_account_loaded):
    """The first web property of the fake async account."""
    return async_account_loaded._webproperties[0]
