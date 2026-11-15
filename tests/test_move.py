"""Unit tests for squares, normal moves, and special moves."""

import unittest

from infinity_chess.move import (
    CAPTURE_FLAGS,
    QUIESCENCE_FLAGS,
    Move,
    MoveFlag,
    SpecialMove,
    Square,
)


class SquareTests(unittest.TestCase):
    def test_algebraic_round_trip_supports_multi_digit_ranks(self) -> None:
        square = Square.from_algebraic("C12")
        self.assertEqual(square, Square(11, 2))
        self.assertEqual(square.to_algebraic(), "c12")
        self.assertEqual(repr(square), "Square(c12)")

    def test_square_offsets_do_not_mutate_the_source(self) -> None:
        source = Square(3, 4)
        self.assertEqual(source + (-2, 1), Square(1, 5))
        self.assertEqual(source, Square(3, 4))

    def test_short_square_notation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Square.from_algebraic("a")


class MoveTests(unittest.TestCase):
    def test_uci_round_trip_and_readable_representation(self) -> None:
        move = Move.from_uci("e2e4")
        self.assertEqual(move, Move(Square(1, 4), Square(3, 4)))
        self.assertEqual(move.to_uci(), "e2e4")
        self.assertEqual(repr(move), "Move(e2e4 [NORMAL])")

    def test_short_uci_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Move.from_uci("e2")

    def test_special_move_adds_correct_promotion_suffix(self) -> None:
        queen = SpecialMove(
            Square.from_algebraic("a7"),
            Square.from_algebraic("a8"),
            MoveFlag.PROMOTION,
            promotion_piece="QUEEN",
        )
        knight = SpecialMove(
            Square.from_algebraic("a7"),
            Square.from_algebraic("a8"),
            MoveFlag.PROMOTION,
            promotion_piece="KNIGHT",
        )
        self.assertEqual(queen.to_uci(), "a7a8q")
        self.assertEqual(knight.to_uci(), "a7a8n")

    def test_capture_and_quiescence_flag_sets_cover_special_captures(self) -> None:
        self.assertIn(MoveFlag.CAPTURE, CAPTURE_FLAGS)
        self.assertIn(MoveFlag.EN_PASSANT, CAPTURE_FLAGS)
        self.assertIn(MoveFlag.PROMOTION_CAPTURE, CAPTURE_FLAGS)
        self.assertIn(MoveFlag.PROMOTION, QUIESCENCE_FLAGS)
        self.assertNotIn(MoveFlag.CASTLE_KING, QUIESCENCE_FLAGS)


if __name__ == "__main__":
    unittest.main()
