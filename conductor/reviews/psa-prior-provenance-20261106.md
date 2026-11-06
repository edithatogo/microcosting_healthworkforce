# PSA prior provenance and release evidence — 6 November 2026

## Original implementation

Git commit `e90eb0fc331435a9d0280ae16859355fe5f3fcd6` introduced the PSA
configuration on 3 August 2025. Its `data/psa_scenarios.json` has the same
SHA-256 (`b683940687c81095ddffd11d708b859101f4b7184499931f6bf7152c8868c1e2`)
as the current file. The introduction contains no cited source for the
distributions. The original code sampled each listed parameter independently,
assigned its draw to the full corresponding column and took the mean of the
calculated row costs. This establishes implementation provenance and the legacy
estimand; it does not establish that the priors are calibrated or the rows
represent a population.

The [Australian Taxation Office historical rate table](https://www.ato.gov.au/api/public/content/0-997b3cca-be74-4b06-ac13-7064a2e7852c)
lists a general superannuation guarantee rate of 10.5% for 2022–23 and 11% for
2023–24. The normal prior's 10.5% mean is consistent with the former rate, but
this is not evidence that it was the author's source, that all workbook roles
have that entitlement, or that a standard deviation of one percentage point
is appropriate. The table also does not determine an employer-specific base,
contribution above the minimum, valuation period or eligibility.

The source investigation identified all 25 original workbook productive-time
values as fractions with nominal value one. The legacy uniform prior is an
absolute 0.95–1.05 draw and half of that continuous distribution lies above
one. Calling it a fraction therefore creates a domain conflict. It could only
be used as a relative index under a separately justified model definition;
the original code and configuration do not establish that interpretation.
No clipping, changed prior or substitution was applied.

## Reuse and current-release evidence

The recorded qualification source hashes for `src/psa_analysis.py`,
`src/psa_simulation.py`, `src/formula_engine.py`, `src/calculations.py`,
`data/psa_scenarios.json` and `data/formulas.json` still match the current
checkout. The lock differs from the original Python 3.15.1 receipt because it
was subsequently qualified for Python 3.15.2; it is not represented as the same
artifact. The previously reported Python 3.15.2 installed-wheel replay and
receiving-main checks remain separate evidence for that later runtime.

As of this review, PR #46 was merged as `5e82c56`; receiving-main CI and
Security passed. The conditional 10,000-draw precision assessment is in the
[precision review](./psa-conditional-precision-20261106.md). A precision target,
scientific uncertainty specification, dependence justification, intended
workforce weights and appropriate allowance eligibility remain unestablished.
The original code establishes equal row weighting as a reproducible legacy
calculation, not its suitability for a national cost estimate.

The practical existing scenario is useful as a conditional compatibility and
software-validation exercise. The earlier panel recommended exactly that
limited interpretation, while retaining scientific validation as separate work.
This report does not assert scientific approval, change the model or promote
an unresolved prior to an evidence-based entitlement.
