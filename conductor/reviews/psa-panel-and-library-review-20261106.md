# PSA panel advice and library alignment — 6 November 2026

## Panel scope and consensus

The user requested advice from a panel of agents. Three independent AI-agent
reviews covered scientific design, numerical evidence and implementation/library
alignment. They used the same retained evidence; their agreement is not an
independent empirical replication or model-owner approval. No panel member edited
files, reran native operations or changed an environment.

All three support conditional computational qualification and retaining current
priors unchanged while scientific provenance is resolved. They advise against
fitting priors to an unexplained scalar or treating static LL/MP/UL summaries as
probability quantiles. The actual software corrections and numerical results are
in the [qualification report](./psa-qualification-20261106.md).

## Options, rationale and tradeoffs

| Option | Rationale and benefits | Tradeoffs and contingency | Recommendation |
|---|---|---|---|
| Retain the current definitions as a labelled exploratory/legacy scenario | Reproducible behavior and independent workbook arithmetic are qualified; avoids inventing new empirical assumptions | No calibrated uncertainty, representative national-cost or decision-validity claim; the scientific tasks remain open | Recommended immediate position |
| Recover an authoritative workforce uncertainty specification and reference derivation | Can resolve units, distribution sources, dependence, weights, valuation period and intended output | Depends on obtaining original documents/generator/joint draws; if recovered, version and qualify only the affected changes | Preferred route to scientific acceptance |
| Commission a new versioned uncertainty model if recovery fails | Explicitly addresses the intended decision, supported data/elicitation and structural uncertainty | New scientific work and approval; not retrospectively claimed as legacy parity | Recommended contingency; retain the current scenario and deterministic base/DSA evidence separately |

More simulation draws can improve Monte Carlo precision within a specified model.
They cannot identify missing priors, recover provenance or approve the estimand.
No new scientific model or parameter values were selected by this panel.

## Scientific-design perspective

Productive time needs a definition before a distribution is chosen. An absolute
fraction, a baseline multiplier and an efficiency index describe different
models. A multiplier preserves row-specific baselines but does not itself supply
an empirically justified distribution. Clipping values changes probability mass
and must not be used to conceal a support/meaning problem.

The normal superannuation prior needs a reason to represent uncertainty rather
than an applicable fixed entitlement. The allowance triangle needs evidence for
its support and mode, including role eligibility and price period. Mathematical
convenience or a plausible-looking range is not calibration.

Common policy uncertainty may justify common draws. Role/state measurement
uncertainty may call for separate or hierarchical effects. Independent row draws
can understate aggregate uncertainty when errors are shared; fully shared draws
can overstate common variation when heterogeneity dominates. Treat such structures
as explicitly labelled sensitivity alternatives until evidence supports a choice.

The equally weighted row mean is an equally weighted basket. Workforce-FTE cost,
workload-weighted average and total expenditure require different quantities and
denominators. Population weights present in the workbook do not establish that
they are appropriate for every workforce estimand.

## Numerical-assurance perspective

The strongest evidence is controlled common-draw replay backed by 300 independently
recalculated original-workbook cells. The 10,000-draw CDF/analytic-moment diagnostics
support declared distribution mechanics, with no scientific prior approval implied.

The old cached-input behavior is a demonstrated defect. Preserving mathematical
raw-input semantics is preferable to reproducing constant outputs that ignored
sampled changes. Historical cost-only archives are descriptive evidence and cannot
uniquely identify their joint input model or seed.

Small Pearson correlations do not prove independence. Finite normal stress values
are not distribution-support boundaries. A programmatic production-runner replay
is not a complete new command-line/native-Excel run. Tail precision needs a stated
target, even when a mean check and 10,000 iterations pass.

## Implementation perspective and actions taken

The panel identified silent skipping, inconsistent API/runner validation and
null-omitting means. The follow-up packet now shares one validated sampler and
fails closed on incomplete models or role costs. A bounded follow-up review found
no blocking defect in that packet. It preserves valid scalar draw order and units.

The original absolute tolerance is now explicit; exact comparison requires both
relative and absolute tolerances to be zero. The one-draw summary edge case is
also fixed. Future arbitrary callbacks should carry their own role-key identity
contract; the current production pipeline's keyed workbook comparisons remain the
basis for its identity assurance.

