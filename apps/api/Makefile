.PHONY: lint lint-fix typecheck test

lint:
	ruff check .
	mypy .

lint-fix:
	ruff check --fix .
	ruff format .

typecheck:
	mypy .

test:
	pytest --cov=app --cov-report=term-missing
