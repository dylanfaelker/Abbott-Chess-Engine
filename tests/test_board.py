"""Board-state tests: FEN, bitboards, copies, application, and undo."""

import unittest

from infinity_chess.board import Board
from infinity_chess.move import Move, Square
from infinity_chess.pieces import Colour, Piece, PieceType


class BoardConstructionTests(unittest.TestCase):
    def test_standard_board_has_expected_layout_bitboards_and_fen(self) -> None:
        board = Board.standard()
        self.assertEqual((board.ranks, board.files), (8, 8))
        self.assertEqual(board.colour_bitboard(Colour.WHITE).bit_count(), 16)
        self.assertEqual(board.colour_bitboard(Colour.BLACK).bit_count(), 16)
        self.assertEqual(board.occupied_bitboard().bit_count(), 32)
        self.assertEqual(board.empty_bitboard().bit_count(), 32)
        self.assertEqual(board.get(Square.from_algebraic("e1")), Piece(PieceType.KING, Colour.WHITE))
        self.assertEqual(board.get(Square.from_algebraic("d8")), Piece(PieceType.QUEEN, Colour.BLACK))
        self.assertEqual(
            board.to_fen(),
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        )

    def test_fen_round_trip_preserves_metadata_and_non_standard_dimensions(self) -> None:
        fen = "3/1Q1/3 b - b2 7 9"
        board = Board.from_fen(fen)
        self.assertEqual((board.ranks, board.files), (3, 3))
        self.assertEqual(board.turn, Colour.BLACK)
        self.assertEqual(board.en_passant_sq, Square.from_algebraic("b2"))
        self.assertEqual(board.halfmove_clock, 7)
        self.assertEqual(board.fullmove_number, 9)
        self.assertEqual(board.to_fen(), fen)

    def test_invalid_fen_rejects_zero_runs_and_inconsistent_rows(self) -> None:
        for fen in ("0", "8/7"):
            with self.subTest(fen=fen), self.assertRaises(ValueError):
                Board.from_fen(fen)


class BoardMutationTests(unittest.TestCase):
    def test_set_updates_bitboards_and_copy_is_independent(self) -> None:
        board = Board(2, 3)
        square = Square(1, 2)
        knight = Piece(PieceType.KNIGHT, Colour.WHITE)
        board.set(square, knight)

        self.assertEqual(board.get(square), knight)
        self.assertTrue(board.bitboard_contains(board.piece_bitboard(Colour.WHITE, PieceType.KNIGHT), square))

        copied = board.copy()
        copied.set(square, None)
        self.assertEqual(board.get(square), knight)
        self.assertIsNone(copied.get(square))

    def test_make_and_unmake_restore_all_normal_move_state(self) -> None:
        board = Board.standard()
        original_fen = board.to_fen()
        original_hash = board.zobrist_hash()
        move = Move.from_uci("e2e4")

        undo = board.make_move(move)
        self.assertEqual(board.get(Square.from_algebraic("e4")), Piece(PieceType.PAWN, Colour.WHITE, True))
        self.assertEqual(board.en_passant_sq, Square.from_algebraic("e3"))
        self.assertEqual(board.turn, Colour.BLACK)
        self.assertEqual(len(board.zobrist_history), 2)

        board.unmake_move(undo)
        self.assertEqual(board.to_fen(), original_fen)
        self.assertEqual(board.zobrist_hash(), original_hash)
        self.assertEqual(len(board.zobrist_history), 1)

    def test_apply_move_returns_changed_copy_without_mutating_source(self) -> None:
        board = Board.standard()
        updated = board.apply_move(Move.from_uci("g1f3"))

        self.assertEqual(board.get(Square.from_algebraic("g1")).piece_type, PieceType.KNIGHT)
        self.assertIsNone(board.get(Square.from_algebraic("f3")))
        self.assertIsNone(updated.get(Square.from_algebraic("g1")))
        self.assertEqual(updated.get(Square.from_algebraic("f3")), Piece(PieceType.KNIGHT, Colour.WHITE, True))

    def test_square_and_piece_iterators_follow_bitboard_contents(self) -> None:
        board = Board(2, 2)
        board.set(Square(0, 1), Piece(PieceType.ROOK, Colour.WHITE))
        board.set(Square(1, 0), Piece(PieceType.BISHOP, Colour.BLACK))

        self.assertEqual(list(board.squares_in_bitboard(board.occupied_bitboard())), [Square(0, 1), Square(1, 0)])
        self.assertEqual(board.first_square_in_bitboard(board.occupied_bitboard()), Square(0, 1))
        self.assertEqual(list(board.pieces_for(Colour.WHITE)), [(Square(0, 1), Piece(PieceType.ROOK, Colour.WHITE))])
        self.assertEqual(board.find_piece(PieceType.BISHOP, Colour.BLACK), Square(1, 0))


if __name__ == "__main__":
    unittest.main()
