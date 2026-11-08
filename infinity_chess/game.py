"""
engine/game.py

Game orchestrates a full match: it owns the board, enforces turn order,
tracks history, and exposes a clean interface for the API layer to use.
Simple state properties are O(1); move operations are dominated by legal move
generation.

The API endpoints (app.py) should talk to Game, not Board directly.
"""

from __future__ import annotations
from typing import Optional

from infinity_chess.board import Board
from infinity_chess.move import Move, Square
from infinity_chess.move_generator import MoveGenerator
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet, InfinityChessRules


class Game:
    """
    A complete game session.

    Attributes:
        board:      Current board state.
        generator:  Move generator (board + rules).
        result:     None while in progress; 'white'/'black'/'draw' when over.

    Args:
        rules (Optional[RuleSet]): Ruleset used to interpret the board.
        board (Optional[Board]): Board position being queried or updated.

    Returns:
    Game: Session containing the current position, rules, and committed history.

    Complexity:
        O(1) for state reads; move operations follow legal move generation cost.
    """

    def __init__(self, rules: Optional[RuleSet] = None, board: Optional[Board] = None):
        """
        Create a game around a board and ruleset.

        Args:
            rules (Optional[RuleSet]): Ruleset used to interpret the board.
            board (Optional[Board]): Board position being queried or updated.

        Returns:
            None: Initializes the Game instance.

        Complexity:
            O(1).
        """
        self.board: Board = board or Board.standard()
        self.rules: RuleSet = rules or InfinityChessRules()
        self.generator: MoveGenerator = MoveGenerator(self.board, self.rules)
        self.history: list[Move] = []
        self.result: Optional[str] = None

    # ── Game state ────────────────────────────────────────────────────────────

    @property
    def turn(self) -> Colour:
        """
        Read the side to move.

        Returns:
            Colour: Side identity.

        Complexity:
            O(1).
        """
        return self.board.turn

    @property
    def is_over(self) -> bool:
        """
        Report whether a result has been stored.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        return self.result is not None

    @property
    def move_count(self) -> int:
        """
        Count committed game moves.

        Returns:
            int: Integer value.

        Complexity:
            O(1).
        """
        return len(self.history)

    # ── Making moves ──────────────────────────────────────────────────────────

    def make_move(self, move: Move) -> bool:
        """
        Attempt to apply a move.
        Returns True if the move was legal and applied, False otherwise.
        Updates result if the move ends the game.

        Args:
            move (Move): Move to apply or inspect.

        Returns:
            bool: true if applied.

        Complexity:
            dominated by legal move generation.
        """
        if self.is_over:
            return False

        legal = self.generator.legal_moves()
        if move not in legal:
            return False

        self.board.make_move(move)
        self.history.append(move)

        over, result = self.generator.game_over()
        if over:
            self.result = result

        return True

    def make_move_uci(self, uci: str) -> bool:
        """
        Apply a move given as a UCI string (e.g. 'e2e4').
        Matches against legal moves — handles promotions by suffix letter.
        Returns True if applied, False if illegal or ambiguous.

        Args:
            uci (str): UCI move text.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
        dominated by legal move generation plus O(L) matching, where L is the
        number of legal moves.
        """
        legal = self.generator.legal_moves()
        matches = [m for m in legal if m.to_uci() == uci]
        if len(matches) == 1:
            return self.make_move(matches[0])
        return False

    # ── Querying state ────────────────────────────────────────────────────────

    def legal_moves(self) -> list[Move]:
        """
        List legal moves for the side to move.

        Returns:
            list[Move]: Move list.

        Complexity:
            O(M*A), as defined by ruleset move and attack checks.
        """
        return self.generator.legal_moves()

    def legal_moves_from(self, sq: Square) -> list[Move]:
        """
        List legal moves from one square.

        Args:
            sq (Square): Source or target board square.

        Returns:
            list[Move]: Move list.

        Complexity:
            O(M*A + L), including filtering all legal moves.
        """
        return self.generator.legal_moves_from(sq)

    def is_in_check(self) -> bool:
        """
        Check whether the side to move is attacked.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P*D), where P is opponent piece count and D move-ray length.
        """
        return self.generator.is_in_check()

    def is_square_attacked(self, sq: Square, by_colour: Colour) -> bool:
        """
        Check attacks on a target square.

        Args:
            sq (Square): Source or target board square.
            by_colour (Colour): Attacking side.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P*D).
        """
        return self.generator.is_square_attacked(sq, by_colour)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_fen(self) -> str:
        """
        Serialize the current game position.

        Returns:
            str: FEN string.

        Complexity:
            O(N).
        """
        return self.board.to_fen()

    @classmethod
    def from_fen(cls, fen: str, rules: Optional[RuleSet] = None) -> "Game":
        """
        Create a game from FEN.

        Args:
            fen (str): FEN text describing the position.
            rules (Optional[RuleSet]): Ruleset used to interpret the board.

        Returns:
            'Game': Game created from the FEN position.

        Complexity:
            O(F + N).
        """
        board = Board.from_fen(fen)
        return cls(rules=rules, board=board)

    def to_dict(self) -> dict:
        """
        Serialize state for API responses.

        Returns:
            dict: Serialized game-state mapping.

        Complexity:
            O(N + move-generation cost).
        """
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
        """
        Render board and result/turn status.

        Returns:
            str: Human-readable string.

        Complexity:
            O(N).
        """
        status = f"Result: {self.result}" if self.is_over else f"Turn: {self.turn.value}"
        return f"{self.board}\n{status}"
