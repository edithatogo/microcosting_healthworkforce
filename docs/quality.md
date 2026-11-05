# Quality gates and applicability

Run `make all` with the repo-local Python 3.15.2 environment. It checks formatting,
Ruff, strict typing, all tests and Bandit. CI additionally verifies the actual
interpreter, installs and exercises the built wheel away from the checkout,
profiles synthetic formulas and uploads full-suite coverage (75% minimum; the
qualified local baseline is 77%). Do not substitute
partial coverage or a skipped suite for this gate.

Hypothesis tests check annual/hourly inversion. Metamorphic tests check monetary
scaling, row permutation, partition independence and inverse productive-hour
scaling. Inputs are synthetic and stay within each algebraic contract's domain;
these properties neither select PSA priors nor establish their provenance.
Replay a reported Hypothesis example from the failure output; its local example
database is supplementary. Test timeouts are 120 seconds; sockets are disabled
except local Unix sockets required by the workbook loader. Retries default to
zero. Known failures require a reason and strict xfail; skips require a real
missing capability.

The mutation workflow runs on demand, weekly and for changes to its rate contracts, with two subprocess workers,
a bounded job timeout, no pardons, and a 95% score floor. Its target is
the rate-conversion boundary; this bounded pilot is not whole-program mutation
coverage. Surviving or uncovered mutants require review before expanding scope.
Unrelated pull requests retain the normal fast lane.

Distributed-system testing is excluded: this library has no distributed state,
consensus or concurrent service protocol. Network contract testing is excluded
from the calculation core: no remote provider is used to calculate costs.
GitHub/Codecov integration is verified separately through exact-commit hosted
checks. Do not invent remote contracts for local workbook calculations.

Workflow syntax is checked with actionlint and security patterns with zizmor.
CodeQL and dependency review supplement Bandit. Gitleaks scans repository
history; native secret scanning and push protection provide additional coverage.
All action references are immutable commits. Renovate updates pins using the
shared preset, with a repository override requiring manual reviewed merges.

A repository administrator should inspect rulesets, required-check names, secret
scanning/push protection and the Codecov exact-commit result after changing CI.
A successful upload alone does not prove a provider status. Keep any private
administrative receipts and workbook qualification evidence outside public code.
The persistent Renovate Dependency Dashboard is an operational control, not a
finite implementation issue to close.
