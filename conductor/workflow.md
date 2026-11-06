# Project Workflow

Adapted from the installed Conductor workflow template to this existing project.
AGENTS.md and explicit user instructions take precedence.

## Ownership and discovery

Inspect the actual worktree, branch, dirty paths, existing ownership and running
operations before writes. One writing chat owns each checkout; isolate parallel
source work. One integrator owns dependency/runtime promotion and remote merges.
Keep the migration owner's private evidence and native operations in place.
Use the integration preflight at the decision point for frozen source packets.

## Task lifecycle

1. Select the next authorized pending plan task and mark it in progress.
2. Record the concrete behavior and acceptance boundary. Add a regression test
   before a behavioral fix where useful; do not add artificial tests for trivial
   reversible documentation changes.
3. Implement the bounded change, preserve unrelated work and run affected tests.
4. Use the worktree's Python 3.15.2 and keep pytest cacheprovider enabled.
   Failure-only reruns use --lf --last-failed-no-failures=none; an empty selection
   proves no tests. Default to zero retries and never retry native mutations.
5. At a coherent milestone run the applicable full gates. Record failures and
   blockers without reducing rules, inventing skips or treating partial coverage
   as complete acceptance.
6. Commit only owned paths with ordinary hooks enabled and a conventional message.
   Record the source commit and scoped evidence in the plan. Reuse unchanged
   evidence with exact revision/content checks.

## Verification and release

Use `make all` for the local format, lint, typing, test and security gate. Build
with `uv build`, inspect package contents and exercise the installed distribution
outside the source checkout. Full original-workbook reconciliation and scientific
PSA acceptance remain separate; only the designated owner performs native replays.

Before a public push inspect the entire outgoing range, including intermediate
commits, and run local Gitleaks and Presidio. Review flagged occurrences against
exact blob hashes/offsets; do not blanket-disable detectors or publish receipts.
Exclude private history, data and generated artifacts from a source-only packet.

Require passing Actions at the exact PR head before merging, then verify the
merge commit on main and its hosted CI. Prune only genuinely merged branches.
Retain unmerged/superseded branches when instructed. Never infer mergeability
or acceptance from a branch name, an old merged PR or an unrelated green job.

## Commands

- Setup: uv sync --locked --python 3.15.2
- Runtime: .venv/bin/python --version
- Application: uv run --locked microcosting-healthworkforce
- Focused tests: uv run --locked pytest tests/test_main.py
- Full local gate: make all
- Build: uv build
- Documentation: make docs

Keep source/output hashes, clean/dirty state, runtime, configuration and seeds
in existing local receipts. Do not introduce a new mandatory approval process,
recurring job or external-message workflow through this document.
