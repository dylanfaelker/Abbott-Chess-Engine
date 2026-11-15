"""Stable engine contract exercised against every released engine version."""

import unittest

from engine.search import MATE_SCORE, Search as CurrentSearch
from engine_v2_1.search import Search as V21Search
from engine_v2_2.search import Search as V22Search
from infinity_chess.board import Board
from infinity_chess.move_generator import MoveGenerator
from infinity_chess.rules import InfinityChessRules


ENGINE_VARIANTS = (
    ("v2.1", V21Search, False),
    ("v2.2", V22Search, True),
    ("current", CurrentSearch, True),
)


def make_search(search_type, supports_is_vary: bool, board: Board):
    """Build any released searcher with evaluation variation disabled when supported."""
    rules = InfinityChessRules()
    if supports_is_vary:
        return search_type(board, rules, isVary=False)
    return search_type(board, rules)


class EngineBasicContractTests(unittest.TestCase):
    MATE_IN_ONE = "k7/6K1/1Q6/8/8/8/8/7B w - - 0 1"
    WHITE_AHEAD = "4k3/8/8/8/8/8/8/4KQ2 w - - 0 1"
    BLACK_AHEAD = "4kq2/8/8/8/8/8/8/4K3 w - - 0 1"

    def test_every_version_finds_a_forced_mate_in_one(self) -> None:
        for name, search_type, supports_is_vary in ENGINE_VARIANTS:
            with self.subTest(engine=name):
                board = Board.from_fen(self.MATE_IN_ONE)
                original_fen = board.to_fen()
                search = make_search(search_type, supports_is_vary, board)

                move, score = search.find_best_move(1)

                self.assertIsNotNone(move)
                self.assertGreaterEqual(score, MATE_SCORE - 1)
                self.assertEqual(
                    MoveGenerator(board.apply_move(move), InfinityChessRules()).game_over(),
                    (True, "white"),
                )
                self.assertEqual(board.to_fen(), original_fen)

    def test_every_version_ranks_an_extra_white_queen_above_an_extra_black_queen(self) -> None:
        for name, search_type, supports_is_vary in ENGINE_VARIANTS:
            with self.subTest(engine=name):
                white_ahead = make_search(search_type, supports_is_vary, Board.from_fen(self.WHITE_AHEAD))
                black_ahead = make_search(search_type, supports_is_vary, Board.from_fen(self.BLACK_AHEAD))

                self.assertGreater(white_ahead.evaluator.evaluate(white_ahead.board), 0)
                self.assertLess(black_ahead.evaluator.evaluate(black_ahead.board), 0)

    def test_every_version_returns_a_legal_move_without_changing_the_position(self) -> None:
        for name, search_type, supports_is_vary in ENGINE_VARIANTS:
            with self.subTest(engine=name):
                board = Board.standard()
                original_fen = board.to_fen()
                original_hash = board.zobrist_hash()
                search = make_search(search_type, supports_is_vary, board)

                move, _ = search.find_best_move(1)

                self.assertIn(move, MoveGenerator(board, InfinityChessRules()).legal_moves())
                self.assertEqual(board.to_fen(), original_fen)
                self.assertEqual(board.zobrist_hash(), original_hash)


if __name__ == "__main__":
    unittest.main()
