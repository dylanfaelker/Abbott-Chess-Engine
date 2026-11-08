"""
engine/evaluate.py

Static position evaluator. Returns a score in centipawns from White's perspective.
Positive = White is better. Negative = Black is better.
Complexity notation: P = occupied piece count and D = longest movement ray.
"""

from __future__ import annotations

from collections import Counter

import random

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

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
    -5, -5,-10,  0,  0,-10, -5, -5,
    10, 10, 10,-20,-20, 10, 10, 10,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -40,-30,-30,-30,-30,-30,-30,-30,
      0,  0,  0,  0,  0,  0,  0,  0,
     -5,  0, 10, 15, 15, 10,  0, -5,
      0,  5, 15, 20, 20, 15,  5,  0,
     -5,  0, 15, 20, 20, 15,  0, -5,
      0,  5, 10, 15, 15, 10,  5,  0,
      0,  0,  0,  5,  5,  0,  0,  0,
    -40,-30,-30,-30,-30,-30,-30,-30,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
      0,  0,  0,  0,  0,  0,  0,  0,
      0,  0,  0,  5,  5,  0,  0,  0,
      0,  5,  5, 10, 10,  5,  5,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     10, 10, 10, 10, 10, 10, 10, 10,
     10, 10,  0,  0,  0,  0, 10, 10,
    -10,-10,-10,-10,-10,-10,-10,-10,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    10, 10, 10, 10, 10, 10, 10, 10,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  5,  5,  5,  0,  0,
]

QUEEN_TABLE = [
    -10,-10,-10, -5, -5, -5,-10,-10,
     -5,  0,  0,  0,  0,  0,  0,  0,
      0,  0,  0,  5,  5,  5,  0,  0,
      0,  0,  0,  5,  5,  5,  0,  0,
      0,  0,  0,  5,  5,  5,  0,  0,
      0,  0,  0,  5,  5,  5,  0,  0,
      0,  0,  0,  0,  0,  0,  0,  0,
    -10,-10,-10,-10, -5,-10,-10,-10,
]

KING_TABLE = [
    -50,-50,-50,-50,-50,-50,-50,-50,
    -50,-50,-50,-50,-50,-50,-50,-50,
    -50,-50,-50,-30,-30,-40,-50,-50,
    -50,-50,-50,-40,-40,-40,-50,-50,
    -30,-30,-30,-30,-30,-30,-30,-30,
    -10,-10,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0,  0, 20,
     30, 20, 10,  0,  0,  0, 10, 20,
]

PIECE_TABLES: dict[PieceType, list[int]] = {
    PieceType.PAWN:   PAWN_TABLE,
    PieceType.KNIGHT: KNIGHT_TABLE,
    PieceType.BISHOP: BISHOP_TABLE,
    PieceType.ROOK:   ROOK_TABLE,
    PieceType.QUEEN:  QUEEN_TABLE,
    PieceType.KING:   KING_TABLE,
}


class Evaluator:
    """
    Static position evaluator using material and board control.
    Extend this class to add custom evaluation terms for your variant.

    Args:
        isVary (bool): Toggle for randomized evaluation variation.

    Returns:
        Evaluator instance: configured evaluator for scoring board positions.

    Complexity:
        O(P*D), where P is piece count and D is movement-ray length.
    """

    def __init__(self, isVary: bool = True):
        """
        Set evaluation options.

        Args:
            isVary (bool): Toggle for randomized evaluation variation.

        Returns:
            None: Initializes the Evaluator instance.

        Complexity:
            O(1).
        """
        self.isVary = isVary

    def evaluate(self, board: Board) -> int:
        """
        Score a position from White's perspective.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: centipawn integer.

        Complexity:
            O(P*D).
        """
        score = 0
        score += self._material(board)
        score += self._control(board)
        score += self._initiative(board)
        score += self._piece_square(board)

        if self.isVary:
            score += random.randint(-5, 5)

        return score

    def _material(self, board: Board) -> int:
        """
        Sum signed piece values.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: material score.

        Complexity:
            O(P).
        """
        score = 0
        for colour in Colour:
            for _, piece in board.pieces_for(colour):
                value = PIECE_VALUES.get(piece.piece_type, 0)
                score += value if piece.colour == Colour.WHITE else -value
        return score

    def _control(self, board: Board) -> int:
        """
        Score attacked squares and king pressure.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: control score.

        Complexity:
            O(P*D).
        """
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
                score += 10# * count
            else:
                score += 5# * count

        # Black control
        for target, count in black_attacks.items():
            if self._is_other_side(board, Colour.BLACK, target):
                score -= 10# * count
            else:
                score -= 5# * count

        # White king danger
        white_king_sq = board.find_piece(PieceType.KING, Colour.WHITE)
        for target in self._king_ring(board, white_king_sq, rules):
            pressure = black_attacks[target] - white_attacks[target]
            if pressure > 0:
                score -= pressure * 20


        # Black king danger
        black_king_sq = board.find_piece(PieceType.KING, Colour.BLACK)
        for target in self._king_ring(board, black_king_sq, rules):
            pressure = white_attacks[target] - black_attacks[target]
            if pressure > 0:
                score += pressure * 20

        return score

    def _king_ring(self, board: Board, sq: Square, rules: InfinityChessRules) -> set[Square]:
        """
        Return valid wrapped neighbors of a king.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            rules (InfinityChessRules): Ruleset used to interpret the board.

        Returns:
            set[Square]: Square set.

        Complexity:
            O(1).
        """
        ring = set()
        for dr in (-1, 0, 1):
            for df in (-1, 0, 1):
                if dr == 0 and df == 0:
                    continue
                target = rules.wrap_square(sq + (dr, df), board)
                if board.in_bounds(target):
                    ring.add(target)
        return ring

    def _is_other_side(self, board: Board, colour: Colour, target: Square) -> bool:
        """
        Check whether a target is on the opponent's half.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.
            target (Square): Target board square.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        half = board.ranks // 2
        if colour == Colour.WHITE:
            return target.rank >= half
        return target.rank < half
    
    def _initiative(self, board: Board) -> int:
        """
        Score the side to move.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: signed initiative score.

        Complexity:
            O(1).
        """

        INITIATIVE_VAL = 20

        return INITIATIVE_VAL / 2 if board.turn == Colour.WHITE else -1 * INITIATIVE_VAL / 2
    
    def _piece_square(self, board: Board) -> int:
        """
        Apply 8x8 piece-square tables.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: positional score (zero off 8x8).

        Complexity:
            O(P) on 8x8, otherwise O(1).
        """
        if board.ranks != 8 or board.files != 8:
            return 0

        # Positions are centered so the opposing king is in the e file
        white_king_file = board.find_piece(PieceType.KING, Colour.WHITE).file
        shift_black = white_king_file - 4

        black_king_file = board.find_piece(PieceType.KING, Colour.BLACK).file
        shift_white = black_king_file - 4

        score = 0
        for colour in Colour:
            for sq, piece in board.pieces_for(colour):
                table = PIECE_TABLES.get(piece.piece_type)
                if table is None:
                    continue
                if piece.colour == Colour.WHITE:
                    sq = InfinityChessRules.wrap_square(sq + (0, shift_white), board)
                    idx = sq.rank * 8 + sq.file
                    score += table[idx]
                else:
                    sq = InfinityChessRules.wrap_square(sq + (0, shift_black), board) # mirroring for black
                    idx = (7 - sq.rank) * 8 + sq.file
                    score -= table[idx]
        return score
