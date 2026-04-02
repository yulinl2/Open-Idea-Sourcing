PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
ENV_FILE := .env
ENV_TEMPLATE := .env.example

.PHONY: help install install-hooks test test-fast test-quiet test-workflows test-workflows-py clean

help:
	@echo "Available targets:"
	@echo "  make install    Create .venv, bootstrap .env (if missing), install dependencies"
	@echo "  source .venv/bin/activate  Activate .venv in the current terminal (macOS/Linux)"
	@echo "  make test       Run full test suite (verbose)"
	@echo "  make test-fast  Run only fast unit tests, skip @pytest.mark.slow classes"
	@echo "  make test-quiet Run full test suite (quiet)"
	@echo "  make test-workflows Run workflow guardrail checks only (no deps)"
	@echo "  make test-workflows-py Run workflow guardrail pytest checks"
	@echo "  make install-hooks Enable local pre-commit and pre-push hooks"
	@echo "  make clean      Remove caches and local venv"

$(VENV_PYTHON):
	$(PYTHON) -m venv --prompt .venv $(VENV)

install: $(VENV_PYTHON)
	$(VENV_PYTHON) -m ensurepip --upgrade
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	@if [ ! -f $(ENV_FILE) ]; then \
		cp $(ENV_TEMPLATE) $(ENV_FILE); \
		echo "Created $(ENV_FILE) from $(ENV_TEMPLATE)."; \
		echo "Next step: edit $(ENV_FILE) and set OPENAI_API_KEY."; \
	else \
		echo "$(ENV_FILE) already exists; leaving it unchanged."; \
	fi
test: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pytest tests/ -v

test-fast: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pytest tests/ -v -m "not slow"

test-quiet: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pytest tests/ -q

test-workflows:
	bash scripts/check_workflow_guardrails.sh

test-workflows-py: $(VENV_PYTHON)
	$(VENV_PYTHON) -m ensurepip --upgrade
	$(VENV_PYTHON) -m pip install -r requirements.txt
	$(VENV_PYTHON) -m pytest tests/test_workflow_guardrails.py -v

install-hooks:
	bash scripts/install-git-hooks.sh

clean:
	rm -rf $(VENV) .pytest_cache
