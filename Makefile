PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
ENV_FILE := .env
ENV_TEMPLATE := .env.example

.PHONY: help install shell test test-quiet clean

help:
	@echo "Available targets:"
	@echo "  make install   Create .venv, bootstrap .env (if missing), install dependencies"
	@echo "  make shell     Start a new terminal with .venv activated"
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
	@. $(VENV)/bin/activate && exec $$SHELL

test:
	$(VENV_PYTHON) -m pytest tests/ -v

test-quiet:
	$(VENV_PYTHON) -m pytest tests/ -q

clean:
	rm -rf $(VENV) .pytest_cache
