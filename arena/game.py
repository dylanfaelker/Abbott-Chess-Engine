"""
arena/game.py

The referee. Plays ONE game between two engine processes.

The referee owns the truth about the position: it validates every move the
engines send against the real rules (infinity_chess), detects mate / stalemate /
draws, keeps the clocks, and applies adjudication. Engines only ever see
`position ... moves ...` + `go ...`.

Terminology: engine "A" is engines[0] and engine "B" is engines[1] in the config,
whichever colour they happen to have in a given game.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

from infinity_chess.board import Board
from infinity_chess.pieces import Colour
from infinity_chess.rules import InfinityChessRules

from .config import EngineConfig, MatchConfig
from .uci_client import (
    EngineCrash, EngineError, EngineStartupError, EngineTimeout, UciEngine,
)

CLOCK_GRACE_S = 1.0        # extra wait beyond an engine's remaining clock before we kill it
MOVETIME_SLACK_S = 5.0     # a movetime engine is killed after 3 * movetime + this


class GameAborted(Exception):
    """The match was interrupted; this game is discarded."""


# ── records ───────────────────────────────────────────────────────────────────

@dataclass
class MoveRecord:
    ply: int                       # 1-based half-move number within the game (after the opening)
    engine: int                    # 0 = engine A, 1 = engine B
    move: str                      # UCI
    depth: int = 0                 # deepest completed iteration (0 if unreported)
    score_cp: Optional[int] = None # engine's own evaluation, side-to-move perspective; mate = +-32000
    mate: Optional[int] = None
    nodes: int = 0                 # 0 if the engine does not report nodes
    time_s: float = 0.0            # wall time measured by the arena


@dataclass
class GameRecord:
    index: int
    opening: str                   # FEN the game started from
    a_is_white: bool
    result: str                    # "1-0", "0-1" or "1/2-1/2"
    reason: str                    # checkmate, stalemate, fifty-move rule, repetition, ...
    moves: list[MoveRecord] = field(default_factory=list)
    duration_s: float = 0.0
    error: str = ""                # engine failure details, if the game ended that way

    @property
    def score_a(self) -> float:
        """Result from engine A's point of view: 1, 0.5 or 0."""
        if self.result == "1/2-1/2":
            return 0.5
        a_won = (self.result == "1-0") == self.a_is_white
        return 1.0 if a_won else 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameRecord":
        data = dict(data)
        data["moves"] = [MoveRecord(**m) for m in data.get("moves", [])]
        return cls(**data)


# ── helpers ───────────────────────────────────────────────────────────────────

def engine_seed(match_seed: int, game_index: int, engine_index: int) -> int:
    """Stable per-game, per-engine seed (independent streams for the two engines)."""
    return random.Random(f"{match_seed}:{game_index}:{engine_index}").randrange(2**31)


def describe_draw(board: Board, rules: InfinityChessRules, legal_count: int) -> str:
    """Why `rules.game_over` reported a draw (same order of checks as the rules)."""
    if legal_count == 0:
        return "stalemate"
    if board.halfmove_clock >= 100:
        return "fifty-move rule"
    if rules._is_insufficient_material(board):
        return "insufficient material"
    return "repetition"


def _go_command(
    ecfg: EngineConfig,
    engines: list[EngineConfig],
    idx: int,
    colour: Colour,
    clocks: list[Optional[float]],
    move_timeout: float,
) -> tuple[str, float]:
    """Build the `go` arguments and the hard timeout (seconds) for one move."""
    parts: list[str] = []
    if ecfg.depth is not None:
        parts += ["depth", str(ecfg.depth)]

    if ecfg.movetime is not None:
        parts += ["movetime", str(max(1, round(ecfg.movetime * 1000)))]
        timeout = ecfg.movetime * 3 + MOVETIME_SLACK_S
    elif ecfg.base is not None:
        own = clocks[idx]
        opp_clock = clocks[1 - idx]
        opp = opp_clock if opp_clock is not None else own
        own_ms, opp_ms = round(own * 1000), round(opp * 1000)
        own_inc = round(ecfg.increment * 1000)
        opp_inc = round(engines[1 - idx].increment * 1000)
        if colour is Colour.WHITE:
            parts += ["wtime", str(own_ms), "btime", str(opp_ms), "winc", str(own_inc), "binc", str(opp_inc)]
        else:
            parts += ["wtime", str(opp_ms), "btime", str(own_ms), "winc", str(opp_inc), "binc", str(own_inc)]
        timeout = own + CLOCK_GRACE_S
    else:
        timeout = move_timeout
    return " ".join(parts), timeout


# ── the game ──────────────────────────────────────────────────────────────────

