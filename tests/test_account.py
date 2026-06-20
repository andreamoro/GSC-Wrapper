"""Tests for ``Account`` and ``WebProperty`` (offline, no live API calls)."""
import pytest

import gsc_wrapper


def test_account_requires_credentials():
    with pytest.raises(Exception):
        gsc_wrapper.Account(None)


def test_account_repr(account):
    assert "gsc_wrapper.account" in repr(account)


def test_getitem_by_url(account):
    site = account["https://www.test1.com/"]
    assert isinstance(site, gsc_wrapper.WebProperty)
    assert site.url == "https://www.test1.com/"


def test_getitem_by_index(account):
    assert account[0].url == "https://www.test1.com/"
    assert account[1].url == "https://www.test2.com/"


def test_getitem_unknown_url_returns_none(account):
    assert account["https://does-not-exist.com/"] is None


def test_webproperty_attributes(site):
    assert site.url == "https://www.test1.com/"
    assert site.permission == "siteOwner"
    assert "WebProperty" in repr(site)


def test_webproperty_equality(account):
    a = account["https://www.test1.com/"]
    b = account["https://www.test1.com/"]
    c = account["https://www.test2.com/"]
    assert a == b
    assert a != c
