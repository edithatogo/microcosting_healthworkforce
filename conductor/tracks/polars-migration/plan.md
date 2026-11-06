# Workforce Polars Migration Plan

Reconstructed 5 November 2026 from verified source and owner evidence; this does
not retrospectively claim every historical phase received Conductor acceptance.
[x] completed; [~] actively executing; [ ] pending. On 6 November the user
selected completion for the conditional exploratory PSA scenario, with scientific
validation tracked separately. Numerical/software qualification is complete;
the assumptions are not scientifically accepted.

## Phase 1: Workbook and calculation contracts

- [x] Inventory workbook/CLI mappings and preserve original inputs and editions.
- [x] Migrate ingestion, formulas, projections and rates to typed Polars tables.
- [x] Reconcile 20 original-workbook scenarios and 500 state-role comparisons.

## Phase 2: Sensitivity analysis and outputs

- [x] Migrate configured DSA inputs, perturbations and output tables.
- [x] Execute seeded PSA through the Polars pipeline.
- [x] Qualify the legacy PSA as an explicitly exploratory scenario: preserve and document parameter meaning, original prior provenance, dependence, aggregation, reference derivation and conditional numerical parity. Record unresolved scientific validation in the separate modernization track.
- [x] Exercise existing CSV/figure outputs through installed-wheel execution.

## Phase 3: Runtime and strict verification

- [x] Qualify locked repo-local Python 3.15.1, promote to3.15.2, and retire active Pipenv/tox runners.
- [x] Preserve Pydantic/Pandera execution contracts and boundary tests.
- [x] Pass strict checks: 51-test hosted baseline, expanded to 100 local/hosted qualified tests on 6 November; full-tree Ruff/format, strict typing and Bandit retained.
- [x] Qualify wheel/sdist licence/content and installed CLI checks.

## Phase 4: Source integration and remaining acceptance

- [x] Review the source-only outgoing packet with local Gitleaks/Presidio.
- [x] Merge CI/runtime integration [PR #43](https://github.com/edithatogo/microcosting_healthworkforce/pull/43) after exact-head Actions and verify main (0985ffd).
- [x] Merge validated Renovate [PR #34](https://github.com/edithatogo/microcosting_healthworkforce/pull/34) after exact-head Actions and verify main (dc4ca0d).
- [x] Close 13 obsolete lockfile PRs as superseded and retain their exact branches until safe ancestry integration/pruning on 6 November.
- [x] Complete the final migration/release evidence review for the user-selected conditional scope; carry scientific validation forward separately.

## Current evidence and remaining acceptance — 6 November 2026

The [prior provenance and release review](../../reviews/psa-prior-provenance-20261106.md)
traces the unchanged PSA configuration to its original implementation and
compares its superannuation mean with the historical ATO schedule. This supports
the historical compatibility description, not calibration, applicability or
approval of a scientific uncertainty model.

The user selected closure for the exploratory scenario and separate scientific
follow-up. [PR #47](https://github.com/edithatogo/microcosting_healthworkforce/pull/47)
adds an explicit exploratory warning to nonempty PSA summaries and documents
that CSV files do not embed scientific qualification. It was merged as
`eab4656` after exact-head checks passed; receiving-main CI and Security passed.
The same 142-test suite passed locally
with Python 3.15.2 and previously qualified dependencies; the separate isolated
dependency sync stalled, so the hosted locked build is the clean-environment
evidence. No draws, priors, result-file schema or costing calculations changed.

## Formal review fixes — 6 November 2026

- [x] Correct the three formal review findings in source commit `9e104d5`:
  the production PSA runner emits its exploratory report, DSA recalculates
  derived outputs for an already-costed base case, and DSA comparison requires
  nonempty finite numeric evidence. The original priors and CSV schema remain
  unchanged.
- [x] Qualify and integrate [PR #48](https://github.com/edithatogo/microcosting_healthworkforce/pull/48)
  as `7edec01`: 149 local tests, Ruff, strict basedpyright and Bandit passed on
  Python 3.15.2 using existing qualified dependencies; exact-head Actions and
  receiving-main CI and Security passed. The full outgoing range was reviewed
  with Gitleaks and Presidio. The new regressions failed before the fix.

The automated PR reviewer questioned whether the warning test could fail; the
existing assertion helper raises on false, the new test failed on the original
code, and a separate unit test checks the report's exact warning text.
Scientific validation remains a separate open modernization task.

The [conditional precision review](../../reviews/psa-conditional-precision-20261106.md)
reuses the hash-verified 10,000-draw output to quantify Monte Carlo uncertainty
in its percentile endpoints and mean. No target precision has been approved, and
the diagnostic does not qualify the priors, dependence, estimand or other
scientific assumptions. Their validation remains open in the modernization track.

Conditional numerical/software parity passes: 12 shared vectors/300 independent
workbook cells and 10, 000 conditional draws. Source scientific-core blobs remain
unchanged after 79c3354. PR #45 integrated the expanded packet as 11df8b3, passing
all exact-head Actions and receiving-main CI/Security. Python 3.15.2 and 100 tests
are qualified; full coverage 77.1%, mutation 42/42, strict typing/Ruff/Bandit and
installed-wheel/CLI gates pass. Fresh 3.15.2 installed-wheel raw/costed parity
passes 20 draws using 25 original prepared workbook rows.

Source investigation resolves productive time as a fraction with baseline 1 for
all 25 rows. The retained conditional simulation mean is [private comparison] below the original
pre-reference midpoint mean [private workbook reference]. The earlier [private comparison] excess was
a comparison with a later unexplained 150000 literal at 8bb90f9, not evidence of
disagreement with the original workbook baseline. Preserve that historical
receipt while using the corrected interpretation.

Scientific acceptance remains open: prior provenance/support, dependence, target
weights/estimand and tail-precision requirements need model-owner decisions.
Retain the nominal-hours baseline and separately labelled productive-hours
scenarios without changing/clipping priors. GHA owns its source-backed scenario
adapter/report; broader modernization remains separately registered.

The 14 historical remote branch heads are now ancestral to main and safely
pruned. The old protocol drafts/source extracts remain in merged history, not
the maintained tree or accepted research. Original private migration/CI history
is integrated locally, and superseded local source branches are pruned. The
temporary public integration worktree is archived; private qualification records
and the original primary checkout are preserved. GitHub issues 30/31/32 are closed;
44 remains the healthy operational Renovate dashboard. Scientific validation
remains open in the modernization track and is not closed by this migration.
