# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2019-01-11
### Added
- passive mode which allows proxy to run without attempting to compile or cache anything

## [0.4.0] - 2019-01-01
### Added
- Fat package support

## [0.3.1] - 2018-12-12
### Fixed
- pin version of prometheus client as 0.5+ is not compatible with sanic-prometheus

## [0.3.0] - 2018-12-06
### Added
- Support for compiling udunits2

## [0.2.0] - 2018-11-20
### Added
- A healthcheck endpoint at `/healthz`
- /metrics

### Changed
- logging

## 0.1.1 - 2018-11-16
### Fixed
- make compile process handle more errors

[unreleased]: https://github.com/ministryofjustice/analytics-platform-cran-proxy/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/ministryofjustice/analytics-platform-cran-proxy/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/ministryofjustice/analytics-platform-cran-proxy/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/ministryofjustice/analytics-platform-cran-proxy/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ministryofjustice/analytics-platform-cran-proxy/compare/v0.1.1...v0.2.0
