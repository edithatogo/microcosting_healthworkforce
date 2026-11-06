# Workforce modernization specification

## Status and purpose

Specification approved by the user on 6 November 2026. Type: refactor and assurance, with optional
feature evaluations. Translate the assessed architecture roadmap into staged,
measurable improvements without changing economic assumptions implicitly.
Planning only; implementation, remote publication and shared registry edits are
not authorized by this draft. All acceptance criteria below are pending.

## Baseline and ownership

Assessment baseline: codex/polars-costing at
55c757956547a8da5ec2384c9b07cef749a74749, in
[local worktree].
This planning chat owns only this new draft track directory. Record its verified
chat identifier before formal integration ownership registration.

Canonical Conductor context already exists in the integration owner's worktree:
[local worktree].
Owner: chat local-only, branch
codex/workforce-conductor. Its conductor/ownership.md and existing Polars migration
track retain ownership of active PSA qualification, tooling/dependency promotion
and shared Conductor records. Do not initialize competing project context here.

On 6 November the owning chat was actively qualifying PSA, original-model common
draw comparisons, error handling, reporting percentiles and library alignment.
Those findings supersede the older checkout assessment where applicable. Consume
its terminal source/evidence handoff before assigning overlapping implementation.
Do not copy private receipts or mutate either lane's running environment.

## Existing architecture to retain

- Restricted arithmetic AST compiler already produces native Polars expressions;
  scalar evaluation reuses it. Do not replace it with SymPy without a new need.
- Existing Pydantic v2 adapters, Pandera Polars integration, Hypothesis,
  pytest-gremlins, NumPy seeded simulation, Matplotlib and Sphinx/Furo/MyST.
- Direct workbook LL/UL outputs and formula-derived midpoint have distinct
  semantics. Preserve original workbook inputs, reference identity and editions.
- Python 3.15.2, uv lock, strict basedpyright, Ruff ALL, Apache-2.0 and ordinary
  Git hooks. Reverify the newest qualified runtime patch at implementation time.

## Required improvements

### Contracts and economic assurance

Complete non-coercing formula/configuration contracts: unique IDs, valid formula
references, dependency cycles, supported operators, required output mappings and
supported calculation methods. Validate DSA variations, filters and parameter
references; validate PSA distribution variants, finite bounds, spread, ordering,
iterations and seeds before simulation. Reuse the active owner's completed work.

Extend existing Pandera input/scenario contracts for identity, required columns,
finite numbers, positive hours, nonnegative applicable monetary/leave values and
scientifically justified rate domains. Do not impose a universal upper bound of
one on every percentage-like input. Decide zero/missing productivity and missing
formula-column compatibility explicitly: current neutral/zero fallbacks must
not silently become strict rejection or accepted scientific input.

Productivity requires a model-owner decision on absolute fractions versus
multipliers. The active PSA review found configured absolute draws of 0.95–1.05;
strict fraction validation cannot be introduced by silently clipping, truncating
or reinterpreting them. Keep legacy reproduction and scientific acceptance
explicitly distinguished until resolved.

Extend Hypothesis tests for conditional cost monotonicity, positive productivity
inverse scaling, joint salary/development-allowance homogeneity, row permutation,
unaffected-row preservation, rate consistency and projection recurrence. Year 0
must be invariant to indexation; later positive costs increase under valid higher
compounding rates. Direct LL/UL outputs are exempt from midpoint formula laws.
Use finite bounded generators and justified floating-point tolerances. Preserve
independent workbook reconciliation; property tests are complementary evidence.

### PSA consolidation and reproducibility

After the owner's terminal handoff, reconcile the reusable API and CLI to one
sampling/calculation core. Test raw and already-costed input frames, unsupported
parameters/distributions, empty/nonfinite results and reporting interpolation.
Retain parameter draw identity, workforce identity, cost aggregation definition,
seed and RNG algorithm/version. Equal seeds across different RNGs are not proof
of identical draws. Baseline compatibility includes one shared parameter draw
across workforce rows per iteration, independent configured parameters and the
existing unweighted mean, pending model-owner decisions.

Retain input/config hashes, model revision, source state, runtime/dependencies,
sampler settings, output digests and failures in private existing receipts.
Report percentile intervals accurately rather than as confidence intervals for
the mean. Do not present a literal workbook reference with unresolved provenance
as scientific validation. Keep implementation parity, distribution checks and
scientific acceptance as separate results.

### Performance qualification

