.DEFAULT_GOAL := help

MARIMO_PORT ?= 2718
NOTEBOOK ?= 01_card_catalog_overview.py

.PHONY: help marimo marimo-edit

help:
	@echo "Available targets:"
	@echo "  make marimo                 Run Marimo notebooks"
	@echo "  make marimo-edit            Open a notebook in edit mode"
	@echo "  make marimo-edit NOTEBOOK=02_dataset_comparison.py"

marimo:
	MARIMO_PORT=$(MARIMO_PORT) docker compose up marimo

marimo-edit:
	MARIMO_PORT=$(MARIMO_PORT) docker compose run --rm --service-ports marimo \
		marimo edit /app/notebooks/$(NOTEBOOK) \
		--host 0.0.0.0 --port 2718
