.DEFAULT_GOAL := help

SUBMISSION_ARCHIVE ?= submissions/honchkrow_expert_turn_loop.tar.gz
HONCHKROW_PORYGON_ARCHIVE ?= submissions/honchkrow_porygon_submission.tar.gz
PACKAGE_BACKEND ?= heuristic
MODEL_DIR ?=
SUBMISSION_ARGS ?=
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
	scripts/download_all_decision_logs.sh
	.venv/bin/python scripts/update_replays_reports.py
