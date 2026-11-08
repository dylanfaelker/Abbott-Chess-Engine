"""
infinity_chess/move.py

Move representation. All moves are immutable dataclasses.

A Move is the minimal unit of action: from square → to square.
SpecialMove extends this for anything that needs extra context 
(promotion, castling, en passant)
Formatting and parsing costs are stated by each method.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class MoveFlag(Enum):
    """
    Classify move behavior.

    Returns:
        MoveFlag member: identity describing the move category.

    Complexity:
        O(1).
    """
    NORMAL            = auto()
    CAPTURE           = auto()
    PROMOTION         = auto()
    PROMOTION_CAPTURE = auto()
    CASTLE_KING       = auto()
    CASTLE_QUEEN      = auto()
    EN_PASSANT        = auto()

CAPTURE_FLAGS     = frozenset({MoveFlag.CAPTURE, MoveFlag.EN_PASSANT, MoveFlag.PROMOTION_CAPTURE})
QUIESCENCE_FLAGS  = CAPTURE_FLAGS | {MoveFlag.PROMOTION}

@dataclass(frozen=True)
class Square:
    """
    A position on the board as (rank, file), both 0-indexed.
    rank 0 = row 1, file 0 = a-file.

    Args:
        rank (int): Zero-based rank coordinate.
        file (int): Zero-based file coordinate.

    Returns:
        Square instance: immutable coordinate; access.

    Complexity:
        O(1).
    """
    rank: int
    file: int

    def to_algebraic(self) -> str:
        """
        Convert this square to algebraic text.

        Returns:
            str: file/rank string.

        Complexity:
            O(log(rank)).
        """
        return f"{chr(ord('a') + self.file)}{self.rank + 1}"

    @staticmethod
    def from_algebraic(notation: str) -> "Square":
        """
        Parse a file/rank string into a square.

        Args:
            notation (str): Algebraic square notation.

        Returns:
            'Square': Offset board coordinate.

        Complexity:
            O(len(notation)).
        """
        if len(notation) < 2:
            raise ValueError(f"Invalid square notation: {notation!r}")
        file = ord(notation[0].lower()) - ord('a')
        rank = int(notation[1:]) - 1
        return Square(rank=rank, file=file)

    def __add__(self, other: tuple[int, int]) -> "Square":
        """
        Convenient offset: Square(3, 4) + (1, 0) → Square(4, 4).
        - (Rank, File)

        Args:
        other (tuple[int, int]): Rank and file offset to apply to this square.

        Returns:
            'Square': new Square.

        Complexity:
            O(1).
        """
        return Square(self.rank + other[0], self.file + other[1])

    def __repr__(self) -> str:
        """
        Return the square's algebraic debug form.

        Returns:
            str: Human-readable string.

        Complexity:
            O(log(rank)).
        """
        return f"Square({self.to_algebraic()})"


@dataclass(frozen=True)
class Move:
    """
    A standard move from one square to another.

    Attributes:
        from_sq:    Origin square.
        to_sq:      Destination square.
        flag:       What kind of move this is (default: NORMAL).

    Args:
        from_sq (Square): Origin square of the move.
        to_sq (Square): Destination square of the move.
        flag (MoveFlag): Category of move, such as capture or castling.

    Returns:
        Move instance: immutable Move value.

    Complexity:
        O(1) to construct and compare.
    """
    from_sq: Square
    to_sq:   Square
    flag:    MoveFlag = MoveFlag.NORMAL

    def to_uci(self) -> str:
        """
        Format this move as UCI.

        Returns:
            str: coordinate string.

        Complexity:
            O(1) for ordinary chess coordinates.
        """
        return f"{self.from_sq.to_algebraic()}{self.to_sq.to_algebraic()}"

    @staticmethod
    def from_uci(uci: str) -> "Move":
        """
        Parse a UCI coordinate move.

        Args:
            uci (str): UCI move text.

        Returns:
            'Move': Parsed Move.

        Complexity:
            O(len(uci)).
        """
        if len(uci) < 4:
            raise ValueError(f"Invalid UCI move: {uci!r}")
        return Move(
            from_sq=Square.from_algebraic(uci[:2]),
            to_sq=Square.from_algebraic(uci[2:4]),
        )

    def __repr__(self) -> str:
        """
        Return a readable move debug form.

        Returns:
            str: Human-readable string.

        Complexity:
            O(1) for ordinary coordinates.
        """
        return f"Move({self.to_uci()} [{self.flag.name}])"


@dataclass(frozen=True)
class SpecialMove(Move):
    """
    Extended move carrying extra context for non-standard actions.

    Extra fields:
        promotion_piece:  Piece type name to promote to (e.g. 'Queen').
        captured_sq:      Square of captured piece if different from to_sq
                          (used for en passant where the capture is off the path).

    Example — promotion:
        SpecialMove(from_sq=e7, to_sq=e8, flag=PROMOTION, promotion_piece='Queen')

    Example — en passant:
        SpecialMove(from_sq=e5, to_sq=d6, flag=EN_PASSANT, captured_sq=d5)

    Args:
        promotion_piece (Optional[str]): Promotion piece name, when this is a promotion.
        captured_sq (Optional[Square]): En-passant capture square when it differs
            from the destination.

    Returns:
        SpecialMove instance: immutable move with promotion or capture metadata.

    Complexity:
        O(1).
    """
    promotion_piece: Optional[str]       = None
    captured_sq:     Optional[Square]    = None

    def to_uci(self) -> str:
        """
        Format the move and promotion suffix.

        Returns:
            str: UCI string.

        Complexity:
            O(1) for ordinary coordinates.
        """
        base = super().to_uci()
        if self.promotion_piece:
            if self.promotion_piece.lower() == "knight":
                return base + "n"
            else:
                return base + self.promotion_piece[0].lower()
        return base
