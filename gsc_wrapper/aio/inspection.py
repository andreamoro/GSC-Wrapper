"""Asynchronous URL Inspection builder.

:class:`AsyncInspectURL` subclasses the synchronous
:class:`gsc_wrapper.inspection.InspectURL` to inherit its URL-bag management
(``add_url``, ``remove_url`` …) unchanged. Only :meth:`execute` and :meth:`get`
are overridden. Crucially, the async ``execute`` inspects every queued URL
*concurrently* (subject to the transport's rate limiter and concurrency cap)
rather than serially - the main reason to reach for the async API here.
"""
from __future__ import annotations

import asyncio
import time

from gsc_wrapper.aio.transport import URL_INSPECTION_URL
from gsc_wrapper.inspection import InspectURL, Report

# Inspection results are cached on each bag item; refresh once older than this
# (seconds). Mirrors the TTL used by the synchronous implementation.
_TTL_SECONDS = 450


class AsyncInspectURL(InspectURL):
    """Async equivalent of :class:`gsc_wrapper.inspection.InspectURL`.

    Examples
    --------
    >>> inspect = AsyncInspectURL(site)
    >>> inspect.add_url(["https://example.com/", "https://example.com/blog"])
    >>> report = await inspect.get()
    <gsc_wrapper.inspection.Report(rows=...)>
    """

    async def execute(self) -> list:
        """Inspect every queued URL concurrently and return the raw results.

        Results are returned in the same order the URLs were added. A still-fresh
        cached result (within the TTL) is reused without a network call.
        """
        results = await asyncio.gather(
            *(self.__inspect(item) for item in self._urls_bag)
        )
        return list(results)

    async def __inspect(self, item) -> dict:
        """Fetch (or reuse the cached) inspection result for a single bag item."""
        if item.expire is None or item.expire + _TTL_SECONDS < time.monotonic():
            body = {
                "inspectionUrl": item.url,
                "siteUrl": self.webproperty.url,
            }
            response = await self.webproperty.account.transport.request(
                "POST", URL_INSPECTION_URL, json=body
            )
            ret = response.get("inspectionResult")
            # Echo back the inspected URL to ease bulk reporting.
            ret.update({"inspectionUrl": item.url})
            item.value = ret
            item.expire = time.monotonic()
        else:
            ret = item.value

        return ret

    async def get(self) -> Report:
        """Inspect every queued URL and wrap the result in a :class:`Report`."""
        raw_data = await self.execute()
        return Report(self.webproperty.url, raw_data)
