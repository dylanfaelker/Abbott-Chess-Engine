"""
infinity_chess/move.py

Move representation. All moves are immutable dataclasses.

A Move is the minimal unit of action: from square → to square.
SpecialMove extends this for anything that needs extra context 
(promotion, castling, en passant)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class MoveFlag(Enum):
    """Flags that distinguish special moves from normal ones."""
    NORMAL        = auto()
    CAPTURE       = auto()
    PROMOTION     = auto()
    CASTLE_KING   = auto()
    CASTLE_QUEEN  = auto()
    EN_PASSANT    = auto()


@dataclass(frozen=True)
class Square:
    """
    A position on the board as (rank, file), both 0-indexed.
    rank 0 = row 1, file 0 = a-file.
    """
    rank: int
    file: int

    def to_algebraic(self) -> str:
        """Convert to algebraic notation e.g. (0, 0) → 'a1'."""
        return f"{chr(ord('a') + self.file)}{self.rank + 1}"

    @staticmethod
    def from_algebraic(notation: str) -> "Square":
        """Parse algebraic notation e.g. 'e4' → Square(rank=3, file=4)."""
        if len(notation) < 2:
            raise ValueError(f"Invalid square notation: {notation!r}")
        file = ord(notation[0].lower()) - ord('a')
        rank = int(notation[1:]) - 1
        return Square(rank=rank, file=file)

    def __add__(self, other: tuple[int, int]) -> "Square":
        """Convenient offset: Square(3, 4) + (1, 0) → Square(4, 4)."""
        return Square(self.rank + other[0], self.file + other[1])

    def __repr__(self) -> str:
        return f"Square({self.to_algebraic()})"


@dataclass(frozen=True)
class Move:
    """
    A standard move from one square to another.

    Attributes:
        from_sq:    Origin square.
        to_sq:      Destination square.
        flag:       What kind of move this is (default: NORMAL).
    """
    from_sq: Square
    to_sq:   Square
    flag:    MoveFlag = MoveFlag.NORMAL

    def to_uci(self) -> str:
        """Return UCI string e.g. 'e2e4'."""
        return f"{self.from_sq.to_algebraic()}{self.to_sq.to_algebraic()}"

    @staticmethod
    def from_uci(uci: str) -> "Move":
        """Parse a UCI string e.g. 'e2e4' → Move."""
        if len(uci) < 4:
            raise ValueError(f"Invalid UCI move: {uci!r}")
        return Move(
            from_sq=Square.from_algebraic(uci[:2]),
            to_sq=Square.from_algebraic(uci[2:4]),
        )

    def __repr__(self) -> str:
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
    """
    promotion_piece: Optional[str]       = None
    captured_sq:     Optional[Square]    = None

    def to_uci(self) -> str:
        base = super().to_uci()
        if self.promotion_piece:
            return base + self.promotion_piece[0].lower()
        return base