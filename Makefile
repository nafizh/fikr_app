run:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run python src/inbox_worker.py

setup:
	uv sync

test:
	uv run pytest
