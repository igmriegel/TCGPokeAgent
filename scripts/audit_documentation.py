"""Verify that canonical documentation stays aligned with the repository."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CODEBASE_MAP = ROOT / "docs" / "CODEBASE_MAP.md"
TASK_INDEX = ROOT / "docs" / "03_tasks" / "TASK_INDEX.md"
ROADMAP = ROOT / "docs" / "04_sprint_plan.md"
FEEDBACK_REGISTER = ROOT / "docs" / "29_gameplay_feedback.md"
SCRIPT_INVENTORY = ROOT / "docs" / "23_scripts_spec.md"
CANONICAL_DOCUMENTS = (
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "PROJECT_STATUS.md",
    CODEBASE_MAP,
    TASK_INDEX,
    ROOT / "docs" / "04_sprint_plan.md",
    ROOT / "docs" / "19_final_harness_checklist.md",
)
FORBIDDEN_CURRENT_CLAIMS = {
    ROOT / "AGENTS.md": ("action.py", "26 markdown files"),
    ROOT / "src" / "README.md": ("Current modules are placeholders",),
    ROOT / "configs" / "README.md": ("YAML files are placeholders",),
    ROOT / "docs" / "01_architecture.md": ("CandidateBuilder",),
    ROOT / "docs" / "12_core_implementation.md": ("src/core/action.py",),
    ROOT / "docs" / "18_config_and_runs.md": ("current YAML files are placeholders",),
}
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
TASK_ID_PATTERN = re.compile(r"^(?:T-\d{3}|HD-\d{2}|FB001-A\d|RF-\d{3}|RA-\d{3})$")
TASK_STATUSES = {"IN_PROGRESS", "READY", "DEFERRED", "DONE"}


@dataclass(frozen=True, slots=True)
class AuditIssue:
    """Describe one documentation consistency failure."""

    source: Path
    message: str

    def render(self) -> str:
        """Return a repository-relative diagnostic."""
        return f"{self.source.relative_to(ROOT)}: {self.message}"


def _anchor(value: str) -> str:
    normalized = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return re.sub(r"[\s\-]+", "-", normalized).strip("-")


def _markdown_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for heading in HEADING_PATTERN.findall(text):
        base = _anchor(heading)
        count = counts.get(base, 0)
        anchors.add(base if count == 0 else f"{base}-{count}")
        counts[base] = count + 1
    return anchors


def _check_links() -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    markdown_files = sorted(
        {
            *ROOT.glob("*.md"),
            *(
                path
                for directory in ("docs", "src", "configs", "scripts")
                for path in (ROOT / directory).rglob("*.md")
            ),
        }
    )
    anchor_cache: dict[Path, set[str]] = {}
    for source in markdown_files:
        for raw_target in LINK_PATTERN.findall(source.read_text(encoding="utf-8")):
            target = raw_target.strip().strip("<>")
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, fragment = target.partition("#")
            destination = (
                source if not path_part else (source.parent / unquote(path_part)).resolve()
            )
            if not destination.exists():
                issues.append(AuditIssue(source, f"broken link target: {target}"))
                continue
            if fragment and destination.suffix.lower() == ".md":
                anchors = anchor_cache.setdefault(destination, _markdown_anchors(destination))
                if unquote(fragment).lower() not in anchors:
                    issues.append(AuditIssue(source, f"missing link anchor: {target}"))
    return issues


def _check_codebase_inventory() -> list[AuditIssue]:
    if not CODEBASE_MAP.exists():
        return [AuditIssue(CODEBASE_MAP, "canonical codebase map is missing")]
    text = CODEBASE_MAP.read_text(encoding="utf-8")
    paths = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src").rglob("*.py")
        if "__pycache__" not in path.parts
    )
    return [
        AuditIssue(CODEBASE_MAP, f"source module is absent from inventory: {path}")
        for path in paths
        if f"`{path}`" not in text
    ]


def _check_script_inventory() -> list[AuditIssue]:
    text = SCRIPT_INVENTORY.read_text(encoding="utf-8")
    paths = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "scripts").iterdir()
        if path.suffix in {".py", ".sh"}
    )
    return [
        AuditIssue(SCRIPT_INVENTORY, f"operational script is absent from inventory: {path}")
        for path in paths
        if path not in text
    ]


def _check_current_claims() -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    for source, forbidden in FORBIDDEN_CURRENT_CLAIMS.items():
        if not source.exists():
            issues.append(AuditIssue(source, "required current-state document is missing"))
            continue
        text = source.read_text(encoding="utf-8")
        issues.extend(
            AuditIssue(source, f"stale current-state claim remains: {claim}")
            for claim in forbidden
            if claim in text
        )
    return issues


def _check_tasks() -> list[AuditIssue]:
    text = TASK_INDEX.read_text(encoding="utf-8")
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not cells or not TASK_ID_PATTERN.fullmatch(cells[0]):
            continue
        status = next((cell for cell in cells if cell in TASK_STATUSES), "")
        if status:
            rows.append((cells[0], status))
    identifiers = [identifier for identifier, _ in rows]
    issues = [
        AuditIssue(TASK_INDEX, f"task ID appears more than once: {identifier}")
        for identifier in sorted(set(identifiers))
        if identifiers.count(identifier) > 1
    ]
    expected = {
        "In progress": sum(status == "IN_PROGRESS" for _, status in rows),
        "Ready": sum(status == "READY" for _, status in rows),
        "Deferred": sum(status == "DEFERRED" for _, status in rows),
    }
    expected["Total open"] = sum(expected.values())
    for label, count in expected.items():
        pattern = rf"^\|\s*{re.escape(label)}\s*\|\s*{count}\s*\|$"
        if not re.search(pattern, text, re.MULTILINE):
            issues.append(AuditIssue(TASK_INDEX, f"summary count for {label} must be {count}"))

    roadmap = ROADMAP.read_text(encoding="utf-8")
    feedback = FEEDBACK_REGISTER.read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not re.fullmatch(r"T-\d{3}", cells[0]):
            continue
        for reference in re.findall(r"FB-\d{4}-\d{3}", cells[4]):
            if reference not in feedback:
                issues.append(
                    AuditIssue(TASK_INDEX, f"{cells[0]} has orphan feedback: {reference}")
                )
        for reference in re.findall(r"\b(?:S\d+|H\d+A?)\b", cells[4]):
            if not re.search(rf"^\|\s*{re.escape(reference)}\s*\|", roadmap, re.MULTILINE):
                issues.append(AuditIssue(TASK_INDEX, f"{cells[0]} has orphan track: {reference}"))

    coverage = text.partition("## Active-track coverage")[2].partition("## Deferred queue")[0]
    for line in roadmap.splitlines():
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"(?:S\d+|H\d+A?)", cells[0]):
            continue
        if cells[2] in {"IN_PROGRESS", "READY"} and not re.search(
            rf"\b{re.escape(cells[0])}\b", coverage
        ):
            issues.append(AuditIssue(ROADMAP, f"active track has no task owner: {cells[0]}"))
    return issues


def audit_repository() -> list[AuditIssue]:
    """Return every detected documentation consistency issue."""
    issues = [
        AuditIssue(path, "required canonical document is missing")
        for path in CANONICAL_DOCUMENTS
        if not path.exists()
    ]
    issues.extend(_check_links())
    issues.extend(_check_codebase_inventory())
    issues.extend(_check_script_inventory())
    issues.extend(_check_current_claims())
    issues.extend(_check_tasks())
    return issues


def main(argv: list[str] | None = None) -> int:
    """Run the audit and return a shell-friendly exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    issues = audit_repository()
    if issues:
        for issue in issues:
            print(issue.render())
        print(f"documentation audit: FAIL ({len(issues)} issues)")
        return 1
    print("documentation audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
