.PHONY: setup test lint run clean

setup:
	python -m pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

lint:
	python -m black src/ tests/
	python -m ruff check src/ tests/

run:
	python -m src.pipeline

clean:
	rm -rf __pycache__ .pytest_cache .coverage dist build *.egg-info
