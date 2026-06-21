"""Asynchronous HTTP transport for the Google Search Console REST API.

The synchronous package leans on ``googleapiclient`` (a blocking client). The
async variant talks to the same REST endpoints directly over ``httpx`` so the
I/O is genuinely non-blocking, while keeping the battle-tested ``google-auth``
credentials objects for token sourcing and refresh.

Three concerns are handled here so the higher level classes stay declarative:

* **Authentication** - an access token is taken from the supplied
  ``google.auth`` credentials. Refreshing a token is a rare, blocking call, so
  it is off-loaded to a worker thread via :func:`asyncio.to_thread` and guarded
  by a lock to avoid a refresh stampede when many requests start at once.
* **Rate limiting** - an :class:`aiolimiter.AsyncLimiter` smooths the request
  rate to stay within Google's per-minute quotas, replacing the crude
  ``time.sleep`` throttle used by the synchronous classes.
* **Concurrency** - a semaphore caps the number of in-flight requests so a large
  fan-out (e.g. inspecting thousands of URLs) cannot exhaust the connection
  pool.
"""
from __future__ import annotations

import asyncio

import httpx
from aiolimiter import AsyncLimiter
from google.auth.transport.requests import Request as _AuthRequest

# Search Analytics and the sites collection live under the historical
# ``webmasters/v3`` service, while URL Inspection is exposed under the newer
# ``searchconsole`` v1 surface. Both are reachable from the googleapis frontend.
SITES_URL = "https://www.googleapis.com/webmasters/v3/sites"
SEARCH_ANALYTICS_URL = (
    "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
)
URL_INSPECTION_URL = (
    "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
)


class GSCApiError(Exception):
    """Raised when the Search Console API returns a non-2xx response.

    The Google error ``message`` is surfaced (when present) so callers get an
    actionable reason instead of a bare status code.
    """

    def __init__(self, status_code: int, message: str,
                 response: httpx.Response | None = None):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"GSC API error {status_code}: {message}")

    @classmethod
    def from_response(cls, response: httpx.Response) -> "GSCApiError":
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except (ValueError, AttributeError):
            message = response.text
        return cls(response.status_code, message, response)


class AsyncTransport:
    """An authenticated, rate-limited async HTTP client for the GSC API.

    Parameters
    ----------
    credentials : google.auth.credentials.Credentials
        Any ``google-auth`` credentials object able to mint an access token
        (OAuth user credentials or a service account).
    max_rate, time_period : float
        Token-bucket settings for :class:`aiolimiter.AsyncLimiter`: at most
        ``max_rate`` requests are allowed per ``time_period`` seconds.
    max_concurrency : int
        Maximum number of simultaneously in-flight requests.
    timeout : float
        Per-request timeout, in seconds.
    client : httpx.AsyncClient, optional
        An externally owned client (mostly for testing). When supplied it is
        *not* closed by :meth:`aclose`.
    """

    def __init__(
        self,
        credentials,
        *,
        max_rate: float = 5.0,
        time_period: float = 1.0,
        max_concurrency: int = 10,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ):
        self._credentials = credentials
        self._limiter = AsyncLimiter(max_rate, time_period)
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._auth_request = _AuthRequest()
        self._refresh_lock = asyncio.Lock()

    async def _ensure_token(self) -> str:
        """Return a valid access token, refreshing it off-thread if needed."""
        if not self._credentials.valid:
            async with self._refresh_lock:
                # Re-check inside the lock: a concurrent caller may have already
                # refreshed while we were waiting.
                if not self._credentials.valid:
                    await asyncio.to_thread(
                        self._credentials.refresh, self._auth_request
                    )
        return self._credentials.token

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Perform an authenticated request and return the decoded JSON body."""
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with self._semaphore, self._limiter:
            response = await self._client.request(
                method, url, json=json, params=params, headers=headers
            )

        if response.is_error:
            raise GSCApiError.from_response(response)

        return response.json()

    async def aclose(self) -> None:
        """Close the underlying client unless it was supplied externally."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()
