# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/` (e.g., `main.py`, `data_loader.py`, `formula_engine.py`, `projection.py`, `rate_converter.py`, `validation.py`, analyses in `dsa_analysis.py`/`psa_analysis.py`).
- Tests: `tests/` (`test_*.py`).
- Data: `data/` (inputs like Excel, `formulas.json`, `dsa_scenarios.json`).
- Docs: `docs/` (Sphinx; output in `docs/_build/html`).
- Outputs & artifacts: `outputs/`, CSV/PNG at repo root for analyses.

Example layout:
```
src/
  main.py  data_loader.py  formula_engine.py  ...
tests/
  test_main.py  test_data_loader.py  ...
data/
  Labour Model - v3, 20240328.xlsx  formulas.json  dsa_scenarios.json
```

## Build, Test, and Development Commands
- Install deps: `make install` (via Pipenv).
- Activate env: `pipenv shell`.
- Run app: `PYTHONPATH=. python3 src/main.py`.
- Unit tests: `make test` (pytest).
- Lint/format: `make lint` / `make format` (Ruff).
- Type check: `make typecheck` (mypy, strict).
- Security scan: `make security` (bandit).
- All checks: `make all`.
- CI suite: `make ci` (tox: tests, lint, mypy, bandit, profiling).
- Docs: `make docs`.

## Coding Style & Naming Conventions
- Python 3.10+; 4-space indentation; max line length 88; double quotes (Ruff config).
- Types: required; mypy `strict = true` on `src/` and `tests/`.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Imports: sorted by Ruff; prefer explicit over wildcard.
- Pre-commit: Ruff (lint/format), mypy, bandit, Commitizen.

## Testing Guidelines
- Framework: pytest; tests live in `tests/` and named `test_*.py` with `test_*` functions.
- Coverage: CI runs `pytest --cov=src`; add tests alongside new modules.
- Run locally: `make test`; target a module with `pipenv run pytest tests/test_data_loader.py -q`.

## Commit & Pull Request Guidelines
- Conventional Commits via Commitizen: e.g., `feat: add DSA plot export`, `fix: handle empty sheet`. Scope optional: `feat(loader): ...`.
- Branching: short, kebab-case, e.g., `feat-dsa-scenarios`.
- PRs: clear description, link issues, include rationale, test coverage notes, and sample outputs/screenshots for reports (CSV/PNG). Ensure `make all` passes.

## Security & Configuration Tips
- Do not commit secrets or proprietary data; prefer small reproducible samples under `data/`.
- Validate new formula parameters via `validation.py`; keep `config.py` changes minimal and documented.
