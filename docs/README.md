# Project documentation

Use these four pages first:

1. [Project status](PROJECT_STATUS.md) — current metrics, release decision, and
   immediate priorities.
2. [Codebase map](CODEBASE_MAP.md) — active paths, consumers, tests, and
   intentionally dormant components.
3. [Task index](03_tasks/TASK_INDEX.md) — executable backlog, owners of work,
   and task counts.
4. [Documentation hub](20_master_index.md) — contracts, implementation guides,
   gameplay knowledge, and historical evidence.

Status is intentionally not repeated across the remaining documents. Sprint
files define scope and gates; `strategy_notes.md` preserves historical evidence;
the acceptance checklist decides whether a release may be promoted.

Run `uv run --frozen python scripts/audit_documentation.py` before committing.
The same drift gate runs in pytest.
