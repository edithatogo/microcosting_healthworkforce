.PHONY: install test lint

install:
	pipenv install --dev

test:
	pipenv run pytest

lint:
	pipenv run ruff check .

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
	make all

docs:
	$(MAKE) -C docs html

changelog:
	pipenv run cz bump --changelog

release:
	make changelog
	git push --tags

