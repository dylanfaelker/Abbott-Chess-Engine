"""
arena/openings.py

Start positions for matches.

Infinity Chess has no opening theory (horizontal wrapping changes the tactics
from move one, so a normal chess book would be misleading). Instead openings
are generated: a handful of random legal half-moves from the starting position,
kept only if the position is playable, i.e.

    * the game is not already over and the side to move is not in check, and
    * material is roughly balanced (|difference| <= max_imbalance centipawns),
      so one side has not simply been handed a free queen by the dice, and
    * the side to move has no winning capture available (nothing is hanging),
      so the opening itself does not decide the game.

Generation is deterministic for a given seed and positions are de-duplicated.
You can also supply your own list: one FEN or EPD per line, `#` for comments.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Callable, Optional

from infinity_chess.board import Board
from infinity_chess.move import CAPTURE_FLAGS
from infinity_chess.pieces import Colour, PieceType
from infinity_chess.rules import InfinityChessRules

from .config import ConfigError, OpeningConfig

# Local copy of the piece values (centipawns) so this module does not depend on any engine.
_MATERIAL = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 300,
    PieceType.BISHOP: 400,   # Infinity Chess: bishops are worth more because of wrapping
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
}


STALE_LIMIT = 3000   # give up after this many consecutive useless attempts


def start_fen() -> str:
    return Board.standard().to_fen()


def material_balance(board: Board) -> int:
    """White material minus black material in centipawns (kings excluded)."""
    total = 0
    for colour, sign in ((Colour.WHITE, 1), (Colour.BLACK, -1)):
        for piece_type, value in _MATERIAL.items():
            total += sign * value * board.piece_bitboard(colour, piece_type).bit_count()
    return total


def _dedupe_key(fen: str) -> str:
    """Position identity: placement, side to move, castling, en passant (no move counters)."""
    return " ".join(fen.split()[:4])


def has_winning_capture(board: Board, rules: InfinityChessRules, moves: list, threshold: int = 100) -> bool:
    """
    True if the side to move can win at least `threshold` centipawns with a single
    capture: it takes a piece worth more than the capturer, or takes something the
    opponent cannot recapture. A cheap stand-in for static exchange evaluation.
    """
    for move in moves:
        if move.flag not in CAPTURE_FLAGS:
            continue
        victim_sq = getattr(move, "captured_sq", None) or move.to_sq
        victim = board.get(victim_sq)
        mover = board.get(move.from_sq)
        if victim is None or mover is None:
            continue
        gain = _MATERIAL.get(victim.piece_type, 0)
        undo = board.make_move(move)
        try:
            if rules.is_square_attacked(board, move.to_sq, board.turn):   # board.turn is now the opponent
                gain -= _MATERIAL.get(mover.piece_type, 0)
        finally:
            board.unmake_move(undo)
        if gain >= threshold:
            return True
    return False


# ── random generation ─────────────────────────────────────────────────────────

def random_opening(
    rng: random.Random,
    plies: int,
    max_imbalance: int = 100,
    rules: Optional[InfinityChessRules] = None,
) -> Optional[str]:
    """
    Play `plies` random legal half-moves from the start position.
    Returns the FEN, or None if the result is rejected as unplayable/unbalanced.
    """
    rules = rules or InfinityChessRules()
    board = Board.standard()
    for _ in range(plies):
        moves = list(rules.legal_moves(board, board.turn))
        if not moves:
            return None
        board.make_move(rng.choice(moves))

    moves = list(rules.legal_moves(board, board.turn))
    over, _ = rules.game_over(board, moves)
    if over or rules.is_in_check(board, board.turn):
        return None
    if abs(material_balance(board)) > max_imbalance:
        return None
    if has_winning_capture(board, rules, moves):
        return None      # someone left a piece hanging; the opening would decide the game
    return board.to_fen()


def generate_openings(
    count: int,
    plies: int = 6,
    seed: int = 0,
    max_imbalance: int = 100,
    progress: Optional[Callable[[int, int], None]] = None,
) -> list[str]:
    """
    Generate `count` distinct balanced openings. Same arguments -> same list.

    Gives up with an error if the position space is exhausted (e.g. asking for
    5,000 distinct 2-ply openings).
    """
    rng = random.Random(seed)
    rules = InfinityChessRules()
    seen: set[str] = set()
    out: list[str] = []
    stale = 0   # consecutive attempts that produced nothing new (rejected or duplicate)
    while len(out) < count:
        fen = random_opening(rng, plies, max_imbalance, rules)
        key = _dedupe_key(fen) if fen else None
        if fen is None or key in seen:
            stale += 1
            if stale >= STALE_LIMIT:
                raise ConfigError(
                    f"Could only generate {len(out)} distinct openings of {plies} plies "
                    f"(max imbalance {max_imbalance}); the space looks exhausted. "
                    f"Use more plies or a larger max imbalance."
                )
            continue
        stale = 0
        seen.add(key)
        out.append(fen)
        if progress and len(out) % 250 == 0:
            progress(len(out), count)
    return out


# ── files ─────────────────────────────────────────────────────────────────────

def _normalise_line(line: str) -> Optional[str]:
    """FEN or EPD line -> full 6-field FEN, or None for blanks/comments."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split()
    if len(parts) < 4:
        raise ValueError(f"expected at least 4 fields (placement, side, castling, en passant): {line!r}")
    if len(parts) >= 6 and parts[4].isdigit() and parts[5].isdigit():
        return " ".join(parts[:6])
    return " ".join(parts[:4]) + " 0 1"      # EPD: drop opcodes, add move counters


def load_opening_file(path: str | Path) -> list[str]:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Opening file not found: {path}")
    fens = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            fen = _normalise_line(raw)
        except ValueError as e:
            raise ConfigError(f"{path}:{number}: {e}") from None
        if fen:
            fens.append(fen)
    if not fens:
        raise ConfigError(f"{path} contains no positions")
    return fens


def write_opening_file(path: str | Path, fens: list[str], header: str = "") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {h}" for h in header.splitlines()] if header else []
    path.write_text("\n".join(lines + fens) + "\n", encoding="utf-8")


def check_opening(fen: str, rules: Optional[InfinityChessRules] = None) -> None:
    """Raise ValueError if `fen` cannot be played from (unparseable or already over)."""
    rules = rules or InfinityChessRules()
    board = Board.from_fen(fen)
    over, result = rules.game_over(board, list(rules.legal_moves(board, board.turn)))
    if over:
        raise ValueError(f"game is already over ({result})")


# ── selection used by the match runner ────────────────────────────────────────

def build_openings(cfg: OpeningConfig, count: int, seed: int) -> list[str]:
    """Return `count` start positions according to `cfg` (deterministic for a seed)."""
    if cfg.source == "start":
        return [start_fen()] * count

    if cfg.source == "random":
        return generate_openings(count, cfg.plies, seed, cfg.max_imbalance)

    book = load_opening_file(cfg.file)           # source == "file"
    rng = random.Random(seed)
    picked: list[str] = []
    while len(picked) < count:                   # cycles (reshuffled) if the file is smaller than count
        batch = book[:]
        rng.shuffle(batch)
        picked.extend(batch[: count - len(picked)])
    rules = InfinityChessRules()
    for fen in picked:
        try:
            check_opening(fen, rules)
        except Exception as e:
            raise ConfigError(f"Bad opening in {cfg.file}: {fen!r}: {e}") from None
    return picked
