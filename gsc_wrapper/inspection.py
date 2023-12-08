from __future__ import annotations
import time
from datetime import datetime
from functools import cache
from typing import Self, overload
from dispatcher import dispatcher
from collections import namedtuple, abc
from gsc_wrapper import account, enums
from gsc_wrapper.util import Util
import googleapiclient.errors


class InspectURL:
    """Returns the results for a given query against the
    Google Search Console - URL Inspection.
    https://developers.google.com/webmaster-tools/v1/api_reference_index#Inspection_tools

    As per Google API implementation, the indexability
    status does not test against a live URL.

    The most important methods are:
    * `execute` which ran a given query and returns all the possible results
    * `get` which execute the query partitioning the results into small chunks
        so not to overload the destination server.
        The method returns a Report object.

    Examples
    --------
    >>> inspect = InspectURL(site)
    >>> inspect.add_url("https://www.andreamoro.eu")
    >>> inspect.get()
    <gsc_wrapper.inspection.Report(rows=...)>

    >>> inspect.execute()
    >>> data = inpsect.execute()
    [Row(),...]
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

        Parameters
        ----------
        url : str
            The URL to be inspected and belonging to the WebProperty.

        Returns
        -------
        gsc_wrapper.insepction.InspectURL
            A reference of the same class to allow methods nestings

        Examples
        --------
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

        Parameters
        ----------
        urls : list
            The list of URLs to be inspected and belonging to the WebProperty.

        Returns
        -------
        gsc_wrapper.inspection.InspectURL
            A reference of the same class to allow methods nestings

        Examples
        --------
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
            raise ValueError(
                "Dimension argument does not match the expected type."
            )

        self.add_url([url], overwrite)
        return self

    @add_url.register
    def __(self, urls: list, overwrite: bool = False):
        """Overloaded method to add a list of URLs to the collection."""
        if not isinstance(urls, list):
            raise ValueError(
                "Dimension argument does not match the expected type."
            )

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

        Parameters
        ----------
        url : str
            The URL to be removed.

        Returns
        -------
        gsc_wrapper.insepction.InspectURL
            A reference of the same class to allow methods nestings


        Examples
        --------
        >>> inspect = InspectURL(site)
        >>> inspect.remove_url(url='https://www.mysite.com/')
        <gsc_wrapper.inspection.InspectURL(...)>
        """
        ...

    @overload
    def remove_url(self, urls: list):
        """Remove a set of URLs from the inspectable collection.

        Parameters
        ----------
        urls : list
            The list of URLs to be removed.

        Returns
        -------
        gsc_wrapper.inspection.InspectURL
            A reference of the same class to allow methods nestings

        Examples
        --------
        >>> inspect = InspectURL(site)
        >>> inspect.remove_url(urls=['https://www.mysite.com/',
            'https://www.mysite.com/blog'])
        <gsc_wrapper.inspection.InspectURL(...)>
        """
        ...

    @overload
    def remove_url(self, index: int):
        """Remove the URLs at the given position within the URLs bag.

        Parameters
        ----------
        index : int
            The index of URLs to be removed.

        Returns
        -------
        gsc_wrapper.inspection.InspectURL
            A reference of the same class to allow methods nesting

        Examples
        --------
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

        Returns
        -------
            None
        """
        self._urls_bag = []
        self._urls_to_inspect = 0

    def execute(self) -> list:
        """Invoke the API to obtain the raw data for the tested URLs.

        Returns
        -------
            list
                A set of Rows with the results of the inspection.
        """
        raw_data = []
        urls_to_check = self._urls_bag.copy()

        try:
            while urls_to_check:
                self._wait()
                self.raw = {
                    "inspectionUrl": urls_to_check.pop(),
                    "siteUrl": self.webproperty.url,
                }
                response = (
                    self.webproperty.account.service.urlInspection()
                    .index()
                    .inspect(body=self.raw)
                    .execute()
                )
                ret = response.get('inspectionResult')
                # Appending the URL inspected as it is not returned back from
                # the API and it will facilite bulk reporting
                ret.update({'inspectionUrl': self.raw.get('inspectionUrl')})
                raw_data.append(ret)

        except googleapiclient.errors.HttpError as e:
            raise e

        return raw_data

    def get(self):
        """Return all the data available for the URLs set while
        returing a Report object.

        Returns
        -------
        gsc_wrapper.inspection.Report
            A `Report` object containing the extracted dataset.

        Examples
        --------
        >>> inspect = Inspection(site)
        >>> inspect.get()
        <gsc_wrapper.inspection.Report(rows=...)>
        """
        raw_data = self.execute()

        # Report stores a copy of the data retrieved with the query.
        return Report(self.webproperty.url, raw_data)

    def _wait(self):
        now = time.time()
        elapsed = now - self._lock
        wait = max(0, 1 - elapsed)
        time.sleep(wait)
        self._lock = time.time()

        return wait


