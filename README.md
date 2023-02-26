# Google Search Console Wrapper

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`gsc_wrapper` takes the pain out of working with the [Google Search
Console](https://support.google.com/webmasters/answer/9128668) Search Analytics Query API. It is written in Python and provides convenient features to make querying a site's search analytics data easier.

This wrapper is inspired (in fact partially replicates some parts) of [Josh Carty's wrapper](https://github.com/joshcarty/google-searchconsole). However, it also introduces fundamental changes to the logic and python coding, some are purely aestetical, others introduce modification that couldn't fit as project fork.  

For more information, see below a description of the main modules along with a comparison with Carty's library.

### Authentication
The authentication process is still managed via Google's library ([API discovery](https://github.com/googleapis/google-api-python-client)), but the flow is no longer managed inside the wrapper. 

Both the `client ID` and the `client secret` have to be generated or loaded, if any, but the implementation logic is now left to the developer. It comes with itself that there is no more functionality to persist the credentials in a token.

While this might be seen as a regression, the externalisation is a feature design choice to allow a more flexible approach to source the Google's authentication token, whether this could be via a web-form approach or via a TUI.  

### Querying
The core of this wrapper is based on the [`search analytics: query`](https://developers.google.com/webmaster-tools/v1/searchanalytics/query) API from Google, and with which you can pull out details from your GSC (Google Search Console Account).
This class prepares the JSON payload to be queried and later consumed via the `Report` class. A report is automatically generated when the `get` method is recalled, in which case the full dataset is lazily returned.
To obtain a snapshot of the data, use the `execute` method.

***Search Type*** can be used to segment the type of insights you want to retried. If you don't use this method, the default value used will be **web**.
```py
query.search_type(gsc_wrapper.search_type.IMAGE)
```

***Date Range*** can be used to box the insights into the specified period. There are several methods to combine the dates and several internal checks to prevent issuing an invalid request. 
Also, the dates take into consideration the `data_state` value (`FINAL` by default), making adjustments if necessary to return details for an entire full day. 

The date range is always double checked to avoid going back more than 16 months or greater than today. If a date range is not specified, by default the start date is set to today -2, and the end date to today -1.

***Filters*** can be applied to the query in the same manner as for the GSC UI. Allowed options are: `contains`, `equals`, `notContains`, `notEquals`, `including Regex` & `excluding Regex`. For instance:

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

For more plain English information about metrics and dimension, check the official [guide](https://support.google.com/webmasters/answer/7576553).

This class has been rewritten to support methods' overloading and acceptance of specific types of arguments from a declarative set of enumerations. In addition, any not allowed permutation is now prevented automatically on the basis of Google's most recent specifications.
Lastly, the specification of a filter whose key has previously been used will automatically drop the previous condition and replace it with the new one unless the optional `append` parameter is set to `True`.

Method cascading has been preserved to allow for more object-oriented API construction.

* **Exploration.** The account hierarchy can be traversed via the returned list of the webproperties (to which the  permission levels is shown). No significant changes here.

* **Exports.** Clean JSON and pandas.DataFrame outputs so you can easily analyse your data in Python or Excel. Added the possibility to persist data into a Python's pickle file.


## Quickstart

In order to work with this package you need to download and install locally my [Multi-Argument Dispatcher package](https://github.com/andreamoro/Dispatcher) and follow the [prerequisites](https://developers.google.com/webmaster-tools/search-console-api-original/v3/prereqs) have to be fullfilled, which can be summarised as per the below:
- At least one [Google Account](https://accounts.google.com/signup/v2/webcreateaccount)
- A website listed into the Google Search Console 
- A project credential on Google's API system (remember to save your credentials somewhere)
-  

After that, executing your first query is as easy as

```python
import gsc_wrapper

credentials = {
    ... # You need to implement the flow and credential logic separately
} 

account = gsc_wrapper.Account(credentials)
site_list = account.webproperties()
site = account[0] # or account['your qualified site name']

data = site.query.filter(gsc_wrapper.country.ITALY)
results = data.execute()
```

### Integration with Pandas DataFrame 
If you wish to load your data directly into a pandas DataFrame, to avoid loading it manually after the extraction, 
you can do it easily: 

```python
report = data.to_dataframe()
```

### Disk Persistance
There are multiple situations where you might want to save your data to avoid further querying the same batch again and again.
This comes handy especially if you want to save part of your daily allowance.

```python
    data = ... your query logic here ... 
    report = data.get()
    report.to_disk('your_file_name.pck')
```

The persistance uses the native Python pickling, saving the data into the local hard drive using the specified file name or a project-consistent filename generated after the queried website.

There is no data compress mechanism, no third party libraries, no database saving logic. More complex requirements have to be provisioned independently.