Compile/reuse formula plans per immutable configuration where benchmarking shows
benefit, with correct mapping/cache invalidation and unchanged error semantics.
Evaluate bounded simulation batches indexed by iteration and workforce identity;
compare identical common draws before benchmarking speed/memory. Test batch-size
independence, row order, final partial batches and bounded memory. Benchmark lazy
execution against eager expressions rather than mandating LazyFrame everywhere.
The delivered table has 25 rows; no unmeasured speedup claim is acceptable.

Trial fastexcel/calamine only for workbook value ingestion. Compare merged header
reconstruction, duplicate labels, row keys, missing/error values, dtypes and
recalculated cached values. Retain LibreOffice recalculation and openpyxl editing
for the independent scenario oracle. openpyxl cannot become a development-only
dependency while runtime workbook editing still requires it. Measure parsing and
end-to-end recalculation separately; retain the qualified reader if parity,
Python 3.15 build support or meaningful benefit is absent. Do not describe Excel
parsing itself as end-to-end zero-copy or promise a fixed speedup.

### Documentation, tooling and packaging

Reconcile current receiving-source commands before editing: README architecture,
Python/runtime setup, actual DSA/PSA modules, installed CLI, LibreOffice and
acceptance limits. Align hooks and Makefile/CI checks with locked Ruff,
basedpyright and Bandit without narrowing scope or reinstating retired runners.
Use the repo-local environment for documentation builds; reconcile saved output
paths. Keep Sphinx/Furo/MyST initially.

Review PyArrow and other direct dependencies against actual/transitive needs;
remove only after clean-package and runtime qualification. Verify wheel/sdist
licence contents and installed CLI outside the checkout, with explicit supported
input/configuration paths. No private workbook/configuration redistribution is
implied. Qualify the existing pytest-gremlins tool on selected formula, projection
and rate code; document surviving mutants and limitations without correctness
guarantees or broad dependency churn.

Inventory tracked OS files, logs, dumps, figures and generated tables. Untrack
only reviewed generated paths, preserving local copies and historical/reference
evidence; deduplicate ignores and move useful parameterised inspection tools to
scripts/. Do not delete inputs, rewrite history or publish generated artifacts.

Draft accurate GitHub description/topics and badges for services actually
configured. A coverage badge needs an operating supported coverage route; a
Scorecard badge needs a qualified workflow. Applying remote metadata or adding a
service is a separate explicit implementation task under the integrator.

## Optional evaluations and deferred scope

- QMC: optional Sobol/Halton sampler only after Monte Carlo parity; validate
  inverse-distribution transforms, dependence, reproducibility and convergence.
  Preserve Sobol balance with power-of-two sample counts and record scrambling.
  Do not silently substitute QMC for the historical RNG.
- Interactive exploration: optional marimo app with synthetic/shareable examples,
  shared calculations and reproducible noninteractive execution. No duplicate
  formulas, auto-publication or private-data embedding.
- ty: advisory comparison only after Python 3.15 syntax/stub compatibility is
  demonstrated; retain strict basedpyright as authoritative until qualified.
- MkDocs/Quarto: evaluate only against an unmet documentation requirement;
  preserve existing documentation until parity, including equations/API links.
- JAX/NumPyro: deferred absent a measured requirement exceeding NumPy/Polars.
- NMB/VOI: blocked on explicit decision alternatives, effectiveness outcomes,
  willingness-to-pay and agreed estimand. Cost tensors alone do not establish VOI.

## Acceptance criteria

1. Each required recommendation has implemented evidence or a specific recorded
   blocker/defer decision; optional evaluations have explicit adopt/defer outcomes.
2. Configuration/domain failures are actionable and happen at the correct boundary;
   compatibility changes and scientific assumptions have explicit decisions.
3. Economic properties and focused regression tests pass; original-model parity
   remains independent and attributable to the designated owner's source revision.
4. Shared-draw results match the accepted baseline within justified tolerances;
   timing/memory comparisons use equivalent workloads and recorded environments.
5. Clean-package/installed-CLI checks, full configured static/security/test gates,
   documentation build and licence checks pass at coherent milestones.
6. Scientific PSA blockers remain visible until authoritative model decisions and
   evidence resolve them; local technical success is not scientific acceptance.
7. No private data, receipts or generated analytical artifacts enter an outgoing
   source packet. Exact-head hosted checks and merge readback are separate gates.

## Authority and integration

No implementation, dependency installation, remote metadata mutation, push,
merge, publication, email or tenant operation is performed by creating this
track. Before registration, reconcile with the existing Conductor owner and
retain the recorded specification and implementation-plan approvals of
6 November 2026. Integrate only the exact reviewed draft directory into the
canonical setup; one integrator updates shared registry and ownership records.
