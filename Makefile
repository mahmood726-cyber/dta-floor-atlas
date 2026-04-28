.PHONY: install test verify reproduce clean

install:
	pip install -e ".[dev]"
	python scripts/preflight_prereqs.py

test:
	pytest -v

verify:
	pytest -v
	python -m dta_floor_atlas.preflight_gate

reproduce:
	python -m dta_floor_atlas.cli reproduce

clean:
	rm -rf outputs/*.json outputs/*.jsonl outputs/r_failures/*.txt build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
