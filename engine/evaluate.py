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
from infinity_chess.geometry import geometry
from config import PIECE_VALUES, PIECE_TABLES, PIECE_TABLES_EG, SIGMA, CONTROL_OWN_HALF, CONTROL_OPPONENT_HALF, KING_DANGER, INITIATIVE_VAL, ENDGAME_PHASE_THRESHOLD, MAX_PHASE
from abbott import is_endgame

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
        self._rules = InfinityChessRules() # TODO make this an input

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
        return self.evaluate_and_is_endgame(board)[0]

    def evaluate_and_is_endgame(self, board: Board):
        """
        Score a position from White's perspective.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: centipawn integer.
            bool: whether we are in endgame phase.

        Complexity:
            O(P*D).
        """
        score = 0

        white_mat, black_mat = self._material(board)
        score += white_mat - black_mat

        # score += self._control(board)

        count_white_pawns = board.bitboards[Colour.WHITE, PieceType.PAWN].bit_count()
        count_black_pawns = board.bitboards[Colour.BLACK, PieceType.PAWN].bit_count()
        phase_value = white_mat + black_mat - (count_white_pawns + count_black_pawns) * 100
        is_endgame = phase_value <= ENDGAME_PHASE_THRESHOLD
        if not is_endgame:
            score += self._king_safety(board)
        
        score += self._initiative(board)
        
        score += self._piece_square(board, phase_value)

        if self.isVary:
            score += random.randint(-SIGMA, SIGMA)

        return score, is_endgame

    def _material(self, board: Board) -> int:
        """
        Sum signed piece values.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: material score of white.
            int: material score of black.

        Complexity:
            O(P).
        """
        score_white = 0
        score_black = 0
        for colour in Colour:
            for piece_type in PieceType:
                if piece_type == PieceType.KING:
                    continue
                value = PIECE_VALUES.get(piece_type, 0)
                bb = board.bitboards[colour, piece_type]
                if colour == Colour.WHITE:
                    score_white += value * bb.bit_count()
                if colour == Colour.BLACK:
                    score_black += value * bb.bit_count()
        return score_white, score_black

    def  _control(self, board: Board) -> int:
        """
        Score attacked squares.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: control score.

        Complexity:
            O(P*D).
        """

        score = 0

        white_attacks: Counter[Square] = Counter()
        for sq, piece in board.pieces_for(Colour.WHITE):
            for target in self._rules.attacks_from(board, sq):
                white_attacks[target] += 1

        black_attacks: Counter[Square] = Counter()
        for sq, piece in board.pieces_for(Colour.BLACK):
            for target in self._rules.attacks_from(board, sq):
                black_attacks[target] += 1

        # White control
        for target, count in white_attacks.items():
            if self._is_other_side(board, Colour.WHITE, target):
                score += CONTROL_OPPONENT_HALF# * count
            else:
                score += CONTROL_OWN_HALF# * count

        # Black control
        for target, count in black_attacks.items():
            if self._is_other_side(board, Colour.BLACK, target):
                score -= CONTROL_OPPONENT_HALF# * count
            else:
                score -= CONTROL_OWN_HALF# * count

        return score


    def _king_safety(self, board: Board) -> int:
        """
        Score king pressure from White's perspective.

        For each square adjacent to a king, penalise 20 per enemy
        attacker in excess of friendly defenders.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            int: control score.

        Complexity:
            O(1): 16 ring squares, each a fixed number of table lookups,
            independent of piece count.
        """
        g = geometry(board.ranks, board.files, self._rules.WRAPS)
        score = 0

        for king_colour, sign in ((Colour.WHITE, -1), (Colour.BLACK, 1)):
            king_bb = board.bitboards[(king_colour, PieceType.KING)]
            if not king_bb:
                continue
            king_idx = (king_bb & -king_bb).bit_length() - 1
            enemy = king_colour.opponent()

            for idx in g.king[king_idx]:
                attackers = self._rules.count_attackers(board, idx, enemy)
                if attackers == 0:
                    continue                      # no pressure: skip the defender count
                defenders = self._rules.count_attackers(board, idx, king_colour)
                if attackers > defenders:
                    score += sign * (attackers - defenders) * KING_DANGER

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

        return INITIATIVE_VAL if board.turn == Colour.WHITE else -1 * INITIATIVE_VAL
    
    def _piece_square(self, board: Board, game_phase: int = MAX_PHASE) -> int:
        """
        Apply 8x8 piece-square tables.

        Args:
            board (Board): Board position being queried or updated.
            game_phase (int): Material value left representing what phase of the game we are in

        Returns:
            int: positional score (zero off 8x8).

        Complexity:
            O(P) on 8x8, otherwise O(1).
        """
        if board.ranks != 8 or board.files != 8:
            return 0

        if is_endgame:
            PST = PIECE_TABLES_EG
        else:
            PST = PIECE_TABLES

        # Positions are centered so the opposing king is in the e file
        white_king = board.find_piece(PieceType.KING, Colour.WHITE)
        black_king = board.find_piece(PieceType.KING, Colour.BLACK)
        if white_king is None or black_king is None:
            return 0
        shift_black = 4 - white_king.file
        shift_white = 4 - black_king.file

        score = 0
        for piece_type, table in PIECE_TABLES.items():
            eg_table = PIECE_TABLES_EG[piece_type]
            bb = board.bitboards[(Colour.WHITE, piece_type)]
            while bb:
                low = bb & -bb # lowest set bit
                rank, file = divmod(low.bit_length() - 1, 8) # finds the index of the lowest bit, then extracts rank/file
                pst_score = table[(7 - rank) * 8 + (file + shift_white) % 8] # table look up to account for flipped board in piece square tables
                eg_pst_score = eg_table[(7 - rank) * 8 + (file + shift_white) % 8]
                score += (pst_score * game_phase // MAX_PHASE + eg_pst_score * (MAX_PHASE - game_phase) // MAX_PHASE) # linear combination of the normal and endgame PSTs
                bb ^= low # clears lowest bit
            bb = board.bitboards[(Colour.BLACK, piece_type)]
            while bb:
                low = bb & -bb
                rank, file = divmod(low.bit_length() - 1, 8)
                pst_score = table[rank * 8 + (file + shift_black) % 8]
                eg_pst_score = eg_table[rank * 8 + (file + shift_black) % 8]
                score -= (pst_score * game_phase // MAX_PHASE + eg_pst_score * (MAX_PHASE - game_phase) // MAX_PHASE)
                bb ^= low
        return score
