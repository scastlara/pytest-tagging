VENV=.venv
BIN=$(VENV)/bin
PYTHON=$(BIN)/python
PYTHON_VERSION=python3.10


$(VENV):
	POETRY_VIRTUALENVS_IN_PROJECT=1 poetry env use $(PYTHON_VERSION)
	poetry install $(ARGS)

.PHONY: format
format:
	$(BIN)/black pytest_tagging tests
	$(BIN)/isort pytest_tagging tests

.PHONY: lint
lint:
	$(BIN)/black --check pytest_tagging tests
	$(BIN)/mypy pytest_tagging

.PHONY: test
test: $(VENV)
	$(BIN)/pytest tests
