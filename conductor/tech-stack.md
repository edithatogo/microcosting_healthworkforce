# Technology Stack

- Python 3.15.2: explicitly selected repo-local interpreter; uv-managed lock and
  environment. Verify the running interpreter rather than trusting manifests.
- Polars and PyArrow: typed tables and calculation expressions. NumPy: seeded
  simulation; openpyxl: workbook ingestion; LibreOffice: independent recalculation.
- Pydantic v2 and Pandera Polars schemas: configuration and table contracts.
- Matplotlib: existing figures; setuptools: wheel and source distribution.
- pytest, Hypothesis and pytest-cov: functional/property tests and coverage.
- Ruff ALL and format check; strict basedpyright over src/tests; Bandit over src.
- Sphinx, Furo and MyST: documentation. Apache-2.0: project-owned code.
- GitHub Actions: locked runtime, tests, full-tree lint/format, typing, security,
  build, installed-wheel CLI and synthetic profiling.

## Authoritative settings

AGENTS.md and pyproject.toml override generic copied style-guide examples:
88 columns, four spaces, double quotes, explicit typing and Ruff. Do not add
pylint, reinstate retired mypy/Pipenv/tox runners or reduce configured scope.
Use the actual Makefile and workflow for current commands.

Optional profiling/mutation tools retain their existing isolated qualification;
no new plugins, environments, hooks or native subscriptions are installed by setup.


## 6 November bounded alignment

Pydantic 2.14.3 and Ruff 0.17.4 were initially qualified with the existing numeric core on
Python 3.15.1 and subsequently on 3.15.2. pytest-timeout 2.4.0, pytest-socket 0.8.1 and pre-commit 4.7.0 are
locked development tools. Make/CI test commands explicitly enforce their guards;
no hook installation or retry policy was introduced. Pandas, SciPy and asteval
are confined to the private legacy-reference environment, and the unused asteval
stub is removed. The full comparison/rationale is in the linked library review.

## Runtime and quality promotion — 6 November 2026

Python 3.15.2 passed the full 100-test local gate, strict typing, Ruff and Bandit.
PR #45 merged source-only PSA/tooling and quality integration; hosted exact-head
and receiving-main checks passed. Mutation qualification is bounded to rate
conversion. Earlier 3.15.1 receipts remain historical evidence.
