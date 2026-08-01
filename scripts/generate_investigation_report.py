"""Generate Investigation Report from CABT replays. Based on v2_checkpoint format."""

from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict
from datetime import date

from cg.api import all_attack, all_card_data


attacks_sdk = {a.attackId: a for a in all_attack()}
cards_sdk = {c.cardId: c for c in all_card_data()}
attack_to_card = {}
for _c in all_card_data():
    for _aid in _c.attacks:
        attack_to_card[_aid] = _c.name


def resolve_deck_name(vis, owner_idx):
    """Extract deck archetype from initial visualization."""
    try:
        action = vis[0]["action"]
        deck_ids = [int(_cid) for _cid in action[owner_idx]]
        counts = Counter(deck_ids)
        pokemon = []
        for _cid, _qty in counts.items():
            _c = cards_sdk.get(_cid)
            if _c and (_c.basic or _c.stage1 or _c.stage2):
                pokemon.append((_c.hp, _c.name, _qty))
        if pokemon:
            pokemon.sort(key=lambda x: (-x[0], -x[2]))
            return " / ".join(p[1] for p in pokemon[:2])
    except (KeyError, IndexError, TypeError):
        pass
    return "unknown"


def parse_replay(fpath, owner_name):
    """Parse a single replay file."""
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
    for _frame in vis:
        for _log in _frame.get("logs", []):
            if _log.get("type") == "Result":
                winner = _log.get("result")
    if winner is None:
        return None

    outcome = "win" if winner == owner_idx else "loss"

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
        "outcome": outcome,
        "first_player": first_player,
        "max_turn": max_turn,
        "opp_archetype": opp_arch,
        "owner_deck": owner_deck_name,
        "attack_usage": dict(attack_usage),
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "evolution_turns": evolution_turns,
    }


