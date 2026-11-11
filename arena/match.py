"""
arena/match.py

Runs a whole match: validates the config, probes both engines, builds the
opening list, plays the games (optionally several at once), writes results to
disk as each game finishes, and produces the summary.

Output directory layout:
    <output_dir>/<name>_<timestamp>/
        config.json      the resolved configuration (incl. the seed actually used)
        games.jsonl      one JSON object per finished game (moves + per-move stats)
        summary.json     machine-readable summary
        summary.txt      the report that was printed
"""

from __future__ import annotations

import json
import os
import platform
import random
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import stats
from .config import ConfigError, EngineConfig, MatchConfig
from .game import GameAborted, GameRecord, play_game
from .openings import build_openings
from .uci_client import EngineError, EngineStartupError, UciEngine, kill_all_engines


def probe_engines(engines: list[EngineConfig], repo_root: Path, log: Callable[[str], None]) -> None:
    """
    Start each engine once. Catches missing packages / broken imports immediately,
    and refuses time-based limits for engines whose Search cannot honour them.
    """
    for e in engines:
        engine = UciEngine(e, repo_root)
        engine.start()                      # raises EngineStartupError with the engine's stderr
        try:
            supports_time = engine.caps.get("timelimit") == "1"
        finally:
            engine.close()
        wants_time = e.movetime is not None or e.base is not None
        if wants_time and not supports_time:
            raise ConfigError(
                f"Engine {e.label!r} ({e.package}) does not support time limits: its "
                f"Search.find_best_move has no `time_limit` parameter. Give it a fixed depth, or add "
                f"time support (see arena/README.md, 'Engine contract')."
            )
        log(f"  {e.label:<14} {e.package:<14} {e.limits_text()}"
            + (f"   root={e.root}" if e.root else ""))


def run_match(
    cfg: MatchConfig,
    repo_root: Path,
    log: Callable[[str], None] = print,
    out_dir: Path | None = None,
) -> tuple[list[GameRecord], dict, Path]:
    """
    Run the match described by `cfg`. Returns (records, summary, output directory).
    Raises ConfigError / EngineStartupError for problems found before play starts.
    """
    cfg.validate()
    if cfg.seed is None:
        cfg.seed = random.SystemRandom().randrange(2**31)
    engines = cfg.resolved_engines()
    names = [e.label for e in engines]

    if cfg.concurrency > (os.cpu_count() or 1):
        log(f"warning: concurrency {cfg.concurrency} exceeds the {os.cpu_count()} CPU cores; "
            f"timings (and time-controlled results) will be distorted")

    log("Engines:")
    probe_engines(engines, repo_root, log)

    n = cfg.games
    pairs = cfg.pair_openings
    n_openings = (n + 1) // 2 if pairs else n
    log(f"Preparing {n_openings} opening(s) [{cfg.openings.source}"
        + (f", {cfg.openings.plies} plies" if cfg.openings.source == 'random' else '') + "] ...")
    openings = build_openings(cfg.openings, n_openings, cfg.seed)

    out_dir = out_dir or _make_output_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "config.json").write_text(json.dumps({
        "config": cfg.to_dict(),
        "resolved_engines": [e.__dict__ for e in engines],
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "started": datetime.now().isoformat(timespec="seconds"),
    }, indent=2), encoding="utf-8")
    log(f"Results will be written to {out_dir}")
    log(f"Playing {n} games, {cfg.concurrency} at a time, seed {cfg.seed}"
        + (" (openings paired: each played with colours swapped)" if pairs else "") + "\n")

    stop = threading.Event()
    records: list[GameRecord] = []
    games_file = (out_dir / "games.jsonl").open("a", encoding="utf-8")
    fatal: list[BaseException] = []

    def task(i: int) -> GameRecord:
        opening = openings[i // 2] if pairs else openings[i]
        return play_game(i, opening, i % 2 == 0, cfg, engines, repo_root, stop)

    pool = ThreadPoolExecutor(max_workers=cfg.concurrency)
    futures = [pool.submit(task, i) for i in range(n)]
    try:
        for fut in as_completed(futures):
            try:
                rec = fut.result()
            except GameAborted:
                continue
            except EngineStartupError as e:
                fatal.append(e)
                stop.set()
                kill_all_engines()
                break
            except Exception as e:                      # a bug in the arena itself
                log("Unexpected error while playing a game:\n" + "".join(traceback.format_exception(e)))
                fatal.append(e)
                stop.set()
                kill_all_engines()
                break

            records.append(rec)
            games_file.write(json.dumps(rec.to_dict()) + "\n")
            games_file.flush()
            log(_game_line(rec, names, len(records), n) + "   | " + stats.progress_line(records, names, n))
    except KeyboardInterrupt:
        log("\nInterrupted: stopping, engines are being shut down. Summarising completed games.")
        stop.set()
        kill_all_engines()
    finally:
        for f in futures:
            f.cancel()
        pool.shutdown(wait=True, cancel_futures=True)
        games_file.close()

    summary = stats.summarize(records, names)
    summary["notes"] = _quality_notes(records, engines, names)
    text = stats.format_summary(summary)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "summary.txt").write_text(text + "\n", encoding="utf-8")
    log("\n" + text)
    if fatal:
        log(f"Match aborted: {fatal[0]}")
        raise fatal[0]
    return records, summary, out_dir


# ── helpers ───────────────────────────────────────────────────────────────────

def _quality_notes(records: list[GameRecord], engines: list[EngineConfig], names: list[str]) -> list[str]:
    """Warnings about how trustworthy this particular run is."""
    notes = []
    for i, e in enumerate(engines):
        if e.movetime is None:
            continue
        frac, worst = stats.overshoot(records, i, e.movetime)
        if frac > 0.10:
            notes.append(
                f"{names[i]} took longer than its {e.movetime:g}s movetime on {100 * frac:.0f}% of moves "
                f"(slowest {worst:.2f}s). A search cannot stop inside depth 1, so this time limit is too short "
                f"for the position complexity; the result is closer to 'depth 1 vs depth 1' than a timed match. "
                f"Use a longer movetime."
            )
    return notes


def _make_output_dir(cfg: MatchConfig) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in cfg.name) or "match"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(cfg.output_dir) / f"{safe}_{stamp}"


def _game_line(rec: GameRecord, names: list[str], done: int, total: int) -> str:
    white, black = (names[0], names[1]) if rec.a_is_white else (names[1], names[0])
    extra = f" ({rec.error.splitlines()[0]})" if rec.error else ""
    return (f"[{done:>{len(str(total))}}/{total}] game {rec.index + 1:<4} {white} (W) vs {black} (B): "
            f"{rec.result:<7} {rec.reason}{extra}, {len(rec.moves)} plies, {stats.fmt_seconds(rec.duration_s)}")
