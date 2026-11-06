# Polars migration and release contract

Use the local codex/polars-costing branch. Preserve workbook originals and previous editions. Validate on repository-local Python 3.15.1. One integrator owns each checkout through hosted readback.

1. Inventory installed commands, legacy script flags, formula operators and source/sheet mappings. Record expected outputs, units, dates, nulls, tie rules and error behaviour.
2. Migrate workbook ingestion, stage/component or role calculations, formula evaluation, scenario and projection logic to typed Polars tables. Preserve unsupported-formula errors and check perturbations propagate. Reconcile against independently recalculated workbook values.
3. Migrate DSA inputs, bounds and rankings. For PSA preserve distribution parameters, dependence and seeds; compare saved draws where available. Reconcile charts and reports with their underlying tables.
4. Install from a clean built distribution and exercise each historical entry point with the original local workbooks, including failure cases. Audit active imports and dependencies for pandas/xarray. Qualify CLI, packaging and targeted tests.
5. At run start record source hashes, clean model commit, config, runtime, seed and backend. Log stage completion, output hashes and failed runs locally. Preserve earlier editions. Only reviewed source changes may enter a public branch.
6. Before push inspect the complete outgoing commit range including intermediate commits, run Gitleaks and Microsoft Presidio locally and review the allowed source paths. Keep workbooks, raw data, run receipts, tables and figures local. Require passing hosted Actions, merge readback, then prune the merged branch only.

Hosting and migration checks remain open until evidence is recorded for each. No workbook or output upload is part of the CI design.

Privacy tools: install presidio-analyzer 2.2.366 and the official en_core_web_sm 3.8.0 model, with Gitleaks 8.30.1 on PATH. Run .venv/bin/python tools/screen_release.py origin/main before push. A finding requires local review. Short English names in source can trigger the PERSON recognizer.

The installed command runner is tools/run_installed.py. Its arguments are the checkout and installed command name. It records the source inputs, active model commit, installed packages, command, terminal status and output digests in an ignored per-run directory. Reconcile against the original before release. Local receipts may contain private paths and must remain local.

Verified 3 November 2026 at f531346. The installed workforce CLI recalculated the base case, evaluated 20 configured scenarios, performed 20 seeded PSA iterations and wrote CSV and figure outputs. Independent recalculation of 20 original workbook copies confirmed all 500 state-role midpoint comparisons within one cent. Preserve the separate archived-DSA comparison because historical assumptions differ. PSA distribution parity, remaining legacy import paths, clean wheel and hosted checks remain open.

4 November. Removed production pandas imports and runtime requirements. A clean wheel environment without pandas or xarray ran the installed command with original workbook inputs. Migrated legacy scenario, reporting and validation tests passed (45 tests). Current locked development environment and workflow use 3.15.1. Strict mypy still reports 278 errors across implementation and tests. A public release requires resolving these errors, final-wheel verification and completed outgoing-history review.

4 November 2026. The development environment uses uv.lock on Python 3.15.1, strict basedpyright on src and tests, Ruff ALL, Bandit and the local Gitleaks/Presidio release screen. Pydantic v2 checks model inputs and Pandera validates Polars outputs or scenario inputs at execution. Hypothesis runs with pytest. Use pytest-gremlins against a selected calculation and Scalene with the profiling dependency group for local investigation. Qualification used real property tests, comparison mutations and a saved CPU profile. Test success and tool installation alone do not close static findings. Keep local profiles and scanner output in .private-runs.


## 4 November 2026: security and safe automated cleanup

Bandit src scan: zero unreviewed findings. Ruff safe fixes and formatting applied to src/tests; unsafe fixes not enabled. Remaining Ruff diagnostics: 369. Qualified-interpreter basedpyright strict: 80 errors, 0 warnings; these remain release blockers. Basedpyright has no autofixer. Explicit nullable defaults and typed header accumulators were repaired without disabling rules.

