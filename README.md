# Google Search Console Wrapper

[![License: GPL 3.0](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl-3.0.txt)


## Package purpose and content

`gsc_wrapper` is a package to take the pain out when working with the [Google Search
Console](https://support.google.com/webmasters/answer/9128668) APIs. 
It is written in Python and provides convenient features to easily query:
- the [Search Analytics](https://developers.google.com/webmaster-tools/v1/api_reference_index#Search_analytics) data
- the [Page Indexing](https://developers.google.com/webmaster-tools/v1/api_reference_index#Inspection_tools) data


## Installation & Requirements

Google Search Console Wrapper requires Python 3.7 or greater. At present the package is not distributed on any repository. 
To use the package, download the code on your local machine then install using the following command:

```bash
    python -m pip install . 
```

**BEWARE**: GSC Wrapper depends from another package of mine - [`multi-args-dispatcher`](https://github.com/andreamoro/Dispatcher) - tha is provisioned by the installation package.


## Quickstart

In order to work with this package the [prerequisites](https://developers.google.com/webmaster-tools/search-console-api-original/v3/prereqs) have to be fullfilled, which can be summarised as per the below:
- A [Google Account](https://accounts.google.com/signup/v2/webcreateaccount) with at least one website registered.
- Access to the [Google API console](https://console.cloud.google.com/apis/library/searchconsole.googleapis.com) - remember to save your credentials somewhere.

After that, executing your first query is really straightforward as per the following example.

_Example:_
```python
import gsc_wrapper

credentials = {
    ... # You need to implement the flow and credential logic separately
} 

account = gsc_wrapper.Account(credentials)
site_list = account.webproperties()
site = account[0] # or account['your qualified site name']
query = gsc_wrapper.Query(site)
data = query.filter(gsc_wrapper.country.ITALY)
results = data.execute()
```


### Authentication
The authentication process is managed via the Google's library ([API discovery](https://github.com/googleapis/google-api-python-client)); however, the flow is not managed inside the wrapper. 

Both the `client ID` and the `client secret` have to be generated and saved in a file containinig the OAuth 2.0 or generated on the fly with the authentication flow provided by Google's library. The implementation logic is left to the developer.

While this might be seen as a regression, the externalisation is a feature design choice to allow a more flexible approach to source the Google's authentication token, whether this could be via a web-form approach or via a TUI.  

The same externalisation applies to service accounts. Build the `google.auth` service-account credentials yourself — useful for non-interactive use on servers, scheduled jobs or CI — and pass the resulting object to `Account`, exactly as you would pass externally-sourced OAuth credentials. A worked example, including Google Workspace domain-wide delegation, is in the [Service Account authentication guide](docs/service-account-auth.md).


### Querying

#### Search Analytics

The role of this class is to pull out details from your GSC (Google Search Console account) using the [`search analytics: query`](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) API from Google. The work is inspired from [Josh Carty's wrapper](https://github.com/joshcarty/google-searchconsole), from which it inherits part of the logic; however, due to the extended code refactoring, branching the original project was nearly impossible.

The basic principle of this class is to prepares the JSON payload to be consumed via the `Report` class. This class supports methods' overloading and acceptance of specific types of arguments from a declarative set of enumerations. In addition, any not-allowed permutation is now prevented on the basis of Google's most recent specifications.
The specification of a filter whose key has previously been used will automatically drop the previous condition and replace it with the new one unless the optional `append` parameter is set to `True`.

A method cascading is in place to allow for more object-oriented API construction.

A report is automatically generated when the `get` method is recalled, in which case the full dataset is lazily returned.
To limit the data to the first batch, or to retrieve the raw data as pulled from the API, use the `execute` method.

***Search Type*** can be used to segment the type of insights you want to retrieve. If you don't use this method, the default value used will be **web**.

_Example:_
```py
query.search_type(gsc_wrapper.search_type.IMAGE)
```

***Date Range*** can be used to box the insights into the specified period. There are several methods to combine the dates and several internal checks to prevent issuing an invalid request. 
Also, the dates take into consideration the `data_state` value (`FINAL` by default), making adjustments if necessary to return details for an entire full day. 

The date range prevents to go back more than 16 months or greater than today. If no range is specified, by default the start date is set to today -2, and the end date to today -1.

***Filters*** can be applied to the query in the same manner as for the GSC UI. Allowed options are: `contains`, `equals`, `notContains`, `notEquals`, `including Regex` & `excluding Regex`.

_Examples:_
```py
site.query.filter(country=gsc_wrapper.country.ITALY)
```
or

```py
site.query.filter(gsc_wrapper.country.ITALY)
```

In using the Regex filters, you must follow [RE2 syntax](https://github.com/google/re2/wiki/Syntax).<br>
```py
query.filter(dimension.PAGE, '/blog/?$', operator.INCLUDING_REGEX)
```

For more plain English information about metrics and dimension, check the official [Google's guide](https://support.google.com/webmasters/answer/7576553).


***Exploration.*** The account hierarchy can be traversed via the returned list of the webproperties (to which the permission levels is shown).

***Exports.*** Clean JSON and pandas.DataFrame outputs so you can easily analyse your data in Python or Excel. Added the possibility to persist data into a Python's pickle file.


#### Page Indexing

The role of this class is to pull out details from your GSC (Google Search Console account) using the [`URL Inspection: index.inspect`](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect) API from Google. 

The basic principle of this class is to prepares the JSON payload to be consumed via the `Report` class implementing methods' overloading where appropriate to faciliate third party developers coding.

A report is automatically generated when the `get` method is recalled, in which case the full dataset is lazily returned.
To limit the data to the first batch, or to retrieve the raw data as pulled from the API, use the `execute` method.


### Asynchronous API

An `asyncio`-native API lives alongside the synchronous one under `gsc_wrapper.aio` (the same names are also re-exported at the top level). It is a drop-in mental model: the declarative builder methods (`range`, `filter`, `dimensions`, `limit`, `add_url`, …) are identical and synchronous, while the network-bound `execute`/`get` become coroutines you `await`.

Under the hood it talks to the REST endpoints directly over [`httpx`](https://www.python-httpx.org/), smooths the request rate with [`aiolimiter`](https://aiolimiter.readthedocs.io/) (replacing the blocking `time.sleep` throttle) and caps concurrency, so bulk operations — notably URL inspection — run **concurrently** instead of one at a time. Access tokens are sourced from the very same `google.auth` credentials objects you already pass to the synchronous `Account`.

The `AsyncAccount` owns its HTTP transport, so use it as an async context manager (or call `await account.aclose()` when done).

_Example:_
```python
import asyncio
import gsc_wrapper
from gsc_wrapper import dimension

async def main():
    credentials = { ... }  # OAuth dict or a google.auth credentials object

    async with gsc_wrapper.AsyncAccount(credentials) as account:
        site = await account.webproperty("https://www.example.com/")

        # Search Analytics
        report = await (
            site.query
            .range(startDate="2022-11-10", days=-7, months=0)
            .dimensions(dimension.DATE)
            .get()
        )

        # URL Inspection — every URL inspected concurrently
        inspect = site.inspect
        inspect.add_url([
            "https://www.example.com/",
            "https://www.example.com/blog",
        ])
        indexing = await inspect.get()

asyncio.run(main())
```

The rate limit and concurrency cap are tunable on `AsyncAccount` (`max_rate`, `time_period`, `max_concurrency`, `timeout`). The returned `Report` objects are exactly the synchronous ones, so every export (`to_dict`, `to_dataframe`, `to_disk`/`from_disk`, …) works identically.

#### Where concurrency actually helps

The two APIs parallelise at different granularities, and it is worth knowing which is which:

- **URL Inspection** issues one independent request per URL, so `await inspect.get()` fans them out with `asyncio.gather` and finishes in roughly the time of a single call — the bigger the batch, the bigger the win.
- **Search Analytics** is a *single* cursor-paginated query: `get()` cannot fetch page _n+1_ until page _n_ comes back, so one report still pages sequentially.
  The async win there comes from running **several independent queries at once** (different sites, date ranges or dimensions) and `await asyncio.gather(...)`-ing them yourself.

#### How it is built (and why)

- **Alongside, not instead of.** The synchronous API is the right default for notebooks, one-off scripts and synchronous call sites; the async API is opt-in for servers and fan-out workloads. Nothing in the sync path changed behaviourally.
- **Thin, shared core.** `AsyncQuery`/`AsyncInspectURL` subclass their synchronous counterparts, inheriting the whole declarative builder unchanged; only `execute`/`get` are overridden to `await`. `Query.get`'s pagination policy is factored into shared helpers so the sync and async versions differ by a single `await`. This keeps the async layer cheap to maintain rather than a parallel copy.
- **Auth is reused.** Tokens come from your existing `google-auth` credentials; only the (infrequent) refresh is off-loaded to a thread and lock-guarded, while
  the actual API calls are fully non-blocking over `httpx`.
- **No magic accessors.** `account[0]` / `len(account)` are intentionally absent on the async side — those dunders cannot be coroutines and the sync ones hide a network call. Use the explicit `await account.webproperties()` and `await account.webproperty(key)` instead. (`Report`'s own dunders are kept, because by then the data is already in memory.)

See [`tests/standalone_async.py`](tests/standalone_async.py) for a runnable demo
that prints data and times the concurrency, fully offline.


### Integration with Pandas DataFrame 
If you wish to load your data directly into a [Pandas DataFrame](https://pandas.pydata.org/), this can be done contextually after the extraction. 
Please pay attention that Pandas has not been included as part of this package requirements, therefore you need to install it separately.
 
_Example:_
```python
report = data.to_dataframe()
```


### Data Persistance
There are situations where you might want to persist your data to query the same batch again and again.
This comes in handy, especially if you want to preserve part of your daily query allowance.

Therefore, with this package, I introduced a disk persistance approach that leans on native Python pickling. When recalling the `to_disk` method, the class will save the data into your local hard drive using either the specified filename or a project-consistent filename generated after the queried website.

_Examples:_
```python
    data = ... your query logic here ... 
    report = data.get()
    report.to_disk('your_file_name.pck')
```

or

```python
    data = ... your query logic here ... 
    report = data.get()
    report.to_disk()
```

Two corresponding methods have been made available to reload persisted information: `from_disk` and `from_datastream`. Both of them returns a `Report` object that can be consumed in the same way as the one returned on a live query.

At present, there is no data compression mechanism, no third-party libraries, and no database saving logic. For more complex requirements, additional code has to be written independently.


## Testing

The package ships with an offline unit-test suite that needs no Google credentials and no network access: it builds an `Account` with empty credentials and injects a fake web-property list, so the live API is never called. The suite covers the enumerations, the `Query` builder, the URL-inspection bag and both `Report` classes, and runs on every push through a GitHub Actions workflow against Python 3.11 to 3.13.

```bash
pip install -e ".[test]"
pytest
```

See the [tests README](tests/README.md) for the suite layout and details.


## Related projects

- [BWT-Wrapper](https://github.com/andreamoro/BWT-Wrapper) — a companion wrapper that applies the same approach to the Bing Webmaster Tools API.


## Changelog

To check out major changes applied to the wrapper or understand the future evolution, you can checkout the [changelog](https://github.com/andreamoro/GSC-Wrapper/blob/master/CHANGELOG.md) file.
