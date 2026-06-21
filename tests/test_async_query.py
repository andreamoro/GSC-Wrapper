"""Tests for AsyncQuery network methods (httpx mocked, no network).

The builder surface (range/filter/dimensions/…) is inherited verbatim from the
synchronous ``Query`` and already exercised by ``test_query.py``; here we only
cover the overridden async ``execute`` and ``get``.
"""
from urllib.parse import quote

import httpx
import respx

from gsc_wrapper import dimension
from gsc_wrapper.aio import AsyncQuery
from gsc_wrapper.aio.transport import SEARCH_ANALYTICS_URL
from gsc_wrapper.query import Report


def _analytics_url(site_url: str) -> str:
    return SEARCH_ANALYTICS_URL.format(site=quote(site_url, safe=""))


def test_is_a_query_subclass(async_site):
    # Inheriting Query means the whole builder API is available unchanged.
    assert isinstance(async_site.query, AsyncQuery)


@respx.mock
async def test_execute_posts_to_encoded_site_url(async_site):
    url = _analytics_url(async_site.url)
    route = respx.post(url).mock(
        return_value=httpx.Response(200, json={"rows": [{"keys": ["2022-01-01"],
                                                         "clicks": 1, "impressions": 2,
                                                         "ctr": 0.5, "position": 1.0}]})
    )

    result = await async_site.query.dimensions(dimension.DATE).execute()

    assert route.called
    assert result["rows"][0]["clicks"] == 1


@respx.mock
async def test_get_pages_until_empty_batch(async_site):
    url = _analytics_url(async_site.url)

    def _row(i):
        return {"keys": [f"2022-01-{i:02d}"], "clicks": i,
                "impressions": i, "ctr": 0.1, "position": 1.0}

    # Two full-ish batches then an empty one signals completion.
    respx.post(url).mock(side_effect=[
        httpx.Response(200, json={"rows": [_row(1), _row(2)]}),
        httpx.Response(200, json={"rows": [_row(3)]}),
        httpx.Response(200, json={"rows": []}),
    ])

    query = async_site.query.dimensions(dimension.DATE).limit(2)
    report = await query.get()

    assert isinstance(report, Report)
    assert len(report) == 3
    assert [r.clicks for r in report] == [1, 2, 3]
    # The live query's limits are restored after paging.
    assert query.raw["startRow"] == 0
    assert query.raw["rowLimit"] == 2


@respx.mock
async def test_get_with_no_rows_returns_empty_report(async_site):
    url = _analytics_url(async_site.url)
    respx.post(url).mock(return_value=httpx.Response(200, json={}))

    report = await async_site.query.dimensions(dimension.DATE).get()

    assert len(report) == 0
