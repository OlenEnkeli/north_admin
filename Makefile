install:
	poetry run install

lint:
	poetry run ruff check . --fix
	poetry run mypy .
	poetry run isort .

test:
	poetry run pytest tests/ -vv

pre-commit: test lint
