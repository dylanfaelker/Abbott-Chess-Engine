"""Rule-set tests for orthodox chess and Infinity Chess file wrapping."""

import unittest

from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag, Square
from infinity_chess.pieces import Colour, Piece, PieceType
from infinity_chess.rules import InfinityChessRules, StandardRules


def moves_from(rules: StandardRules, board: Board, square: str):
    return list(rules.pseudo_legal_moves(board, Square.from_algebraic(square)))


class StandardRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = StandardRules()

    def test_pawn_double_push_captures_and_all_promotion_choices(self) -> None:
        board = Board.from_fen("4k3/1p6/P7/8/8/8/4P3/4K3 w - - 0 1")
        pawn_moves = moves_from(self.rules, board, "e2")
        self.assertIn(Move(Square.from_algebraic("e2"), Square.from_algebraic("e4")), pawn_moves)

        capture_moves = moves_from(self.rules, board, "a6")
        self.assertIn(
            Move(Square.from_algebraic("a6"), Square.from_algebraic("b7"), MoveFlag.CAPTURE),
            capture_moves,
        )

        promotion_board = Board.from_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        promotions = moves_from(self.rules, promotion_board, "a7")
        self.assertEqual({move.promotion_piece for move in promotions}, {"QUEEN", "ROOK", "BISHOP", "KNIGHT"})
        self.assertTrue(all(move.flag is MoveFlag.PROMOTION for move in promotions))

    def test_castling_and_en_passant_are_generated_only_when_legal(self) -> None:
        castle_board = Board.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        castle_moves = list(self.rules.legal_moves(castle_board, Colour.WHITE))
        self.assertIn(Move(Square.from_algebraic("e1"), Square.from_algebraic("g1"), MoveFlag.CASTLE_KING), castle_moves)
        self.assertIn(Move(Square.from_algebraic("e1"), Square.from_algebraic("c1"), MoveFlag.CASTLE_QUEEN), castle_moves)

        ep_board = Board.from_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        ep_moves = list(self.rules.legal_moves(ep_board, Colour.WHITE))
        en_passant = [move for move in ep_moves if move.flag is MoveFlag.EN_PASSANT]
        self.assertEqual(len(en_passant), 1)
        self.assertEqual(en_passant[0].to_uci(), "e5d6")

    def test_legal_moves_exclude_moves_that_expose_the_king(self) -> None:
        board = Board.from_fen("k3r3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        legal = list(self.rules.legal_moves(board, Colour.WHITE))

        self.assertNotIn(Move(Square.from_algebraic("e2"), Square.from_algebraic("d2")), legal)
        self.assertIn(Move(Square.from_algebraic("e2"), Square.from_algebraic("e8"), MoveFlag.CAPTURE), legal)

    def test_checkmate_stalemate_and_draw_conditions(self) -> None:
        mate = Board.from_fen("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1")
        stalemate = Board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        kings_only = Board.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")

        self.assertTrue(self.rules.is_checkmate(mate, Colour.BLACK))
        self.assertEqual(self.rules.game_over(mate), (True, "white"))
        self.assertTrue(self.rules.is_stalemate(stalemate, Colour.BLACK))
        self.assertEqual(self.rules.game_over(stalemate), (True, "draw"))
        self.assertTrue(self.rules.is_draw(kings_only))

        fifty_move = Board.from_fen("4k3/8/8/8/8/8/4Q3/4K3 w - - 100 1")
        self.assertTrue(self.rules.is_draw(fifty_move))

        repetition = Board.from_fen("4k3/8/8/8/8/8/4Q3/4K3 w - - 0 1")
        repetition.zobrist_history.extend([repetition.zobrist_hash(), repetition.zobrist_hash()])
        self.assertTrue(self.rules.is_draw(repetition))


class InfinityChessRulesTests(unittest.TestCase):
    def test_files_wrap_for_rook_attacks_but_standard_rules_do_not(self) -> None:
        board = Board.from_fen("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")
        rook = Square.from_algebraic("a1")
        wrapped = set(InfinityChessRules().attacks_from(board, rook))
        orthodox = set(StandardRules().attacks_from(board, rook))

        self.assertIn(Square.from_algebraic("h1"), wrapped)
        self.assertIn(Square.from_algebraic("g1"), wrapped)
        self.assertNotIn(Square.from_algebraic("h1"), orthodox)

    def test_wrap_square_handles_negative_and_oversized_files(self) -> None:
        board = Board(8, 8)
        self.assertEqual(InfinityChessRules.wrap_square(Square(3, -1), board), Square(3, 7))
        self.assertEqual(InfinityChessRules.wrap_square(Square(3, 9), board), Square(3, 1))


if __name__ == "__main__":
    unittest.main()
