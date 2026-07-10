PYTHON ?= python3
VENV ?= .venv
ACTIVATE = . $(VENV)/bin/activate

.PHONY: venv install test run smoke eval-safe eval-risky history-report lint

venv:
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip

install: venv
	$(ACTIVATE) && pip install -e '.[dev]'

test:
	$(ACTIVATE) && pytest

run:
	$(ACTIVATE) && uvicorn app.main:app --reload

smoke:
	$(ACTIVATE) && python scripts/smoke_predict.py

eval-safe:
	$(ACTIVATE) && PYTHONPATH=src:. python -m model_serving_canary_platform.cli evaluate data/rollout_eval_safe.json --output reports/rollout-safe.json

eval-risky:
	$(ACTIVATE) && PYTHONPATH=src:. python -m model_serving_canary_platform.cli evaluate data/rollout_eval_risky.json --output reports/rollout-risky.json || test $$? -eq 2

history-report:
	$(ACTIVATE) && PYTHONPATH=src:. python -m model_serving_canary_platform.cli history data/rollout_history.json --output reports/rollout-history.json --markdown reports/rollout-history.md || test $$? -eq 2

lint:
	$(ACTIVATE) && python -m compileall app src tests
