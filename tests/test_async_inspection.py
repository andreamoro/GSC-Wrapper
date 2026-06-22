"""Tests for AsyncInspectURL network methods (httpx mocked, no network).

The URL-bag management is inherited from the synchronous ``InspectURL`` and
covered by ``test_inspection.py``; here we focus on the overridden async
``execute``/``get`` and their concurrent, cached behaviour.
"""
import httpx
import respx

from gsc_wrapper.aio import AsyncInspectURL
from gsc_wrapper.aio.transport import URL_INSPECTION_URL
from gsc_wrapper.inspection import Report


def _inspection_response(request=None, verdict="PASS"):
    # Usable both as a respx ``side_effect`` (called with the request) and
    # standalone (no argument).
    return httpx.Response(
        200,
        json={"inspectionResult": {"indexStatusResult": {"verdict": verdict}}},
    )


def test_is_an_inspecturl_subclass(async_site):
    assert isinstance(async_site.inspect, AsyncInspectURL)


async def test_execute_inspects_each_url_in_order(async_site, respx_mock):
    route = respx_mock.post(URL_INSPECTION_URL).mock(side_effect=_inspection_response)

    inspect = async_site.inspect
    inspect.add_url(["https://www.test1.com/", "https://www.test1.com/blog"])

    results = await inspect.execute()

    assert len(results) == 2
    assert route.call_count == 2
    # Results carry the inspected URL back, in the order URLs were added.
    assert [r["inspectionUrl"] for r in results] == [
        "https://www.test1.com/",
        "https://www.test1.com/blog",
    ]


async def test_results_are_cached_within_ttl(async_site, respx_mock):
    route = respx_mock.post(URL_INSPECTION_URL).mock(side_effect=_inspection_response)

    inspect = async_site.inspect
    inspect.add_url("https://www.test1.com/")

    await inspect.execute()
    await inspect.execute()  # still fresh: served from the per-URL cache

    assert route.call_count == 1


async def test_get_returns_report(async_site, respx_mock):
    respx_mock.post(URL_INSPECTION_URL).mock(side_effect=_inspection_response)

    inspect = async_site.inspect
    inspect.add_url("https://www.test1.com/")

    report = await inspect.get()

    assert isinstance(report, Report)
    assert len(report) == 1


async def test_empty_bag_yields_empty_results(async_site):
    results = await async_site.inspect.execute()
    assert results == []
