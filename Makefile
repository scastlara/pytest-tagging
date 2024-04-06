PYTHON?=python3.12
VENV_TEST=venv/venv_test
VENV=.venv

$(VENV_TEST):
	POETRY_VIRTUALENVS_IN_PROJECT=1 poetry env use $(PYTHON)
	poetry install

venv: $(VENV_TEST)

lint: venv
	$(VENV)/bin/ruff format --check pytest_tagging tests
	$(VENV)/bin/ruff check pytest_tagging tests
	$(VENV)/bin/mypy pytest_tagging tests

unit-tests: venv
	$(VENV)/bin/pytest

format:
	$(VENV)/bin/ruff check pytest_tagging tests --fix
	$(VENV)/bin/ruff format pytest_tagging tests

test: lint unit-tests
