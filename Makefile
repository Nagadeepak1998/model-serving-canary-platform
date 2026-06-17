PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: venv install test run smoke

venv:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip

install: venv
	$(ACTIVATE) && pip install -e .[dev]

test:
	$(ACTIVATE) && pytest

run:
	$(ACTIVATE) && uvicorn app.main:app --reload

smoke:
	$(ACTIVATE) && python scripts/smoke_predict.py
