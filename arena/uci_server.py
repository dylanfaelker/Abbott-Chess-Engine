#!/usr/bin/env python3
"""
arena/uci_server.py

A UCI-style front end for the Infinity Chess engines. The arena starts one of
these per engine per game and talks to it over stdin/stdout, so engines are
fully isolated from each other (no shared memory, no shared module state) and
can be killed if they hang.

Run by hand to poke at an engine:

    python arena/uci_server.py --engine engine
    > uci
    > position startpos moves e2e4
    > go depth 3
    < info depth 3 score cp 25 nodes 2612 time 1870 nps 1396 pv d7d5
    < bestmove d7d5

This file is deliberately standalone (standard library + the repo's own modules)
so `--root` can point at a *different checkout* (e.g. a git worktree of an older
commit) and both the engine and the game rules are loaded from there.

Dialect
-------
Standard UCI, with the parts that make no sense for this game left out and one
extension:

    uci / isready / ucinewgame / quit            as usual
    setoption name Vary value true|false         engine's random eval noise (isVary)
    setoption name Seed value N                  seeds Python's `random` for reproducibility
    setoption name Horizon value N               moves assumed left when managing a clock
    position startpos|fen <FEN> [moves m1 m2 ..] FEN may be any position of this variant
    go [depth N] [movetime MS]
       [wtime MS btime MS winc MS binc MS movestogo N]
    (no `stop`: the search is synchronous; the arena kills the process on timeout)

    info string caps timelimit=0|1               extension, sent during the handshake:
                                                 does this engine's Search accept time_limit?

Engine contract (what `<package>/search.py` must provide)
---------------------------------------------------------
    Search(board, rules, [isVary])
    Search.find_best_move(depth, [time_limit])   -> (Move | None, score)
        time_limit is in seconds; the search must return the best move from the
        last completed iteration when it expires. `score` is in centipawns from the
        side to move's point of view (negamax), mate = +-(MATE_SCORE - plies).
    Search.nodes_searched                        (optional) nodes visited by the last search
    Search.depth_reached                         (optional) deepest completed iteration
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import math
import os
import random
import re
import sys
import time
import traceback

DEFAULT_DEPTH = 2          # used when `go` carries no limit at all (matches the /move endpoint)
UNLIMITED_DEPTH = 64       # depth ceiling when only a time limit is given
DEFAULT_HORIZON = 30       # moves assumed left when managing a clock
MIN_BUDGET_MS = 10         # never allocate less than this per move

_UCI_MOVE = re.compile(r"^([a-z])(\d+)([a-z])(\d+)([qrbn]?)$")


def out(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def log_err(line: str) -> None:
    sys.stderr.write(line + "\n")
    sys.stderr.flush()


class UciServer:
    def __init__(self, package: str, name: str | None = None):
        # Imported here, after main() has put the chosen repo root on sys.path.
        from infinity_chess.board import Board
        from infinity_chess.move import Square
        from infinity_chess.pieces import Colour
        from infinity_chess.rules import InfinityChessRules

        self.Board, self.Square, self.Colour = Board, Square, Colour
        self.rules = InfinityChessRules()

        module = importlib.import_module(f"{package}.search")
        self.Search = module.Search
        self.mate_score = getattr(module, "MATE_SCORE", 100_000_000)
        self.name = name or package

        init_params = inspect.signature(self.Search.__init__).parameters
        find_params = inspect.signature(self.Search.find_best_move).parameters
        self.accepts_vary = "isVary" in init_params
        self.supports_time = "time_limit" in find_params

        self.vary = True
        self.horizon = DEFAULT_HORIZON
        self.board = Board.standard()

    # ── command loop ──────────────────────────────────────────────────────

    def run(self) -> None:
        while True:
            line = sys.stdin.readline()
            if not line:            # arena closed the pipe
                return
            tokens = line.split()
            if not tokens:
                continue
            cmd, args = tokens[0], tokens[1:]
            if cmd == "uci":
                self.cmd_uci()
            elif cmd == "isready":
                out("readyok")
            elif cmd == "setoption":
                self.cmd_setoption(args)
            elif cmd == "ucinewgame":
                self.board = self.Board.standard()
            elif cmd == "position":
                self.cmd_position(args)
            elif cmd == "go":
                self.cmd_go(args)
            elif cmd == "quit":
                return
            # anything else is ignored, as UCI requires

    def cmd_uci(self) -> None:
        out(f"id name {self.name}")
        out("id author Abbott Chess Engine arena")
        out("option name Vary type check default true")
        out("option name Seed type spin default 0 min 0 max 2147483647")
        out(f"option name Horizon type spin default {DEFAULT_HORIZON} min 1 max 500")
        out(f"info string caps timelimit={1 if self.supports_time else 0}")
        out("uciok")

    def cmd_setoption(self, args: list[str]) -> None:
        # setoption name <name...> [value <value...>]
        try:
            name_i = args.index("name")
        except ValueError:
            return
        value_i = args.index("value") if "value" in args else len(args)
        name = " ".join(args[name_i + 1:value_i]).lower()
        value = " ".join(args[value_i + 1:])
        if name == "vary":
            self.vary = value.strip().lower() in ("true", "1", "yes", "on")
        elif name == "seed":
            random.seed(int(value))
        elif name == "horizon":
            self.horizon = max(1, int(value))

    # ── position ──────────────────────────────────────────────────────────

    def cmd_position(self, args: list[str]) -> None:
        if not args:
            return
        if "moves" in args:
            split = args.index("moves")
            head, moves = args[:split], args[split + 1:]
        else:
            head, moves = args, []

        if head[0] == "startpos":
            board = self.Board.standard()
        elif head[0] == "fen":
            board = self.Board.from_fen(" ".join(head[1:]))
        else:
            raise ValueError(f"Bad position command: {' '.join(args)}")

        for uci in moves:
            self.apply_uci(board, uci)
        self.board = board

    def apply_uci(self, board, uci: str) -> None:
        """
        Apply a move the arena has already validated. Only the moving piece's
        pseudo-legal moves are generated, which keeps replaying a long move list cheap.
        """
        m = _UCI_MOVE.match(uci)
        if not m:
            raise ValueError(f"Malformed move {uci!r}")
        from_sq = self.Square(int(m.group(2)) - 1, ord(m.group(1)) - ord("a"))
        for move in self.rules.pseudo_legal_moves(board, from_sq):
            if move.to_uci() == uci:
                board.make_move(move)
                return
        raise ValueError(f"Move {uci!r} is not possible in position {board.to_fen()}")

    # ── go ────────────────────────────────────────────────────────────────

    def cmd_go(self, args: list[str]) -> None:
        started = time.perf_counter()

        params: dict[str, int] = {}
        i = 0
        while i < len(args):
            if args[i] in ("depth", "movetime", "wtime", "btime", "winc", "binc", "movestogo") and i + 1 < len(args):
                params[args[i]] = int(args[i + 1])
                i += 2
            else:
                i += 1

        time_limit = self.time_limit_seconds(params)
        depth = params.get("depth")
        if depth is None:
            depth = UNLIMITED_DEPTH if time_limit is not None else DEFAULT_DEPTH

        kwargs = {}
        if time_limit is not None:
            if self.supports_time:
                kwargs["time_limit"] = time_limit
            else:
                out("info string warning: engine has no time_limit support, searching to fixed depth")
                if "depth" not in params:
                    depth = DEFAULT_DEPTH

        search_kwargs = {"isVary": self.vary} if self.accepts_vary else {}
        # Search on a copy so self.board stays exactly as `position` left it.
        searcher = self.Search(self.board.copy(), self.rules, **search_kwargs)
        move, score = searcher.find_best_move(depth, **kwargs)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        nodes = int(getattr(searcher, "nodes_searched", 0) or 0)
        reached = int(getattr(searcher, "depth_reached", depth) or 0)
        nps = int(nodes * 1000 / elapsed_ms) if elapsed_ms > 0 else 0

        if move is None:
            out("bestmove 0000")
            return
        out(f"info depth {reached} score {self.format_score(score)} nodes {nodes} "
            f"time {elapsed_ms} nps {nps} pv {move.to_uci()}")
        out(f"bestmove {move.to_uci()}")

    def time_limit_seconds(self, params: dict[str, int]) -> float | None:
        """Turn movetime / clock parameters into a soft per-move limit in seconds."""
        if "movetime" in params:
            return max(params["movetime"], MIN_BUDGET_MS) / 1000.0
        white = self.board.turn == self.Colour.WHITE
        remaining = params.get("wtime" if white else "btime")
        if remaining is None:
            return None
        increment = params.get("winc" if white else "binc", 0)
        horizon = params.get("movestogo") or self.horizon
        budget = remaining / horizon + 0.8 * increment
        budget = min(budget, remaining * 0.5)       # never plan to burn more than half the clock
        return max(budget, MIN_BUDGET_MS) / 1000.0

    def format_score(self, score) -> str:
        if score is None or (isinstance(score, float) and math.isinf(score)):
            return "cp 0"
        s = int(score)
        if abs(s) >= self.mate_score - 10_000:
            plies = self.mate_score - abs(s)
            moves = (plies + 1) // 2
            return f"mate {moves if s > 0 else -moves}"
        return f"cp {s}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="UCI front end for an Infinity Chess engine package")
    ap.add_argument("--engine", required=True, help="package at the repo root, e.g. engine or engine_v2_2")
    ap.add_argument("--root", default=None, help="repo root to load code from (default: the repo this file is in)")
    ap.add_argument("--name", default=None, help="name reported in 'id name'")
    args = ap.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(args.root) if args.root else os.path.dirname(here)
    # Keep this folder off sys.path (so its module names can't shadow anything) and put the root first.
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != here]
    sys.path.insert(0, root)

    try:
        server = UciServer(args.engine, args.name)
        server.run()
    except KeyboardInterrupt:
        return 0
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
