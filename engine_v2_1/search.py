"""
engine/search.py

Negamax search with alpha-beta pruning.
"""

from __future__ import annotations
from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag
from infinity_chess.move_generator import MoveGenerator
from engine.evaluate import Evaluator, PIECE_VALUES
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet

MATE_SCORE = 100_000_000
INF = float("inf")


class Search:
    def __init__(self, board: Board, rules: RuleSet | None = None):
        """Create a search object for a board position and ruleset."""
        self.board = board
        self.generator = MoveGenerator(board, rules)
        self.evaluator = Evaluator()
        self.nodes_searched = 0

    def find_best_move(self, depth: int) -> tuple[Move | None, int]:
        """Run iterative deepening up to depth and return the best move and score."""
        self.nodes_searched = 0
        best_move = None
        best_score = -INF
        alpha, beta = -INF, INF

        for move in self.generator.legal_moves():
            new_board = self.board.apply_move(move)
            child = Search(new_board, self.generator.rules)
            score = -child._negamax(depth - 1, -beta, -alpha, 1)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move, best_score

    def _negamax(self, depth: int, alpha: float, beta: float, ply: int) -> int:
        """Search a position with negamax, alpha-beta"""
        self.nodes_searched += 1

        over, result = self.generator.game_over()
        if over:
            if result in ("white", "black"):
                loser = Colour.WHITE if result == "black" else Colour.BLACK
                return -(MATE_SCORE - ply) if self.board.turn == loser else (MATE_SCORE - ply) # To prefer earlier mates
            return 0 # draw

        if depth == 0:
            return self.evaluator.evaluate(self.board)
        
        best_score = -INF

        for move in self.generator.legal_moves():
            new_board = self.board.apply_move(move)
            child = Search(new_board, self.generator.rules)
            score = -child._negamax(depth - 1, -beta, -alpha, ply + 1)

            best_score = max(best_score, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        return best_score