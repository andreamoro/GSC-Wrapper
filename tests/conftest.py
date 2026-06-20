"""Shared pytest fixtures.

The whole suite runs fully offline: no Google credentials, no network.
An ``Account`` is built with empty (``None``) credentials, exactly the way the
manual ``test.py`` script builds its fake object, and the web-property list is
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
