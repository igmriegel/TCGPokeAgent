"""Analyze Giovanni promotion and development in recent downloaded submissions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval.giovanni_analysis import (  # noqa: E402
    OWNER_NAME,
    analyze_submissions,
    audit_to_dict,
    combined_to_dict,
    render_markdown,
)

REPLAY_DIR = ROOT / "data" / "raw" / "kaggle" / "replays"
METADATA_PATH = ROOT / "data" / "raw" / "kaggle" / "submission_metadata.json"
MAP_PATH = ROOT / "data" / "raw" / "kaggle" / "episode_to_submission.json"


def _latest_downloaded(limit: int) -> list[str]:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    episode_map = {str(k): str(v) for k, v in json.loads(MAP_PATH.read_text()).items()}
    episodes = {
        path.stem.removeprefix("episode-").removesuffix("-replay")
        for path in REPLAY_DIR.rglob("episode-*-replay.json")
    }
    available = {episode_map[episode] for episode in episodes if episode in episode_map}

    def date(row: dict[str, str]) -> datetime:
        try:
            return datetime.fromisoformat(row.get("date", ""))
        except ValueError:
            return datetime.min

    rows = [
        row
        for row in metadata
        if row.get("status") == "SubmissionStatus.COMPLETE" and row.get("ref") in available
    ]
    return [str(row["ref"]) for row in sorted(rows, key=date, reverse=True)[:limit]]


def main() -> int:
    """Run the recent Giovanni audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    submission_ids = args.submission_id or _latest_downloaded(args.limit)
    audits = analyze_submissions(submission_ids, REPLAY_DIR)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.output_dir / (
        f"recent_{len(submission_ids)}_submissions_giovanni_{datetime.now():%Y%m%d}"
    )
    payload = {
        "schema_version": "giovanni-audit-v1",
        "owner_name": OWNER_NAME,
        "submission_ids": submission_ids,
        "submissions": [audit_to_dict(audit) for audit in audits],
        "combined": combined_to_dict(audits),
    }
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    markdown_path.write_text(render_markdown(audits), encoding="utf-8")
    print(json.dumps(payload["combined"], indent=2, ensure_ascii=False))
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
