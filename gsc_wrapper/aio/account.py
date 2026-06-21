"""Asynchronous counterparts to :class:`gsc_wrapper.account` objects."""
from __future__ import annotations

from google.auth.credentials import Credentials as GoogleCredentials

from gsc_wrapper.account import (
    WebProperty,
    build_credentials,
    credentials_identifier,
)
from gsc_wrapper.aio.transport import AsyncTransport, SITES_URL


class AsyncAccount:
    """Async equivalent of :class:`gsc_wrapper.account.Account`.

    It owns an :class:`~gsc_wrapper.aio.transport.AsyncTransport`, so it should
    be closed when finished - either via ``await account.aclose()`` or by using
    it as an async context manager::

        async with AsyncAccount(credentials) as account:
            properties = await account.webproperties()

    Credentials are accepted exactly as by the synchronous ``Account``: either a
    ``dict`` of OAuth user credentials or an already-built ``google.auth``
    credentials object (e.g. a service account).

    Parameters
    ----------
    credentials : dict | google.auth.credentials.Credentials
        The credentials used to authenticate every request.
    transport : AsyncTransport, optional
        A pre-built transport. When omitted one is created from ``credentials``;
        the remaining keyword arguments tune that default transport.
    max_rate, time_period, max_concurrency, timeout
        Forwarded to :class:`~gsc_wrapper.aio.transport.AsyncTransport`.
    """

    def __init__(
        self,
        credentials: dict | GoogleCredentials,
        *,
        transport: AsyncTransport | None = None,
        max_rate: float = 5.0,
        time_period: float = 1.0,
        max_concurrency: int = 10,
        timeout: float = 30.0,
    ):
        if not credentials:
            raise ValueError(
                "A credential object is required. Class can't be initialised."
            )

        self.cred = build_credentials(credentials)
        self.transport = transport or AsyncTransport(
            self.cred,
            max_rate=max_rate,
            time_period=time_period,
            max_concurrency=max_concurrency,
            timeout=timeout,
        )
        self._webproperties: list[AsyncWebProperty] = []

    async def webproperties(self) -> list["AsyncWebProperty"]:
        """Return every web property associated with this account.

        The result is memoised after the first call.

        Examples
        --------
        >>> properties = await account.webproperties()
        >>> properties[0]
        <gsc_wrapper.aio.account.AsyncWebProperty(url='...')>
        """
        if not self._webproperties:
            data = await self.transport.request("GET", SITES_URL)
            self._webproperties = [
                AsyncWebProperty(raw, self)
                for raw in data.get("siteEntry", [])
            ]

        return self._webproperties

    async def webproperty(self, key: str | int) -> "AsyncWebProperty | None":
        """Return a single web property by exact URL or by index.

        Examples
        --------
        >>> site = await account.webproperty("https://www.example.com/")
        >>> first = await account.webproperty(0)
        """
        properties = await self.webproperties()

        if isinstance(key, str):
            match = [p for p in properties if p.url == key]
            return match[0] if match else None

        return properties[key]

    async def aclose(self) -> None:
        """Close the underlying transport."""
        await self.transport.aclose()

    async def __aenter__(self) -> "AsyncAccount":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        identifier = credentials_identifier(self.cred)
        return f"<gsc_wrapper.aio.account.AsyncAccount(credentials='{identifier}')>"


class AsyncWebProperty(WebProperty):
    """Async equivalent of :class:`gsc_wrapper.account.WebProperty`.

    The raw-data handling (``permission_levels``, ``__init__``, ``__eq__``) is
    inherited unchanged from :class:`~gsc_wrapper.account.WebProperty`; only the
    :attr:`query` and :attr:`inspect` helpers are overridden to return async
    builders bound to this property::

        report = await site.query.range(start, days=-7).dimensions(...).get()
        report = await site.inspect.add_url(url).get()
    """

    @property
    def query(self):
        """A fresh :class:`~gsc_wrapper.aio.query.AsyncQuery` for this property."""
        from gsc_wrapper.aio.query import AsyncQuery

        return AsyncQuery(self)

    @property
    def inspect(self):
        """A fresh :class:`~gsc_wrapper.aio.inspection.AsyncInspectURL`."""
        from gsc_wrapper.aio.inspection import AsyncInspectURL

        return AsyncInspectURL(self)

    def __repr__(self) -> str:
        return (
            f"<gsc_wrapper.aio.account.AsyncWebProperty(url='{self.url}', "
            f"permission='{self.permission}')>"
        )
