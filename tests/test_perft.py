"""
Perft tests for StandardRules.

Perft counts the leaf nodes of the legal-move tree to a fixed depth. For
orthodox chess the correct numbers are well known, so any mismatch points at a
move-generation bug (castling, en passant, promotion, pins, checks...).

Reference values: https://www.chessprogramming.org/Perft_Results

Run from the repository root:

    python -m unittest tests.test_perft -v

Deeper (slow in pure Python) depths are skipped unless you opt in:

    set PERFT_DEEP=1        (PowerShell: $env:PERFT_DEEP = "1")
    python -m unittest tests.test_perft -v

Only StandardRules is tested here. InfinityChessRules wraps files, so the
orthodox numbers do not apply to it.
"""

import os
import unittest

from infinity_chess.board import Board
from infinity_chess.pieces import PieceType
from infinity_chess.rules import StandardRules

DEEP = os.environ.get("PERFT_DEEP") == "1"


def perft(board: Board, rules: StandardRules, depth: int) -> int:
    """
    Count leaf nodes of the legal-move tree.

    Uses bulk counting at depth 1 (the number of legal moves is the number of
    leaves), which avoids a make/unmake for every leaf.
    """
    if depth == 0:
        return 1
    moves = list(rules.legal_moves(board, board.turn))
    if depth == 1:
        return len(moves)

    total = 0
    for move in moves:
        undo = board.make_move(move)
        try:
            total += perft(board, rules, depth - 1)
        finally:
            board.unmake_move(undo)
    return total


def perft_divide(board: Board, rules: StandardRules, depth: int) -> dict[str, int]:
    """Per-root-move node counts. Compare against a reference engine to find a bug."""
    result: dict[str, int] = {}
    for move in list(rules.legal_moves(board, board.turn)):
        undo = board.make_move(move)
        try:
            result[move.to_uci()] = perft(board, rules, depth - 1)
        finally:
            board.unmake_move(undo)
    return result


# (name, fen, {depth: expected nodes}, {deeper depth: expected nodes})
# The second dict only runs with PERFT_DEEP=1.
POSITIONS = (
    (
        "start position",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        {1: 20, 2: 400, 3: 8_902},
        {4: 197_281},
    ),
    (
        "kiwipete (castling, pins, en passant, promotions)",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        {1: 48, 2: 2_039},
        {3: 97_862},
    ),
    (
        "position 3 (en passant discovered checks, endgame)",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        {1: 14, 2: 191, 3: 2_812, 4: 43_238},
        {5: 674_624},
    ),
    (
        "position 4 (promotions, castling into/out of check)",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        {1: 6, 2: 264},
        {3: 9_467},
    ),
    (
        "position 4 mirrored (black to move)",
        "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1",
        {1: 6, 2: 264},
        {3: 9_467},
    ),
    (
        "position 5 (promotion with check, discovered attacks)",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        {1: 44, 2: 1_486},
        {3: 62_379},
    ),
    (
        "position 6 (symmetrical middlegame)",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
        {1: 46, 2: 2_079},
        {3: 89_890},
    ),
)


class PerftTests(unittest.TestCase):
    """Node counts for the standard perft suite."""

    def setUp(self) -> None:
        self.rules = StandardRules()

    def _check(self, name: str, fen: str, depth: int, expected: int) -> None:
        board = Board.from_fen(fen)
        fen_before, hash_before = board.to_fen(), board.zobrist_hash()
        history_before = list(board.zobrist_history)

        actual = perft(board, self.rules, depth)

        if actual != expected:
            divide = perft_divide(board, self.rules, depth)
            breakdown = "\n".join(f"  {uci}: {count}" for uci, count in sorted(divide.items()))
            self.fail(
                f"{name}, depth {depth}: expected {expected:,} nodes, got {actual:,}\n"
                f"FEN: {fen}\nPer-move breakdown:\n{breakdown}"
            )

        # perft must leave the board exactly as it found it
        self.assertEqual(board.to_fen(), fen_before, f"{name}: FEN changed after perft")
        self.assertEqual(board.zobrist_hash(), hash_before, f"{name}: hash changed after perft")
        self.assertEqual(board.zobrist_history, history_before, f"{name}: hash history changed")
        self.assertEqual(board.hash, board.recompute_hash(), f"{name}: incremental hash drifted")

    def test_standard_depths(self) -> None:
        for name, fen, expected, _deep in POSITIONS:
            for depth, nodes in expected.items():
                with self.subTest(position=name, depth=depth):
                    self._check(name, fen, depth, nodes)

    @unittest.skipUnless(DEEP, "set PERFT_DEEP=1 to run the slow, deeper perft depths")
    def test_deep_depths(self) -> None:
        for name, fen, _expected, deep in POSITIONS:
            for depth, nodes in deep.items():
                with self.subTest(position=name, depth=depth):
                    self._check(name, fen, depth, nodes)


class PerftSpecialMoveTests(unittest.TestCase):
    """Small hand-checkable positions that isolate one rule each."""

    def setUp(self) -> None:
        self.rules = StandardRules()

    def _count(self, fen: str, depth: int) -> int:
        return perft(Board.from_fen(fen), self.rules, depth)

    def test_promotion_generates_four_choices_per_move(self) -> None:
        # White pawn on a7: a8 promotion x4, plus king moves. Black king far away.
        board = Board.from_fen("7k/P7/8/8/8/8/8/4K3 w - - 0 1")
        moves = list(self.rules.legal_moves(board, board.turn))
        promos = [m for m in moves if m.promotion_piece]
        self.assertEqual(len(promos), 4)
        self.assertEqual(len(moves), 4 + 5)  # 4 promotions + 5 king moves

    def test_castling_both_sides_available(self) -> None:
        # 19 rook moves + 5 king moves + 2 castles (known perft(1) = 26).
        board = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        self.assertEqual(len(list(self.rules.legal_moves(board, board.turn))), 26)

    def test_castling_blocked_by_attacked_transit_square(self) -> None:
        # Black rook on f8 attacks f1, so white cannot castle kingside, only queenside.
        board = Board.from_fen("4kr2/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        castles = [m for m in self.rules.legal_moves(board, board.turn) if abs(m.to_sq.file - m.from_sq.file) == 2
                   and board.get(m.from_sq).piece_type is PieceType.KING]
        self.assertEqual({m.to_uci() for m in castles}, {"e1c1"})

    def test_en_passant_that_exposes_the_king_is_illegal(self) -> None:
        # Capturing e5xd6 would remove both pawns from rank 5 and expose the white king to the rook.
        board = Board.from_fen("8/8/8/KpP4r/8/8/8/7k w - b6 0 1")
        ucis = {m.to_uci() for m in self.rules.legal_moves(board, board.turn)}
        self.assertNotIn("c5b6", ucis)

    def test_stalemate_and_checkmate_have_zero_moves(self) -> None:
        self.assertEqual(self._count("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", 1), 0)  # stalemate
        self.assertEqual(self._count("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1", 1), 0)  # checkmate


if __name__ == "__main__":
    unittest.main()
