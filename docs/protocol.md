# Frozen monitoring protocol

**Protocol version:** 1.0.0  
**Frozen:** 13 August 2026  
**Source selected before evaluation:** ECB `EXR.D.USD.EUR.SP00.A`

This protocol was fixed before running the complete historical evaluation and before tuning any
detector against observed outcomes. A short metadata and recent-response audit was used only to
confirm that the official endpoint, fields, and series identity were technically viable.

## Confirmatory contract checks

The following checks produce a hard `failure`:

1. the response cannot be retrieved or parsed as CSV;
2. any required field in `contract.py::REQUIRED_COLUMNS` is absent;
3. any pinned identity field differs from `contract.py::IDENTITY`;
4. an observation date or value is invalid, non-finite, or non-positive;
5. observation dates are duplicated or not ascending;
6. after 18:00 Europe/Berlin, the latest observation predates the latest expected TARGET
   operating day.

The TARGET calendar is defined as weekdays excluding New Year's Day, Good Friday, Easter Monday,
1 May, Christmas Day, and 26 December. The algorithm is tested against fixed calendar examples.

## Predeclared statistical review signal

For positive observations, calculate one-day log returns. Using the latest return as the candidate
and up to 250 preceding returns as the baseline, calculate:

`robust z = (candidate - median(baseline)) / (1.4826 × MAD(baseline))`

The signal is evaluated only with at least 60 observations. Absolute robust z-scores of 6 or more
produce `review`, never `failure`. If MAD is zero, an unequal candidate yields an infinite review
score; an equal candidate yields zero.

This heuristic is intentionally conservative but is not a calibrated hypothesis test: exchange-rate
returns need not be stationary or independent, and repeated scheduled monitoring changes the
long-run false-alert probability. No p-value is reported.

## Validation plan

The implementation must pass deterministic tests covering:

- a valid contract response;
- every hard-failure class;
- weekends and recurring TARGET closing days;
- a synthetically injected extreme observation that triggers review without contract failure;
- an ordinary synthetic sequence that remains clear.

Synthetic mutation tests validate implementation sensitivity; they do not estimate real-world
error prevalence. Live observations are evaluated only after these tests pass.

## Amendments

Any changed field, threshold, calendar rule, or interpretation requires a versioned protocol
amendment explaining the reason. It must not silently overwrite version 1.0.0.
