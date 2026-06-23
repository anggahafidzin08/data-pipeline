.PHONY: setup test lint run clean

setup:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	black src/ tests/
	ruff check src/ tests/

run:
	python -m src.pipeline

clean:
	rm -rf __pycache__ .pytest_cache .coverage dist build *.egg-info