class Report:
    """Unpack the `Inspection` raw data into a report that can be
    consumed in different manners.
    The class does not execute any query directly.
    """

    def __init__(self, webproperty: str, raw: list):
        self.webproperty = webproperty

        if isinstance(raw, list) and len(raw) > 0:
            self.raw = raw
            self.rows = []
            self._append()

        self.__enums_map = {
            'indexStatusResult.verdict': enums.verdict,
            'indexStatusResult.robotsTxtState': enums.robotsTxtState,
            'indexStatusResult.indexingState': enums.indexingState,
            'indexStatusResult.pageFetchState': enums.pageFetchState,
            'indexStatusResult.crawledAs': enums.crawlerAgent,
            'mobileUsabilityResult.verdict': enums.verdict,
            'mobileUsabilityIssue.issueType': enums.mobileUsabilityIssueType,
            'mobileUsabilityIssue.severity': enums.severity,
            'ampInspectionResult.verdict': enums.verdict,
            'ampInspectionResult.robotsTxtState': enums.robotsTxtState,
            'ampInspectionResult.indexingState': enums.indexingState,
            'ampInspectionResult.ampIndexStatusVerdict': enums.verdict,
            'ampInspectionResult.pageFetchState': enums.pageFetchState,
            'ampIssue.severity': enums.severity,
            'richResultsResult.verdict': enums.verdict,
            'richResultsIssue.severity': enums.severity,
        }

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, key):
        return self.rows[key]

    def __contains__(self, item):
        return item in self.rows

    def __len__(self):
        return len(self.rows)

    def __repr__(self):
        return f"<gsc_wrapper.inspection.Report(rows={len(self)})>"

    @property
    def first(self):
        if len(self.rows) == 0:
            return None

        return self.rows[0]

    @property
    def last(self):
        if len(self.rows) == 0:
            return None

        return self.rows[-1]

    def _append(self):
        """Build a browsable sets of rows.
        Depending from the `full_data` argument the returned
        dataset can contain a limited set of details.
        """
        raw_copy = self.raw.copy()

        while raw_copy:
            self.rows.append(self.__toNametuple(raw_copy.pop()))

    def __toNametuple(self, collection: dict) -> namedtuple:
        """Intenal auxiliary method to transform a dictionary
        into a nested named tuple.

        Parameters
        ----------
        collection : dictionary
            The named tuple to convert

        Returns
        -------
            namedtuple
        """
        return namedtuple(
            "Rows", collection.keys()
        )(*tuple(
            map(lambda x: x
                if not isinstance(x, dict)
                else self.__toNametuple(x), collection.values())))

    def __toDict(self, collection: namedtuple) -> dict:
        """Intenal auxiliary method to transform a nested named tuple
        into a dictionary.

        Parameters
        ----------
        collection : namedtuple
            The named tuple to convert

        Returns
        -------
            dictionary
        """
        if isinstance(collection, tuple) and hasattr(collection, '_asdict'):
            return {
                k: self.__toDict(v) for k, v in collection._asdict().items()
            }
        elif isinstance(collection, list):
            return [self.__toDict(item) for item in collection]
        else:
            return collection

    def __toFlattenDict(
        self,
        dictionary: dict,
        parent_key=False,
        sep='.'
    ) -> dict:
        """Intenal auxiliary method to transform a nested dictionary into a
        flatten dictionary.

        Parameters
        ----------
        dictionary : dict
            The dictionary to flatten
        parent_key : string
            The string to prepend to dictionary's keys
        sep : string
            The string used to separate flattened keys

        Returns
        -------
        dict
            A flattened dictionary
        """
        items = []

        for key, value in dictionary.items():
            new_key = str(parent_key) + sep + key if parent_key else key
            if isinstance(value, abc.MutableMapping):
                items.extend(self.__toFlattenDict(value, new_key, sep).items())
            elif isinstance(value, list):
                for k, v in enumerate(value):
                    items.extend(
                        self.__toFlattenDict({str(k): v}, new_key).items()
                    )
            else:
                try:
                    value = self._Report__enums_map[new_key][value].value
                    # items.append((new_key,
                    #               )
                except KeyError:
                    pass
                finally:
                    items.append((new_key, value))
        return dict(items)

    @cache
    def to_dataframe(self) -> object:
        """Convert the resultset into a Pandas DataFrame for machine learning
        analysis or on-the-fly querying.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with the flattened results.
            Results are automatically expanded and gaps filled in.

        """
        import pandas as pd

        union = []
        raw_copy = self.raw.copy()

        while raw_copy:
            union.append(self.__toFlattenDict(raw_copy.pop()))

        return pd.DataFrame(union)

    def to_disk(self, filename="") -> str | None:
        """Persist the dictionary with the data on disk. If the filename is
        not given, one will be generated automatically.
        A new file with a different suffix will be generated if the given one
        already exists.

        Parameters
        ----------
        filename : str
            The name of the while where the data will be persisted.

        Returns
        -------
        str
            The filename were data was persisteed. An empty string
        """
        import pathlib
        import pickle
        import re

        if filename == "":
            # This is calibrated around the webproperty format
            domain = re.sub(r"[./]", "_", self.webproperty).\
                replace("__", "_").replace(":", "")
            filename = datetime.today().strftime("%Y%m%d") + \
                "_" + domain + "_inspection.pck"

        unique_path = Util.get_filename(pathlib.Path.cwd(), filename)
        try:
            data = [{"url": self.webproperty}, self.raw]

            if unique_path != "":
                with open(unique_path, "wb") as f:
                    pickle.dump(data, f)
                    return str(unique_path)
            else:
                return ''
        except OSError as e:
            raise OSError(f"{type(e)}: {e}")

    @classmethod
    def from_disk(cls, filename: str) -> Self | None:
        """Load a file from the disk a previously saved report stored
        with the GSC Wrapper class.

        Parameters
        ----------
        filename : str
            The name of the file used to persist data

        Returns
        -------
        Report or None
            The unpacked rows.
        """
        import pickle

        if filename != "":
            try:
                with open(filename, "rb") as f:
                    data = pickle.load(f)
                    return cls(data[0].get("url"), data[1])
            except OSError as e:
                raise OSError(f"{type(e)}: {e}")

        return None

    @classmethod
    def from_datastream(cls, data: bytes) -> Self | None:
        """Rebuild the report with the GSC Wrapper class using
        the data stream passed in the argument.

        Parameters
        ----------
        data : byte
            The dara stream containing the report details

        Returns
        -------
        Report or None
            The unpacked rows.
        """
        import pickle

        if data:
            data = pickle.loads(data)
            return cls(data[0]["url"], data[1])

        return None
