.DEFAULT_GOAL := help

SUBMISSION_ARCHIVE ?= submission.tar.gz
PACKAGE_BACKEND ?= heuristic
MODEL_DIR ?=
SUBMISSION_ARGS ?=

.PHONY: help build-package submit-kaggle update-replays-reports

help:
	@echo "Available targets:"
	@echo "  make build-package         Build the submission archive"
	@echo "  make submit-kaggle         Run gates and submit to Kaggle"
	@echo "  make update-replays-reports Download replays and refresh reports"

build-package:
	scripts/build_package.sh "$(SUBMISSION_ARCHIVE)" "$(PACKAGE_BACKEND)" "$(MODEL_DIR)"

submit-kaggle:
	scripts/submit_simulation.sh --archive "$(SUBMISSION_ARCHIVE)" $(SUBMISSION_ARGS)

update-replays-reports:
	scripts/download_all_replays.sh
	scripts/generate_investigation_report.sh
	@for report in perf_reports/INVESTIGATION_REPORT_*.html; do \
		[ "$$report" = "perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html" ] && continue; \
		submission_id=$${report##*/INVESTIGATION_REPORT_}; \
		submission_id=$${submission_id%.html}; \
		scripts/generate_investigation_report.sh \
			data/raw/kaggle/kaggle_gameplay_runs "$$report" "Igor Riegel" \
			--submission-id "$$submission_id"; \
	done
