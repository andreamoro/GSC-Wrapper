from __future__ import annotations
import collections
import time
from datetime import date
from typing import Self, overload

import googleapiclient.errors
from dateutil.relativedelta import relativedelta
from dispatcher import dispatcher
from gsc_wrapper import enums, account
from gsc_wrapper.util import Util


class Query:
    """Returns the results for a given query against the
    Google Search Console - Search Analytics.
    https://developers.google.com/webmaster-tools/v1/api_reference_index#Search_analytics

    The most important methods are:
    * `execute` which ran a given query and returns all the possible results
    * `get` which execute the query partitioning the results into small chunks
        so not to overload the destination server.
        The method returns a Report object.

    There are also the following other methods with which it will be
    possible to interact with the class:
    * `range` to specify a date range for your query.
    * `dimension` to specify the dimensions you would like report on.
    A value between:
    - country,
    - device,
    - page,
    - query,
    - searchAppearance: this cannot be combined with anything else, and
        the aggregation type has to be "By Page"
    * `filter` to specify which rows to filter by.
    * `limit` to specify a subset of results.

    Examples
    --------
    >>> query = Query(site)
    >>> query.range(startDate='2022-11-10', days=-7, months=0)\\
            .dimension(gsc_wrapper.dimension.DATE).get()
    <gsc_wrapper.query.Report(rows=...)>

    >>> query = Query(site)
    >>> query = query.range(startDate='2022-11-10', days=-7, months=0)\\
    ...              .dimension(gsc_wrapper.dimension.DATE,
    ...                         gsc_wrapper.dimension.QUERY)\\
    ...              .filter('query', 'dress', 'contains')\\
    ...              .filter('page', '/womens-clothing/', 'contains')\\
    ...              .limit(20000)
    >>> data = query.get()
    <gsc_wrapper.query.Report(rows=...)>
    """

    _lock = 0

    def __init__(self, webproperty: account.WebProperty | None):
        if not webproperty:
            raise TypeError("A Webproperty is required prior querying data.")

        self.webproperty = webproperty
        self._startDate = date.today() - relativedelta(days=2)
        self._endDate = date.today() - relativedelta(days=1)
        self.raw = {
            "startDate": self._startDate.isoformat(),
            "endDate": self._endDate.isoformat(),
            "dataState": "final",
            "aggregationType": "auto",
        }
        self.limit(25000)

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.raw == other.raw
        return False

    def __repr__(self):
        return f"<gsc_wrapper.query.Query({self.raw})>"

    @property
    def startDate(self) -> date:
        return self._startDate

    @property
    def endDate(self) -> date:
        return self._endDate

    @property
    def filters(self) -> list:
        _filters: list = self.raw.get("dimensionFilterGroups", [])

        if isinstance(_filters, list) and len(_filters) > 1:
            return [f.get("filters", "")[0] for f in _filters]
        else:
            return _filters[0].get("filters", "")

    def data_state(
            self,
            data_state: enums.data_state = enums.data_state.FINAL
    ):
        """Return a new query filtering by fresh (not finalized) data or
        full-state data.

        Parameters
        ----------
        data_state : gsc_wrapper.data_state
            The data_state you would like to use.
            Possible values:
            - 'FINAL' (default = d-1 backward),
            - 'ALL' (finalised & fresh data).

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.data_state(gsc_wrapper.data_state.FINAL)
        <gsc_wrapper.query.Query(...)>
        """

        # Check for the right data type
        if isinstance(data_state, enums.data_state):
            data_state = data_state.value
        else:
            raise ValueError("Data State argument does not match the expected\
                    type.")

        # self.raw["dataState"] = data_state
        # self.raw.update({"dataState": data_state})
        self.raw |= {"dataState": data_state}

        return self

    def dimensions(
        self,
        *dimensions: enums.dimension | list[enums.dimension] | tuple[enums.dimension],
    ):
        """Return a query that fetches the specified dimensions.

        Parameters
        ----------
        *dimensions : enums.dimension
            Dimensions you would like to report on.
            Possible values:
            - country
            - device
            - page
            - query
            - SearchAppearance (can appear only on its own).

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.dimension(dimension.DATE, dimension.PAGE)
        <gsc_wrapper.query.Query(...)>
        """

        if isinstance(dimensions, enums.dimension):
            # self.raw["dimensions"] = dimensions.value
            self.raw |= {"dimensions": dimensions.value}
        elif type(dimensions) is list or tuple:
            # self.raw["dimensions"] = [
            #     v.value
            #     for _, v in enumerate(dimensions)
            #     if isinstance(v, enums.dimension)
            # ]
            self.raw |= {
                "dimensions": [
                    v.value
                    for _, v in enumerate(dimensions)
                    if isinstance(v, enums.dimension)
                ],
            }
        else:
            raise ValueError("Dimension argument doesn't match the\
                    expected type.")

        if enums.dimension.SEARCH_APPEARANCE in dimensions \
            and len(dimensions) > 1:
            # SEARCH_APPEARANCE cannot be combined with any other dimensions.
            # Remove it to prevent the executed query throwing an error.
            self.raw.get("dimensions")\
                .remove(enums.dimension.SEARCH_APPEARANCE)

        return self

    def __filter_remove(self, list, filter: str, expression: str) -> None:
        """Private method to remove a filter assuming it's present in the
        collection.
        The filter name is assumed to be the key item.

        Parameters
        ----------
        list : list
            the filters collection
        filter : str
            the ID of the filter to remove
        expression : str
            The corresponding matching value.
            If ALL, all filters of the same type will be removed.

        Returns
        -------
        None
        """
        if list is not None:
            for item in list[::-1]:
                if item.get("filters")[0].get("dimension") == filter:
                    if (
                        expression == "ALL"
                        or item.get("filters")[0].get("expression") == expression
                    ):
                        list.remove(item)

    def __filter_build(
            self,
            dimension: str,
            expression: str,
            operator: str
    ) -> dict:
        """Private method to build the filter conditions to be applied to
        a given query.

        Group_type is currently hardcoded as no other options are allowed
        at present.

        Parameters
        ----------
            dimension: str
                The dimention to include in the filter.
            expression: str
                The value to use during the filtering operation
            operator: str
                The condition to apply when filtering.

        Returns
        -------
            dict
        """
        group_type = "and"
        dimension_filter = {
            "dimension": dimension,
            "expression": expression,
            "operator": operator,
        }
        filter_group = {"groupType": group_type, "filters": [dimension_filter]}

        return filter_group

    @overload
    def filter(
        self,
        country: enums.country,
        operator: enums.operator = enums.operator.EQUALS,
        append: bool = False,
    ):
        """Return a Query instance with a filter aimed at limiting
        results by the specified country.

        Parameters
        ----------
        country : gsc_wrapper.country
            The country you would like to filter on.
        operator : str
            The operator you would like to use to filter.
            Possible values are
            - equals (default)
            - contains
            - notContains
            - includingRegex
            - excludingRegex
        append : bool
            Delete a filter with the same key if it exists.
            Can be optional, hence False.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.filter(country.ITALY, operator.EQUAL)
        <gsc_wrapper.query.Query(...)>

        >>> query.filter(country=country.UNITED_KINGDOM,
            operator.NOT_CONTAINS)
        <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def filter(
        self,
        dimension: enums.dimension,
        expression: str,
        operator: enums.operator = enums.operator.EQUALS,
        append: bool = False,
    ):
        """Return a Query instance with a filter aimed at limiting
        results by the specified dimension.

        Parameters
        ----------
        dimension : gsc_wrapper.dimension
            Dimension you would like to filter on.
        expression : str
            The value you would like to filter.
        operator : str
            The operator you would like to use to filter.
            Possible values:
            - equals (default)
            - contains
            - notContains
            - includingRegex
            - excludingRegex
        append : bool
            Delete a filter with the same key if it exists.
            Can be optional, hence False.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.filter(dimension=dimension.PAGE, expression='/blog',
            operator=operator.CONTAINS)
        <gsc_wrapper.query.Query(...)>

        >>> query.filter(dimension.PAGE, '/blog/?$',
            operator.INCLUDING_REGEX)
        <gsc_wrapper.query.Query(...)>
        """
        ...

    @dispatcher
    def filter(self):
        """Method not implementated as a fallback to warn developers."""
        raise NotImplementedError(
            "The required method signature is not implemented yet."
        )

    @filter.register
    def __(
        self,
        dimension: enums.dimension,
        expression: str,
        operator: enums.operator = enums.operator.EQUALS,
        append: bool = False,
    ):
        """Overloaded method to work with all other type of filters."""

        # Check for the right data type
        if isinstance(dimension, enums.dimension):
            _dimension: str = dimension.value
        else:
            raise ValueError("Dimension argument does not match the expected type.")

        # SEARCH_APPEARANCE is a dimension that can be used only at
        # a "metric" level.
        # Prevent the query to return errors by not doing anything.
        if enums.dimension.SEARCH_APPEARANCE.value in dimension:
            return self

        # Check for the right data type
        if isinstance(operator, enums.operator):
            _operator: str = operator.value
        else:
            raise ValueError(
                "Operator argument does not match the \
                    expected type."
            )

        # Remove the existing filter if it has been previously used
        if not append:
            self.__filter_remove(
                self.raw.get("dimensionFilterGroups"), dimension.value, "ALL"
            )

        filter = self.__filter_build(_dimension, expression, _operator)
        self.raw.setdefault("dimensionFilterGroups", []).append(filter)

        return self

    @filter.register
    def __(
        self,
        country: enums.country,
        operator: enums.operator = enums.operator.EQUALS,
        append: bool = False,
    ):
        """Overloaded method to work specifically with a country data type."""

        # Check for the right data type
        if isinstance(country, enums.country):
            _country: str = country.value
        else:
            raise ValueError("Dimension argument doesn't match the expected\
                    type.")

        # Check for the right data type
        if isinstance(operator, enums.operator):
            _operator: str = operator.value
        else:
            raise ValueError("Operator argument doesn't match the expected\
                    type.")

        # Remove the existing filter if it has been previously used
        if not append:
            self.__filter_remove(
                self.raw.get("dimensionFilterGroups"), "country", "ALL"
            )

        filter = self.__filter_build("country", _country, _operator)
        self.raw.setdefault("dimensionFilterGroups", []).append(filter)

        return self

    @overload
    def filter_remove(self, country: enums.country):
        """
        Return a query upon the given country has been removed from the
        query.

        Parameters
        ----------
        country : gsc_wrapper.country
            Country used to identify the filter to remove.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> site.query.filter_remove(country_name)
        <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def filter_remove(self, dimension: enums.dimension, expression: str):
        """
        Return a query upon the given dimension has been removed from the
        query.

        Parameters
        ----------
        dimension : enum.dimension
            Dimension used to identify the filter to remove.
        expression : str
            Value used to identify the filter to remove.
            It works in pair with the dimension.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> site.query.filter_remove(
                dimension=dimension.PAGE,
                expression='/blog/'
            )
        <gsc_wrapper.query.Query(...)>

        >>> site.query.filter(dimension.PAGE, '/blog/')
        <gsc_wrapper.query.Query(...)>
        """
        ...

    @dispatcher
    def filter_remove(self):
        """Method not implementated as a fallback to warn developers."""
        raise NotImplementedError("Method not implementated on purpose.")

    @filter_remove.register
    def __(self, dimension: enums.dimension, expression: str):
        """Overloaded method to remove the dimension filter."""
        self.__filter_remove(
            self.raw.get("dimensionFilterGroups"), dimension.value, expression
        )

    @filter_remove.register
    def __(self, country: enums.country):
        """Overloaded method to remove the country filter."""
        self.__filter_remove(
            self.raw.get("dimensionFilterGroups"), "country", country.value
        )

    def limit(self, *limit):
        """
        Return a query limiting the number of rows returned. It can also
        be used to offset a certain number of rows using a SQL-like syntax.

        Parameters
        ----------
        *limit : int
            The maximum number of rows to return.
            Whenever two values are provided, these will be interpreted as
            the lower and higher bounds.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> site.query.limit(10)
        <gsc_wrapper.query.Query(...)>

        >>> site.query.limit(10, 10)
        <gsc_wrapper.query.Query(...)>
        """
        if len(limit) == 2:
            start, maximum = limit
        else:
            start = 0
            maximum = limit[0]

        self.raw |= {
            "startRow": start,
            "rowLimit": 25000 if maximum > 25000 else maximum,
        }

        return self

    @overload
    def range(self, startDate: date, endDate: date):
        """
        Return a query that fetches metrics within a given date range.

        Parameters
        ----------
        startDate : date
            Query start date.
        endDate : date
            Query end date.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.range(startDate=date(2022, 10, 10),
                        endDate=date(2022, 11, 10))
        <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def range(self, startDate: str, endDate: str):
        """
        Return a query that fetches metrics within a given date range.

        Parameters
        ----------
        startDate : str
            Query start date in ISO format.
        endDate : str
            Query end date in ISO format.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> site.query.range(startDate='2022-10-10', endDate='2022-11-10')
        <gsc_wrapper.query.Query('2022-10-10', '2022-11-10')>
        """
        ...

    @overload
    def range(self, startDate: date, days: int, months: int):
        """
        Return a query that fetches metrics within a given date range.
        If months is negative the start and end date will be adjusted
        accordingly.

        Parameters
        ----------
        startDate : date
            The query start date.
        days : int
            The number of days to add or substract from the start date.
        months : int
            The number of months to add or substract from the start date.
            If months is negative, startDate is adjusted accordingly.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.range(startDate=date(2022, 10, 10),
            days=0, months=1)
        <gsc_wrapper.query.Query(...)>

        >>> query.range(date(2022, 10, 10), 0, -1)
        <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def range(self, startDate: str, days: int, months: int):
        """
        Return a query that fetches metrics within a given date range.
        If months is negative the start and end date will be adjusted
        accordingly.

        Parameters
        ----------
        startDate : str
            Query start date in ISO format.
        days : int
            The number of days to add or substract from startDate.
            If days is negative, startDate is adjusted accordingly.
        months : int
            The number of months to add or substract from the start date.
            If months is negative, startDate is adjusted accordingly.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nesting

        Examples
        --------
        >>> query = Query(site)
        >>> query.range(startDate='2022-10-18', days=1, months=0)
        <gsc_wrapper.query.Query(...)>

        >>> query.range('2022-10-18', -1, 0)
        <gsc_wrapper.query.Query(...)>
        """
        ...

    def __range_build(self, startDate: date, endDate: date):
        # Private method to build the range field
        today = date.today()
        max_old_date = date.today() + relativedelta(months=-16, days=-1)

        # If the datastate require a full data set and the starting date
        # is today, the date is arbitrarily changed.
        if self.raw["dataState"] == enums.data_state.FINAL.value:
            if startDate >= today:
                startDate = today - relativedelta(days=1)
            if endDate >= today:
                endDate = today - relativedelta(days=1)

        if startDate < max_old_date:
            startDate = max_old_date

        if startDate > endDate:
            endDate, startDate = startDate, endDate

        self._startDate = startDate
        self._endDate = endDate
        self.raw |= {
            "startDate": startDate.isoformat(),
            "endDate": endDate.isoformat()
        }

        return self

    @dispatcher
    def range(self):
        """The base implementation dispatching the call to the right
        overload."""
        raise NotImplementedError("Method not implementated on purpose.")

    @range.register
    def __(self, startDate: str, days: int, months: int):
        """Overload using a date in string forms, and an int days and
        months version to build the end date."""

        if startDate == "":
            startDate = str(date.today())

        try:
            return self.range.register[("date", "int", "int")](
                self, date.fromisoformat(startDate), days, months
            )
        except Exception:
            raise ValueError("The requested date is not in ISO format.")

    @range.register
    def __(self, startDate: date, days: int = 0, months: int = 0):
        """Overload using a date, and integer days and months to build
        the end date."""

        # Max start date adjustment will be done later
        endDate = startDate + relativedelta(days=days, months=months)

        if days + months < 0:
            # Date swapping to ensure periods validity
            startDate, endDate = endDate, startDate

        return self.__range_build(startDate, endDate)

    @range.register
    def __(self, startDate: str, endDate: str):
        """Overload using start and end date as string to build
        the end date."""

        return self.__range_build(
            date.fromisoformat(startDate), date.fromisoformat(endDate)
        )

    @range.register
    def __(self, startDate: date, endDate: date):
        """Overloaded using date argurments to build the end date."""

        return self.__range_build(startDate, endDate)

    def search_type(
        self,
        search_type: enums.search_type = enums.search_type.WEB
    ):
        """Return a new query that filters for the specified search type.
        This can be seen as a metric.

        Parameters
        ----------
        search_type : gsc_wrapper.search_type
            The search type you would like to report on.

        Returns
        -------
        gsc_wrapper.query.Query
            A reference of the same class to allow methods nestings

        Examples
        --------
        >>> query = Query(site)
        >>> query.search_type(gsc_wrapper.search_type.WEB)
        <gsc_wrapper.query.Query(...)>
        """
        # Check for the right data type
        if isinstance(search_type, enums.search_type):
            search_type = search_type.value
        else:
            raise ValueError(
                "Search Type argument does not match the \
                expected type."
            )

        # self.raw |= {"type": search_type}
        self.raw.setdefault("type", str(search_type))

        return self

    def get(self) -> Report:
        """Return all the data available for a given query chunking
        the resultset into batches and retrieving the information
        into a report.

        Returns
        -------
        gsc_wrapper.query.Report
            A `Report` object containing the extracted dataset.

        Examples
        --------
        >>> query = Query(site)
        >>> query.get()
        <gsc_wrapper.query.Report(rows=...)>
        """
        raw_data = []
        startRow = self.raw.get("startRow", 0)
        step = self.raw.get("rowLimit", 25000)
        chunck_len = 0
        is_complete = False

        while not is_complete:
            chunk = self.execute()

            if chunk.get("rows"):
                raw_data += chunk.get("rows")
                chunck_len = len(raw_data)
            else:
                is_complete = True

            # Move to the next "batch"
            self.raw["startRow"] += step

        # Report stores a copy of the query object for reference.
        # Overwriting the limit boundaries to have vibility on the
        # processed data.
        query = self.raw.copy()
        query["startRow"] = startRow
        query["rowLimit"] = chunck_len

        # Resetting the limit to the original values
        self.limit(startRow, step)

        return Report(self.webproperty.url, query, raw_data)

    def __validate_query(self):
        """Internal method to avoid query errors that could be flagged at
        run-time."""

        # Case 1: Type = GOOGLE_NEWS cannot accet a filter
        # where Dimension is QUERY
        if self.raw.get("type") and "google_news" in self.raw.get("type"):
            self.__filter_remove(self.raw.get("dimensionFilterGroups"), "query", "ALL")

    def execute(self) -> object:
        """Invoke the API to obtain the raw data as per the specified query.
        Set the boundaries with the `limit` method to extract a specific
        subset.

        When a larger dataset is expected the get() method should be used
        so the cursor approach kicks-in.
        """
        self.__validate_query()

        try:
            self._wait()
            response = (
                self.webproperty.account.service.searchanalytics()
                .query(siteUrl=self.webproperty.url, body=self.raw)
                .execute()
            )

        except googleapiclient.errors.HttpError as e:
            raise e

        return response

    def _wait(self):
        now = time.time()
        elapsed = now - self._lock
        wait = max(0, 1 - elapsed)
        time.sleep(wait)
        self._lock = time.time()

        return wait