def play_game(
    index: int,
    opening_fen: str,
    a_is_white: bool,
    cfg: MatchConfig,
    engines: list[EngineConfig],
    repo_root: Path,
    stop: threading.Event,
) -> GameRecord:
    """
    Play one game. Raises EngineStartupError if an engine cannot be started
    (a configuration problem, not a game result) and GameAborted if `stop` is set.
    """
    rules = InfinityChessRules()
    board = Board.from_fen(opening_fen)
    white_idx = 0 if a_is_white else 1
    idx_of = {Colour.WHITE: white_idx, Colour.BLACK: 1 - white_idx}

    procs: dict[int, UciEngine] = {}
    records: list[MoveRecord] = []
    played: list[str] = []
    clocks: list[Optional[float]] = [e.base for e in engines]
    resign_streak = [0, 0]
    draw_streak = 0
    started = time.perf_counter()
    error = ""

    def winner_result(winner_idx: int) -> str:
        return "1-0" if winner_idx == white_idx else "0-1"

    result, reason = "1/2-1/2", ""
    try:
        for i, ecfg in enumerate(engines):
            procs[i] = UciEngine(ecfg, repo_root, seed=engine_seed(cfg.seed or 0, index, i))
            procs[i].start()
            procs[i].new_game()

        while True:
            if stop.is_set():
                raise GameAborted()

            legal = list(rules.legal_moves(board, board.turn))
            over, winner = rules.game_over(board, legal)
            if over:
                if winner in ("white", "black"):
                    result = "1-0" if winner == "white" else "0-1"
                    reason = "checkmate"
                else:
                    result, reason = "1/2-1/2", describe_draw(board, rules, len(legal))
                break
            if len(played) >= cfg.max_plies:
                result, reason = "1/2-1/2", "max plies"
                break

            colour = board.turn
            idx = idx_of[colour]
            ecfg, eng = engines[idx], procs[idx]
            go_args, timeout = _go_command(ecfg, engines, idx, colour, clocks, cfg.move_timeout)

            try:
                eng.set_position(opening_fen, played)
                res = eng.go(go_args, timeout)
            except EngineTimeout:
                if clocks[idx] is not None:
                    result, reason = winner_result(1 - idx), "loss on time"
                else:
                    result, reason = winner_result(1 - idx), "engine timeout"
                error = f"{ecfg.label} did not answer within {timeout:.1f}s"
                break
            except EngineCrash as e:
                if stop.is_set():
                    raise GameAborted() from None
                result, reason = winner_result(1 - idx), "engine crash"
                error = str(e)
                break

            move = next((m for m in legal if m.to_uci() == res.bestmove), None)
            if move is None:
                result, reason = winner_result(1 - idx), "illegal move"
                error = f"{ecfg.label} played {res.bestmove!r} in {board.to_fen()}"
                break

            if clocks[idx] is not None:
                clocks[idx] -= res.wall_s
                if clocks[idx] <= 0:
                    result, reason = winner_result(1 - idx), "loss on time"
                    error = f"{ecfg.label} flagged ({clocks[idx]:.2f}s left)"
                    records.append(_record(len(played) + 1, idx, res))
                    played.append(res.bestmove)
                    break
                clocks[idx] += ecfg.increment

            board.make_move(move)
            played.append(res.bestmove)
            records.append(_record(len(played), idx, res))

            # ── adjudication (both off unless configured) ──
            score = res.score_cp
            if cfg.resign_cp is not None:
                resign_streak[idx] = resign_streak[idx] + 1 if (score is not None and score <= -cfg.resign_cp) else 0
                if resign_streak[idx] >= cfg.resign_moves:
                    result, reason = winner_result(1 - idx), "adjudicated resignation"
                    break
            if cfg.draw_cp is not None:
                draw_streak = draw_streak + 1 if (score is not None and abs(score) <= cfg.draw_cp) else 0
                if len(played) >= cfg.draw_after and draw_streak >= 2 * cfg.draw_moves:
                    result, reason = "1/2-1/2", "adjudicated draw"
                    break
    finally:
        for p in procs.values():
            p.close()

    return GameRecord(
        index=index, opening=opening_fen, a_is_white=a_is_white,
        result=result, reason=reason, moves=records,
        duration_s=time.perf_counter() - started, error=error,
    )


def _record(ply: int, engine_idx: int, res) -> MoveRecord:
    return MoveRecord(
        ply=ply, engine=engine_idx, move=res.bestmove, depth=res.depth,
        score_cp=res.score_cp, mate=res.mate, nodes=res.nodes, time_s=round(res.wall_s, 4),
    )
