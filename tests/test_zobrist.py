import random
import unittest

from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag, Square
from infinity_chess.pieces import Colour, Piece, PieceType
from infinity_chess.rules import StandardRules


class IncrementalZobristTests(unittest.TestCase):
    def test_initial_hashes_match_recomputation(self) -> None:
        large_board = Board(10, 12)
        large_board.set(Square(9, 11), Piece(PieceType.QUEEN, Colour.WHITE))
        for board in (
            Board.standard(),
            Board.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
            large_board,
        ):
            self.assertEqual(board.hash, board.recompute_hash())

    def test_castling_and_en_passant_hashes(self) -> None:
        rules = StandardRules()
        positions = (
            (
                "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                Square(0, 4), Square(0, 6), MoveFlag.CASTLE_KING,
            ),
            (
                "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
                Square(4, 4), Square(5, 3), MoveFlag.EN_PASSANT,
            ),
        )
        for fen, from_sq, to_sq, flag in positions:
            board = Board.from_fen(fen)
            moves = [
                candidate
                for candidate in rules.legal_moves(board, board.turn)
                if candidate.from_sq == from_sq
                and candidate.to_sq == to_sq
                and candidate.flag == flag
            ]
            self.assertEqual(len(moves), 1)
            move = moves[0]
            undo = board.make_move(move)
            self.assertEqual(board.hash, board.recompute_hash())
            board.unmake_move(undo)
            self.assertEqual(board.hash, board.recompute_hash())

    def test_hash_matches_recomputation_through_random_moves_and_undo(self) -> None:
        board = Board.standard()
        rules = StandardRules()
        rng = random.Random(41)
        undos = []

        for _ in range(100):
            legal_moves = list(rules.legal_moves(board, board.turn))
            if not legal_moves:
                break
            undos.append(board.make_move(rng.choice(legal_moves)))
            self.assertEqual(board.hash, board.recompute_hash())

        while undos:
            board.unmake_move(undos.pop())
            self.assertEqual(board.hash, board.recompute_hash())


if __name__ == "__main__":
    unittest.main()
