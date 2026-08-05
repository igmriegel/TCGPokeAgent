"""Generate an HTML investigation report from archived CABT replay JSON files.

The report is an analysis artifact, not an evaluation gate. It scans replay
files from a directory, filters out malformed or unrelated episodes, derives a
deck label from the opening visualization, and aggregates attack, damage, turn,
and matchup summaries into a standalone HTML page.
"""

from __future__ import annotations

import argparse
import csv
import html as html_module
import io
import json
import pathlib
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cg.api import all_attack, all_card_data  # noqa: E402
from src.core.archetype import (  # noqa: E402
    resolve_deck_archetype,
    resolve_deck_archetype_lines,
)

COMPETITION = "pokemon-tcg-ai-battle"
SUBMISSION_MAP_PATH = Path("data/raw/kaggle/episode_to_submission.json")
SUBMISSION_METADATA_CACHE_PATH = Path("data/raw/kaggle/submission_metadata.json")

attacks_sdk = {a.attackId: a for a in all_attack()}
cards_sdk = {c.cardId: c for c in all_card_data()}
attack_to_card = {}
for _c in all_card_data():
    for _aid in _c.attacks:
        attack_to_card[_aid] = _c.name

ABOMASNOW_WEAKNESS_TYPE = 8
ABOMASNOW_WEAKNESS_NAME = "Metal"


def _load_submission_map() -> dict[str, str]:
    """Load the episode-to-submission mapping if it exists."""
    if not SUBMISSION_MAP_PATH.exists():
        return {}
    raw_map = json.loads(SUBMISSION_MAP_PATH.read_text())
    return {str(key): str(value) for key, value in raw_map.items()}


