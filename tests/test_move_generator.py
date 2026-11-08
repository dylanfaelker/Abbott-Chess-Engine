"""Integration tests for the Board/RuleSet facade used by engines and games."""

import unittest

from infinity_chess.board import Board
from infinity_chess.move import Move, Square
from infinity_chess.move_generator import MoveGenerator
from infinity_chess.pieces import Colour
from infinity_chess.rules import InfinityChessRules, StandardRules


class MoveGeneratorTests(unittest.TestCase):
    def test_default_generator_uses_infinity_rules_and_initial_position_has_twenty_moves(self) -> None:
        generator = MoveGenerator(Board.standard())
        self.assertIsInstance(generator.rules, InfinityChessRules)
        self.assertEqual(len(generator.legal_moves()), 20)

    def test_legal_moves_from_empty_and_occupied_squares(self) -> None:
        board = Board.standard()
        generator = MoveGenerator(board, StandardRules())

        self.assertEqual(generator.legal_moves_from(Square.from_algebraic("e4")), [])
        self.assertEqual(
            {move.to_uci() for move in generator.legal_moves_from(Square.from_algebraic("e2"))},
            {"e2e3", "e2e4"},
        )

    def test_pseudo_moves_and_attacks_are_available_without_legal_filtering(self) -> None:
        board = Board.from_fen("4k3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        generator = MoveGenerator(board, StandardRules())

        self.assertIn("e2e8", {move.to_uci() for move in generator.pseudo_legal_moves(Square.from_algebraic("e2"))})
        self.assertTrue(generator.is_square_attacked(Square.from_algebraic("e8"), Colour.WHITE))
        self.assertFalse(generator.is_in_check(Colour.WHITE))

    def test_apply_move_returns_a_new_generator_and_preserves_original_board(self) -> None:
        generator = MoveGenerator(Board.standard(), StandardRules())
        updated = generator.apply_move(Move.from_uci("e2e4"))

        self.assertIsNot(updated.board, generator.board)
        self.assertEqual(generator.board.to_fen().split()[1], "w")
        self.assertEqual(updated.board.to_fen().split()[1], "b")
        self.assertIn("e7e5", {move.to_uci() for move in updated.legal_moves()})

    def test_terminal_status_can_reuse_precomputed_legal_moves(self) -> None:
        board = Board.from_fen("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1")
        generator = MoveGenerator(board, StandardRules())
        legal_moves = generator.legal_moves()

        self.assertEqual(legal_moves, [])
        self.assertEqual(generator.game_over(legal_moves), (True, "white"))


if __name__ == "__main__":
    unittest.main()
