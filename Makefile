.PHONY: install test lint format format-check typecheck security all ci docs

install:
	uv sync --locked --python 3.15.1

test:
	MPLBACKEND=Agg uv run --locked pytest --disable-socket --allow-unix-socket --timeout=120

lint:
	uv run --locked ruff check .

format:
	uv run --locked ruff format .

format-check:
	uv run --locked ruff format --check .

typecheck:
	uv run --locked basedpyright

security:
	uv run --locked bandit -r src

all:
	make format-check
	make lint
	make typecheck
	make test
	make security

ci:
	make all

docs:
	uv run --locked sphinx-build -M html docs/source docs/build

changelog:
	uv run --locked cz bump --changelog

release:
	make changelog
	git push --tags

