"""Unit tests for immutable piece values and their enums."""

from dataclasses import FrozenInstanceError
import unittest

from infinity_chess.pieces import (
    B_KING,
    W_QUEEN,
    Colour,
    Piece,
    PieceType,
    make_piece,
)


class ColourTests(unittest.TestCase):
    def test_opponents_and_display_values(self) -> None:
        self.assertIs(Colour.WHITE.opponent(), Colour.BLACK)
        self.assertIs(Colour.BLACK.opponent(), Colour.WHITE)
        self.assertEqual(repr(Colour.WHITE), "white")


class PieceTypeTests(unittest.TestCase):
    def test_symbols_round_trip_for_every_piece_type(self) -> None:
        for piece_type in PieceType:
            with self.subTest(piece_type=piece_type):
                self.assertIs(PieceType.from_symbol(piece_type.symbol()), piece_type)
                self.assertIs(PieceType.from_symbol(piece_type.symbol().upper()), piece_type)

    def test_sliding_piece_classification_and_invalid_symbol(self) -> None:
        self.assertTrue(PieceType.QUEEN.is_sliding())
        self.assertTrue(PieceType.ROOK.is_sliding())
        self.assertTrue(PieceType.BISHOP.is_sliding())
        self.assertFalse(PieceType.KNIGHT.is_sliding())
        self.assertFalse(PieceType.PAWN.is_sliding())
        with self.assertRaises(ValueError):
            PieceType.from_symbol("x")


class PieceTests(unittest.TestCase):
    def test_symbol_colour_comparison_and_moved_copy(self) -> None:
        pawn = Piece(PieceType.PAWN, Colour.WHITE)
        moved_pawn = pawn.with_moved()

        self.assertEqual(pawn.symbol(), "P")
        self.assertEqual(B_KING.symbol(), "k")
        self.assertTrue(pawn.is_opponent(B_KING))
        self.assertFalse(pawn.is_opponent(W_QUEEN))
        self.assertFalse(pawn.has_moved)
        self.assertTrue(moved_pawn.has_moved)
        self.assertEqual(moved_pawn.piece_type, PieceType.PAWN)

    def test_pieces_are_immutable_and_factory_creates_unmoved_piece(self) -> None:
        piece = make_piece(PieceType.QUEEN, Colour.BLACK)
        self.assertEqual(piece, Piece(PieceType.QUEEN, Colour.BLACK))
        with self.assertRaises(FrozenInstanceError):
            piece.has_moved = True  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
