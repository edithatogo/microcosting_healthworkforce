.PHONY: install test lint

install:
	pipenv install --dev

test:
	pipenv run pytest

lint:
	pipenv run ruff .

format:
	pipenv run ruff format .

typecheck:
	pipenv run mypy

security:
	pipenv run bandit -r src

all:
	make format
	make lint
	make typecheck
	make test
	make security

ci:
	tox

