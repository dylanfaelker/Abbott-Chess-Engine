"""
arena/stats.py

Turn a list of GameRecords into a summary: results, strength estimate, and
per-engine speed analytics. Pure functions over records, so the same code
serves the live progress line, the final report, and `python -m arena report`.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Optional, Sequence

from .game import GameRecord

Z95 = 1.959964  # 95% two-sided normal quantile


# ── strength maths ────────────────────────────────────────────────────────────

def elo_from_score(score: float) -> float:
    """Elo difference implied by a score fraction in [0, 1] (+-inf at the extremes)."""
    if score <= 0.0:
        return -math.inf
    if score >= 1.0:
        return math.inf
    return -400.0 * math.log10(1.0 / score - 1.0)


def score_confidence(wins: int, draws: int, losses: int, z: float = Z95) -> tuple[float, float, float]:
    """(score, low, high): score fraction and its normal-approximation interval."""
    n = wins + draws + losses
    if n == 0:
        return 0.5, 0.0, 1.0
    s = (wins + 0.5 * draws) / n
    var = (wins * (1 - s) ** 2 + draws * (0.5 - s) ** 2 + losses * (0 - s) ** 2) / n
    se = math.sqrt(var / n)
    return s, max(0.0, s - z * se), min(1.0, s + z * se)


def elo_interval(wins: int, draws: int, losses: int) -> tuple[float, float, float]:
    """(elo, low, high) for engine A relative to engine B."""
    s, lo, hi = score_confidence(wins, draws, losses)
    return elo_from_score(s), elo_from_score(lo), elo_from_score(hi)


def likelihood_of_superiority(wins: int, losses: int) -> float:
    """
    P(A is really stronger than B), ignoring draws (the usual LOS formula).
    0.5 when there is nothing to separate them.
    """
    decisive = wins + losses
    if decisive == 0:
        return 0.5
    return 0.5 * (1.0 + math.erf((wins - losses) / math.sqrt(2.0 * decisive)))


# ── summary ───────────────────────────────────────────────────────────────────

def _percentile(sorted_values: Sequence[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    k = min(len(sorted_values) - 1, max(0, math.ceil(p * len(sorted_values)) - 1))
    return sorted_values[k]


def _wdl(games: Sequence[GameRecord]) -> tuple[int, int, int]:
    w = sum(1 for g in games if g.score_a == 1.0)
    d = sum(1 for g in games if g.score_a == 0.5)
    return w, d, len(games) - w - d


def engine_move_stats(games: Sequence[GameRecord], engine: int) -> dict[str, Any]:
    times, nodes, depths = [], [], []
    for g in games:
        for m in g.moves:
            if m.engine == engine:
                times.append(m.time_s)
                nodes.append(m.nodes)
                depths.append(m.depth)
    n = len(times)
    out: dict[str, Any] = {"moves": n}
    if n == 0:
        return out
    times_sorted = sorted(times)
    out["avg_time_s"] = sum(times) / n
    out["median_time_s"] = _percentile(times_sorted, 0.5)
    out["p95_time_s"] = _percentile(times_sorted, 0.95)
    out["max_time_s"] = times_sorted[-1]
    out["total_time_s"] = sum(times)
    if any(nodes):
        out["avg_nodes"] = sum(nodes) / n
        out["nodes_per_s"] = sum(nodes) / sum(times) if sum(times) > 0 else 0.0
    reported = [d for d in depths if d > 0]
    if reported:
        out["avg_depth"] = sum(reported) / len(reported)
        out["min_depth"], out["max_depth"] = min(reported), max(reported)
    return out


def overshoot(games: Sequence[GameRecord], engine: int, movetime_s: float, tolerance: float = 1.25) -> tuple[float, float]:
    """
    For a fixed-movetime engine: (fraction of moves that took longer than
    tolerance * movetime + 50ms, slowest move in seconds).
    """
    times = [m.time_s for g in games for m in g.moves if m.engine == engine]
    if not times:
        return 0.0, 0.0
    late = sum(1 for t in times if t > movetime_s * tolerance + 0.05)
    return late / len(times), max(times)


def summarize(games: Sequence[GameRecord], names: Sequence[str]) -> dict[str, Any]:
    """Everything the report shows, as plain data (JSON-serialisable apart from +-inf)."""
    games = sorted(games, key=lambda g: g.index)
    w, d, l = _wdl(games)
    n = len(games)
    elo, elo_lo, elo_hi = elo_interval(w, d, l)
    score = (w + 0.5 * d) / n if n else 0.0

    a_white = [g for g in games if g.a_is_white]
    a_black = [g for g in games if not g.a_is_white]
    white_points = sum(g.score_a if g.a_is_white else 1.0 - g.score_a for g in games)

    plies = [len(g.moves) for g in games]
    return {
        "engines": list(names),
        "games": n,
        "a": {"wins": w, "draws": d, "losses": l, "score": score},
        "elo": {"diff": elo, "low": elo_lo, "high": elo_hi},
        "los": likelihood_of_superiority(w, l),
        "as_white": dict(zip(("wins", "draws", "losses"), _wdl(a_white))),
        "as_black": dict(zip(("wins", "draws", "losses"), _wdl(a_black))),
        "white_score": white_points / n if n else 0.0,
        "terminations": dict(Counter(g.reason for g in games).most_common()),
        "failures": {
            names[i]: sum(1 for g in games if g.error and _loser(g) == i)
            for i in (0, 1)
        },
        "plies": {
            "avg": sum(plies) / n if n else 0.0,
            "min": min(plies, default=0),
            "max": max(plies, default=0),
        },
        "total_duration_s": sum(g.duration_s for g in games),
        "engine_stats": [engine_move_stats(games, 0), engine_move_stats(games, 1)],
    }


def _loser(g: GameRecord) -> int:
    """Index (0/1) of the engine that lost game `g`."""
    return 1 if g.score_a == 1.0 else 0


# ── formatting ────────────────────────────────────────────────────────────────

def _fmt_elo(x: float) -> str:
    if math.isinf(x):
        return "+inf" if x > 0 else "-inf"
    if round(x) == 0:
        return "0"
    return f"{x:+.0f}"


def fmt_seconds(s: float) -> str:
    if s < 1:
        return f"{s * 1000:.0f}ms"
    if s < 120:
        return f"{s:.2f}s"
    return f"{int(s // 60)}m{int(s % 60):02d}s"


def progress_line(games: Sequence[GameRecord], names: Sequence[str], total: int) -> str:
    w, d, l = _wdl(games)
    n = len(games)
    pct = 100.0 * (w + 0.5 * d) / n if n else 0.0
    return f"{names[0]} +{w} ={d} -{l}  ({pct:.1f}%)  [{n}/{total}]"


def format_summary(s: dict[str, Any]) -> str:
    a_name, b_name = s["engines"]
    n = s["games"]
    if n == 0:
        return "No completed games."
    a = s["a"]
    lines: list[str] = []
    add = lines.append

    add("=" * 72)
    add(f"{a_name}  vs  {b_name}      ({n} games)")
    add("=" * 72)
    add(f"{a_name:<22} wins {a['wins']:>4}   draws {a['draws']:>4}   losses {a['losses']:>4}"
        f"      score {100 * a['score']:.1f}%")
    e = s["elo"]
    lo, hi = _fmt_elo(e["low"]), _fmt_elo(e["high"])
    add(f"Elo difference ({a_name} - {b_name}): {_fmt_elo(e['diff'])}   95% interval [{lo}, {hi}]")
    add(f"Likelihood of superiority: {100 * s['los']:.1f}%  "
        f"(chance {a_name} is truly stronger; draws ignored)")
    if hi_is_unclear(e):
        add("  -> the interval includes 0: not enough games to separate these engines yet.")
    add("")

    aw, ab = s["as_white"], s["as_black"]
    add(f"{a_name} as White: +{aw['wins']} ={aw['draws']} -{aw['losses']}"
        f"     as Black: +{ab['wins']} ={ab['draws']} -{ab['losses']}"
        f"     (White scores {100 * s['white_score']:.1f}% overall)")
    p = s["plies"]
    add(f"Game length: avg {p['avg']:.0f} plies (min {p['min']}, max {p['max']})"
        f"      total play time {fmt_seconds(s['total_duration_s'])}")
    add("Endings: " + ", ".join(f"{k} {v}" for k, v in s["terminations"].items()))
    bad = {k: v for k, v in s["failures"].items() if v}
    if bad:
        add("!! Engine failures (timeouts / illegal moves / crashes): " + ", ".join(f"{k} {v}" for k, v in bad.items()))
    add("")

    add("Per-move analytics")
    header = f"{'':<22}{'moves':>7}{'avg time':>10}{'p95':>9}{'max':>9}{'avg nodes':>12}{'nodes/s':>10}{'avg depth':>11}"
    add(header)
    for name, st in zip(s["engines"], s["engine_stats"]):
        if not st.get("moves"):
            add(f"{name:<22}{'-':>7}")
            continue
        nodes = f"{st['avg_nodes']:,.0f}" if "avg_nodes" in st else "n/a"
        nps = f"{st['nodes_per_s']:,.0f}" if "nodes_per_s" in st else "n/a"
        depth = f"{st['avg_depth']:.2f}" if "avg_depth" in st else "n/a"
        add(f"{name:<22}{st['moves']:>7}{fmt_seconds(st['avg_time_s']):>10}{fmt_seconds(st['p95_time_s']):>9}"
            f"{fmt_seconds(st['max_time_s']):>9}{nodes:>12}{nps:>10}{depth:>11}")
    add("")
    for note in s.get("notes", []):
        add(f"NOTE: {note}")
    if s.get("notes"):
        add("")
    return "\n".join(lines)


def hi_is_unclear(elo: dict[str, float]) -> bool:
    return elo["low"] < 0.0 < elo["high"]
