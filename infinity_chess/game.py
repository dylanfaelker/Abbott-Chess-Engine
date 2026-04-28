"""
engine/game.py

Game orchestrates a full match: it owns the board, enforces turn order,
tracks history, and exposes a clean interface for the API layer to use.

The API endpoints (app.py) should talk to Game, not Board directly.
"""

from __future__ import annotations
from typing import Optional

from infinity_chess.board import Board
from infinity_chess.move import Move, Square
from infinity_chess.move_generator import MoveGenerator
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet, StandardRules


class Game:
    """
    A complete game session.

    Attributes:
        board:      Current board state.
        generator:  Move generator (board + rules).
        result:     None while in progress; 'white'/'black'/'draw' when over.
    """

    def __init__(self, rules: Optional[RuleSet] = None, board: Optional[Board] = None):
        self.board: Board = board or Board.standard()
        self.rules: RuleSet = rules or StandardRules()
        self.generator: MoveGenerator = MoveGenerator(self.board, self.rules)
        self.result: Optional[str] = None

    # ── Game state ────────────────────────────────────────────────────────────

    @property
    def turn(self) -> Colour:
        return self.board.turn

    @property
    def is_over(self) -> bool:
        return self.result is not None

    @property
    def move_count(self) -> int:
        return len(self.board.history)

    # ── Making moves ──────────────────────────────────────────────────────────

    def make_move(self, move: Move) -> bool:
        """
        Attempt to apply a move.
        Returns True if the move was legal and applied, False otherwise.
        Updates result if the move ends the game.
        """
        if self.is_over:
            return False

        legal = self.generator.legal_moves()
        if move not in legal:
            return False

        self.board = self.board.apply_move(move)
        self.generator = MoveGenerator(self.board, self.rules)

        over, result = self.generator.game_over()
        if over:
            self.result = result

        return True

    def make_move_uci(self, uci: str) -> bool:
        """
        Apply a move given as a UCI string (e.g. 'e2e4').
        Matches against legal moves — handles promotions by suffix letter.
        Returns True if applied, False if illegal or ambiguous.
        """
        legal = self.generator.legal_moves()
        matches = [m for m in legal if m.to_uci() == uci]
        if len(matches) == 1:
            return self.make_move(matches[0])
        return False

    # ── Querying state ────────────────────────────────────────────────────────

    def legal_moves(self) -> list[Move]:
        return self.generator.legal_moves()

    def legal_moves_from(self, sq: Square) -> list[Move]:
        return self.generator.legal_moves_from(sq)

    def is_in_check(self) -> bool:
        return self.generator.is_in_check()

    def is_square_attacked(self, sq: Square, by_colour: Colour) -> bool:
        return self.generator.is_square_attacked(sq, by_colour)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_fen(self) -> str:
        return self.board.to_fen()

    @classmethod
    def from_fen(cls, fen: str, rules: Optional[RuleSet] = None) -> "Game":
        board = Board.from_fen(fen)
        return cls(rules=rules, board=board)

    def to_dict(self) -> dict:
        """Serialise game state for the API response."""
        over, result = self.generator.game_over()
        return {
            "fen":        self.to_fen(),
            "turn":       self.turn.value,
            "move_count": self.move_count,
            "in_check":   self.is_in_check(),
            "is_over":    over,
            "result":     result,
        }

    # ── Display ───────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        status = f"Result: {self.result}" if self.is_over else f"Turn: {self.turn.value}"
        return f"{self.board}\n{status}"