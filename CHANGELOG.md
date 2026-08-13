# Changelog

All notable public changes to Data Contract Observatory are recorded here. The project follows
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-08-13

- Stabilize the product and preserve the frozen protocol 1.0.0.
- Add a versioned nine-fault suite, controlled false-alert measurement and Wilson intervals.
- Add a 7,010-prefix replay of the current historical vintage, explicitly separated from revision evidence.
- Add append-only prospective evidence runs, normalized state and revision deltas on `evidence`.
- Separate product version, prospective runs, retrospective replay and synthetic evidence on the site.

## [0.1.0] - 2026-08-13

### Added

- Frozen protocol 1.0.0 for ECB series `EXR.D.USD.EUR.SP00.A`.
- Hard schema, identity, value, uniqueness, ordering, transport, and TARGET-day freshness checks.
- Separately labelled robust statistical review signal for the latest one-day log return.
- Nine deterministic calendar, contract, transport, and synthetic mutation tests.
- Interactive failure laboratory and machine-readable latest observation report.
- Scheduled auditable observation workflow and GitHub Pages deployment.
- Citation, security, contribution, licensing, and research-scope documentation.

### Initial result

The first complete frozen-protocol run inspected 385 observations, passed every hard contract
check, and emitted no statistical review signal. This result describes that recorded response only;
it does not establish the future reliability of the source.

[0.1.0]: https://github.com/lindgreendavid/data-contract-observatory/releases/tag/v0.1.0
[1.0.0]: https://github.com/lindgreendavid/data-contract-observatory/releases/tag/v1.0.0
