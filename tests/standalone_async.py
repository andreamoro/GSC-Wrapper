"""Manual, runnable demo of the ASYNC API - the async sibling of ``standalone_sync.py``.

Like ``standalone_sync.py`` this is a standalone script, NOT part of the pytest suite
(pytest only collects ``test_*.py``). It mirrors the same ``Authenticate``
dispatch with three flows:

* ``"test"``    - fully offline; a stub transport returns canned data so the
                  script prints real rows and demonstrates concurrent URL
                  inspection without any Google credentials or network.
* ``"service"`` - programmatic service account (reads config.toml), real network.
* ``"oauth"``   - reuses the interactive Selenium flow from ``standalone_sync.py`` to source
                  credentials, then drives the async client.

Run (offline, prints data out of the box):

    python tests/standalone_async.py
"""
import asyncio
import time
import tomllib
from datetime import date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import gsc_wrapper
from gsc_wrapper.aio import AsyncAccount
from gsc_wrapper.aio.account import AsyncWebProperty


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE_URL = "https://www.andreamoro.eu/"

# Artificial per-request latency for the offline stub, so the concurrency of
# URL inspection is visible in wall-clock time.
_STUB_LATENCY = 0.4


# ---------------------------------------------------------------------------
# Offline stub transport: returns canned data, no network.
# ---------------------------------------------------------------------------
class StubTransport:
    """Stands in for ``AsyncTransport``; branches on the endpoint URL."""

    def __init__(self):
        self.calls = 0

    async def request(self, method, url, *, json=None, params=None):
        self.calls += 1
        await asyncio.sleep(_STUB_LATENCY)

        if "searchAnalytics" in url:
            # Return one page on the first batch, then nothing so the cursor
            # in AsyncQuery.get() terminates.
            if (json or {}).get("startRow", 0) == 0:
                return {"rows": [
                    {"keys": ["2024-01-01"], "clicks": 11, "impressions": 120,
                     "ctr": 0.09, "position": 4.1},
                    {"keys": ["2024-01-02"], "clicks": 7, "impressions": 80,
                     "ctr": 0.08, "position": 5.3},
                ]}
            return {"rows": []}

        # URL inspection
        return {"inspectionResult": {
            "indexStatusResult": {"verdict": "PASS", "coverageState": "Indexed"},
        }}

    async def aclose(self):
        pass


def _offline_account() -> AsyncAccount:
    """An ``AsyncAccount`` wired to the stub transport (no credentials needed).

    The credentials dict is only used to satisfy the constructor; the stub
    transport never refreshes a token or makes a real call.
    """
    fake_credentials = {
        "token": None, "refresh_token": None,
        "client_id": None, "client_secret": None,
        "token_uri": gsc_wrapper.GOOGLE_TOKEN_URI,
        "scopes": SCOPES,
    }
    return AsyncAccount(fake_credentials, transport=StubTransport())


# ---------------------------------------------------------------------------
# Authentication flows (mirror standalone_sync.py).
# ---------------------------------------------------------------------------
def authenticate_test() -> AsyncWebProperty:
    """Offline fake: stub transport + an injected web-property list."""
    account = _offline_account()
    account._webproperties = [
        AsyncWebProperty(
            {"siteUrl": SITE_URL, "permissionLevel": "siteOwner"}, account
        )
    ]
    return account._webproperties[0]


def authenticate_service_account() -> AsyncWebProperty:
    """Programmatic service account (real network). Reads config.toml, exactly
    like ``standalone_sync.py`` but hands the credentials to ``AsyncAccount``."""
    from google.oauth2 import service_account

    with open(Path(__file__).parent / "config.toml", "rb") as f:
        service = tomllib.load(f).get("credentials", {}).get("service", {})

    credentials = service_account.Credentials.from_service_account_file(
        service["key_file"], scopes=SCOPES,
    )
    if "subject" in service:
        credentials = credentials.with_subject(service["subject"])

    account = AsyncAccount(credentials)
    return _site_holder(account)


