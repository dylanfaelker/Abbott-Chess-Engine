"""
arena/cli.py

    python -m arena run       play a match
    python -m arena openings  generate a big file of balanced random openings
    python -m arena report    re-print the summary of a finished (or interrupted) run
    python -m arena replay    show one game move by move, with per-move stats

Run from the repository root.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import stats
from .config import ConfigError, MatchConfig, parse_time_control
from .game import GameRecord
from .uci_client import EngineError

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── run ───────────────────────────────────────────────────────────────────────

def _add_run_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", help="JSON config file (command-line options override it)")
    p.add_argument("--engine", action="append", metavar="SPEC",
                   help="PACKAGE[:key=value,...]; give it twice. Keys: name, depth, movetime, tc, base, inc, vary, root")
    p.add_argument("-n", "--games", type=int, help="number of games (default 20)")
    p.add_argument("-j", "--concurrency", type=int, help="games played at the same time (default 1)")
    p.add_argument("--seed", type=int, help="seed for openings and engine noise (default: random, recorded)")
    p.add_argument("--name", help="label for the output folder")
    p.add_argument("--out", help="output directory (default arena/results)")

    g = p.add_argument_group("limits (defaults for any engine that does not set its own)")
    g.add_argument("--depth", type=int, help="max search depth")
    g.add_argument("--movetime", type=float, help="seconds per move")
    g.add_argument("--tc", metavar="BASE[+INC]", help="game clock in seconds, e.g. 60+0.5 (sudden death with increment)")

    g = p.add_argument_group("openings")
    g.add_argument("--openings", metavar="start|random|FILE",
                   help="start position, random balanced openings (default), or a FEN/EPD file")
    g.add_argument("--opening-plies", type=int, help="random openings: half-moves to play (default 6)")
    g.add_argument("--max-imbalance", type=int, help="random openings: max material difference in centipawns (default 100)")
    g.add_argument("--no-pairs", action="store_true", help="do not replay each opening with colours swapped")

    g = p.add_argument_group("game control")
    g.add_argument("--max-plies", type=int, help="draw after this many half-moves (default 300)")
    g.add_argument("--move-timeout", type=float, help="kill an engine that needs longer than this per move when it has no time limit (default 600s)")
    g.add_argument("--resign", type=int, metavar="CP", help="adjudicate a loss when an engine's own score is <= -CP ...")
    g.add_argument("--resign-moves", type=int, help="... for this many consecutive moves (default 4)")
    g.add_argument("--draw", type=int, metavar="CP", help="adjudicate a draw when both scores stay within +-CP ...")
    g.add_argument("--draw-moves", type=int, help="... for this many moves each (default 8)")
    g.add_argument("--draw-after", type=int, help="... but only after this many plies (default 80)")


def build_config(args: argparse.Namespace) -> MatchConfig:
    data: dict = {}
    if args.config:
        try:
            data = json.loads(Path(args.config).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {args.config}") from None
        except json.JSONDecodeError as e:
            raise ConfigError(f"{args.config}: invalid JSON ({e})") from None

    if args.engine:
        data["engines"] = list(args.engine)

    direct = {
        "games": args.games, "concurrency": args.concurrency, "seed": args.seed, "name": args.name,
        "output_dir": args.out, "depth": args.depth, "movetime": args.movetime,
        "max_plies": args.max_plies, "move_timeout": args.move_timeout,
        "resign_cp": args.resign, "resign_moves": args.resign_moves,
        "draw_cp": args.draw, "draw_moves": args.draw_moves, "draw_after": args.draw_after,
    }
    data.update({k: v for k, v in direct.items() if v is not None})

    if args.tc:
        data["base"], data["increment"] = parse_time_control(args.tc)
        data.pop("tc", None)
    if args.no_pairs:
        data["pair_openings"] = False

    # openings: merge CLI flags into whatever the config file had
    opening = data.get("openings", {})
    if isinstance(opening, str):
        from .config import OpeningConfig
        opening = OpeningConfig.from_string(opening).__dict__.copy()
    opening = dict(opening)
    if args.openings:
        from .config import OpeningConfig
        opening.update(OpeningConfig.from_string(args.openings).__dict__)
    if args.opening_plies is not None:
        opening["plies"] = args.opening_plies
    if args.max_imbalance is not None:
        opening["max_imbalance"] = args.max_imbalance
    if opening:
        data["openings"] = opening

    return MatchConfig.from_dict(data)


def cmd_run(args: argparse.Namespace) -> int:
    from .match import run_match
    cfg = build_config(args)
    run_match(cfg, REPO_ROOT)
    return 0


# ── openings ──────────────────────────────────────────────────────────────────

def cmd_openings(args: argparse.Namespace) -> int:
    from .openings import generate_openings, write_opening_file
    out = Path(args.out)
    print(f"Generating {args.count} openings ({args.plies} plies, max imbalance {args.max_imbalance}, seed {args.seed}) ...")
    fens = generate_openings(
        args.count, args.plies, args.seed, args.max_imbalance,
        progress=lambda done, total: print(f"  {done}/{total}", flush=True),
    )
    write_opening_file(out, fens, (
        f"Infinity Chess random openings: {args.count} positions, {args.plies} random plies from the start position,\n"
        f"material imbalance <= {args.max_imbalance}cp, seed {args.seed}. One FEN per line."))
    print(f"Wrote {len(fens)} openings to {out}")
    print(f"Use them with:  python -m arena run ... --openings {out}")
    return 0


# ── report / replay ───────────────────────────────────────────────────────────

def _load_run(path: str) -> tuple[list[GameRecord], list[str], Path]:
    p = Path(path)
    games_file = p if p.is_file() else p / "games.jsonl"
    folder = games_file.parent
    if not games_file.is_file():
        raise ConfigError(f"No games.jsonl found at {path}")
    records = [GameRecord.from_dict(json.loads(line))
               for line in games_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    names = ["A", "B"]
    cfg_file = folder / "config.json"
    if cfg_file.is_file():
        resolved = json.loads(cfg_file.read_text(encoding="utf-8")).get("resolved_engines", [])
        if len(resolved) == 2:
            names = [r.get("name") or r["package"] for r in resolved]
    return records, names, folder


def cmd_report(args: argparse.Namespace) -> int:
    records, names, _ = _load_run(args.path)
    print(stats.format_summary(stats.summarize(records, names)))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from infinity_chess.board import Board
    from infinity_chess.rules import InfinityChessRules

    records, names, _ = _load_run(args.path)
    by_index = {r.index + 1: r for r in records}
    if args.game not in by_index:
        raise ConfigError(f"Game {args.game} not found. Available: {min(by_index)}..{max(by_index)}")
    g = by_index[args.game]
    white, black = (names[0], names[1]) if g.a_is_white else (names[1], names[0])

    print(f"Game {args.game}: {white} (White) vs {black} (Black)   result {g.result} by {g.reason}")
    if g.error:
        print(f"  error: {g.error.splitlines()[0]}")
    print(f"Start FEN: {g.opening}\n")
    print(f"{'ply':>4}  {'side':<5} {'engine':<14} {'move':<7} {'depth':>5} {'score':>8} {'nodes':>9} {'time':>8}")

    board = Board.from_fen(g.opening)
    rules = InfinityChessRules()
    for m in g.moves:
        side = "White" if board.turn.value == "white" else "Black"
        score = f"M{m.mate:+d}" if m.mate is not None else ("" if m.score_cp is None else f"{m.score_cp:+d}")
        print(f"{m.ply:>4}  {side:<5} {names[m.engine]:<14} {m.move:<7} {m.depth:>5} {score:>8} "
              f"{m.nodes:>9,} {stats.fmt_seconds(m.time_s):>8}")
        for legal in rules.legal_moves(board, board.turn):
            if legal.to_uci() == m.move:
                board.make_move(legal)
                break
    print(f"\nFinal position:\n{board}\nFEN: {board.to_fen()}")
    return 0


# ── entry point ───────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m arena", description="Engine-vs-engine testing for Infinity Chess")
    sub = ap.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="play a match between two engines",
                         formatter_class=argparse.RawDescriptionHelpFormatter,
                         description="Play a match between two engines and report W/D/L, Elo and speed analytics.",
                         epilog="""examples:
  python -m arena run --engine engine:name=v2.3 --engine engine_v2_2:name=v2.2 --depth 3 -n 40 -j 4
  python -m arena run --engine engine:name=v2.3 --engine engine_v2_2:name=v2.2 --movetime 0.5 -n 100 -j 4
  python -m arena run --engine engine:name=v2.3 --engine engine_v2_2:name=v2.2 --tc 30+0.3 --openings arena/openings/random6.epd
  python -m arena run --config arena/configs/depth_match.json -n 10""")
    _add_run_args(run)
    run.set_defaults(func=cmd_run)

    op = sub.add_parser("openings", help="generate a file of random balanced openings")
    op.add_argument("--count", type=int, default=10000)
    op.add_argument("--plies", type=int, default=6)
    op.add_argument("--seed", type=int, default=1)
    op.add_argument("--max-imbalance", type=int, default=100)
    op.add_argument("--out", default="arena/openings/random.epd")
    op.set_defaults(func=cmd_openings)

    rep = sub.add_parser("report", help="summarise a results folder")
    rep.add_argument("path", help="results folder (or its games.jsonl)")
    rep.set_defaults(func=cmd_report)

    rp = sub.add_parser("replay", help="show one game move by move")
    rp.add_argument("path", help="results folder (or its games.jsonl)")
    rp.add_argument("--game", type=int, required=True, help="game number as shown in the progress lines (1-based)")
    rp.set_defaults(func=cmd_replay)
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except EngineError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
