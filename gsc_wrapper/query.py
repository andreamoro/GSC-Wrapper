import collections
import time
from datetime import date
from typing import Type, overload

import googleapiclient.errors
from dateutil.relativedelta import relativedelta
from dispatcher import dispatcher
from typing_extensions import Self

from gsc_wrapper import enums


class Query:
    """
    Returns the results for a given query against the
    Google Search Console - Search Results.

    The most important methods are:
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
    
    Usage:
    >>> site.query.range(startDate='2022-11-10', days=-7, months=0)\\
            .dimension(gsc_wrapper.dimension.DATE).get()
    <gsc_wrapper.query.Report(rows=...)>
    
    >>> query = site.query.range(startDate='2022-11-10', days=-7, months=0)\\
    ...                   .dimension(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.QUERY)\\
    ...                   .filter('query', 'dress', 'contains')\\
    ...                   .filter('page', '/womens-clothing/', 'contains')\\
    ...                   .limit(20000)
    >>> query.get()
    <gsc_wrapper.query.Report(rows=...)>
    """

    _lock = 0

    def __init__(self, api):
        self.api = api
        self._startDate = date.today() - relativedelta(days=2)
        self._endDate = date.today() - relativedelta(days=1)
        self.raw = {
            'startDate': self._startDate.isoformat(),
            'endDate': self._endDate.isoformat(),
            'dataState': 'final',
            'aggregationType': 'auto'
        }
        self.limit(25000)

    @property
    def startDate(self):
        return self._startDate

    @property
    def endDate(self):
        return self._endDate

    def data_state(self, 
                data_state: enums.data_state = enums.data_state.FINAL):
        """
        Return a new query filtering by fresh (not finalized) data or
        full-state data.

        Args:
            data_state (gsc_wrapper.data_state):
                The data_state you would like to use.
                Possible values:
                - 'FINAL' (default = d-1 backward),
                - 'ALL' (finalised & fresh data).

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> query.data_state(gsc_wrapper.data_state.FINAL)
            <gsc_wrapper.query.Query(...)>
        """

        # Check for the right data type
        if isinstance(data_state, enums.data_state):
            data_state = data_state.value
        else:
            raise ValueError("Data State argument does not match the expected type.")

        self.raw['dataState'] = data_state

        return self

    def dimensions(self, *dimensions: enums.dimension):
        """
        Return a query that fetches the specified dimensions.
        Args:
            *dimensions(enums.dimension):
                Dimensions you would like to report on.
                Possible values:
                - country
                - device
                - page
                - query
                * SearchAppearance can be specified
                only on its own.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.dimension(dimension.DATE, dimension.PAGE)
            <gsc_wrapper.query.Query(...)>
        """

        if isinstance(dimensions, enums.dimension):
            self.raw['dimensions'] = dimensions.value
        elif type(dimensions) is list or tuple:
            self.raw['dimensions'] = [
                v.value
                for _, v in enumerate(dimensions)
                if isinstance(v, enums.dimension)
            ]
        else:
            raise ValueError("Dimension argument does not match the expected type.")
        # SEARCH_APPEARANCE cannot be combined with any other dimension type
        # Prevent the query to return errors
        if enums.dimension.SEARCH_APPEARANCE in dimensions and \
           len(dimensions) > 1:
            self.raw['dimensions'].remove(enums.dimension.SEARCH_APPEARANCE)

        return self

    def __filter_remove(self, list, filter, expression) -> None:
        """Private method to remove a filter assuming it's present in the
        collection.
        The filter name is assumed to be the key item.

        Args:
            list       (list) : the filters collection
            filter     (str)  : the ID of the filter to remove
            expression (str)  : the corresponding matching value.
                    If ALL, all filters of the same type will be removed.

        Returns:
            None
        """
        if not list is None:
            for item in list[::-1]:
                if item.get('filters')[0].get('dimension') == filter:
                    if expression == 'ALL' or \
                        item.get('filters')[0].get('expression') == expression:
                        list.remove(item)

    def __filter_build(
            self,
            dimension: str,
            expression: str,
            operator: str) -> dict:
        # Private method to build the filter with the given values

        # Enforcing the group_type as no other options are allowed at present
        group_type = 'and'

        dimension_filter = {
            'dimension': dimension,
            'expression': expression,
            'operator': operator
        }

        filter_group = {
            'groupType': group_type,
            'filters': [dimension_filter]
        }

        return filter_group

    @overload
    def filter(
            self,
            country: enums.country,
            operator: enums.operator,
            append: bool):
        """
        Return a query that filters rows by the specified country.

        Args:
            country  (gsc_wrapper.country): The country you would like to
                                            filter on.
            operator (str)                : The operator you would like to use
                                            to filter.
                                            Possible values are
                                            - equals (default)
                                            - contains
                                            - notContains
                                            - includingRegex
                                            - excludingRegex
            append   (bool)               : Delete a filter with the same key
                                            if it exists.
                                            Can be optional, hence False.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.filter(country.ITALY, operator.EQUAL)
            <gsc_wrapper.query.Query(...)>

            >>> site.query.filter(country=country.UNITED_KINGDOM, operator.NOT_CONTAINS)
            <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def filter(
            self, 
            dimension: enums.dimension, 
            expression: str,
            operator: enums.operator, 
            append: bool):
        """
        Return a query that filters rows by the specified filter.

        Args:
            dimension  (gsc_wrapper.dimension): Dimension you would like to
                                                filter on.
            expression (str)                  : The value you would like to
                                                filter.
            operator   (str)                  : The operator you would like to
                                                use to filter.
                                                Possible values:
                                                - equals (default)
                                                - contains
                                                - notContains
                                                - includingRegex
                                                - excludingRegex
            append     (bool)                 : Delete a filter with the same
                                                key if it exists.
                                                Can be optional, hence False.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.filter(dimension=dimension.PAGE, expression='/blog', operator=operator.CONTAINS)
            <gsc_wrapper.query.Query(...)>

            >>> site.query.filter(dimension.PAGE, '/blog/?$', operator.INCLUDING_REGEX)
            <gsc_wrapper.query.Query(...)>
        """
        ...

    @dispatcher
    def filter(self):
        raise NotImplementedError("Method not implementated on purpose.")

    @filter.register
    def __(self, dimension: enums.dimension,
           expression: str, operator: enums.operator = enums.operator.EQUALS,
           append: bool = False):
        """Overloaded method to work with all other type of filters."""

        # Check for the right data type
        if isinstance(dimension, enums.dimension):
            dimension = dimension.value
        else:
            raise ValueError("Dimension argument does not match the expected type.")

        # SEARCH_APPEARANCE is a dimension that can be used only at a "metric" level
        # Prevent the query to return errors by not doing anything
        if enums.dimension.SEARCH_APPEARANCE.value in dimension:
            return self

        # Check for the right data type
        if isinstance(operator, enums.operator):
            operator = operator.value
        else:
            raise ValueError("Operator argument does not match the expected type.")

        # Remove the existing filter if it has been previously used
        if not append:
            self.__filter_remove(self.raw.get('dimensionFilterGroups'), dimension, 'ALL')

        filter = self.__filter_build(dimension, expression, operator)
        self.raw.setdefault('dimensionFilterGroups', []).append(filter)

        return self

    @filter.register
    def __(self, country: enums.country,
           operator: enums.operator = enums.operator.EQUALS,
           append: bool = False):
        """Overloaded method to work specifically with a country data type."""

        # Check for the right data type
        if isinstance(country, enums.country):
            country = country.value
        else:
            raise ValueError("Dimension argument does not match the expected type.")

        # Check for the right data type
        if isinstance(operator, enums.operator):
            operator = operator.value
        else:
            raise ValueError("Operator argument does not match the expected type.") 

        # Remove the existing filter if it has been previously used
        if not append:
            self.__filter_remove(self.raw.get('dimensionFilterGroups'), 'country', 'ALL')

        filter = self.__filter_build('country', country, operator)
        self.raw.setdefault('dimensionFilterGroups', []).append(filter)

        return self

    @overload
    def filter_remove(self, country: enums.country):
        """
        Return a query upon the given country has been removed from the
        query.

        Args:
            country  (gsc_wrapper.country): Country used to identify the
            filter to remove.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.filter_remove(country_name)
            <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def filter_remove(self, dimension: enums.dimension, expression: str):
        """
        Return a query upon the given dimension has been removed from the
        query.

        Args:
            dimension  (enum.dimension): Dimension used to identify the
                filter to remove.
            expression (str)           : Value used to identify the 
                filter to remove.
                It works in pair with the dimension.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.filter_remove(dimension=dimension.PAGE, expression='/blog/')
            <gsc_wrapper.query.Query(...)>

            >>> site.query.filter(dimension.PAGE, '/blog/')
            <gsc_wrapper.query.Query(...)>
        """
        ...

    @dispatcher
    def filter_remove(self):
        raise NotImplementedError("Method not implementated on purpose.")

    @filter_remove.register
    def __(self, dimension: enums.dimension, expression: str):
        """Overloaded method to remove the dimension filter."""
        self.__filter_remove(self.raw.get('dimensionFilterGroups'),
                dimension.value,
                expression)

    @filter_remove.register
    def __(self, country: enums.country):
        """Overloaded method to remove the country filter."""
        self.__filter_remove(self.raw.get('dimensionFilterGroups'),
                'country',
                country)

    def limit(self, *limit):
        """
        Return a query limiting the number of rows returned. It can also
        be used to offset a certain number of rows using a SQL-like syntax.

        Args:
            *limit (int): The maximum number of rows to return.
                Whenever two values are provided, these will be
                interpreted as the lower and higher bounds.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
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

        self.raw.update({
            'startRow': start,
            'rowLimit': 25000 if maximum > 25000 else maximum
        })

        return self

    @overload
    def range(self, startDate: date, endDate: date):
        """
        Return a query that fetches metrics within a given date range.

        Args:
            startDate (date): Query start date.
            endDate (date): Query end date.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.range(startDate=date(2022, 10, 10), startDate=date(2022, 11, 10))
            <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def range(self, startDate: str, endDate: str):
        """
        Return a query that fetches metrics within a given date range.

        Args:
            startDate (str): Query start date in ISO format.
            endDate   (str): Query end date in ISO format.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
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

        Args:
            startDate (date): Query start date.
            days      (int) : The number of days to add or substract from the
                              start date.
            months    (int) : The number of months to add or substract from
                              the start date.
                              If months is negative, startDate is adjusted 
                              accordingly.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.range(startDate=date(2022, 10, 10), days=0, months=1)
            <gsc_wrapper.query.Query(...)>

            >>> site.query.range(date(2022, 10, 10), 0, -1)
            <gsc_wrapper.query.Query(...)>
        """
        ...

    @overload
    def range(self, startDate: str, days: int, months: int):
        """
        Return a query that fetches metrics within a given date range.
        If months is negative the start and end date will be adjusted
        accordingly.

        Args:
            startDate (str):    Query start date in ISO format.
            days      (int):    The number of days to add or substract from
                                startDate.
                                If days is negative, startDate is adjusted
                                accordingly.
            months    (int):    The number of months to add or substract from
                                the start date.
                                If months is negative, startDate is adjusted
                                accordingly.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.query.range(startDate='2022-10-18', days=1, months=0)
            <gsc_wrapper.query.Query(...)>

            >>> site.query.range('2022-10-18', -1, 0)
            <gsc_wrapper.query.Query(...)>
        """
        ...

    def __range_build(self, startDate: date, endDate: date):
        # Private method to build the range field
        today = date.today()
        max_old_date = date.today() + relativedelta(months=-16, days=-1)

        # If the datastate require a full data set and the starting date
        # is today, the date is arbitrarily changed.
        if self.raw['dataState'] == enums.data_state.FINAL.value:
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

        self.raw.update({
            'startDate': startDate.isoformat(),
            'endDate': endDate.isoformat()
        })

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

        if startDate == '':
            startDate = date.today()

        try:
            return self.range.register[('date', 'int', 'int')](self, date.fromisoformat(startDate), days, months)
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

        return self.__range_build(date.fromisoformat(startDate),
                                  date.fromisoformat(endDate))

    @range.register
    def __(self, startDate: date, endDate: date):
        """Overloaded using date argurments to build the end date."""

        return self.__range_build(startDate, endDate)

    def search_type(self,
                    search_type: enums.search_type = enums.search_type.WEB):
        """
        Return a new query that filters for the specified search type.
        This can be seen as a metric.

        Args:
            search_type (gsc_wrapper.search_type): The search type you would
            like to report on.

        Returns:
            `gsc_wrapper.query.Query`

        Usage:
            >>> site.uery.search_type(gsc_wrapper.search_type.WEB)
            <gsc_wrapper.query.Query(...)>
        """
        self.raw['type'] = search_type.value

        return self

    def get(self) -> 'Report':
        """Return the full batch of data by processing the constructed query
        and invoking the API.
        It returns the dataset in a Report object.

        Returns:
            `gsc_wrapper.query.Report`

        Usage:
            >>> site.query.get()
            <gsc_wrapper.query.Report(rows=...)>
        """
        raw_data = []
        startRow = self.raw.get('startRow', 0)
        step = self.raw.get('rowLimit', 25000)
        chunck_len = 0
        is_complete = False

        while not is_complete:
            chunk = self.execute()

            if chunk.get('rows'):
                raw_data += chunk.get('rows')
                chunck_len = len(raw_data)
            else:
                is_complete = True

            # Move to the next "batch"
            self.raw['startRow'] += step

        # Report stores a copy of the query object for reference.
        # Overwriting the limit boundaries to have vibility on the
        # processed data.
        query = self.raw.copy()
        query['startRow'] = startRow
        query['rowLimit'] = chunck_len

        # Resetting the limit to the original values
        self.limit(startRow, step)

        return Report(self.api.url, query, raw_data)

    def __validate_query(self):
        """Internal method to avoid query errors that could be flagged at
        run-time."""

        # Case 1: Type = GOOGLE_NEWS cannot accet a filter
        # where Dimension is QUERY
        if self.raw.get('type') and 'google_news' in self.raw.get('type'):
            self.__filter_remove(self.raw.get('dimensionFilterGroups'), 'query', 'ALL')

    def execute(self):
        """Invoke the API to process the query with the given parameters,
        returning a response containing the raw data.
        Set the boundaries with the `limit` method to extract a specific
        subset.

        When a larger dataset is expected the get() method should be used
        so the cursor approach kicks-in.
        """
        url = self.api.url
        self.__validate_query()

        try:
            self._wait()
            response = self.api.account.service.searchanalytics().query(
                siteUrl=url, body=self.raw).execute()

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

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.raw == other.raw
        return False

    def __repr__(self):
        return f"<gsc_wrapper.query.Query({self.raw})>"


