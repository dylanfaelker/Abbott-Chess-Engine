"""
infinity_chess/pieces.py

Piece class - pure data class
Lookups use fixed-size enums and take O(1) time.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Colour(Enum):
    """
    One side of a chess position.

    Returns:
        Colour member: identity for one side of the position.

    Complexity:
        O(1).
    """
    WHITE = "white"
    BLACK = "black"

    def opponent(self) -> "Colour":
        """
        Return the opposing side.

        Returns:
            'Colour': Colour.

        Complexity:
            O(1).
        """
        return Colour.BLACK if self == Colour.WHITE else Colour.WHITE

    def __repr__(self) -> str:
        """
        Return the lowercase side name.

        Returns:
            str: Human-readable string.

        Complexity:
            O(1).
        """
        return self.value


class PieceType(Enum):
    """
    All recognised piece types.

    Returns:
        PieceType member: identity used by rules and evaluation.

    Complexity:
        O(1).
    """
    PAWN   = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK   = "rook"
    QUEEN  = "queen"
    KING   = "king"

    def symbol(self) -> str:
        """
        Single-character symbol used in FEN-style notation.

        Returns:
            str: lowercase piece letter.

        Complexity:
            O(1).
        """
        return {
            PieceType.PAWN:   'p',
            PieceType.KNIGHT: 'n',
            PieceType.BISHOP: 'b',
            PieceType.ROOK:   'r',
            PieceType.QUEEN:  'q',
            PieceType.KING:   'k',
        }.get(self, self.value[0])

    @staticmethod
    def from_symbol(symbol: str) -> "PieceType":
        """
        Parse a FEN piece letter.

        Args:
            symbol (str): Single-character piece symbol.

        Returns:
            'PieceType': PieceType.

        Complexity:
            O(1) for the fixed six-piece table.
        """
        lookup = {pt.symbol(): pt for pt in PieceType}
        s = symbol.lower()
        if s not in lookup:
            raise ValueError(f"Unknown piece symbol: {symbol!r}")
        return lookup[s]

    def is_sliding(self) -> bool:
        """
        True for pieces that move along lines (bishop, rook, queen).

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        return self in {PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN}


@dataclass(frozen=True)
class Piece:
    """
    An immutable piece identity: what type it is and which side owns it.

    Frozen so pieces can be used as dict keys and in sets.
    Board stores Piece objects (or None) on each square.

    Args:
        piece_type (PieceType): Kind of chess piece.
        colour (Colour): Side that owns the piece.
        has_moved (bool): Whether this piece has already moved.

    Returns:
        Piece instance: immutable piece value.

    Complexity:
        O(1) to construct, compare, or hash.
    """
    piece_type: PieceType
    colour:     Colour

    # Tracks whether this piece has moved — needed for castling rights, pawn double-push eligibility
    has_moved: bool = False

    def symbol(self) -> str:
        """
        Upper-case for white, lower-case for black.
        Matches standard FEN convention.

        Returns:
            str: one-character FEN symbol.

        Complexity:
            O(1).
        """
        s = self.piece_type.symbol()
        return s.upper() if self.colour == Colour.WHITE else s.lower()

    def is_opponent(self, other: "Piece") -> bool:
        """
        Compare this piece's colour with another.

        Args:
            other ('Piece'): Offset tuple or comparison value supplied by the caller.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        return self.colour != other.colour

    def with_moved(self) -> "Piece":
        """
        Copy this piece with moved status set.

        Returns:
            'Piece': Piece.

        Complexity:
            O(1).
        """
        return Piece(self.piece_type, self.colour, has_moved=True)

    def __repr__(self) -> str:
        """
        Return a readable colour/type label.

        Returns:
            str: Human-readable string.

        Complexity:
            O(1).
        """
        return f"{self.colour.value} {self.piece_type.value}"



def make_piece(piece_type: PieceType, colour: Colour) -> Piece:
    """
    Construct an unmoved piece.

    Args:
        piece_type (PieceType): Piece kind being queried.
        colour (Colour): Piece side or side being queried.

    Returns:
        Piece: Cached immutable piece value.

    Complexity:
        O(1).
    """
    return Piece(piece_type=piece_type, colour=colour)


W_PAWN   = Piece(PieceType.PAWN,   Colour.WHITE)
W_KNIGHT = Piece(PieceType.KNIGHT, Colour.WHITE)
W_BISHOP = Piece(PieceType.BISHOP, Colour.WHITE)
W_ROOK   = Piece(PieceType.ROOK,   Colour.WHITE)
W_QUEEN  = Piece(PieceType.QUEEN,  Colour.WHITE)
W_KING   = Piece(PieceType.KING,   Colour.WHITE)

B_PAWN   = Piece(PieceType.PAWN,   Colour.BLACK)
B_KNIGHT = Piece(PieceType.KNIGHT, Colour.BLACK)
B_BISHOP = Piece(PieceType.BISHOP, Colour.BLACK)
B_ROOK   = Piece(PieceType.ROOK,   Colour.BLACK)
B_QUEEN  = Piece(PieceType.QUEEN,  Colour.BLACK)
B_KING   = Piece(PieceType.KING,   Colour.BLACK)
