# v1.0.0 release audit

Audit date: 2026-08-13. Scientific baseline: `8cb106f58a907a5984315ff0faa300837b2e9654`.
The exact product-release commit is the commit resolved by annotated tag `v1.0.0`.

## Evidence checked

- Primary source: ECB series `EXR.D.USD.EUR.SP00.A` through the official SDMX data API.
- The operational run inspected 385 recent observations through 2026-08-13 and returned
  `contract_status=pass`, `review_status=clear`; its source SHA-256 is stored in the report.
- The frozen v1 suite contains one clean control and nine injected faults covering transport,
  schema, identity, type, duplication, ordering, invalid value, freshness and extreme return.
  All nine expected classifications were observed; the one control emitted no false alert.
- A retrospective replay evaluated 7,010 prefixes of the current historical vintage: zero hard
  contract failures and nine review signals. It is explicitly not historical revision evidence.

## Prospective evidence boundary

The `evidence` branch starts an append-only series of immutable runs, normalized states and
date/value/status deltas. At v1.0.0 there is one real prospective run, so no longitudinal rate or
60-day claim is made. Detection-rate and false-alert intervals in `reports/v1-evaluation.json`
describe only the controlled suite and retrospective current-vintage replay.
