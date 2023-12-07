# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Asynchronous methods for fast processing.

## [2.0.0] - 2023-12-07

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
