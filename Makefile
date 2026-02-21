.PHONY: run test lint ui

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	ruff check .

ui:
	streamlit run ui/chat.py