def _list_completed_submissions() -> list[dict[str, str]]:
    """Fetch completed Kaggle submissions for the current competition.

    Returns:
        Completed submission rows from Kaggle or the local metadata cache.

    Raises:
        RuntimeError: If neither the Kaggle API nor a metadata cache is
            available. Generating a report with fabricated metadata is unsafe.
    """
    try:
        result = subprocess.run(
            ["kaggle", "competitions", "submissions", COMPETITION, "-v"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        if SUBMISSION_METADATA_CACHE_PATH.exists():
            cached = json.loads(SUBMISSION_METADATA_CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(cached, list):
                return [row for row in cached if row.get("status") == "SubmissionStatus.COMPLETE"]
        raise RuntimeError(
            "Kaggle submission metadata unavailable: API request failed and cache "
            f"{SUBMISSION_METADATA_CACHE_PATH} is missing or invalid."
        ) from error

    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    completed = [row for row in rows if row.get("status") == "SubmissionStatus.COMPLETE"]
    SUBMISSION_METADATA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUBMISSION_METADATA_CACHE_PATH.write_text(json.dumps(completed, indent=2) + "\n")
    return completed


def _parse_submission_date(value: str) -> datetime:
    """Parse a Kaggle submission timestamp.

    Args:
        value: Submission date string from the Kaggle CLI.

    Returns:
        A datetime value that can be used for sorting.
    """
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def _episode_id_from_path(replay_path: Path) -> str:
    """Return the episode ID encoded in a replay filename."""
    return replay_path.stem.removeprefix("episode-")


def _filter_replay_paths(replay_paths: list[Path], submission_id: str | None) -> list[Path]:
    """Filter replay paths by the local episode-to-submission map.

    Args:
        replay_paths: Replay files available for analysis.
        submission_id: Optional Kaggle submission ID to select.

    Returns:
        Replay paths belonging to the selected submission, or all paths when no
        submission was selected.

    Raises:
        ValueError: If the selected submission has no mapped episodes.
    """
    if submission_id is None:
        return replay_paths

    submission_map = _load_submission_map()
    mapped_episodes = {
        episode_id
        for episode_id, mapped_submission_id in submission_map.items()
        if mapped_submission_id == submission_id
    }
    if not mapped_episodes:
        raise ValueError(
            f"No episodes found for submission ID {submission_id!r} in {SUBMISSION_MAP_PATH}."
        )

    return [
        replay_path
        for replay_path in replay_paths
        if _episode_id_from_path(replay_path) in mapped_episodes
    ]


def _build_submission_rows(
    raw_results: list[dict[str, object]],
    submission_id: str | None = None,
    mapped_episode_count: Counter[str] | None = None,
    parsed_episode_count: Counter[str] | None = None,
    unprocessed_episode_count: Counter[str] | None = None,
) -> list[dict[str, object]]:
    """Build submission summary rows from local and Kaggle sources.

    Args:
        raw_results: Parsed replay results used to calculate local outcomes.
        submission_id: Optional ID that limits the returned rows to one submission.

    Returns:
        Submission rows for the combined report or the selected submission.
    """
    submission_map = _load_submission_map()
    episode_counts = mapped_episode_count or Counter(
        mapped_submission_id
        for mapped_submission_id in submission_map.values()
        if mapped_submission_id.isdigit()
    )
    parsed_counts = parsed_episode_count or Counter()
    unprocessed_counts = unprocessed_episode_count or Counter()
    outcome_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"w": 0, "l": 0, "draw": 0})

    for result in raw_results:
        episode_id = str(result["episode_id"])
        mapped_submission_id = submission_map.get(episode_id)
        if not mapped_submission_id or not mapped_submission_id.isdigit():
            continue
        if result["outcome"] == "win":
            outcome_counts[mapped_submission_id]["w"] += 1
        elif result["outcome"] == "loss":
            outcome_counts[mapped_submission_id]["l"] += 1
        else:
            outcome_counts[mapped_submission_id]["draw"] += 1

    submission_rows: list[dict[str, object]] = []
    for row in _list_completed_submissions():
        candidate_id = row.get("ref", "")
        if not candidate_id:
            continue
        if submission_id is not None and candidate_id != submission_id:
            continue
        submission_rows.append(
            {
                "id": candidate_id,
                "date": row.get("date", ""),
                "desc": row.get("description", "") or row.get("fileName", ""),
                "kaggle": float(row["publicScore"]) if row.get("publicScore") else None,
                "episodes": episode_counts.get(candidate_id, 0),
                "parsed": parsed_counts.get(candidate_id, 0),
                "unprocessed": unprocessed_counts.get(candidate_id, 0),
                "w": outcome_counts[candidate_id]["w"],
                "l": outcome_counts[candidate_id]["l"],
                "draw": outcome_counts[candidate_id]["draw"],
            }
        )

    submission_rows.sort(key=lambda row: _parse_submission_date(str(row["date"])), reverse=True)
    if submission_rows:
        best_score = max(
            (row["kaggle"] for row in submission_rows if row["kaggle"] is not None),
            default=None,
        )
        latest_id = str(submission_rows[0]["id"])
        for row in submission_rows:
            row["best"] = row["kaggle"] is not None and row["kaggle"] == best_score
            row["latest"] = str(row["id"]) == latest_id

    return submission_rows


def resolve_deck_name(vis, owner_idx):
    """Extract a deck archetype label from the opening visualization.

    Args:
        vis: Replay visualization frames.
        owner_idx: Player index whose deck should be summarized.

    Returns:
        A heuristic archetype label, or ``"unknown"`` when it cannot be derived.
    """
    try:
        action = vis[0]["action"]
        deck_ids = [int(_cid) for _cid in action[owner_idx]]
        return resolve_deck_archetype(deck_ids, cards_sdk.get)
    except (KeyError, IndexError, TypeError):
        pass
    return "unknown"


def _dominant_metal_deck(deck_ids: list[int]) -> bool:
    """Return whether either of the two dominant Pokémon lines is Metal."""
    return any(
        energy_type == ABOMASNOW_WEAKNESS_TYPE
        for _, _, energy_type in resolve_deck_archetype_lines(deck_ids, cards_sdk.get)
    )


def parse_replay(fpath, owner_name):
    """Parse one replay file and return the derived analysis payload.

    The parser ignores malformed replays, files that do not mention the
    requested owner, and episodes without a result record.

    Args:
        fpath: Path to a replay JSON file.
        owner_name: Kaggle agent name used to locate the controlled player.

    Returns:
        A dictionary with match outcome, archetype labels, and action summaries,
        or ``None`` if the replay should be skipped.
    """
    data = json.loads(pathlib.Path(fpath).read_text())
    try:
        vis = data["steps"][0][0]["visualize"]
    except (KeyError, IndexError, TypeError):
        return None

    info = data.get("info", {})
    agents = info.get("Agents", [])
    owner_idx = None
    for _i, _a in enumerate(agents):
        if _a.get("Name") == owner_name:
            owner_idx = _i
            break
    if owner_idx is None:
        return None

    winner = None
    result_reason = None
    for _frame in vis:
        for _log in _frame.get("logs", []):
            if _log.get("type") == "Result":
                winner = _log.get("result")
                result_reason = _log.get("reason")
    if winner is None:
        return None

    outcome = "win" if winner == owner_idx else "loss" if winner in {0, 1} else "draw"

    first_player = None
    for _frame in vis:
        _fp = _frame.get("current", {}).get("firstPlayer", -1)
        if _fp >= 0:
            first_player = _fp
            break

    max_turn = 0
    for _frame in vis:
        _tv = _frame.get("current", {}).get("turn", 0)
        max_turn = max(max_turn, _tv)

    terminal_current = next(
        (
            _frame.get("current", {})
            for _frame in reversed(vis)
            if isinstance(_frame.get("current", {}), dict)
        ),
        {},
    )
    terminal_players = terminal_current.get("players", [])
    owner_terminal_state = (
        terminal_players[owner_idx]
        if isinstance(terminal_players, list) and owner_idx < len(terminal_players)
        else {}
    )
    opponent_idx = 1 - owner_idx
    opponent_terminal_state = (
        terminal_players[opponent_idx]
        if isinstance(terminal_players, list) and opponent_idx < len(terminal_players)
        else {}
    )

    def terminal_active(state):
        """Return the terminal Active Pokémon name and HP."""
        active = state.get("active", []) if isinstance(state, dict) else []
        pokemon = active[0] if active else {}
        return pokemon.get("name", "None"), pokemon.get("hp", "N/A")

    owner_active_name, owner_active_hp = terminal_active(owner_terminal_state)
    opponent_active_name, opponent_active_hp = terminal_active(opponent_terminal_state)
    owner_prizes_remaining = len(owner_terminal_state.get("prize", []))
    opponent_prizes_remaining = len(opponent_terminal_state.get("prize", []))
    opponent_deck_remaining = opponent_terminal_state.get("deckCount", "N/A")

    opponent_has_weakness_type = False
    opponent_dominant_metal = False
    try:
        opening_action = vis[0]["action"]
        opponent_card_ids = opening_action[opponent_idx]
        opponent_dominant_metal = _dominant_metal_deck(
            [int(card_id) for card_id in opponent_card_ids]
        )
        opponent_has_weakness_type = any(
            cards_sdk.get(int(_card_id), None) is not None
            and cards_sdk[int(_card_id)].cardType == 0
            and cards_sdk[int(_card_id)].energyType == ABOMASNOW_WEAKNESS_TYPE
            for _card_id in opponent_card_ids
        )
    except (KeyError, IndexError, TypeError, ValueError):
        pass

    last_frame_per_turn = {}
    for _fi, _frame in enumerate(vis):
        _curr = _frame.get("current", {})
        _turn = _curr.get("turn", 0)
        _players = _curr.get("players", [])
        if _players:
            last_frame_per_turn[_turn] = _players

    opp_arch = resolve_deck_name(vis, 1 - owner_idx)
    owner_deck_name = resolve_deck_name(vis, owner_idx)

    attack_usage = Counter()
    damage_dealt = []
    damage_taken = []
    evolution_turns = []

    for _frame in vis:
        for _log in _frame.get("logs", []):
            if _log.get("type") == "Attack":
                _aid = _log.get("attackId", 0)
                _pidx = _log.get("playerIndex", -1)
                if _pidx == owner_idx:
                    _a = attacks_sdk.get(_aid)
                    if _a:
                        _cn = attack_to_card.get(_aid, f"atk_{_aid}")
                        attack_usage[f"{_cn}: {_a.name}"] += 1

            if _log.get("type") == "HpChange":
                _pidx = _log.get("playerIndex", -1)
                _val = _log.get("value", 0)
                if _val < 0:
                    if _pidx == owner_idx:
                        damage_taken.append(abs(_val))
                    else:
                        damage_dealt.append(abs(_val))

            if _log.get("type") == "Evolve" and _log.get("playerIndex") == owner_idx:
                evolution_turns.append(_frame.get("current", {}).get("turn", 0))

    episode_id = pathlib.Path(fpath).stem.replace("episode-", "")
    return {
        "episode_id": episode_id,
        "owner_index": owner_idx,
        "outcome": outcome,
        "first_player": first_player,
        "max_turn": max_turn,
        "opp_archetype": opp_arch,
        "owner_deck": owner_deck_name,
        "attack_usage": dict(attack_usage),
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "evolution_turns": evolution_turns,
        "lost_to_no_pokemon_by_turn_2": outcome == "loss" and result_reason == 3 and max_turn <= 2,
        "lost_to_no_pokemon_by_turn_3": outcome == "loss" and result_reason == 3 and max_turn <= 3,
        "opponent_has_weakness_type": opponent_has_weakness_type,
        "opponent_dominant_metal": opponent_dominant_metal,
        "lost_to_deck_out": outcome == "loss" and result_reason == 2,
        "owner_prizes_remaining": owner_prizes_remaining,
        "opponent_prizes_remaining": opponent_prizes_remaining,
        "owner_active_name": owner_active_name,
        "owner_active_hp": owner_active_hp,
        "opponent_active_name": opponent_active_name,
        "opponent_active_hp": opponent_active_hp,
        "opponent_deck_remaining": opponent_deck_remaining,
    }


def generate_report(
    replay_dir: pathlib.Path,
    owner_name: str,
    output_path: pathlib.Path,
    submission_id: str | None = None,
) -> None:
    """Generate the HTML investigation report from a replay directory.

    Args:
        replay_dir: Directory containing replay JSON files.
        owner_name: Kaggle agent name used to identify the target player.
        output_path: Destination HTML file.
        submission_id: Optional Kaggle submission ID used to limit the report.
    """
    raw_results = []
    mapped_episode_count = Counter()
    parsed_episode_count = Counter()
    unprocessed_episode_count = Counter()
    submission_map = _load_submission_map()
    replay_paths = _filter_replay_paths(sorted(replay_dir.glob("*.json")), submission_id)
    for _fp in replay_paths:
        episode_id = _episode_id_from_path(_fp)
        mapped_submission_id = submission_map.get(episode_id)
        if mapped_submission_id:
            mapped_episode_count[mapped_submission_id] += 1
        try:
            _res = parse_replay(_fp, owner_name)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            _res = None
        if _res is not None:
            _res.setdefault("lost_to_no_pokemon_by_turn_2", False)
            _res.setdefault("lost_to_no_pokemon_by_turn_3", False)
            _res.setdefault("opponent_has_weakness_type", False)
            _res.setdefault("lost_to_deck_out", False)
            _res.setdefault("owner_prizes_remaining", 0)
            _res.setdefault("opponent_prizes_remaining", 0)
            _res.setdefault("owner_active_name", "Unknown")
            _res.setdefault("owner_active_hp", "N/A")
            _res.setdefault("opponent_active_name", "Unknown")
            _res.setdefault("opponent_active_hp", "N/A")
            _res.setdefault("opponent_deck_remaining", "N/A")
            _res.setdefault("opponent_dominant_metal", False)
            raw_results.append(_res)
            if mapped_submission_id:
                parsed_episode_count[mapped_submission_id] += 1
        elif mapped_submission_id:
            unprocessed_episode_count[mapped_submission_id] += 1

    games_win = sum(1 for _x in raw_results if _x["outcome"] == "win")
    games_loss = sum(1 for _x in raw_results if _x["outcome"] == "loss")
    total = games_win + games_loss
    wr = games_win / total * 100 if total else None

    first_wins = 0
    first_losses = 0
    second_wins = 0
    second_losses = 0
    for _x in raw_results:
        _fp = _x["first_player"]
        if _fp is None:
            continue
        if _fp == _x.get("owner_index", 0):
            if _x["outcome"] == "win":
                first_wins += 1
            else:
                first_losses += 1
        else:
            if _x["outcome"] == "win":
                second_wins += 1
            else:
                second_losses += 1

    first_total = first_wins + first_losses
    second_total = second_wins + second_losses
    first_wr = first_wins / first_total * 100 if first_total else None
    second_wr = second_wins / second_total * 100 if second_total else None

    losses_without_field_through_turn_2 = sum(
        _x["lost_to_no_pokemon_by_turn_2"] for _x in raw_results
    )
    losses_without_field_through_turn_3 = sum(
        _x["lost_to_no_pokemon_by_turn_3"] for _x in raw_results
    )
    losses_to_weakness_type = sum(
        _x["outcome"] == "loss" and _x["opponent_has_weakness_type"] for _x in raw_results
    )
    losses_to_deck_out = sum(_x["lost_to_deck_out"] for _x in raw_results)

    donk_records = [_x for _x in raw_results if _x["lost_to_no_pokemon_by_turn_3"]]
    donk_by_archetype: dict[str, list[dict[str, object]]] = defaultdict(list)
    for _x in donk_records:
        donk_by_archetype[_x["opp_archetype"]].append(_x)

    metal_matchups: dict[str, dict[str, int]] = defaultdict(lambda: {"w": 0, "l": 0})
    for _x in raw_results:
        if _x["opponent_dominant_metal"]:
            metal_matchups[_x["opp_archetype"]][_x["outcome"][0]] += 1

    deck_out_records = [_x for _x in raw_results if _x["lost_to_deck_out"]]

    atk_win = Counter()
    atk_loss = Counter()
    dmg_dealt_win = []
    dmg_dealt_loss = []
    dmg_taken_win = []
    dmg_taken_loss = []
    evo_win = []
    evo_loss = []
    turn_lengths_win = []
    turn_lengths_loss = []
    opp_archetypes = Counter()
    deck_names = Counter()
    matchup_data = defaultdict(lambda: {"w": 0, "l": 0, "loss_turns": [], "win_turns": []})

    for _x in raw_results:
        _o = _x["outcome"]
        if _o not in {"win", "loss"}:
            continue
        (atk_win if _o == "win" else atk_loss).update(_x["attack_usage"])
        (dmg_dealt_win if _o == "win" else dmg_dealt_loss).extend(_x["damage_dealt"])
        (dmg_taken_win if _o == "win" else dmg_taken_loss).extend(_x["damage_taken"])
        (evo_win if _o == "win" else evo_loss).extend(_x["evolution_turns"])
        (turn_lengths_win if _o == "win" else turn_lengths_loss).append(_x["max_turn"])
        deck_names[_x["owner_deck"]] += 1
        opp_archetypes[_x["opp_archetype"]] += 1

        _arch = _x["opp_archetype"]
        if _o == "win":
            matchup_data[_arch]["w"] += 1
            matchup_data[_arch]["win_turns"].append(_x["max_turn"])
        else:
            matchup_data[_arch]["l"] += 1
            matchup_data[_arch]["loss_turns"].append(_x["max_turn"])

    def avg(lst):
        return sum(lst) / len(lst) if lst else None

    def fmt_avg(value):
        return f"{value:.1f}" if value is not None else "N/A"

    def fmt_wr(value):
        return f"{value:.1f}%" if value is not None else "N/A"

    avg_turns_win = avg(turn_lengths_win)
    avg_turns_loss = avg(turn_lengths_loss)
    d_w_total = sum(dmg_dealt_win)
    d_w_hits = len(dmg_dealt_win) or 1
    t_w_total = sum(dmg_taken_win)
    t_w_hits = len(dmg_taken_win) or 1
    d_l_total = sum(dmg_dealt_loss)
    d_l_hits = len(dmg_dealt_loss) or 1
    t_l_total = sum(dmg_taken_loss)
    t_l_hits = len(dmg_taken_loss) or 1
    deck_label = deck_names.most_common(1)[0][0] if deck_names else "Unknown"
    analyzed = len(raw_results)
    draws = sum(1 for result in raw_results if result["outcome"] == "draw")

    def fmt(n):
        return f"{n:,}"

    all_atks = sorted(set(list(atk_win.keys()) + list(atk_loss.keys())))
    atk_rows = ""
    for _k in all_atks:
        _w = atk_win.get(_k, 0)
        _l = atk_loss.get(_k, 0)
        _t = _w + _l
        _parts = _k.split(": ", 1)
        _card_name = _parts[0] if len(_parts) == 2 else _k
        _atk_name = _parts[1] if len(_parts) == 2 else _k
        atk_rows += (
            f"<tr><td>{html_module.escape(str(_atk_name))}</td>"
            f"<td>{html_module.escape(str(_card_name))}</td>"
            f'<td class="win">{_w}</td><td class="loss">{_l}</td><td>{_t}</td></tr>\n'
        )

    def threat_bar(wr):
        filled = int(wr / 100 * 8)
        empty = 8 - filled
        color = "var(--red)" if wr < 40 else ("var(--orange)" if wr < 50 else "var(--green)")
        return f'<td style="color:{color};font-weight:700">{"█" * filled}{"░" * empty}</td>'

    def confidence_label(sample):
        if sample >= 10:
            return '<td style="color:var(--green)">High</td>'
        elif sample >= 5:
            return '<td style="color:var(--green)">Med</td>'
        else:
            return '<td style="color:var(--yellow)">Low</td>'

    sorted_matchups = sorted(matchup_data.items(), key=lambda x: x[1]["w"], reverse=True)

    opp_rows = ""
    for _arch, _data in sorted_matchups:
        _w = _data["w"]
        _l = _data["l"]
        _total = _w + _l
        _wr = _w / _total * 100 if _total else 0
        _avg_loss = avg(_data["loss_turns"])
        _avg_win = avg(_data["win_turns"])
        _cls = "win" if _wr >= 50 else "loss"
        opp_rows += (
            f"<tr><td>{html_module.escape(str(_arch))}</td>"
            f'<td class="win">{_w}</td><td class="loss">{_l}</td>'
            f'<td class="{_cls}">{fmt_wr(_wr)}</td><td>{fmt_avg(_avg_loss)}</td>'
            f"<td>{fmt_avg(_avg_win)}</td><td>{_total}</td></tr>\n"
        )

    worst_matchups = [(k, v) for k, v in sorted_matchups if (v["w"] + v["l"]) >= 5]
    worst_matchups = sorted(
        worst_matchups,
        key=lambda x: x[1]["w"] / (x[1]["w"] + x[1]["l"]) if (x[1]["w"] + x[1]["l"]) else 0,
    )

    worst_rows = ""
    for _arch, _data in worst_matchups[:10]:
        _w = _data["w"]
        _l = _data["l"]
        _total = _w + _l
        _wr = _w / _total * 100 if _total else 0
        _avg_loss = avg(_data["loss_turns"])
        worst_rows += (
            f"<tr><td>{html_module.escape(str(_arch))}</td>"
            f'<td class="loss">{_w}</td><td class="loss">{_l}</td>'
            f'<td class="loss">{fmt_wr(_wr)}</td><td>{fmt_avg(_avg_loss)}</td>'
            f"<td>{_total}</td>{threat_bar(_wr)}</tr>\n"
        )

    best_matchups = [(k, v) for k, v in sorted_matchups if (v["w"] + v["l"]) >= 5]
    best_matchups = sorted(
        best_matchups,
        key=lambda x: x[1]["w"] / (x[1]["w"] + x[1]["l"]) if (x[1]["w"] + x[1]["l"]) else 0,
        reverse=True,
    )

    best_rows = ""
    for _arch, _data in best_matchups[:10]:
        _w = _data["w"]
        _l = _data["l"]
        _total = _w + _l
        _wr = _w / _total * 100 if _total else 0
        _avg_win = avg(_data["win_turns"])
        best_rows += (
            f"<tr><td>{html_module.escape(str(_arch))}</td>"
            f'<td class="win">{_w}</td><td class="loss">{_l}</td>'
            f'<td class="win">{fmt_wr(_wr)}</td><td>{fmt_avg(_avg_win)}</td>'
            f"<td>{_total}</td>{confidence_label(_total)}</tr>\n"
        )

    donk_rows = ""
    for _arch, _records in sorted(donk_by_archetype.items()):
        _turn_2 = sum(_x["lost_to_no_pokemon_by_turn_2"] for _x in _records)
        _replays = ", ".join(
            f"{_x['episode_id']} (T{2 if _x['lost_to_no_pokemon_by_turn_2'] else 3})"
            for _x in sorted(_records, key=lambda item: int(item["episode_id"]))
        )
        donk_rows += (
            f"<tr><td>{html_module.escape(str(_arch))}</td><td>{len(_records)}</td>"
            f"<td>{_turn_2}</td><td>{len(_records) - _turn_2}</td><td>{_replays}</td></tr>\n"
        )

    metal_rows = ""
    for _arch, _data in sorted(metal_matchups.items()):
        _total = _data["w"] + _data["l"]
        _wr = _data["w"] / _total * 100 if _total else 0
        metal_rows += (
            f"<tr><td>{html_module.escape(str(_arch))}</td>"
            f'<td class="win">{_data["w"]}</td><td class="loss">{_data["l"]}</td>'
            f'<td class="{"win" if _wr >= 50 else "loss"}">{_wr:.1f}%</td>'
            f"<td>{_total}</td></tr>\n"
        )

    deck_out_rows = ""
    for _x in sorted(deck_out_records, key=lambda item: int(item["episode_id"])):
        deck_out_rows += (
            f"<tr><td>{_x['episode_id']}</td><td>{_x['owner_prizes_remaining']}</td>"
            f"<td>{_x['opponent_prizes_remaining']}</td>"
            f"<td>{html_module.escape(str(_x['owner_active_name']))}</td>"
            f"<td>{html_module.escape(str(_x['owner_active_hp']))}</td>"
            f"<td>{html_module.escape(str(_x['opponent_active_name']))}</td>"
            f"<td>{html_module.escape(str(_x['opponent_active_hp']))}</td>"
            f"<td>{_x['opponent_deck_remaining']}</td>"
            f"<td>{html_module.escape(str(_x['opp_archetype']))}</td></tr>\n"
        )

    submissions = _build_submission_rows(
        raw_results,
        submission_id,
        mapped_episode_count,
        parsed_episode_count,
        unprocessed_episode_count,
    )

    sub_rows = ""
    for _s in submissions:
        _badges = []
        if _s.get("best"):
            _badges.append('<span class="badge badge-w">BEST</span>')
        if _s.get("latest"):
            _badges.append('<span class="badge badge-l">LATEST</span>')
        _badge = " ".join(_badges)
        _swr = _s["w"] / (_s["w"] + _s["l"]) * 100 if (_s["w"] + _s["l"]) else None
        _scls = "win" if _swr is not None and _swr >= 50 else "loss"
        _kcls = (
            "var(--accent)"
            if (_s["kaggle"] or 0) >= 500
            else ("var(--orange)" if (_s["kaggle"] or 0) >= 480 else "var(--green)")
        )
        sub_rows += (
            f"<tr><td>{html_module.escape(str(_s['id']))} {_badge or '&mdash;'}</td>"
            f"<td>{html_module.escape(str(_s['id']))}</td>"
            f"<td>{html_module.escape(str(_s['desc']))}</td>"
            f'<td style="font-weight:700;color:{_kcls}">'
            f"{_s['kaggle'] if _s['kaggle'] is not None else 'N/A'}</td>"
            f"<td>{_s['episodes']}</td><td>{_s['parsed']}</td>"
            f'<td class="win">{_s["w"]}</td><td class="loss">{_s["l"]}</td>'
            f'<td class="draw">{_s["draw"]}</td><td>{_s["unprocessed"]}</td>'
            f'<td class="{_scls}">{fmt_wr(_swr)}</td></tr>\n'
        )

    donk_empty = '<tr><td colspan="5">No donk losses in this scope.</td></tr>'
    metal_empty = '<tr><td colspan="5">No Metal-type opponent decks in this scope.</td></tr>'
    deck_out_empty = '<tr><td colspan="9">No deck-out losses in this scope.</td></tr>'

    now = date.today().strftime("%b %d %Y")
    escaped_deck_label = html_module.escape(str(deck_label))
    escaped_submission_id = html_module.escape(str(submission_id)) if submission_id else ""
    report_title = (
        f"Investigation Report — Submission {escaped_submission_id} — {escaped_deck_label}"
        if submission_id
        else f"Investigation Report — {escaped_deck_label}"
    )
    report_heading = (
        f"Investigation Report — Submission {escaped_submission_id}"
        if submission_id
        else "Investigation Report"
    )
    report_subtitle = (
        f"Submission {escaped_submission_id} &bull; {escaped_deck_label} &bull; "
        f"{analyzed} parsed matches "
        f"({games_win}W/{games_loss}L/{draws}D) &bull; {now}"
        if submission_id
        else f"{escaped_deck_label} &bull; {analyzed} parsed matches "
        f"({games_win}W/{games_loss}L/{draws}D) &bull; {now}"
    )
    submission_section_title = (
        "Selected Submission Summary" if submission_id else "Submission History"
    )
    matchup_section_title = (
        f"Matchup Analysis &mdash; Submission {escaped_submission_id}"
        if submission_id
        else "Matchup Analysis (All Submissions Combined)"
    )
    footer_scope = (
        f"Submission {escaped_submission_id} &bull; {escaped_deck_label}"
        if submission_id
        else escaped_deck_label
    )
    first_wr_class = "loss" if first_wr is not None and first_wr < 50 else "win"
    second_wr_class = "win" if second_wr is not None and second_wr >= 50 else "loss"
    advantage_class = (
        "win" if second_wr is not None and first_wr is not None and second_wr > first_wr else "loss"
    )
    advantage_label = (
        "2nd"
        if second_wr is not None and first_wr is not None and second_wr > first_wr
        else "1st"
        if second_wr is not None and first_wr is not None and second_wr < first_wr
        else "Even"
    )
    advantage_value = (
        second_wr - first_wr if second_wr is not None and first_wr is not None else None
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{report_title}</title>
<style>
  :root {{
    --bg:#0f172a; --surface:#1e293b; --surface2:#334155; --border:#475569;
    --text:#e2e8f0; --muted:#94a3b8; --accent:#38bdf8; --green:#4ade80;
    --red:#f87171; --yellow:#facc15; --orange:#fb923c;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg);
    color:var(--text); line-height:1.6; padding:2rem;
  }}
  .container {{ max-width:1200px; margin:0 auto; }}
  h1 {{ font-size:1.8rem; margin-bottom:0.3rem; color:var(--accent); }}
  h2 {{
    font-size:1.3rem; margin-top:2rem; margin-bottom:0.8rem;
    border-bottom:2px solid var(--accent); padding-bottom:0.3rem;
  }}
  h3 {{ font-size:1.1rem; margin-top:1.2rem; margin-bottom:0.5rem; color:var(--accent); }}
  .subtitle {{ color:var(--muted); font-size:0.9rem; margin-bottom:2rem; }}
  table {{ width:100%; border-collapse:collapse; margin:1rem 0; font-size:0.85rem; }}
  th,td {{ padding:0.5rem 0.6rem; text-align:left; border-bottom:1px solid var(--border); }}
  th {{ background:var(--surface2); color:var(--accent); font-weight:600; }}
  tr:hover {{ background:rgba(56,189,248,0.05); }}
  .win {{ color:var(--green); font-weight:600; }}
  .loss {{ color:var(--red); font-weight:600; }}
  .draw {{ color:var(--yellow); font-weight:600; }}
  .card {{
    background:var(--surface); border:1px solid var(--border);
    border-radius:8px; padding:1.2rem; margin:1rem 0;
  }}
  .card-title {{ font-weight:600; color:var(--accent); margin-bottom:0.5rem; }}
  .highlight {{
    background:rgba(251,146,60,0.15); border-left:4px solid var(--orange);
    padding:0.8rem 1rem; border-radius:0 6px 6px 0; margin:1rem 0;
  }}
  .insight {{
    background:rgba(74,222,128,0.1); border-left:4px solid var(--green);
    padding:0.8rem 1rem; border-radius:0 6px 6px 0; margin:1rem 0;
  }}
  .warning {{
    background:rgba(248,113,113,0.15); border-left:4px solid var(--red);
    padding:0.8rem 1rem; border-radius:0 6px 6px 0; margin:1rem 0;
  }}
  .badge {{
    display:inline-block; padding:0.15rem 0.5rem; border-radius:999px;
    font-size:0.75rem; font-weight:600;
  }}
  .badge-w {{ background:rgba(74,222,128,0.2); color:var(--green); }}
  .badge-l {{ background:rgba(248,113,113,0.2); color:var(--red); }}
  code {{
    background:var(--surface2); padding:0.15rem 0.4rem; border-radius:4px;
    font-size:0.85rem;
  }}
  ul,ol {{ padding-left:1.5rem; margin:0.5rem 0; }}
  li {{ margin:0.3rem 0; }}
  .metric-row {{ display:flex; gap:1rem; flex-wrap:wrap; margin:1rem 0; }}
  .metric {{
    background:var(--surface); border:1px solid var(--border);
    border-radius:8px; padding:1rem 1.2rem; min-width:140px; flex:1;
  }}
  .metric-label {{
    font-size:0.75rem; color:var(--muted); text-transform:uppercase;
    letter-spacing:0.05em;
  }}
  .metric-value {{ font-size:1.6rem; font-weight:700; margin-top:0.2rem; }}
  .table-scroll {{ overflow-x:auto; }}
  @media (max-width:700px) {{ body {{ padding:0.8rem; }} }}
</style>
</head>
<body>
<div class="container">

<h1>{report_heading}</h1>
<p class="subtitle">
  {report_subtitle}
</p>

<h2>1 &mdash; Executive Summary</h2>
<div class="metric-row">
  <div class="metric">
    <div class="metric-label">Total Replays</div>
    <div class="metric-value" style="color:var(--accent)">{total}</div>
  </div>
  <div class="metric">
    <div class="metric-label">Overall W/L</div>
    <div class="metric-value">
      <span class="win">{games_win}</span>/<span class="loss">{games_loss}</span>
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Win Rate</div>
    <div class="metric-value" style="color:var(--yellow)">{fmt_wr(wr)}</div>
  </div>
  <div class="metric">
    <div class="metric-label">Avg Win Turn</div>
    <div class="metric-value">{fmt_avg(avg_turns_win)}</div>
  </div>
  <div class="metric">
    <div class="metric-label">Avg Loss Turn</div>
    <div class="metric-value">{fmt_avg(avg_turns_loss)}</div>
  </div>
</div>

<h2>2 &mdash; {submission_section_title}</h2>
<table>
  <thead>
    <tr>
      <th>Submission</th><th>Kaggle ID</th><th>Description</th><th>Kaggle Score</th>
      <th>Mapped Episodes</th><th>Parsed</th><th>W</th><th>L</th><th>Draws</th>
      <th>Unprocessed</th><th>Win Rate (W+L)</th>
    </tr>
  </thead>
  <tbody>
    {sub_rows}
  </tbody>
</table>

<h2>3 &mdash; First vs Second Player</h2>
<div class="metric-row">
  <div class="metric">
    <div class="metric-label">First Player WR</div>
    <div class="metric-value {first_wr_class}">{fmt_wr(first_wr)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {first_wins}W / {first_losses}L ({first_total}g)
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Second Player WR</div>
    <div class="metric-value {second_wr_class}">{fmt_wr(second_wr)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {second_wins}W / {second_losses}L ({second_total}g)
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Advantage</div>
    <div class="metric-value {advantage_class}">
      {fmt_wr(advantage_value)}
    </div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {advantage_label} player
    </div>
  </div>
</div>

<h2>4 &mdash; Early Losses and Weakness Matchups</h2>
<div class="metric-row">
  <div class="metric">
    <div class="metric-label">Donk: no Pokémon through turn 2</div>
    <div class="metric-value loss">{losses_without_field_through_turn_2}</div>
    <div style="font-size:0.8rem;color:var(--muted)">losses only</div>
  </div>
  <div class="metric">
    <div class="metric-label">Donk: no Pokémon through turn 3</div>
    <div class="metric-value loss">{losses_without_field_through_turn_3}</div>
    <div style="font-size:0.8rem;color:var(--muted)">losses only</div>
  </div>
  <div class="metric">
    <div class="metric-label">Losses to {ABOMASNOW_WEAKNESS_NAME} Pokémon</div>
    <div class="metric-value loss">{losses_to_weakness_type}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      opponent deck contained at least one {ABOMASNOW_WEAKNESS_NAME}-type Pokémon
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Losses by deck-out</div>
    <div class="metric-value loss">{losses_to_deck_out}</div>
    <div style="font-size:0.8rem;color:var(--muted)">explicit replay termination reason</div>
  </div>
</div>
<div class="highlight">
  Donk is counted when the replay explicitly ends because we have no Pokémon in
  play (termination reason 3) by the specified global turn. The weakness count uses the opening
  opponent deck list and counts a match once if it contains a {ABOMASNOW_WEAKNESS_NAME}
  Pokémon; it does not claim that Pokémon was the attacker.
</div>

<h3>4.1 &mdash; Donk Details</h3>
<table>
  <thead><tr><th>Opponent Archetype</th><th>Total</th><th>By Turn 2</th>
    <th>By Turn 3</th><th>Replay IDs</th></tr></thead>
  <tbody>{donk_rows or donk_empty}</tbody>
</table>

<h3>4.2 &mdash; Metal Matchups</h3>
<p>Matchups vs decks with a dominant Metal archetype.</p>
<table>
  <thead><tr><th>Opponent Archetype</th><th>Wins</th><th>Losses</th>
    <th>Win Rate</th><th>Total</th></tr></thead>
  <tbody>{metal_rows or metal_empty}</tbody>
</table>

<h3>4.3 &mdash; Individual Deck-out Losses</h3>
<table>
  <thead><tr><th>Replay</th><th>Our Prizes Left</th><th>Opponent Prizes Left</th>
    <th>Our Active</th><th>Our HP</th><th>Opponent Active</th><th>Opponent HP</th>
    <th>Opponent Deck Cards</th><th>Opponent Archetype</th></tr></thead>
  <tbody>{deck_out_rows or deck_out_empty}</tbody>
</table>

<h2>5 &mdash; Attack Usage</h2>
<div class="table-scroll">
<table>
  <thead><tr><th>Attack (uses)</th><th>Card</th><th>Win</th>
    <th>Loss</th><th>Total Uses</th></tr></thead>
  <tbody>{atk_rows}</tbody>
</table>
</div>

<h2>6 &mdash; Damage Distribution</h2>
<div class="metric-row">
  <div class="metric">
    <div class="metric-label">Win: Dealt</div>
    <div class="metric-value win">{fmt(d_w_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {len(dmg_dealt_win)} hits, avg {d_w_total // d_w_hits}
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Win: Taken</div>
    <div class="metric-value win">{fmt(t_w_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {len(dmg_taken_win)} hits, avg {t_w_total // t_w_hits}
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Loss: Dealt</div>
    <div class="metric-value loss">{fmt(d_l_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {len(dmg_dealt_loss)} hits, avg {d_l_total // d_l_hits}
    </div>
  </div>
  <div class="metric">
    <div class="metric-label">Loss: Taken</div>
    <div class="metric-value loss">{fmt(t_l_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">
      {len(dmg_taken_loss)} hits, avg {t_l_total // t_l_hits}
    </div>
  </div>
</div>

<h2>7 &mdash; {matchup_section_title}</h2>

<div class="highlight">
  <strong>{len(matchup_data)} unique opponent archetypes</strong> faced across {total} games.
  Focus on archetypes with 5+ total games for reliable signal.
</div>

<h3>7.1 &mdash; Worst Matchups (Top 10, minimum 5 games)</h3>
<div class="table-scroll">
<table>
  <thead>
    <tr>
      <th>Opponent Archetype</th><th>W</th><th>L</th><th>Win Rate</th>
      <th>Avg Loss Turn</th><th>Sample</th><th>Threat</th>
    </tr>
  </thead>
  <tbody>
    {worst_rows}
  </tbody>
</table>
</div>

<h3>7.2 &mdash; Best Matchups (Top 10, minimum 5 games)</h3>
<div class="table-scroll">
<table>
  <thead>
    <tr>
      <th>Opponent Archetype</th><th>W</th><th>L</th><th>Win Rate</th>
      <th>Avg Win Turn</th><th>Sample</th><th>Confidence</th>
    </tr>
  </thead>
  <tbody>
    {best_rows}
  </tbody>
</table>
</div>

<h3>7.3 &mdash; All Matchups (Full Table)</h3>
<div class="table-scroll">
<table>
  <thead>
    <tr>
      <th>Opponent Archetype</th><th>W</th><th>L</th><th>Win Rate</th>
      <th>Avg Loss Turn</th><th>Avg Win Turn</th><th>Total</th>
    </tr>
  </thead>
  <tbody>
    {opp_rows}
  </tbody>
</table>
</div>

<p style="margin-top:3rem;color:var(--muted);font-size:0.8rem;text-align:center;">
  Auto-generated &bull; {footer_scope} &bull; {total} replays &bull; {now}
</p>

</div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"Report generated: {output_path}")
    print(f"Total replays: {total}")
    print(f"W/L: {games_win}/{games_loss} ({fmt_wr(wr)})")
    print(f"Unique archetypes: {len(matchup_data)}")


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the report generator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "replay_dir",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path("data/raw/kaggle/kaggle_gameplay_runs"),
        help="Directory containing the replay JSON files.",
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path("perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html"),
        help="Destination HTML report path.",
    )
    parser.add_argument(
        "owner_name",
        nargs="?",
        default="Igor Riegel",
        help="Kaggle agent name used to identify the controlled player.",
    )
    parser.add_argument(
        "--submission-id",
        help="Limit the report to episodes mapped to this Kaggle submission ID.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the replay analysis CLI."""
    args = _parser().parse_args(argv)
    try:
        generate_report(
            args.replay_dir,
            args.owner_name,
            args.output_path,
            submission_id=args.submission_id,
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
