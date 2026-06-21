# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-06-21

### Added
- Asynchronous API under `gsc_wrapper.aio`, re-exported at the top level: `AsyncAccount`, `AsyncWebProperty`, `AsyncQuery`, `AsyncInspectURL`, `AsyncTransport` and `GSCApiError`. It lives **alongside** the synchronous API — existing synchronous code is unaffected.
- `AsyncTransport`: an authenticated, non-blocking HTTP layer over `httpx` talking directly to the Search Console REST endpoints. Request rate limiting via `aiolimiter` replaces the blocking `time.sleep` throttle, a semaphore caps in-flight requests, and `GSCApiError` surfaces the API's error message.
- Concurrent URL inspection: `AsyncInspectURL.execute` inspects every queued URL with `asyncio.gather` instead of serially — the headline reason to use the async API.
- `tests/standalone_async.py`: a runnable demo (the async sibling of `standalone_sync.py`) that prints real data offline via a stub transport and shows both the inspection (intra-operation) and reporting (cross-query fan-out) concurrency wins.
- Offline async test suite (httpx mocked with `respx`, no network); `pytest-asyncio` and `respx` added to the `[test]` extra and `asyncio_mode = "auto"` configured.

### Changed
- Added `httpx` and `aiolimiter` as runtime dependencies (both rely only on Python ≥ 3.11, already required).
- Token sourcing reuses the existing `google-auth` credentials; the rare token refresh is off-loaded to a worker thread and guarded by a lock against a refresh stampede.
- Internal de-duplication so the async layer adds little maintenance: `AsyncQuery`/`AsyncInspectURL` subclass the sync builders (declarative API inherited verbatim); `Query.get`'s cursor logic is factored into shared `_paginate_init`/`_merge_chunk`/`_build_report` helpers so sync and async `get` differ only by `await`; `AsyncWebProperty` subclasses `WebProperty`; credential building/identifying is shared via `build_credentials`/`credentials_identifier`.
- The manual integration script `tests/test.py` is renamed to `tests/standalone_sync.py` for symmetry with the async demo (neither is collected by pytest).
- The standalone scripts' configuration moved from INI to TOML (`tests/config.toml`, read with the stdlib `tomllib`); `config.ini.example` becomes `config.toml.example`. The package itself reads no configuration, so this is test-only.

### Fixed
- Suppressed a Pyrefly `bad-class-definition` false positive on the runtime-built `Report` namedtuple in `query.py` (the dynamic field list is valid; the static checker cannot model it), matching the existing suppression in `inspection.py`.

## [2.1.0] - 2026-06-20

### Added
- Service account authentication: `Account` now accepts a pre-built `google.auth` credentials object (e.g. a service account) in addition to the OAuth user-credentials dict, enabling non-interactive, programmatic access. Documented in `docs/service-account-auth.md`, including Google Workspace domain-wide delegation.
- Offline unit-test suite under `tests/` (84 tests) that needs no Google credentials and no network access, plus a `[test]` optional-dependencies extra and a `pytest` configuration in `pyproject.toml`.
- GitHub Actions workflow running the test suite against Python 3.11, 3.12 and 3.13.

### Fixed
- `MyEnumMeta.__contains__` now correctly reports membership by value, member name or member, and no longer swallows results via dead branches.
- `InspectURL.remove_url` now matches the stored `UrlBag` objects by URL (previously it never removed anything), keeps `urls_to_inspect` in sync, and invalidates the cached `urls` property. The index-based removal now validates bounds correctly.
- `InspectURL.UrlBag.__eq__` compares against the correct type and returns `NotImplemented` for foreign types.
- `Query` removes the `SEARCH_APPEARANCE` enum *value* (not the member) from the dimensions list, preventing a `ValueError` when combined with other dimensions.

### Changed
- Declared `requires-python = ">=3.11"` (the code relies on `typing.Self`) and corrected the license metadata to the SPDX identifier `GPL-3.0-only`.
- Synced `__version__` in the package with the project version.

## [2.0.3] - 2026-03-01

### Fixed
- Fixed dimension comparison for SEARCH_APPEARANCE in the Query class.

### Added
- Added `requirements-dev.txt` to support local development testing of dependencies.

## [2.0.2] - 2024-01-26

### Added
- Basic cachine mechanism for the Inspect class to accelerate data retrieval.


## [2.0.1] - 2023-12-07

### Added
- Added cache mechanism for the Query.to_dataframe() method.
- The Inspection Results DataFrame object now returns descriptive values of the reported statuses.


## [2.0.0] - 2023-12-03

### Added
- A URL Inspection class to inspect the status of the pages in the Google index
- A new `Report` class under the `inspection` module to extract the Inspected URLs results
- A Selenium dependency now exists as the test class now uses some automation logic to accelerate the login process when a credential file does not exist.

### Changed
- The Query class no longer expose the WebProperty attribute, which now has to be instantiated separately
- The Report class within the Query module got the `url` param changed to `webproperty`
- Upgrade dependencies: Google OAuth 2.0 Library for Python (google-auth)
- Upgrade dependencies: Google API Client (google-api-python-client)
- Upgrade dependencies: Multi-args-dispatcher (https://github.com/andreamoro/Dispatcher)
- Type hints improvements to increase code readbility and compliance to best practices
- Doc strings have been amended for better reading, also switching to numpydoc format


## [1.0.2] - 2023-06-15

### Added
- Introduce a new from_datastream method


## [1.0.1] - 2023-03-23

### Changed
- Update of Google API Client Library

### Fixed
- Dependency package to the [Multi-Arguments Dispatcher](https://github.com/andreamoro/Dispatcher)


## [1.0.0] - 2023-02-26

### Added
- Initial Release based on the Search Analytics API and Josh Carty's wrapper (which has been extensively refactored).
