"""
infinity_chess/move_generator.py

MoveGenerator is a thin orchestrator that ties together the Board and RuleSet.

The search and API endpoints talk to MoveGenerator rather than calling
RuleSet directly
"""

from __future__ import annotations
from typing import Iterator, Optional

from infinity_chess.board import Board
from infinity_chess.move import Move, Square
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet, InfinityChessRules


class MoveGenerator:
    """
    Generate legal moves and answer game-state questions for a board and rule set.

    Usage:
        gen = MoveGenerator(board)                      # standard rules
        gen = MoveGenerator(board, MyCustomRules())     # custom rules

    The search engine holds a MoveGenerator and calls:
        gen.legal_moves(colour)   → moves to try
        gen.game_over()           → when to stop searching

    Complexity notation: M is the number of candidate moves, A is the cost of a
    king-safety check, L is the number of legal moves, and D is the longest ray.

    Args:
        board (Board): Board position being queried or updated.
        rules (Optional[RuleSet]): Ruleset used to interpret the board.

    Returns:
        MoveGenerator: Object bound to a board and ruleset for move/state queries.

    Complexity:
        O(M*A) for legal generation, where M is candidate moves and A is the
        king-safety check cost.
    """

    def __init__(self, board: Board, rules: Optional[RuleSet] = None):
        """
        Bind a board to rules.

        Args:
            board (Board): Board position being queried or updated.
            rules (Optional[RuleSet]): Ruleset used to interpret the board.

        Returns:
            None: Initializes the MoveGenerator instance.

        Complexity:
            O(1).
        """
        self.board = board
        self.rules: RuleSet = rules or InfinityChessRules()

    # ── Move generation ───────────────────────────────────────────────────────

    def legal_moves(self, colour: Optional[Colour] = None) -> list[Move]:
        """
        Return all legal moves for `colour` (defaults to board.turn).
        Returns a list (not a generator) so it can be iterated multiple times.

        Args:
            colour (Optional[Colour]): Piece side or side being queried.

        Returns:
            list[Move]: list of legal Moves.

        Complexity:
            O(M*A), based on candidate moves M and attack-check cost A.
        """
        colour = colour or self.board.turn
        return list(self.rules.legal_moves(self.board, colour))

    def legal_moves_from(self, sq: Square) -> list[Move]:
        """
        Filter legal moves to one origin.

        Args:
            sq (Square): Source or target board square.

        Returns:
            list[Move]: Move list.

        Complexity:
            O(M*A + L), with L legal moves.
        """
        piece = self.board.get(sq)
        if piece is None:
            return []
        all_legal = self.legal_moves(piece.colour)
        return [m for m in all_legal if m.from_sq == sq]

    def pseudo_legal_moves(self, sq: Square) -> list[Move]:
        """
        Pseudo-legal moves from a square (not filtered for check).
        Useful for highlighting attacked squares even if the king is exposed.

        Args:
            sq (Square): Source or target board square.

        Returns:
            list[Move]: Move list.

        Complexity:
            O(D), where D is the longest board ray.
        """
        return list(self.rules.pseudo_legal_moves(self.board, sq))

    def attacks_from(self, sq: Square) -> list[Square]:
        """
        Return every square covered by the piece at a square.

        Coverage includes empty and friendly-occupied squares, unlike legal
        move generation.

        Args:
            sq (Square): Square occupied by the attacking piece.

        Returns:
            list[Square]: Covered destination squares.

        Complexity:
            O(D), where D is the longest movement ray.
        """
        return list(self.rules.attacks_from(self.board, sq))

    # ── Game state queries ────────────────────────────────────────────────────

    def game_over(self, legal_moves: Optional[list[Move]] = None) -> tuple[bool, Optional[str]]:
        """
        Check terminal status, optionally reusing legal moves.

        Args:
        legal_moves (Optional[list[Move]]): Previously generated legal moves,
            when available.

        Returns:
            tuple[bool, Optional[str]]: (over, result).

        Complexity:
        O(L + draw-check cost), or O(1) plus draw checks when moves are supplied.
        """
        return self.rules.game_over(self.board, legal_moves)

    def is_in_check(self, colour: Optional[Colour] = None) -> bool:
        """
        Check the requested side or side to move.

        Args:
            colour (Optional[Colour]): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P*D).
        """
        colour = colour or self.board.turn
        return self.rules.is_in_check(self.board, colour)

    def is_square_attacked(self, sq: Square, by_colour: Colour) -> bool:
        """
        Check attacks on a square.

        Args:
            sq (Square): Source or target board square.
            by_colour (Colour): Attacking side.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P*D).
        """
        return self.rules.is_square_attacked(self.board, sq, by_colour)

    def is_checkmate(self, colour: Optional[Colour] = None) -> bool:
        """
        Test check plus absence of legal moves.

        Args:
            colour (Optional[Colour]): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(L*A).
        """
        colour = colour or self.board.turn
        return self.rules.is_checkmate(self.board, colour)

    def is_stalemate(self, colour: Optional[Colour] = None) -> bool:
        """
        Test no check plus absence of legal moves.

        Args:
            colour (Optional[Colour]): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(L*A).
        """
        colour = colour or self.board.turn
        return self.rules.is_stalemate(self.board, colour)

    # ── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> "MoveGenerator":
        """
        Return a new MoveGenerator for the board state after `move` is applied.
        The original MoveGenerator is unchanged.

        Args:
            move (Move): Move to apply or inspect.

        Returns:
            'MoveGenerator': new MoveGenerator.

        Complexity:
            O(N + H) for board copying.
        """
        new_board = self.board.apply_move(move)
        return MoveGenerator(new_board, self.rules)
