# Workforce PSA qualification — 6 November 2026

> **Reference correction:** The comparison with 150000 below is retained as
> historical evidence, not the original workbook midpoint reference. A later
> source investigation traced the original midpoint mean to [private workbook reference];
> the retained simulation mean is [private comparison] below it. See the [panel/source
> correction](./psa-panel-and-library-review-20261106.md#source-investigation-correction--6-november-2026).

## Outcome and acceptance boundary

Conditional numerical qualification passed. Scientific PSA acceptance remains
blocked by missing provenance and decisions about units, dependence, aggregation
and the unexplained workbook reference. The current priors and original workbook
were preserved. Three independent AI-agent reviews are advisory and do not replace
empirical evidence or model-owner approval.

The final calculation source is local commit `79c3354`. It has 95 passing tests,
full-tree Ruff ALL and formatting, basedpyright zero errors/warnings and Bandit
zero findings. The new packet has not been pushed or qualified by hosted Actions.
The successful 5 November hosted checks refer to the earlier receiving commits.

## Original model and evidence reviewed

- Original workbook: `data/Labour Model - v3, 20240328.xlsx`; SHA-256
  `c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca`.
- Frozen legacy Python source: `dd61438`. Its global NumPy random calls are not
  treated as stream-equivalent to the current seeded Generator.
- Original PSA JSON was introduced at `e90eb0f` and its definitions remain intact.
- `PSA - Validation` was added at `8bb90f9`: one literal expected mean, with no
  formula or recovered derivation. Its population, weights and stochastic basis
  are unspecified in the inspected evidence.
- The workbook's two other PSA archives contain static LL/MP/UL summaries. No
  random-generation/correlation formulas or joint workforce input draws were
  found in the inspected workbook and retained handoff. This does not establish
  that no external generator/specification exists elsewhere.
- Two archived cost-result CSVs contain 1,000 iterations each; one varies and one
  is constant. Neither records a seed or sampled parameter columns. They cannot
  establish historical draw-level replay.
- The retained protocol draft describes illustrative distributions and simulations,
  without specifying these numeric priors, dependence or weighting. Its examples
  do not provide an authoritative parameterized specification. That branch remains
  unmodified and outside accepted publication scope.
- The migration owner confirmed the prior 25-output/20-iteration equivalence and
  500-value DSA evidence were not scientific PSA qualification. Genomics' archived
  assay draws are separate and were not borrowed as a workforce specification.

## Qualification results

| Check | Result | Scope |
|---|---|---|
| Fixed common draws | 12 vectors: eight seeded draws plus four finite stress cases | Same declared normal/uniform/triangular inputs across implementations; finite normal stress values are not boundaries of unbounded normal support |
| Legacy/current parity | Frozen legacy raw-input runner, corrected raw/costed API and production runner method agree | Controlled common-draw replay on Python 3.15.1; not historical same-seed/native-binary reproduction |
| Independent original-workbook comparison | 300 state-role cells; maximum absolute difference 8.15e-10, against 0.01 tolerance | Each draw applied to a fresh original workbook copy, independently recalculated by LibreOffice; original file unchanged |
| Aggregated workbook means | Maximum difference 1.75e-10 | The implemented unweighted 25-row mean |
| Production simulation | 10,000 iterations at seed 20261103 | Conditional on current JSON and independent common-row draws |
| Marginal CDF checks | p-values 0.2154, 0.5533, 0.4788 | Pre-specified family alpha 0.001 across three checks; non-rejection does not establish empirical calibration |
| Analytic mean check | 1.434 Monte Carlo standard errors from closed-form expectation; limit 6 | Analytic moments derived from recalculated workbook costs and the declared independent priors |
| Empirical parameter correlations | Maximum absolute Pearson correlation 0.0117; diagnostic limit 0.06 | Detects conspicuous linear dependence; does not prove independence or justify it scientifically |
| Shared-contract replay | All 10,000 parameter vectors and simulation results byte-for-byte unchanged | Compares the bounded method-fix packet with the later shared-execution packet |
| Clean installed wheel | 20 distinct seeded costs, raw/costed parity, empty-evidence rejection | Installed module imported outside checkout; package and source-distribution licence/content checked |

The production runner method was exercised programmatically with persisted CSV
and figure output. This is not a claim that a new complete fresh-process CLI/DSA
workbook replay or native Excel acceptance was performed. Prior unchanged DSA
reconciliation evidence is retained with its original owner.

## Method corrections completed

1. Recalculate derived Y0 costs when a caller supplies an already-costed base case.
   The original calculated-input path could produce constant costs despite changed
   inputs. Raw-input mathematical semantics are the reference; that defect is not
   preserved as a compatibility requirement.
2. Share one strict sampling path between API and production runner. Positive integer
   iterations, nonnegative integer seed, finite supported distributions, valid bounds,
   unique parameters and unambiguous existing target columns are required. Unknown
   definitions now fail instead of being silently skipped. No prior is clipped or
   reparameterized.
3. Require the expected number of finite numeric row costs before averaging. The
   production pipeline preserves row identity, independently checked against workbook
   keys; the generic callback boundary does not certify arbitrary role-key permutations.
4. Reject empty, missing, nonnumeric, nonfinite or ambiguous reference evidence.
   Mean comparison alone never establishes distribution/dependence qualification.
5. Preserve earlier default relative/absolute tolerances explicitly as 1e-3/1e-8.
   Both must be zero for exact equality.
6. Use linear percentiles, matching the earlier pandas definition, and label them
   simulation percentile intervals. A single iteration reports undefined sample
   deviation and no estimated interval, instead of raising or inventing precision.

## Scientific assumptions and genuine blockers

| Topic | Implemented assumption | Decision/evidence still needed |
|---|---|---|
| Superannuation | Absolute normal draw, mean 0.105 and SD 0.01 | Relevant period, applicable entitlement/mix, why stochastic, source and support |
| Productive time | Absolute uniform draw 0.95–1.05 replaces every row's value | Absolute productive fraction, relative baseline multiplier, or productivity index; denominator and units |
| Allowance | Absolute triangular draw 0/500/2000 for every row | Currency/year, eligibility and evidence for support/mode; the implied mean is 833.33, not 500 |
| Dependence | Parameters sampled separately; each draw shared across all 25 rows | Empirical or elicited dependence, common policy versus role/state-specific uncertainty |
| Estimand | Equal-weight mean of state-role unit costs | Intended population/output and defensible FTE, role, workload or other weights, if relevant |
| Scalar reference | Mean-only comparison to the archived literal | Derivation, source inputs/draws, units, period, aggregation and approval |
| Tail precision | Empirical 2.5th/97.5th percentiles | A declared Monte Carlo precision target and its assessment; 10,000 draws alone is not a tail-precision qualification |

49.54% of retained productive-time draws exceed one. That conflicts with a strict
productive-hours/paid-hours fraction, but may be interpretable for a separately
defined relative efficiency index. The available evidence does not choose between
those meanings. No truncation, rescaling or reinterpretation was applied.

The simulated mean is [private comparison] above the archived scalar and does not match its
comparison tolerance. It agrees with the analytic expectation under the declared
model, so matching that scalar is not a reason to tune priors or change the workbook.
The scalar/reference discrepancy remains unresolved.

## Reproducibility and ownership

The final shared-contract run began clean at `79c3354`, with source/config/lock,
original-workbook and oracle-script hashes. Runtime packages, seed, prepared inputs,
parameter traces, cost outputs and output hashes are retained privately and were
reverified. The earlier clean run at `32b2a5a` and its oracle script are preserved.

Private receipts remain under `.private-runs/psa-qualification/`, including
`evidence-shared-contract/started.json`, `finished.json`, `workbook-parity.json`,
`conditional-statistics.json`, sampled traces and `wheel-verification.json` in the
parent qualification directory. These paths contain private model evidence and
must not be pushed. The original migration checkout and its evidence remain intact.

## Technical references

- [NumPy random stream compatibility](https://numpy.org/doc/stable/reference/random/compatibility.html): stream reproduction has stricter requirements than equal seed values alone.
- [Polars Series quantiles](https://docs.pola.rs/api/python/stable/reference/series/api/polars.Series.quantile.html) and [pandas Series quantiles](https://pandas.pydata.org/docs/reference/api/pandas.Series.quantile.html): interpolation is explicit in the corrected report.

See [panel advice and library review](./psa-panel-and-library-review-20261106.md)
for options, tradeoffs, contingencies and the recommended decision path.
