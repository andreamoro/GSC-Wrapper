# Test suite

Unit tests for `gsc_wrapper`. The suite runs fully offline: it builds an
`Account` with empty credentials and injects a fake web-property list, so **no
Google credentials and no network access are required** — the live API is never
called.

## Running

```bash
pip install -e ".[test]"
pytest
```

## Layout

| File | Covers |
| --- | --- |
| `conftest.py` | Shared fixtures (`account`, `site`, `query`, `inspect`) |
| `test_enums.py` | Enum values and the `MyEnumMeta` metaclass |
| `test_util.py` | `Util.get_filename` |
| `test_account.py` | `Account` / `WebProperty` lookup and equality |
| `test_query.py` | `Query` builder: `range`, `dimensions`, `filter`, `limit`, … |
| `test_query_report.py` | Search-analytics `Report` (rows, dataframe, disk round-trip) |
| `test_inspection.py` | `InspectURL` URL bag management |
| `test_inspection_report.py` | URL-inspection `Report` (enum flattening, disk round-trip) |

`test.py` is the original manual, browser-driven authentication / integration
script. It needs real credentials and a browser, so it is **not** collected by
pytest (the configuration only collects `test_*.py`).
