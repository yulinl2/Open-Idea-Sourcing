PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
ENV_FILE := .env
ENV_TEMPLATE := .env.example

.PHONY: help install shell load-env test test-quiet clean

help:
	@echo "Available targets:"
	@echo "  make install   Create .venv, bootstrap .env (if missing), install dependencies"
	@echo "  make shell     Start a new terminal with .venv activated"
	@echo "  make load-env  Start a new terminal with .venv activated and .env loaded"
	@echo "  make test      Run test suite (verbose)"
	@echo "  make test-quiet Run test suite (quiet)"
	@echo "  make clean     Remove caches and local venv"

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

install: $(VENV_PYTHON)
	@if [ ! -f $(ENV_FILE) ]; then \
		cp $(ENV_TEMPLATE) $(ENV_FILE); \
		echo "Created $(ENV_FILE) from $(ENV_TEMPLATE)."; \
		echo "Next step: edit $(ENV_FILE) and set OPENAI_API_KEY."; \
	else \
		echo "$(ENV_FILE) already exists; leaving it unchanged."; \
	fi
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

shell: $(VENV_PYTHON)
	@echo "Starting a new terminal with $(VENV) activated."
	@echo "Exit that terminal to return to your previous terminal."
	@. $(VENV)/bin/activate && exec $${SHELL:-/bin/sh}

load-env: $(VENV_PYTHON)
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(ENV_FILE) not found. Run 'make install' first, then edit $(ENV_FILE)."; \
		exit 1; \
	fi
	@echo "Starting a new terminal with $(VENV) activated and $(ENV_FILE) loaded."
	@echo "Exit that terminal to return to your previous terminal."
	@. $(VENV)/bin/activate && set -a && . ./$(ENV_FILE) && set +a && exec $${SHELL:-/bin/sh}

test: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pytest tests/ -v

test-quiet: $(VENV_PYTHON)
	$(VENV_PYTHON) -m pytest tests/ -q

clean:
	rm -rf $(VENV) .pytest_cache
