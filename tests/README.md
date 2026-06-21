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
| `conftest.py` | Shared fixtures (sync and async: `account`, `site`, `query`, `inspect`, `async_account`, `async_site`, …) |
| `test_enums.py` | Enum values and the `MyEnumMeta` metaclass |
| `test_util.py` | `Util.get_filename` |
| `test_account.py` | `Account` / `WebProperty` lookup and equality |
| `test_query.py` | `Query` builder: `range`, `dimensions`, `filter`, `limit`, … |
| `test_query_report.py` | Search-analytics `Report` (rows, dataframe, disk round-trip) |
| `test_inspection.py` | `InspectURL` URL bag management |
| `test_inspection_report.py` | URL-inspection `Report` (enum flattening, disk round-trip) |
| `test_async_transport.py` | `AsyncTransport` auth header, error mapping, token refresh (httpx mocked with `respx`) |
| `test_async_account.py` | `AsyncAccount` / `AsyncWebProperty` fetch, cache, lookup, context manager |
| `test_async_query.py` | `AsyncQuery.execute` / `get` paging |
| `test_async_inspection.py` | `AsyncInspectURL` concurrent inspection and TTL cache |

The async tests are equally offline: httpx is mocked with `respx` and a fake,
always-valid credentials object means no token refresh and no network.

## Standalone scripts (not collected by pytest)

`standalone_sync.py` and `standalone_async.py` are manual, runnable demos — the
configuration only collects `test_*.py`, so neither is picked up by pytest.

- `standalone_sync.py` (formerly `test.py`) — the original browser-driven
  authentication / integration script; its `"oauth"`/`"service"` flows need real
  credentials (and a browser for OAuth).
- `standalone_async.py` — the async counterpart. Its default `"test"` flow is
  fully offline (a stub transport returns canned data), so it prints real rows
  and demonstrates concurrent URL inspection with no credentials:

  ```bash
  python tests/standalone_async.py
  ```