LibreOffice subprocess calls use argument lists, shell=False and a 120-second timeout. Exact B404/B603 annotations document reviewed local executable use; no global security exclusions. All 46 tests pass.

Evidence is retained locally under .private-runs; no inputs or generated data added to Git. No push, PR or public release in this pass.


## 4 November 2026: strict-check repair, edition 1

Strict basedpyright now reports zero errors and zero warnings across 29 files. Validated row-filter boundary, typed intermediate collections and workbook scalar handling. Narrow local typing contracts cover the exercised asteval and Matplotlib APIs, with real plotting/CLI execution as runtime evidence. Trial matplotlib-stubs was removed because it installs pandas; no pandas dependency was retained. A genuine Pandera PolarsData callback defect was caught by the installed CLI and fixed, with a new positive/zero/duplicate-iteration regression test. Full tests: 47 passed. Ruff remains open with 185 findings; no rule exclusions were added. Original workbook baseline and all 20 scenario copies passed; final source-hashed replay recorded separately.

Both Bandit scans have zero unreviewed findings. Strict checker modes and scan scope remain intact. Logging formatting and exception messages are corrected, with explicit no-result annotations where implementation permits. Source/run journal now records source hashes, dirty state, uv.lock hash and prepared input hashes at execution. Whole-package migration, remaining static findings, privacy release review and hosted CI are not complete. No public release or manuscript-price change.

Final source-hashed replay: 20261104T043011413140Z, model 1b71abb822e810ed7454ea2b7e72122b4ee21e82, clean source at run start, exit zero, all output hashes reverified. The corresponding detailed receipt remains private. The genomic persisted success flag was repaired to agree with numeric/presence acceptance before this final replay.

Final source-hashed replay: 20261104T051357955150Z, model 31d65b8f187d0743ea2cb8324d67f20910618ab7, clean source at run start, exit zero, all output hashes reverified. The corresponding detailed receipt remains private. The workflow regressions and strict warnings have been repaired; remaining static errors stay open.

Final source-hashed replay: 20261104T052000616461Z, model 78878619a5bcaa3d6e03ae778363297562913ebd, clean source at run start, exit zero, all output hashes reverified. The corresponding detailed receipt remains private. The workflow regressions and strict warnings have been repaired; remaining static errors stay open.

Final source-hashed replay: 20261104T053338168849Z, model 361249bae7a9dd087eed90257d9506ae796ae97a, clean source at run start, exit zero, all output hashes reverified. The corresponding detailed receipt remains private. The workflow regressions and strict warnings have been repaired; remaining static errors stay open.

Final source-hashed replay: 20261104T063401225443Z, model 400dd1f80e62e1e3e120440226a5dae475cda085, clean source at run start, exit zero, all output hashes reverified. The corresponding detailed receipt remains private. The workflow regressions and strict warnings have been repaired; remaining static errors stay open.

Edition 6: legacy scalar evaluation now shares the restricted Polars compiler; see GHA reports/microcosting-repair-v6. Replay a6b3ee4 passed before annotation-only Mapping correction; no same-revision replay claim. Genomics remains open.

Edition 7: clean source replay 20261104T064522265388Z passed, output and source hashes reverified. GHA reports/microcosting-repair-v7 retains evidence. Genomics foundational parsed variants validated; other variants and legacy pandas paths remain open.

5 November, edition 11: installed replay 20261104T224221751439Z passed on clean b89fff86f828fdbd6e3c262159ea5d47eb210047; source/lock/output hashes reverified. GHA reports/microcosting-repair-v11 records Polars financial-table differential checks, workforce retired-interpreter removal and bounded NIM qualification. Strict release gates remain open.

5 November, edition 17: Source unchanged; prior 49-test and 500-value workbook evidence reused. Refreshed typing zero errors/warnings; 99 Ruff findings remain. Fourteen existing PRs lack passing required Actions. Outgoing-history privacy review and strict/hosted gates remain separate. No push/merge or worktree deletion; retain pending branches. GHA reports/microcosting-repair-v17 records exact evidence and disposition.
