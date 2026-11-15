"""Tests for Game's stateful player-facing workflow."""

import unittest

from infinity_chess.board import Board
from infinity_chess.game import Game
from infinity_chess.move import Square
from infinity_chess.pieces import Colour
from infinity_chess.rules import StandardRules


class GameTests(unittest.TestCase):
    def test_uci_moves_update_turn_history_and_serialized_state(self) -> None:
        game = Game(rules=StandardRules())

        self.assertTrue(game.make_move_uci("e2e4"))
        self.assertEqual(game.turn, Colour.BLACK)
        self.assertEqual(game.move_count, 1)
        self.assertEqual(game.to_fen(), "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")

        state = game.to_dict()
        self.assertEqual(state["turn"], "black")
        self.assertEqual(state["move_count"], 1)
        self.assertFalse(state["is_over"])
        self.assertIsNone(state["result"])

    def test_illegal_or_ambiguous_uci_does_not_change_game(self) -> None:
        game = Game(rules=StandardRules())
        initial_fen = game.to_fen()

        self.assertFalse(game.make_move_uci("e2e5"))
        self.assertFalse(game.make_move_uci("not-a-move"))
        self.assertEqual(game.to_fen(), initial_fen)
        self.assertEqual(game.move_count, 0)

    def test_fen_constructor_and_legal_moves_from_delegate_to_bound_generator(self) -> None:
        game = Game.from_fen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1", rules=StandardRules())

        self.assertEqual(game.legal_moves_from(Square.from_algebraic("e2"))[0].to_uci(), "e2e3")
        self.assertEqual({move.to_uci() for move in game.legal_moves_from(Square.from_algebraic("e2"))}, {"e2e3", "e2e4"})

    def test_game_records_checkmate_and_rejects_later_moves(self) -> None:
        board = Board.from_fen("7k/8/5KQ1/8/8/8/8/8 w - - 0 1")
        game = Game(rules=StandardRules(), board=board)

        self.assertTrue(game.make_move_uci("g6g7"))
        self.assertTrue(game.is_over)
        self.assertEqual(game.result, "white")
        self.assertFalse(game.make_move_uci("h8h7"))


if __name__ == "__main__":
    unittest.main()
