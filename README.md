# Data Contract Observatory

[![CI](https://github.com/lindgreendavid/data-contract-observatory/actions/workflows/ci.yml/badge.svg)](https://github.com/lindgreendavid/data-contract-observatory/actions/workflows/ci.yml)
[![Pages](https://github.com/lindgreendavid/data-contract-observatory/actions/workflows/pages.yml/badge.svg)](https://github.com/lindgreendavid/data-contract-observatory/actions/workflows/pages.yml)

**Stable software release:** [v1.0.0](https://github.com/lindgreendavid/data-contract-observatory/releases/tag/v1.0.0).

An inspectable observability case study for a real, regularly updated public-data series. The first
contract monitors the European Central Bank's daily US dollar/euro reference-rate series without
mistaking unusual exchange-rate movement for proof of a source error.

## Question

When does a stable, machine-consumed public-data series cease to satisfy its declared operational
contract, and how can that failure be distinguished from an unusual but valid observation?

## Current result

Product and protocol 1.0.0 are stable. The core implements strict schema, identity, value, uniqueness, ordering,
and TARGET-day freshness checks. A predeclared robust statistical signal is separately classified
as `review`. The frozen fault suite correctly classifies all nine controlled faults; the single
clean control emits no false alert. A retrospective replay covers 7,010 prefixes of the current
historical vintage. These are synthetic and retrospective evaluations, not historical revision
observations. Prospective revision evidence begins with the first immutable evidence-branch run.

## Interactive experience

The [public website](https://lindgreendavid.github.io/data-contract-observatory/) turns the contract into a controlled failure laboratory: remove a required field,
change the series identity, simulate lateness, or inject an extreme return and inspect which claim
the evidence permits.

## Evidence

- Official series: [`EXR.D.USD.EUR.SP00.A`](https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A)
- [Bounded research scope](docs/research-scope.md)
- [Frozen protocol](docs/protocol.md)
- [Machine-readable contract](contracts/ecb-exr-usd-eur.json)
- [v1 machine-readable evaluation](reports/v1-evaluation.json)
- [`evidence` branch](https://github.com/lindgreendavid/data-contract-observatory/tree/evidence) with immutable runs, normalized state, and index
- Deterministic synthetic mutation tests in [`tests/`](tests/)

## Reproduce

Python 3.10–3.13 and the standard library are sufficient.

```bash
python -m unittest discover -s tests -v
python -m data_contract_observatory.cli --input tests/fixtures/ecb_valid.csv
```

To perform a live observation after installing the package:

```bash
python -m pip install -e .
contract-observe --output site/data/latest.json
```

## Boundary

A hard failure establishes only that a response violated this repository's declared consumer
contract at a recorded time. A statistical signal requests inspection; it does not establish that
the ECB, the series, or an exchange-rate observation is wrong. This is neither financial advice nor
an exchange-rate forecasting system.

## Citation

Use [`CITATION.cff`](CITATION.cff) and see the versioned [`CHANGELOG.md`](CHANGELOG.md). Source methodology remains attributable to the European Central
Bank; the monitoring software and explanation are MIT-licensed.

Part of [Lab Notes](https://blog-interactive.lindgreendavid.workers.dev/) — bounded,
reproducible, and open.
