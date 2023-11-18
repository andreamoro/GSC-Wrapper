import time
from typing import Type, overload
from gsc_wrapper import account, enums, inspection
from dispatcher import dispatcher
import googleapiclient.errors


class InspectURL:
    """Returns the results for a given query against the
    Google Search Console - URL Inspection.

    As per Google API implementation, the indexability
    status does not test against a live URL.


    Usage:
    """

    _lock = 0

    def __init__(self, webproperty: account.WebProperty | None):
        if not webproperty:
            raise TypeError("A Webproperty is required prior querying data.")

        self.webproperty = webproperty
        self._urls_to_inspect = 0
        self._urls_bag = []
        self.raw = {
            "inspectionUrl": "",
            "siteUrl": webproperty.url,
        }

    def __repr__(self):
        return f"<gsc_wrapper.inspection.InspectURL({self.raw})>"

    @property
    def urls_to_inspect(self) -> int:
        return self._urls_to_inspect

    @overload
    def add_url(self, url: str, overwrite: bool = False):
        """Add a URL to the inspectable collection.


        Args:
            url  (str): A valid URL queryable via the WebProperty.

        Returns:
            `gsc_wrapper.insepction.InspectURL`

        Usage:
            # >>> site.query.filter(country.ITALY, operator.EQUAL)
            # <gsc_wrapper.query.Query(...)>

            # >>> site.query.filter(country=country.UNITED_KINGDOM,
            #     operator.NOT_CONTAINS)
            # <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def add_url(self, urls: list | tuple, overwrite: bool = False):
        """Add a set of URLs to the inspectable collection.


        Args:
            urls  (list | tuple): The list of URLs to be inspected

        Returns:
            `gsc_wrapper.inspection.InspectURL`

        Usage:
            # >>> site.query.filter(dimension=dimension.PAGE, expression='/blog',
            #     operator=operator.CONTAINS)
            # <gsc_wrapper.query.Query(...)>

            # >>> site.query.filter(dimension.PAGE, '/blog/?$',
            #     operator.INCLUDING_REGEX)
            # <gsc_wrapper.query.Query(...)>
        """
        ...

    @dispatcher
    def add_url(self):
        """Method not implementated as a fallback to warn developers."""
        raise NotImplementedError(
            "The required method signature is not implemented yet."
        )

    @add_url.register
    def __(self, url: str, overwrite: bool = False):
        """Overloaded method to add a single URL to the collection."""
        if not isinstance(url, str):
            raise ValueError("Dimension argument does not match the expected type.")

        self.add_url([url], overwrite)
        return self

    @add_url.register
    def __(self, urls: list, overwrite: bool = False):
        """Overloaded method to add a list of URLs to the collection."""
        if not isinstance(urls, list):
            raise ValueError("Dimension argument does not match the expected type.")

        if overwrite:
            self._urls_bag = urls
        else:
            self._urls_bag += urls

        self._urls_to_inspect = len(self._urls_bag)
        # prepare the JSON payload for the first query
        self.raw |= {
            "inspectionUrl": urls[0],
            "siteUrl": self.webproperty.url,
        }
        return self

    def execute(self):
        """Invoke the API to query the account and obtain the raw data.

        # Set the boundaries with the `limit` method to extract a specific
        # subset.

        # When a larger dataset is expected the get() method should be used
        # so the cursor approach kicks-in.
        """

        #### t.urlInspection().index().inspect(body=urltoinspect).execute()

        try:
            self._wait()
            response = (
                self.webproperty.account.service.urlInspection()
                .index()
                .inspect(body=self.raw)
                .execute()
            )

        except googleapiclient.errors.HttpError as e:
            raise e

        return response

    def get(self, urls: list | str) -> Type["inspection.Report"]:
        """Return the full batch of data by processing the requested
        URL throught the API call.
        It returns a Report object containing the extracted dataset.


        Returns:
            `gsc_wrapper.inspection.Report`

        Usage:
            >>> site.query.get()
            <gsc_wrapper.query.Report(rows=...)>
        """
        # Convert a single URL into a list for code uniformity
        if isinstance(urls, str):
            urls_to_check = [urls]
        else:
            urls_to_check = urls

        raw_data = []
        while urls_to_check:
            self.raw = {
                "inspectedURL": urls_to_check.pop(),
                "siteURL": self.webproperty.url,
            }

            chunk = self.execute()

            # if chunk.get("rows"):
            raw_data += chunk.get("rows")
            #     chunck_len = len(raw_data)
            # else:
            #     is_complete = True

        # Report stores a copy of the query object for reference.
        # Overwriting the limit boundaries to have vibility on the
        # processed data.
        # query = self.raw.copy()
        # query["startRow"] = startRow
        # query["rowLimit"] = chunck_len

        # # Resetting the limit to the original values
        # self.limit(startRow, step)

        return Report(self.webproperty.url, query, raw_data)

    def _wait(self):
        now = time.time()
        elapsed = now - self._lock
        wait = max(0, 1 - elapsed)
        time.sleep(wait)
        self._lock = time.time()

        return wait


class Report:
    """Unpack the raw data previously queried via the Query class into a report
    object ready to be consumed. The class does not execute any query directly.
    A Report can be explicitly created using the `Query.get()` method."""

    ...
