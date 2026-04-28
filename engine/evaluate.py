"""
engine/evaluate.py

Static position evaluator. Returns a score in centipawns from White's perspective.
Positive = White is better. Negative = Black is better.
"""

from __future__ import annotations

from collections import Counter

from infinity_chess.board import Board
from infinity_chess.move import Square
from infinity_chess.pieces import Piece, PieceType, Colour
from infinity_chess.rules import InfinityChessRules


PIECE_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 300,
    PieceType.BISHOP: 400,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 100000,
}


class Evaluator:
    """
    Static position evaluator using material and board control.
    Extend this class to add custom evaluation terms for your variant.
    """

    def evaluate(self, board: Board) -> int:
        """Score in centipawns from White's perspective."""
        score = 0
        score += self._material(board)
        score += self._control(board)
        return score

    def _material(self, board: Board) -> int:
        score = 0
        for sq in board.all_squares():
            piece = board.get(sq)
            if piece is None:
                continue
            value = PIECE_VALUES.get(piece.piece_type, 0)
            score += value if piece.colour == Colour.WHITE else -value
        return score

    def _control(self, board: Board) -> int:
        rules = InfinityChessRules()

        score = 0

        white_attacks: Counter[Square] = Counter()
        for sq, piece in board.pieces_for(Colour.WHITE):
            for move in rules.pseudo_legal_moves(board, sq, _for_attack_check=True):
                white_attacks[move.to_sq] += 1

        black_attacks: Counter[Square] = Counter()
        for sq, piece in board.pieces_for(Colour.BLACK):
            for move in rules.pseudo_legal_moves(board, sq, _for_attack_check=True):
                black_attacks[move.to_sq] += 1

        # White control
        for target, count in white_attacks.items():
            if self._is_other_side(board, Colour.WHITE, target):
                score += 20# * count
            else:
                score += 10# * count

        # Black control
        for target, count in white_attacks.items():
            if self._is_other_side(board, Colour.BLACK, target):
                score -= 20# * count
            else:
                score -= 10# * count

        # White king danger
        white_king_sq = board.find_piece(PieceType.KING, Colour.WHITE)
        for target in self._king_ring(board, white_king_sq, rules):
            pressure = black_attacks[target] - white_attacks[target]
            if pressure > 0:
                score -= pressure * 25


        # Black king danger
        black_king_sq = board.find_piece(PieceType.KING, Colour.BLACK)
        for target in self._king_ring(board, black_king_sq, rules):
            pressure = white_attacks[target] - black_attacks[target]
            if pressure > 0:
                score += pressure * 25

        return score


    def _king_ring(self, board: Board, sq: Square, rules: InfinityChessRules) -> set[Square]:
        ring = set()
        for dr in (-1, 0, 1):
            for df in (-1, 0, 1):
                if dr == 0 and df == 0:
                    continue
                target = rules.wrap_square(sq + (dr, df))
                if board.in_bounds(target):
                    ring.add(target)
        return ring

    def _is_other_side(self, board: Board, colour: Colour, target: Square) -> bool:
        half = board.ranks // 2
        if colour == Colour.WHITE:
            return target.rank >= half
        return target.rank < half
