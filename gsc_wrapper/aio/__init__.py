"""Asynchronous API for the Google Search Console wrapper.

This subpackage mirrors the synchronous top-level classes with non-blocking,
``asyncio``-native equivalents built on ``httpx`` and ``aiolimiter``. It lives
alongside the synchronous API - importing it changes nothing for existing
synchronous users.

Usage
-----
>>> from gsc_wrapper.aio import AsyncAccount
>>> async with AsyncAccount(credentials) as account:
...     site = await account.webproperty("https://www.example.com/")
...     report = await site.query.dimensions(dimension.DATE).get()
"""
from gsc_wrapper.aio.account import AsyncAccount, AsyncWebProperty
from gsc_wrapper.aio.query import AsyncQuery
from gsc_wrapper.aio.inspection import AsyncInspectURL
from gsc_wrapper.aio.transport import AsyncTransport, GSCApiError

__all__ = (
    "AsyncAccount",
    "AsyncWebProperty",
    "AsyncQuery",
    "AsyncInspectURL",
    "AsyncTransport",
    "GSCApiError",
)
