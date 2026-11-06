# Microcosting Health Workforce

Translate the original workforce Excel cost model into reproducible, typed Polars
calculations for base-year labour costs, projections, rate conversion, DSA and
seeded PSA. Preserve jurisdiction/role identity, units, formula errors and
reference workbook assumptions. Preserve original inputs and earlier editions.

The supported interface is the installed `microcosting-healthworkforce` command.
It produces cost/scenario tables and figures, with workbook reconciliation kept
separate from scientific validation of uncertainty assumptions.

## Current scope

The workforce calculation source has migrated from pandas and the separate scalar
interpreter to Polars expressions. Local independent workbook comparisons cover
20 scenarios and 500 state-role values. Strict tooling and package/CLI checks
are qualified on Python 3.15.2. PR #45 and receiving-main CI/security/Codecov are
verified. The migration is complete for the user-selected exploratory PSA scope;
scientific PSA prior/dependence/weighting validation remains open in the
workforce modernization track.

Genomics and manuscript/publication work belong to separate project owners.
This Conductor setup does not change their acceptance status or authorize any
publication, external correspondence or new native operation.

## User-confirmed expansion — 6 November 2026

Plan two linked tracks: all-jurisdiction/all-sector workforce source coverage
(public-sector first), and versioned re-extraction with static snapshot plus
effective-dated activity/roster microcosting. Preserve the legacy model and keep
PSA separate. The intake audit documents all 20 worksheets and 94 physical regions;
current typed/calculation incorporation is partial. Both expansion tracks were
approved and registered; their source applicability and costing work remain open.
