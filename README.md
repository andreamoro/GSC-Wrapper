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

BEWARE: GSC wrapper depends from another package of mine - [`multi-args-dispatcher`](https://github.com/andreamoro/Dispatcher) which has not yet distributed on a public repository. The installation package is setup to provision the file for you. 


## Quickstart

In order to work with this package the [prerequisites](https://developers.google.com/webmaster-tools/search-console-api-original/v3/prereqs) have to be fullfilled, which can be summarised as per the below:
- At least one [Google Account](https://accounts.google.com/signup/v2/webcreateaccount) with at least one website registered.
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
