.PHONY: install test lint

install:
	pipenv install --dev

test:
	pipenv run pytest

lint:
	pipenv run ruff .

format:
	pipenv run ruff format .