class Report:
    """
    Unpack the raw data previously queried via the Query class into a report 
    object ready to be consumed. The class does not execute any query directly. 
    A Report can be explicitly created using the `Query.get()` method.

    Args
        url   (str) : The site being queried.
                This is stored for reference only.
        query (dict) : The dictionary containing the query used
                to generate the report.
                This is stored for reference only.
        raw (dict) : The raw data queried via the Query class.

    Usage:
    >>> report = site.query.range(startDate=date.today(), days=1, months=0)\
                    .dimension(gsc_wrapper.dimension.DATE).get()
    >>> report
    <gsc_wrapper.query.Report(rows=...)>

    >>> data = site.query.filter(country=gsc_wrapper.country.ITALY).execute()
    >>> report = gsc_wrapper.Report(site.url, site.query.raw, data.get('rows'))
    >>> report
    <gsc_wrapper.query.Report(rows=...)>

    You can access the data using:
    >>> report = site.query.range(startDate=date.today(), days=1, months=0)\
                     .dimension(gsc_wrapper.dimension.DATE).get()
    >>> report.rows
    [Row(...), ..., Row(...)]
    """

    def __init__(self, url: str, query, raw):
        self.url = url
        self.query = query

        if type(raw) is not list and 'keys' in raw[0].keys():
            raise TypeError("Raw data is not in the expected format.")

        base_metrics = ['clicks', 'impressions', 'ctr', 'position']

        # Not all metrics are supported by all reports types.
        if self.query.get('search_type') and \
                self.query.get('search_type') in ('discover', 'google_news'):
            base_metrics.remove('position')

        self.dimensions = self.query.get('dimensions')
        self.columns = self.dimensions + base_metrics
        self.row = collections.namedtuple('Row', self.columns)
        self.rows = []
        self.raw = raw
        self.append(raw)

    def append(self, raw):
        for row in raw:
            row = row.copy()
            dimensions = dict(zip(self.dimensions, row.pop('keys', [])))
            self.rows.append(self.row(**row, **dimensions))

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

    def to_dict(self):
        return [dict(row._asdict()) for row in self.rows]

    def to_dataframe(self):
        import pandas
        return pandas.DataFrame(self.rows)

    def to_disk(self, filename='') -> str | None:
        """Persist the dictionary with the data on disk. If the filename is
        not given, one will be generated automatically.
        A mechanism to avoid overwriting an existing file had been included.

        Args
            filename (str): The name of the while where the data will be
            persisted.

        Returns
            str. The filename were data was persisteed or None
        """
        import pathlib
        import pickle
        import re

        if filename == '':
            domain = re.sub(r'[./]', '_', self.url).replace('__', '_').replace(':', '')
            filename = date.today().strftime("%Y%m%d") + '_' + domain + '.pck'

        dir = pathlib.Path.cwd()
        unique_path = dir / filename

        if unique_path.exists():
            filename = filename.replace('.pck', '{:03d}.pck')
            counter = 0
            while True:
                counter += 1
                unique_path = dir / filename.format(counter)
                if not unique_path.exists():
                    break

        try:
            data = [{'url': self.url, 'query': self.query}, self.raw]

            if unique_path != '':
                with open(unique_path, 'wb') as f:
                    pickle.dump(data, f)
                    return unique_path
            else:
                return None
        except:
            return None

    @classmethod
    def from_disk(cls, filename: str) -> 'Report':
        """Load a file from the disk a previously saved report stored
        with the GSC Wrapper class.

        Args
            filename (str): The name of the file used to persist data

        Returns
            Report. The unpacked rows.
        """
        import pickle

        if filename != '':
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                return cls(data[0].get('url'),
                           data[0].get('query'),
                           data[1])

        return None

    @classmethod
    def from_datastream(cls, data: bytes) -> 'Report':
        """Rebuild the report with the GSC Wrapper class using
        the data stream passed in the argument.

        Args
            data (byte): The dara stream containing the report details

        Returns
            Report. The unpacked rows.
        """
        import pickle

        if data:
            data = pickle.loads(data)
            return cls(data[0]['url'],
                        data[0]['query'],
                        data[1])

        return None