For scientific acceptance, retain source/version, actual RNG/backend identity,
scenario order/hash, seed, lock/runtime, prepared inputs, formula identity,
aggregation and percentile definition, and joint parameter traces. Existing
private frozen evidence is preserved. A reusable cross-project simulation package
is deferred until a stable common contract and release need are established.

## Library comparison and justified workforce changes

The genomics repository was an actively edited, read-only comparator. Its manifests
and installed-package snapshot were inspected; its source, environments and
private evidence were not changed. Genomics' assay draw archive is not a workforce
uncertainty specification.

| Library/capability | Workforce disposition | Rationale and tradeoff |
|---|---|---|
| Polars 2.1.0, NumPy 2.5.4, PyArrow 26.0.1, openpyxl 3.1.5, Pandera 0.35.0 | Retained shared numeric/workbook foundation | Already aligned in the inspected environments; existing workload needs them |
| Pydantic 2.14.3 | Upgraded from 2.14.2; minimum and lock aligned | Strict run/distribution contracts follow the same validated-contract approach as genomics; new bounds are mathematical validity checks, not new empirical priors |
| Ruff 0.17.4 | Upgraded from 0.17.3 | Full ALL scope retained; no rule exclusions added |
| pytest-timeout 2.4.0 and pytest-socket 0.8.1 | Added and qualified on repo-local Python 3.15.1 | Explicit 120-second tests, Python network sockets disabled, Unix sockets allowed; no retries; native child-process networking is not controlled by these plugins |
| pre-commit 4.7.0 | Added and configuration validated | Uses existing locked local hooks; no hooks were installed into another checkout |
| Matplotlib and local typing subset | Retained | Required plots remain exercised; avoid unnecessary pandas-dependent development stubs for this workload |
| pandas 3.1.1, SciPy 1.18.1, asteval 1.0.10 | Isolated private reference environment only | Needed for frozen legacy code and independent CDF comparison; absent from workforce runtime/dev dependency declarations; unused production asteval stub removed |
| Genomics Flask, NumPy Financial, YAML/Plotly/reporting stack | No workforce dependency added | No current workforce interface/calculation requires those capabilities |
| Genomics optional formatting/selection/audit helpers | No wholesale adoption | Ruff already supplies formatting/import checks; its actively edited selector was not copied; current targeted pytest cache practice is retained |

The candidate environment passed 67 tests and strict checks before promotion.
Following shared-contract and reporting fixes, the final local gate passed 95 tests,
formatting, full-tree lint, basedpyright and Bandit. Wheel/sdist contents and an
installed-wheel PSA replay were verified. Normal Git hooks remained enabled;
private qualification environments and receipts were kept separate from runtime
and source distribution.

## Recommended decision sequence and genuine contingencies

1. Retain current input definitions and the conditional numerical qualification.
2. Obtain a model-owner specification for parameter meaning/units, evidence,
   dependence, row sharing, weighting and scalar derivation.
3. If unavailable, commission a separately versioned model and use the current
   model only for explicitly conditional/exploratory scenarios. Keep deterministic
   original-workbook/DSA results available with their existing limitations.
4. Qualify any scientific changes, set a Monte Carlo tail-precision target, and
   complete scientific/release review. Source-only privacy screening and hosted
   checks are also required before integrating the new local software packet.

No distributions, weights, reference values or original inputs were changed to
resolve the discrepancy. No panel advice is recorded as scientific approval.

## Source investigation correction — 6 November 2026

The retained private source review traces original
workbook L3 and history. All 25 included rows store productive-time fraction 1
(number format 0.0%). Legacy PSA uses absolute draws. Original pre-reference
midpoint mean is [private workbook reference]; retained conditional mean is [private comparison] lower.
The 150000 literal was introduced at 8bb90f9 without recovered derivation; the
earlier [private comparison] comparison does not establish disagreement with the original
workbook baseline. Historical receipts remain intact. Reference-introduction
formulas agree with current formulas to 1.16e-10. No priors were calibrated.

Retain nominal-hours baseline and separately labelled productive-hours scenarios.
Scientific prior provenance, dependence, weights and tail precision remain open.
The unit investigation resolves the workbook representation; it does not approve
absolute prior support above 1 as a productive-hours fraction.

## GHA terminal evidence handoff — 6 November 2026

A separate owner supplied a terminal evidence handoff. Its detailed results and private evidence remain with that owner. Scientific prior provenance, dependence, weighting and tail precision remain open.
