"""Asynchronous Search Analytics query builder.

:class:`AsyncQuery` subclasses the synchronous :class:`gsc_wrapper.query.Query`
to inherit its entire declarative builder surface (``range``, ``dimensions``,
``filter``, ``limit``, ``data_state``, ``search_type`` …) untouched - those
methods are pure, network-free transformations of ``self.raw`` and return
``self`` for chaining. Only the two methods that actually hit the network,
:meth:`execute` and :meth:`get`, are overridden to await the async transport.
"""
from __future__ import annotations

from urllib.parse import quote

from gsc_wrapper.aio.transport import SEARCH_ANALYTICS_URL
from gsc_wrapper.query import Query, Report


class AsyncQuery(Query):
    """Async equivalent of :class:`gsc_wrapper.query.Query`.

    Examples
    --------
    >>> query = AsyncQuery(site)
    >>> report = await (
    ...     query.range(startDate="2022-11-10", days=-7, months=0)
    ...     .dimensions(dimension.DATE)
    ...     .get()
    ... )
    <gsc_wrapper.query.Report(rows=...)>
    """

    async def execute(self) -> dict:
        """Invoke the API once and return the raw JSON for the current window.

        Use :meth:`get` to page through the full result set.
        """
        # Reuse the synchronous guard (name-mangled private on ``Query``).
        self._Query__validate_query()

        site = quote(self.webproperty.url, safe="")
        url = SEARCH_ANALYTICS_URL.format(site=site)

        return await self.webproperty.account.transport.request(
            "POST", url, json=self.raw
        )

    async def get(self) -> Report:
        """Page through every batch and return a :class:`Report`.

        The cursor logic (batch setup, row accumulation, report assembly) is
        inherited from :class:`~gsc_wrapper.query.Query`; this override differs
        only by awaiting each batch.
        """
        raw_data: list = []
        startRow, step = self._paginate_init()

        while True:
            chunk = await self.execute()
            if self._merge_chunk(raw_data, chunk):
                break
            self.raw["startRow"] += step

        return self._build_report(raw_data, startRow, step)
