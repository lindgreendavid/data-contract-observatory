# Changelog

All notable public changes to Data Contract Observatory are recorded here. The project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

- Post-hoc, not preregistered: review-threshold audit (`src/data_contract_observatory/threshold_audit.py`,
  `reports/post-release-threshold-audit.json`). On the checksummed ECB snapshot to 2026-08-13 the frozen
  replay reproduces exactly (7,010 days, 0 contract failures, 9 review signals); the review rule fires
  far more often than a normal-returns model predicts (9 signals at z >= 6 against about 0.00001 expected;
  175 against 18.9 at z >= 3).
- Clarified in the evaluation limits that the nine-of-nine detection is a regression test of hand-made faults,
  not a detection-rate estimate, and that replay prefixes overlap.
- Redesigned site with the shared Lab Notes design system (light and dark, self-hosted Geist, no third-party requests).

- Synchronize the site's offline prospective-run fallback with the two-run evidence index; the
  live counter remains evidence-branch-driven and no longitudinal performance claim is added.

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