class _site_holder:
    """Tiny awaitable-less helper: resolves the site lazily in the test fns."""

    def __init__(self, account: AsyncAccount):
        self.account = account

    async def resolve(self) -> AsyncWebProperty:
        return await self.account.webproperty(SITE_URL)


async def Authenticate(method: str = "test") -> AsyncWebProperty:
    """Dispatch to a flow and return a resolved ``AsyncWebProperty``."""
    if method == "test":
        return authenticate_test()
    if method == "service":
        holder = authenticate_service_account()
        return await holder.resolve()
    raise ValueError(
        f"Unknown method '{method}'. Use 'test' or 'service' "
        "(reuse standalone_sync.py for the interactive 'oauth' flow)."
    )


# ---------------------------------------------------------------------------
# The demos - both PRINT data.
# ---------------------------------------------------------------------------
async def test_search_analytics(site: AsyncWebProperty):
    print("=== Search Analytics (async) ===")
    query = site.query.range(
        startDate=date(2024, 1, 1), days=1, months=0
    ).dimensions(gsc_wrapper.dimension.DATE)

    print("query.raw:", query.raw)

    report = await query.get()
    print(f"rows returned: {len(report)}")
    for row in report:
        print(f"  {row.date}  clicks={row.clicks}  impressions={row.impressions} "
              f"ctr={row.ctr}  position={row.position}")
    print("to_dict():", report.to_dict())
    print()


async def test_search_analytics_concurrent(site: AsyncWebProperty):
    # A single report pages sequentially (cursor), so the reporting async win
    # comes from running several INDEPENDENT queries at once - here, one per
    # dimension - via asyncio.gather.
    print("=== Search Analytics (async, concurrent fan-out) ===")
    dimensions = [
        gsc_wrapper.dimension.DATE,
        gsc_wrapper.dimension.QUERY,
        gsc_wrapper.dimension.PAGE,
        gsc_wrapper.dimension.COUNTRY,
    ]

    async def run(dim):
        query = site.query.range(
            startDate=date.today(), days=-7, months=0
        ).dimensions(dim)
        return await query.get()

    start = time.perf_counter()
    reports = await asyncio.gather(*(run(d) for d in dimensions))
    elapsed = time.perf_counter() - start

    # Each query makes 2 calls: one page of rows + a terminating empty page.
    serial = _STUB_LATENCY * 2 * len(dimensions)
    print(f"ran {len(dimensions)} independent queries in {elapsed:.2f}s "
          f"(serial would be ~{serial:.2f}s -> ~{serial / elapsed:.1f}x faster)")
    for dim, report in zip(dimensions, reports):
        print(f"  dimension={dim.value}: {len(report)} rows")
    print()


async def test_url_inspection(site: AsyncWebProperty):
    print("=== URL Inspection (async, concurrent) ===")
    urls = [f"{SITE_URL}page-{i}" for i in range(6)]
    inspect = site.inspect
    inspect.add_url(urls)

    start = time.perf_counter()
    report = await inspect.get()
    elapsed = time.perf_counter() - start

    serial = _STUB_LATENCY * len(urls)
    print(f"inspected {len(report)} URLs in {elapsed:.2f}s "
          f"(serial would be ~{serial:.2f}s -> ~{serial / elapsed:.1f}x faster)")
    for row in report:
        print(f"  {row.inspectionUrl}  verdict={row.indexStatusResult.verdict} "
              f"state={row.indexStatusResult.coverageState}")
    print()


async def main(method: str = "test"):
    # method="test"    -> offline fake (default; no creds, prints data)
    # method="service" -> programmatic service account (real network)
    site = await Authenticate(method=method)

    await test_search_analytics(site)
    await test_search_analytics_concurrent(site)
    await test_url_inspection(site)


if __name__ == "__main__":
    asyncio.run(main(method="test"))
