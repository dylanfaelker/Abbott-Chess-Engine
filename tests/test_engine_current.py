"""Tests for search/evaluation features unique to the current ``engine`` package."""

import unittest

from engine.search import INF, Search
from infinity_chess.board import Board
from infinity_chess.move import MoveFlag, Square
from infinity_chess.move_generator import MoveGenerator
from infinity_chess.pieces import Colour, Piece, PieceType
from infinity_chess.rules import InfinityChessRules


class CurrentEngineTests(unittest.TestCase):
    def test_evaluation_can_be_made_deterministic_and_includes_initiative(self) -> None:
        board = Board.from_fen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        search = Search(board, InfinityChessRules(), isVary=False)

        white_to_move_score = search.evaluator.evaluate(board)
        self.assertEqual(search.evaluator.evaluate(board), white_to_move_score)

        black_to_move = board.copy()
        black_to_move.turn = Colour.BLACK
        self.assertNotEqual(white_to_move_score - search.evaluator.evaluate(black_to_move), 0)

    def test_non_eight_by_eight_board_skips_piece_square_tables(self) -> None:
        board = Board(10, 10)
        # Add both kings so this is also a valid evaluation fixture.
        board.set(Square(0, 4), Piece(PieceType.KING, Colour.WHITE))
        board.set(Square(9, 4), Piece(PieceType.KING, Colour.BLACK))
        search = Search(board, InfinityChessRules(), isVary=False)
        self.assertEqual(search.evaluator._piece_square(board), 0)

    def test_move_ordering_prioritizes_en_passant_and_then_transposition_move(self) -> None:
        board = Board.from_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        search = Search(board, InfinityChessRules(), isVary=False)
        ordered = search._ordered_moves(board, 0)
        en_passant = next(move for move in ordered if move.flag is MoveFlag.EN_PASSANT)
        quiet_pawn_push = next(move for move in ordered if move.to_uci() == "e5e6")

        self.assertLess(ordered.index(en_passant), ordered.index(quiet_pawn_push))

        search.transposition_table[board.zobrist_hash()] = {"move": quiet_pawn_push}
        self.assertEqual(search._ordered_moves(board, 0)[0], quiet_pawn_push)

    def test_quiescence_search_includes_en_passant_as_a_tactical_capture(self) -> None:
        board = Board.from_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        search = Search(board, InfinityChessRules(), isVary=False)

        class EnPassantAwareEvaluator:
            def evaluate(self, position: Board) -> int:
                pawn = position.get(Square.from_algebraic("d6"))
                return 1_000 if pawn and pawn.piece_type is PieceType.PAWN and pawn.colour is Colour.WHITE else 0

        search.evaluator = EnPassantAwareEvaluator()
        legal_moves = MoveGenerator(board, InfinityChessRules()).legal_moves()
        self.assertEqual(search._quiescence(board, -INF, INF, legal_moves), 1_000)

    def test_depth_two_search_restores_board_and_caches_subpositions(self) -> None:
        board = Board.from_fen("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        original_fen = board.to_fen()
        original_hash = board.zobrist_hash()
        search = Search(board, InfinityChessRules(), isVary=False)

        move, _ = search.find_best_move(2)

        self.assertIsNotNone(move)
        self.assertGreater(search.nodes_searched, 0)
        self.assertTrue(search.transposition_table)
        self.assertEqual(board.to_fen(), original_fen)
        self.assertEqual(board.zobrist_hash(), original_hash)


if __name__ == "__main__":
    unittest.main()
