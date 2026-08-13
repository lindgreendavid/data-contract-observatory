# Research scope

## Bounded question

When does a stable, machine-consumed public-data series cease to satisfy its declared operational
contract, and how can that failure be distinguished from an unusual but valid observation?

## Primary source

The case study is the European Central Bank's daily US dollar/euro reference-rate series,
`EXR.D.USD.EUR.SP00.A`, accessed through the ECB Data Portal's SDMX 2.1 REST service. The series is
official, public, machine-readable, and normally updated every TARGET operating day. The ECB says
the rates are set through a daily central-bank concertation procedure, usually published around
16:00 CET, quoted against the euro, and intended for information rather than transaction use.

Primary documentation:

- [ECB Data Portal API overview](https://data.ecb.europa.eu/help/api/overview)
- [ECB API data-query specification](https://data.ecb.europa.eu/help/api/data)
- [Pinned series page](https://data.ecb.europa.eu/data/datasets/EXR/EXR.D.USD.EUR.SP00.A)
- [Reference rates and publication schedule](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)
- [ECB reference-rate framework](https://www.ecb.europa.eu/stats/pdf/exchange/Frameworkfortheeuroforeignexchangereferencerates.en.pdf)
- [ECB long-term TARGET closing calendar](https://www.ecb.europa.eu/press/pr/date/2000/html/pr001214_4.en.html)

## Unit of observation

One published reference-rate observation for one calendar date. `OBS_VALUE` is the number of US
dollars per euro; it is not a transactional quote and this project performs no investment analysis.

## What is evaluated

1. Transport and parseability.
2. Required schema and pinned series identity.
3. Date/value validity, uniqueness, and chronological order.
4. Publication freshness after a conservative 18:00 Europe/Frankfurt grace period on TARGET days.
5. A separately labelled review signal for an extreme latest one-day log return.

## What is not evaluated

- whether the exchange rate is economically “correct”;
- market manipulation, forecasting, or investment performance;
- ECB's unpublished upstream inputs or internal tolerance checks;
- all possible forms of data drift;
- the reliability of public-data portals in general from this single case.

## Epistemic boundary

A contract failure supports only the claim that the response does not satisfy this repository's
predeclared consumer contract at the recorded time. A statistical review signal supports only a
request for inspection. Neither establishes that the ECB published an erroneous value.