def generate_report(replay_dir: pathlib.Path, owner_name: str, output_path: pathlib.Path) -> None:
    """Generate the investigation report HTML."""
    submission_map_path = pathlib.Path("data/raw/kaggle/episode_to_submission.json")
    submission_map = {}
    if submission_map_path.exists():
        submission_map = json.loads(submission_map_path.read_text())

    raw_results = []
    for _fp in sorted(replay_dir.glob("*.json")):
        _res = parse_replay(_fp, owner_name)
        if _res is not None:
            raw_results.append(_res)

    games_win = sum(1 for _x in raw_results if _x["outcome"] == "win")
    games_loss = sum(1 for _x in raw_results if _x["outcome"] == "loss")
    total = games_win + games_loss
    wr = games_win / total * 100 if total else 0

    first_wins = 0
    first_losses = 0
    second_wins = 0
    second_losses = 0
    for _x in raw_results:
        _fp = _x["first_player"]
        if _fp is None:
            continue
        if _fp == 0:
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
    first_wr = first_wins / first_total * 100 if first_total else 0
    second_wr = second_wins / second_total * 100 if second_total else 0

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
        return sum(lst) / len(lst) if lst else 0

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
    evo_w_avg = avg(evo_win)
    evo_l_avg = avg(evo_loss)
    deck_label = deck_names.most_common(1)[0][0] if deck_names else "Unknown"

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
        atk_rows += f'<tr><td>{_atk_name}</td><td>{_card_name}</td><td class="win">{_w}</td><td class="loss">{_l}</td><td>{_t}</td></tr>\n'

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
        opp_rows += f'<tr><td>{_arch}</td><td class="win">{_w}</td><td class="loss">{_l}</td><td class="{_cls}">{_wr:.1f}%</td><td>{_avg_loss:.1f}</td><td>{_avg_win:.1f}</td><td>{_total}</td></tr>\n'

    worst_matchups = [(k, v) for k, v in sorted_matchups if (v["w"] + v["l"]) >= 5]
    worst_matchups = sorted(worst_matchups, key=lambda x: x[1]["w"] / (x[1]["w"] + x[1]["l"]) if (x[1]["w"] + x[1]["l"]) else 0)

    worst_rows = ""
    for _arch, _data in worst_matchups[:10]:
        _w = _data["w"]
        _l = _data["l"]
        _total = _w + _l
        _wr = _w / _total * 100 if _total else 0
        _avg_loss = avg(_data["loss_turns"])
        worst_rows += f'<tr><td>{_arch}</td><td class="loss">{_w}</td><td class="loss">{_l}</td><td class="loss">{_wr:.1f}%</td><td>{_avg_loss:.1f}</td><td>{_total}</td>{threat_bar(_wr)}</tr>\n'

    best_matchups = [(k, v) for k, v in sorted_matchups if (v["w"] + v["l"]) >= 5]
    best_matchups = sorted(best_matchups, key=lambda x: x[1]["w"] / (x[1]["w"] + x[1]["l"]) if (x[1]["w"] + x[1]["l"]) else 0, reverse=True)

    best_rows = ""
    for _arch, _data in best_matchups[:10]:
        _w = _data["w"]
        _l = _data["l"]
        _total = _w + _l
        _wr = _w / _total * 100 if _total else 0
        _avg_win = avg(_data["win_turns"])
        best_rows += f'<tr><td>{_arch}</td><td class="win">{_w}</td><td class="loss">{_l}</td><td class="win">{_wr:.1f}%</td><td>{_avg_win:.1f}</td><td>{_total}</td>{confidence_label(_total)}</tr>\n'

    SUBMISSIONS = [
        {"label": "Sub 1", "id": "55088176", "kaggle": 539.2, "episodes": 48, "w": 21, "l": 27, "best": True, "desc": "v2_Mega_Abomasnow"},
        {"label": "Sub 2", "id": "55093119", "kaggle": 478.6, "episodes": 54, "w": 24, "l": 30, "best": False, "desc": "heuristic current-deck rulebox-prizecheck"},
        {"label": "Sub 3", "id": "55119505", "kaggle": 490.4, "episodes": 46, "w": 27, "l": 19, "best": False, "desc": "v3_Mega_Abomasnow hdi_v1"},
    ]

    sub_rows = ""
    for _s in SUBMISSIONS:
        _badge = '<span class="badge badge-w">BEST</span>' if _s["best"] else ('<span class="badge badge-l">LATEST</span>' if _s == SUBMISSIONS[-1] else "")
        _swr = _s["w"] / (_s["w"] + _s["l"]) * 100 if (_s["w"] + _s["l"]) else 0
        _scls = "win" if _swr >= 50 else "loss"
        _kcls = "var(--accent)" if _s["kaggle"] >= 500 else ("var(--orange)" if _s["kaggle"] >= 480 else "var(--green)")
        sub_rows += f'<tr><td>{_s["label"]} {_badge}</td><td>{_s["id"]}</td><td>{_s["desc"]}</td><td style="font-weight:700;color:{_kcls}">{_s["kaggle"]}</td><td>{_s["episodes"]}</td><td class="win">{_s["w"]}</td><td class="loss">{_s["l"]}</td><td class="{_scls}">{_swr:.1f}%</td></tr>\n'

    now = date.today().strftime("%b %d %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Investigation Report — {deck_label}</title>
<style>
  :root {{ --bg:#0f172a; --surface:#1e293b; --surface2:#334155; --border:#475569; --text:#e2e8f0; --muted:#94a3b8; --accent:#38bdf8; --green:#4ade80; --red:#f87171; --yellow:#facc15; --orange:#fb923c; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; padding:2rem; }}
  .container {{ max-width:1200px; margin:0 auto; }}
  h1 {{ font-size:1.8rem; margin-bottom:0.3rem; color:var(--accent); }}
  h2 {{ font-size:1.3rem; margin-top:2rem; margin-bottom:0.8rem; border-bottom:2px solid var(--accent); padding-bottom:0.3rem; }}
  h3 {{ font-size:1.1rem; margin-top:1.2rem; margin-bottom:0.5rem; color:var(--accent); }}
  .subtitle {{ color:var(--muted); font-size:0.9rem; margin-bottom:2rem; }}
  table {{ width:100%; border-collapse:collapse; margin:1rem 0; font-size:0.85rem; }}
  th,td {{ padding:0.5rem 0.6rem; text-align:left; border-bottom:1px solid var(--border); }}
  th {{ background:var(--surface2); color:var(--accent); font-weight:600; }}
  tr:hover {{ background:rgba(56,189,248,0.05); }}
  .win {{ color:var(--green); font-weight:600; }}
  .loss {{ color:var(--red); font-weight:600; }}
  .draw {{ color:var(--yellow); font-weight:600; }}
  .card {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:1.2rem; margin:1rem 0; }}
  .card-title {{ font-weight:600; color:var(--accent); margin-bottom:0.5rem; }}
  .highlight {{ background:rgba(251,146,60,0.15); border-left:4px solid var(--orange); padding:0.8rem 1rem; border-radius:0 6px 6px 0; margin:1rem 0; }}
  .insight {{ background:rgba(74,222,128,0.1); border-left:4px solid var(--green); padding:0.8rem 1rem; border-radius:0 6px 6px 0; margin:1rem 0; }}
  .warning {{ background:rgba(248,113,113,0.15); border-left:4px solid var(--red); padding:0.8rem 1rem; border-radius:0 6px 6px 0; margin:1rem 0; }}
  .badge {{ display:inline-block; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.75rem; font-weight:600; }}
  .badge-w {{ background:rgba(74,222,128,0.2); color:var(--green); }}
  .badge-l {{ background:rgba(248,113,113,0.2); color:var(--red); }}
  code {{ background:var(--surface2); padding:0.15rem 0.4rem; border-radius:4px; font-size:0.85rem; }}
  ul,ol {{ padding-left:1.5rem; margin:0.5rem 0; }}
  li {{ margin:0.3rem 0; }}
  .metric-row {{ display:flex; gap:1rem; flex-wrap:wrap; margin:1rem 0; }}
  .metric {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:1rem 1.2rem; min-width:140px; flex:1; }}
  .metric-label {{ font-size:0.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.05em; }}
  .metric-value {{ font-size:1.6rem; font-weight:700; margin-top:0.2rem; }}
  .table-scroll {{ overflow-x:auto; }}
  @media (max-width:700px) {{ body {{ padding:0.8rem; }} }}
</style>
</head>
<body>
<div class="container">

<h1>Investigation Report</h1>
<p class="subtitle">{deck_label} &bull; {total} replays ({games_win}W/{games_loss}L) &bull; {now}</p>

<h2>1 &mdash; Executive Summary</h2>
<div class="metric-row">
  <div class="metric"><div class="metric-label">Total Replays</div><div class="metric-value" style="color:var(--accent)">{total}</div></div>
  <div class="metric"><div class="metric-label">Overall W/L</div><div class="metric-value"><span class="win">{games_win}</span>/<span class="loss">{games_loss}</span></div></div>
  <div class="metric"><div class="metric-label">Win Rate</div><div class="metric-value" style="color:var(--yellow)">{wr:.1f}%</div></div>
  <div class="metric"><div class="metric-label">Avg Win Turn</div><div class="metric-value">{avg_turns_win:.1f}</div></div>
  <div class="metric"><div class="metric-label">Avg Loss Turn</div><div class="metric-value">{avg_turns_loss:.1f}</div></div>
</div>

<h2>2 &mdash; Submission History</h2>
<table>
  <thead>
    <tr><th>Submission</th><th>Kaggle ID</th><th>Description</th><th>Kaggle Score</th><th>Episodes</th><th>W</th><th>L</th><th>Win Rate</th></tr>
  </thead>
  <tbody>
    {sub_rows}
  </tbody>
</table>

<h2>3 &mdash; First vs Second Player</h2>
<div class="metric-row">
  <div class="metric">
    <div class="metric-label">First Player WR</div>
    <div class="metric-value {"loss" if first_wr < 50 else "win"}">{first_wr:.1f}%</div>
    <div style="font-size:0.8rem;color:var(--muted)">{first_wins}W / {first_losses}L ({first_total}g)</div>
  </div>
  <div class="metric">
    <div class="metric-label">Second Player WR</div>
    <div class="metric-value {"win" if second_wr >= 50 else "loss"}">{second_wr:.1f}%</div>
    <div style="font-size:0.8rem;color:var(--muted)">{second_wins}W / {second_losses}L ({second_total}g)</div>
  </div>
  <div class="metric">
    <div class="metric-label">Advantage</div>
    <div class="metric-value" style="color:var(--green)">+{second_wr - first_wr:.1f}%</div>
    <div style="font-size:0.8rem;color:var(--muted)">{"2nd" if second_wr > first_wr else "1st"} player</div>
  </div>
</div>

<h2>4 &mdash; Attack Usage</h2>
<div class="table-scroll">
<table>
  <thead><tr><th>Attack</th><th>Card</th><th>Win</th><th>Loss</th><th>Total</th></tr></thead>
  <tbody>{atk_rows}</tbody>
</table>
</div>

<h2>5 &mdash; Damage Distribution</h2>
<div class="metric-row">
  <div class="metric">
    <div class="metric-label">Win: Dealt</div>
    <div class="metric-value win">{fmt(d_w_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">{len(dmg_dealt_win)} hits, avg {d_w_total // d_w_hits}</div>
  </div>
  <div class="metric">
    <div class="metric-label">Win: Taken</div>
    <div class="metric-value win">{fmt(t_w_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">{len(dmg_taken_win)} hits, avg {t_w_total // t_w_hits}</div>
  </div>
  <div class="metric">
    <div class="metric-label">Loss: Dealt</div>
    <div class="metric-value loss">{fmt(d_l_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">{len(dmg_dealt_loss)} hits, avg {d_l_total // d_l_hits}</div>
  </div>
  <div class="metric">
    <div class="metric-label">Loss: Taken</div>
    <div class="metric-value loss">{fmt(t_l_total)}</div>
    <div style="font-size:0.8rem;color:var(--muted)">{len(dmg_taken_loss)} hits, avg {t_l_total // t_l_hits}</div>
  </div>
</div>

<h2>6 &mdash; Matchup Analysis (All Submissions Combined)</h2>

<div class="highlight"><strong>{len(matchup_data)} unique opponent archetypes</strong> faced across {total} games. Focus on archetypes with 5+ total games for reliable signal.</div>

<h3>6.1 &mdash; Worst Matchups (Top 10 by win rate)</h3>
<div class="table-scroll">
<table>
  <thead>
    <tr><th>Opponent Archetype</th><th>W</th><th>L</th><th>Win Rate</th><th>Avg Loss Turn</th><th>Sample</th><th>Threat</th></tr>
  </thead>
  <tbody>
    {worst_rows}
  </tbody>
</table>
</div>

<h3>6.2 &mdash; Best Matchups (Top 10 by win rate)</h3>
<div class="table-scroll">
<table>
  <thead>
    <tr><th>Opponent Archetype</th><th>W</th><th>L</th><th>Win Rate</th><th>Avg Win Turn</th><th>Sample</th><th>Confidence</th></tr>
  </thead>
  <tbody>
    {best_rows}
  </tbody>
</table>
</div>

<h3>6.3 &mdash; All Matchups (Full Table)</h3>
<div class="table-scroll">
<table>
  <thead>
    <tr><th>Opponent Archetype</th><th>W</th><th>L</th><th>Win Rate</th><th>Avg Loss Turn</th><th>Avg Win Turn</th><th>Total</th></tr>
  </thead>
  <tbody>
    {opp_rows}
  </tbody>
</table>
</div>

<p style="margin-top:3rem;color:var(--muted);font-size:0.8rem;text-align:center;">Auto-generated &bull; {deck_label} &bull; {total} replays &bull; {now}</p>

</div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"Report generated: {output_path}")
    print(f"Total replays: {total}")
    print(f"W/L: {games_win}/{games_loss} ({wr:.1f}%)")
    print(f"Unique archetypes: {len(matchup_data)}")


if __name__ == "__main__":
    import sys
    replay_dir = pathlib.Path("data/raw/kaggle/kaggle_gameplay_runs")
    output_path = pathlib.Path("perf_reports/INVESTIGATION_REPORT_ABOMASNOW.html")
    owner_name = "Igor Riegel"

    if len(sys.argv) > 1:
        replay_dir = pathlib.Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = pathlib.Path(sys.argv[2])
    if len(sys.argv) > 3:
        owner_name = sys.argv[3]

    generate_report(replay_dir, owner_name, output_path)
