.DEFAULT_GOAL := help

SUBMISSION_ARCHIVE ?= submissions/honchkrow_expert_turn_loop.tar.gz
HONCHKROW_PORYGON_ARCHIVE ?= submissions/honchkrow_porygon_submission.tar.gz
PACKAGE_BACKEND ?= heuristic
MODEL_DIR ?=
SUBMISSION_ARGS ?=
KAGGLE_JSON ?= $(CURDIR)/kaggle.json

ifneq ($(wildcard $(KAGGLE_JSON)),)
KAGGLE_API_TOKEN ?= $(shell jq -r '.key // empty' "$(KAGGLE_JSON)" 2>/dev/null)
export KAGGLE_API_TOKEN
endif

.PHONY: help build-abomasnow-package build-honchkrow-porygon-package submit-kaggle update-replays-reports

help:
	@echo "Available targets:"
	@echo "  make build-abomasnow-package  Build the Abomasnow package explicitly"
	@echo "  make build-honchkrow-porygon-package  Build the Honchkrow/Porygon package"
	@echo "  make submit-kaggle         Run gates and submit to Kaggle"
	@echo "  make update-replays-reports Download replays and refresh reports"

build-abomasnow-package:
	scripts/build_package.sh "$(SUBMISSION_ARCHIVE)" "$(PACKAGE_BACKEND)" "$(MODEL_DIR)"

build-honchkrow-porygon-package:
	scripts/build_honchkrow_porygon_package.sh "$(HONCHKROW_PORYGON_ARCHIVE)"

submit-kaggle:
	scripts/submit_simulation.sh --archive "$(SUBMISSION_ARCHIVE)" --package-kind honchkrow_porygon --agent-mode expert_turn_loop $(SUBMISSION_ARGS)

update-replays-reports:
	scripts/download_all_replays.sh
	.venv/bin/python scripts/update_replays_reports.py