class Report:
    """Unpack the `Query` raw data into a report that can be
    consumed in different manners.
    The class does not execute any query directly.

    Parameters
    ----------
    webproperty : str
        The site being queried, stored for reference.
    query : dict
        The dictionary containing the query used to generate the report,
        stored for reference.
    raw : dict
        The raw data queried via the Query class.

    Examples
    --------
    >>> site = account["www.test1.com"]
    >>> query = gsc_wrapper.Query(site)
    >>> report = query.range(startDate=date.today(), days=1, months=0)\
                    .dimension(gsc_wrapper.dimension.DATE).get()
    >>> report
    <gsc_wrapper.query.Report(rows=...)>


    >>> data = query.filter(country=gsc_wrapper.country.ITALY).execute()
    >>> report = gsc_wrapper.Report(site.url, site.query.raw, data.get('rows'))
    >>> report
    <gsc_wrapper.query.Report(rows=...)>


    You can access the data using:
    >>> report = query.range(startDate=date.today(), days=1, months=0)\
            .dimension(gsc_wrapper.dimension.DATE).get()
    >>> report.rows
    [Row(...), ..., Row(...)]
    """

    def __init__(self, webproperty: str, query, raw: list):
        self.webproperty = webproperty
        self.query = query

        if type(raw) is not list and "keys" in raw[0].keys():
            raise TypeError("Raw data is not in the expected format.")

        base_metrics = ["clicks", "impressions", "ctr", "position"]

        # Not all metrics are supported by all reports types.
        if self.query.get("search_type") and self.query.get("search_type") in (
            "discover",
            "google_news",
        ):
            base_metrics.remove("position")

        self.dimensions = self.query.get("dimensions", list())
        self.columns = self.dimensions + base_metrics
        self.row = collections.namedtuple("Row", self.columns)
        self.rows = []
        self.raw = raw
        self._append()

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, key):
        return self.rows[key]

    def __contains__(self, item):
        return item in self.rows

    def __len__(self):
        return len(self.rows)

    def __repr__(self):
        return f"<gsc_wrapper.query.Report(rows={len(self)})>"

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
        for row in self.raw:
            row = row.copy()
            dimensions = dict(zip(self.dimensions, row.pop("keys", [])))
            self.rows.append(self.row(**dimensions, **row))

    def to_dict(self) -> dict:
        return [dict(row._asdict()) for row in self.rows]

    def to_dataframe(self) -> object:
        """Convert the resultset into a Pandas DataFrame for machine learning
        analysis or on-the-fly querying.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with the flattened rsults.
        """
        import pandas
        return pandas.DataFrame(self.rows)

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
        str or None
            The filename were data was persisteed
        """
        import pathlib
        import pickle
        import re

        if filename == "":
            # This is calibrated around the webproperty format
            domain = re.sub(r"[./]", "_", self.webproperty).replace("__", "_").replace(":", "")
            filename = date.today().strftime("%Y%m%d") + \
                "_" + domain + "query.pck"

        # dir = pathlib.Path.cwd()
        # unique_path = dir / filename

        # if unique_path.exists():
        #     filename = filename.replace(".pck", "{:03d}.pck")
        #     counter = 0
        #     while True:
        #         counter += 1
        #         unique_path = dir / filename.format(counter)
        #         if not unique_path.exists():
        #             break
        unique_path = Util.get_filename(pathlib.Path.cwd(), filename)
        try:
            data = [{"url": self.webproperty, "query": self.query}, self.raw]

            if unique_path != "":
                with open(unique_path, "wb") as f:
                    pickle.dump(data, f)
                    return str(unique_path)
            else:
                return None
        except OSError as e:
            print(f"{type(e)}: {e}")
            return None

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
                    return cls(data[0].get("url"), data[0].get("query"), data[1])
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
            return cls(data[0]["url"], data[0]["query"], data[1])

        return None
