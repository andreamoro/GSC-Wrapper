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
        The URL must be fully qualified and belong to the inspected
        WebProperty.


        Args:
            url  (str): The URL to be inspected and belonging to the
            WebProperty.

        Returns:
            `gsc_wrapper.insepction.InspectURL`

        Usage:
            >>> inspect = InspectURL(site)
            >>> inspect.add_url(url='https://www.mysite.com/')
            <gsc_wrapper.inspection.InspectURL(...)>
        """
        ...

    @overload
    def add_url(self, urls: list, overwrite: bool = False):
        """Add a set of URLs to the inspectable collection.
        URLs have to be fully qualified and belong to the inspected
        WebProperty.


        Args:
            urls  (list): The list of URLs to be inspected and belonging
            to the WebProperty.

        Returns:
            `gsc_wrapper.inspection.InspectURL`

        Usage:
            >>> inspect = InspectURL(site)
            >>> inspect.add_url(urls=['https://www.mysite.com/',
                'https://www.mysite.com/blog'])
            <gsc_wrapper.inspection.InspectURL(...)>
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

        # prepare the JSON payload so to have always one line to test
        self.raw |= {
            "inspectionUrl": urls[0],
            "siteUrl": self.webproperty.url,
        }
        return self

    @overload
    def remove_url(self, url: str):
        """Remove a URL from the inspectable collection.


        Args:
            url  (str): The URL to be removed.

        Returns:
            `gsc_wrapper.insepction.InspectURL`

        Usage:
            >>> inspect = InspectURL(site)
            >>> inspect.remove_url(url='https://www.mysite.com/')
            <gsc_wrapper.inspection.InspectURL(...)>
        """
        ...

    @overload
    def remove_url(self, urls: list):
        """Remove a set of URLs from the inspectable collection.


        Args:
            urls  (list): The list of URLs to be removed.

        Returns:
            `gsc_wrapper.inspection.InspectURL`

        Usage:
            >>> inspect = InspectURL(site)
            >>> inspect.remove_url(urls=['https://www.mysite.com/',
                'https://www.mysite.com/blog'])
            <gsc_wrapper.inspection.InspectURL(...)>
        """
        ...

    @overload
    def remove_url(self, index: int):
        """Remove the URLs at the given position within the URLs bag.


        Args:
            index  (int): The index of URLs to be removed.

        Returns:
            `gsc_wrapper.inspection.InspectURL`

        Usage:
            >>> inspect = InspectURL(site)
            >>> inspect.remove_url(index)
            <gsc_wrapper.inspection.InspectURL(...)>
        """
        ...

    @dispatcher
    def remove_url(self):
        """Method not implementated as a fallback to warn developers."""
        raise NotImplementedError(
            "The required method signature is not implemented yet."
        )

    @remove_url.register
    def __(self, url: str):
        if not isinstance(url, str):
            raise ValueError("The supplied argument is not a string.")

        try:
            self._urls_bag.remove(url)
            self.urls_to_inspect -= 1
        except ValueError:
            pass

    @remove_url.register
    def __(self, urls: list):
        if not isinstance(urls, list):
            raise ValueError("The supplied argument is not a list.")

        while urls:
            self.remove_url(urls.pop())

    @remove_url.register
    def __(self, index: int):
        if not isinstance(index, int):
            raise ValueError("The supplied argument is not an integer.")

        if len(self._urls_bag) >= index:
            del self._urls_bag[index]
            self.urls_to_inspect -= 1
        else:
            raise ValueError("The supplied index is not in the URLs bag.")

    def remove_all_urls(self):
        """Remove all the URLs from the inspection bag.
        """
        self._urls_bag = []
        self._urls_to_inspect = 0

    def execute(self):
        """Invoke the API to obtain the results raw data for the URLs tested.

        # When a larger dataset is expected the get() method should be used
        # so the cursor approach kicks-in.
        """
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

    def get(self) -> Type["inspection.Report"]:
        """Return the full batch of data by processing the requested
        URL throught the API call.
        It returns a Report object containing the extracted dataset.


        Returns:
            `gsc_wrapper.inspection.Report`

        Usage:
            >>> inspect = Inspection(site)
            >>> inspect.get()
            <gsc_wrapper.inspection.Report(rows=...)>
        """
        raw_data = []
        urls_to_check = self._urls_bag.copy()
        while urls_to_check:
            self.raw = {
                "inspectedURL": urls_to_check.pop(),
                "siteURL": self.webproperty.url,
            }

            raw_data += self.execute()

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
