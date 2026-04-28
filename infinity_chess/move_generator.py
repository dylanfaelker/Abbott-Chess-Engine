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
from infinity_chess.rules import RuleSet, StandardRules


class MoveGenerator:
    """
    Generates legal moves and answers game-state questions for a given
    board + rule set combination.

    Usage:
        gen = MoveGenerator(board)                      # standard rules
        gen = MoveGenerator(board, MyCustomRules())     # custom rules

    The search engine holds a MoveGenerator and calls:
        gen.legal_moves(colour)   → moves to try
        gen.game_over()           → when to stop searching
    """

    def __init__(self, board: Board, rules: Optional[RuleSet] = None):
        self.board = board
        self.rules: RuleSet = rules or StandardRules()

    # ── Move generation ───────────────────────────────────────────────────────

    def legal_moves(self, colour: Optional[Colour] = None) -> list[Move]:
        """
        Return all legal moves for `colour` (defaults to board.turn).
        Returns a list (not a generator) so it can be iterated multiple times.
        """
        colour = colour or self.board.turn
        return list(self.rules.legal_moves(self.board, colour))

    def legal_moves_from(self, sq: Square) -> list[Move]:
        """Return all legal moves originating from a specific square."""
        piece = self.board.get(sq)
        if piece is None:
            return []
        all_legal = self.legal_moves(piece.colour)
        return [m for m in all_legal if m.from_sq == sq]

    def pseudo_legal_moves(self, sq: Square) -> list[Move]:
        """
        Pseudo-legal moves from a square (not filtered for check).
        Useful for highlighting attacked squares even if the king is exposed.
        """
        return list(self.rules.pseudo_legal_moves(self.board, sq))

    # ── Game state queries ────────────────────────────────────────────────────

    def game_over(self) -> tuple[bool, Optional[str]]:
        """Return (is_over, result). Result is 'white', 'black', 'draw', or None."""
        return self.rules.game_over(self.board)

    def is_in_check(self, colour: Optional[Colour] = None) -> bool:
        colour = colour or self.board.turn
        return self.rules.is_in_check(self.board, colour)

    def is_square_attacked(self, sq: Square, by_colour: Colour) -> bool:
        return self.rules.is_square_attacked(self.board, sq, by_colour)

    def is_checkmate(self, colour: Optional[Colour] = None) -> bool:
        colour = colour or self.board.turn
        return self.rules.is_checkmate(self.board, colour)

    def is_stalemate(self, colour: Optional[Colour] = None) -> bool:
        colour = colour or self.board.turn
        return self.rules.is_stalemate(self.board, colour)

    # ── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> "MoveGenerator":
        """
        Return a new MoveGenerator for the board state after `move` is applied.
        The original MoveGenerator is unchanged.
        """
        new_board = self.board.apply_move(move)
        return MoveGenerator(new_board, self.rules)