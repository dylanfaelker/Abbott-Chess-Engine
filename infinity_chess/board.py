"""
infinity_chess/board.py

Board state: the grid, piece positions, and game metadata.
Backed by bitboards plus move undo support.
Complexity notation: N = ranks*files, P = occupied pieces, and H = stored game
history length.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional, Iterator

from infinity_chess.move import Move, MoveFlag, SpecialMove, Square
from infinity_chess.pieces import Colour, Piece, PieceType

#TODO move zobrist hashing to its own file

_ZOBRIST_SEED = 0xDFAE


@dataclass(frozen=True)
class _ZobristKeys:
    """
    Hash tables for one board shape.

    Args:
        ZPIECE (dict[tuple[Colour, PieceType], tuple[int, ...]]): Random key for each
            colour/type combination and square.
        ZTURN (int): Random key toggled when the side to move changes.
        ZEP (tuple[int, ...]): Random key for each en-passant target square.
        ZCASTLE (dict[str, int]): Random key for each castling right.

    Returns:
        _ZobristKeys instance: piece/turn/EP/castling keys; lookup.

    Complexity:
        O(1).
    """

    ZPIECE: dict[tuple[Colour, PieceType], tuple[int, ...]]
    ZTURN: int
    ZEP: tuple[int, ...]
    ZCASTLE: dict[str, int]


_ZOBRIST_KEYS: dict[tuple[int, int], _ZobristKeys] = {}


def _zobrist_keys(ranks: int, files: int) -> _ZobristKeys:
    """
    Return deterministic tables for a board shape.

    Args:
        ranks (int): Number of ranks in the board.
        files (int): Number of files in the board.

    Returns:
        _ZobristKeys: cached tables.

    Complexity:
        O(N) on a cache miss, O(1) on a hit.
    """
    dimensions = (ranks, files)
    keys = _ZOBRIST_KEYS.get(dimensions)
    if keys is None:
        rng = random.Random(_ZOBRIST_SEED)
        size = ranks * files
        piece_keys = {
            (colour, piece_type): tuple(rng.getrandbits(64) for _ in range(size))
            for colour in Colour
            for piece_type in PieceType
        }
        keys = _ZobristKeys(
            ZPIECE=piece_keys,
            ZTURN=rng.getrandbits(64),
            ZEP=tuple(rng.getrandbits(64) for _ in range(size)),
            ZCASTLE={right: rng.getrandbits(64) for right in "KQkq"},
        )
        _ZOBRIST_KEYS[dimensions] = keys
    return keys


_PIECE_CACHE: dict[tuple[PieceType, Colour, bool], Piece] = {}


def _piece_obj(piece_type: PieceType, colour: Colour, has_moved: bool) -> Piece:
    """
    Return the cached immutable piece value.

    Args:
        piece_type (PieceType): Piece kind being queried.
        colour (Colour): Piece side or side being queried.
        has_moved (bool): Whether the piece has moved previously.

    Returns:
        Piece: Cached immutable piece value.

    Complexity:
        O(1) average.
    """
    key = (piece_type, colour, has_moved)
    piece = _PIECE_CACHE.get(key)
    if piece is None:
        piece = Piece(piece_type, colour, has_moved=has_moved)
        _PIECE_CACHE[key] = piece
    return piece


@dataclass(frozen=True)
class UndoState:
    """
    Snapshot of move effects needed to restore a Board.

    Args:
        move (Move): Move being undone.
        moved_piece (Piece): Piece moved by the recorded move.
        captured_piece (Optional[Piece]): Piece captured by the move, or None.
        captured_sq (Optional[Square]): En-passant capture square when it differs
            from the destination.
        prev_en_passant_sq (Optional[Square]): En-passant target before the move.
        prev_halfmove_clock (int): Halfmove clock value before the move.
        prev_fullmove_number (int): Fullmove number before the move.
        prev_turn (Colour): Side to move before the move.
        prev_moved_mask (int): Moved-piece bit mask before the move.
        prev_hash (int): Zobrist hash before the move.

    Returns:
        UndoState instance: state snapshot used to restore the prior position.

    Complexity:
        O(1) to construct.
    """
    move: Move
    moved_piece: Piece
    captured_piece: Optional[Piece]
    captured_sq: Optional[Square]
    prev_en_passant_sq: Optional[Square]
    prev_halfmove_clock: int
    prev_fullmove_number: int
    prev_turn: Colour
    prev_moved_mask: int
    prev_hash: int


class Board:
    """
    Mutable game position for a rectangular board.

    Bitboards are the source of truth for piece placement. A flat occupancy cache
    is maintained so public square lookups stay O(1) without scanning all 12
    piece bitboards. Inputs are dimensions or parsed moves; outputs are position
    queries and serialized state. Basic lookups are O(1), while full-board scans
    are O(ranks*files).

    Args:
        ranks (int): Number of ranks in the board.
        files (int): Number of files in the board.

    Returns:
        Board instance: position state and queries.

    Complexity:
        O(1) for cached lookups and O(N) for full-board operations.
    """

    def __init__(self, ranks: int = 8, files: int = 8):
        """
        Create an empty board.

        Args:
            ranks (int): Number of ranks in the board.
            files (int): Number of files in the board.

        Returns:
            None: Initializes the Board instance.

        Complexity:
            O(N) for the square cache.
        """
        self.ranks = ranks
        self.files = files
        self._zobrist = _zobrist_keys(ranks, files)
        self.hash = 0
        self._board_mask: int = (1 << (ranks * files)) - 1 # Bitboard full of 1s
        self.turn: Colour = Colour.WHITE
        self.en_passant_sq: Optional[Square] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.zobrist_history: list[int] = []  # position hashes after each move

        self.bitboards: dict[tuple[Colour, PieceType], int] = {
            (colour, piece_type): 0
            for colour in Colour
            for piece_type in PieceType
        }
        self._occupied_bitboard = 0
        self._moved_mask: int = 0
        self._square_cache: list[Optional[tuple[PieceType, Colour]]] = [None] * (ranks * files)

    def copy(self) -> "Board":
        """
        Copy the position and histories.

        Returns:
            'Board': independent Board.

        Complexity:
            O(N + H).
        """
        new = Board.__new__(Board)
        new.ranks = self.ranks
        new.files = self.files
        new._zobrist = self._zobrist
        new.hash = self.hash
        new._board_mask = self._board_mask
        new.turn = self.turn
        new.en_passant_sq = self.en_passant_sq
        new.halfmove_clock = self.halfmove_clock
        new.fullmove_number = self.fullmove_number
        new.zobrist_history = self.zobrist_history[:]
        new.bitboards = self.bitboards.copy()
        new._occupied_bitboard = self._occupied_bitboard
        new._moved_mask = self._moved_mask
        new._square_cache = self._square_cache[:]
        return new

    def _index(self, sq: Square) -> int:
        """
        Flatten a square to its bit/cache index.

        Args:
            sq (Square): Source or target board square.

        Returns:
            int: integer index.

        Complexity:
            O(1).
        """
        return sq.rank * self.files + sq.file

    def _mask(self, sq: Square) -> int:
        """
        Return a one-bit mask for a square.

        Args:
            sq (Square): Source or target board square.

        Returns:
            int: integer bitmask.

        Complexity:
            O(1).
        """
        return 1 << self._index(sq)

    def _square_from_index(self, idx: int) -> Square:
        """
        Convert a flat index to a square.

        Args:
            idx (int): Flat board-square index.

        Returns:
            Square: Board coordinate.

        Complexity:
            O(1).
        """
        return Square(idx // self.files, idx % self.files)

    @staticmethod
    def _iter_bits(bitboard: int) -> Iterator[int]:
        """
        Yield indexes of set bits.

        Args:
            bitboard (int): Integer bit mask containing selected board squares.

        Returns:
            Iterator[int]: index iterator.

        Complexity:
            O(k), where k is set-bit count.
        """
        while bitboard:
            lsb = bitboard & -bitboard
            yield lsb.bit_length() - 1
            bitboard ^= lsb

    @staticmethod
    def _entry_symbol(piece_type: PieceType, colour: Colour) -> str:
        """
        Format a piece as a case-sensitive FEN symbol.

        Args:
            piece_type (PieceType): Piece kind being queried.
            colour (Colour): Piece side or side being queried.

        Returns:
            str: one character.

        Complexity:
            O(1).
        """
        symbol = piece_type.symbol()
        return symbol.upper() if colour == Colour.WHITE else symbol

    def _entry_at_index(self, idx: int) -> Optional[tuple[PieceType, Colour]]:
        """
        Read the cached type/colour at an index.

        Args:
            idx (int): Flat board-square index.

        Returns:
            Optional[tuple[PieceType, Colour]]: tuple or None.

        Complexity:
            O(1).
        """
        return self._square_cache[idx]

    def _piece_at_index(self, idx: int) -> Optional[Piece]:
        """
        Build the cached Piece value at an index.

        Args:
            idx (int): Flat board-square index.

        Returns:
            Optional[Piece]: Piece or None.

        Complexity:
            O(1) average.
        """
        entry = self._square_cache[idx]
        if entry is None:
            return None
        piece_type, colour = entry
        has_moved = bool(self._moved_mask & (1 << idx))
        return _piece_obj(piece_type, colour, has_moved)

    def _clear_index(self, idx: int) -> None:
        """
        Remove a piece and update occupancy, bitboards, and hash.

        Args:
            idx (int): Flat board-square index.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        entry = self._square_cache[idx]
        if entry is None:
            return
        piece_type, colour = entry
        mask = 1 << idx
        self.hash ^= self._zobrist.ZPIECE[(colour, piece_type)][idx]
        self.bitboards[(colour, piece_type)] &= ~mask
        self._occupied_bitboard &= ~mask
        self._moved_mask &= ~mask
        self._square_cache[idx] = None

    def _place_piece_at_index(
        self,
        idx: int,
        piece_type: PieceType,
        colour: Colour,
        has_moved: bool,
    ) -> None:
        """
        Place a piece and update occupancy, bitboards, and hash.

        Args:
            idx (int): Flat board-square index.
            piece_type (PieceType): Piece kind being queried.
            colour (Colour): Piece side or side being queried.
            has_moved (bool): Whether the piece has moved previously.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        mask = 1 << idx
        self.hash ^= self._zobrist.ZPIECE[(colour, piece_type)][idx]
        self.bitboards[(colour, piece_type)] |= mask
        self._occupied_bitboard |= mask
        if has_moved:
            self._moved_mask |= mask
        else:
            self._moved_mask &= ~mask
        self._square_cache[idx] = (piece_type, colour)

    def _replace_index(self, idx: int, piece: Optional[Piece]) -> None:
        """
        Replace an indexed square's piece.

        Args:
            idx (int): Flat board-square index.
            piece (Optional[Piece]): Piece involved in the operation.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        self._clear_index(idx)
        if piece is not None:
            self._place_piece_at_index(idx, piece.piece_type, piece.colour, piece.has_moved)

    def _has_unmoved_piece_at_index(self, idx: int, piece_type: PieceType, colour: Colour) -> bool:
        """
        Check for a matching unmoved piece.

        Args:
            idx (int): Flat board-square index.
            piece_type (PieceType): Piece kind being queried.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        entry = self._square_cache[idx]
        if entry != (piece_type, colour):
            return False
        return not bool(self._moved_mask & (1 << idx))

    def get(self, sq: Square) -> Optional[Piece]:
        """
        Look up a piece by square.

        Args:
            sq (Square): Source or target board square.

        Returns:
            Optional[Piece]: Piece or None.

        Complexity:
            O(1).
        """
        return self._piece_at_index(self._index(sq))

    def set(self, sq: Square, piece: Optional[Piece]) -> None:
        """
        Set or clear a square and refresh castling hash state.

        Args:
            sq (Square): Source or target board square.
            piece (Optional[Piece]): Piece involved in the operation.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        old_castling = set(self._castling_rights())
        self._replace_index(self._index(sq), piece)
        new_castling = set(self._castling_rights())
        for right in old_castling ^ new_castling:
            self.hash ^= self._zobrist.ZCASTLE[right]

    def colour_bitboard(self, colour: Colour) -> int:
        """
        Return a side's occupied-square mask.

        Args:
            colour (Colour): Piece side or side being queried.

        Returns:
            int: bitboard.

        Complexity:
            O(1).
        """
        return (
            self.bitboards[(colour, PieceType.PAWN)]
            | self.bitboards[(colour, PieceType.KNIGHT)]
            | self.bitboards[(colour, PieceType.BISHOP)]
            | self.bitboards[(colour, PieceType.ROOK)]
            | self.bitboards[(colour, PieceType.QUEEN)]
            | self.bitboards[(colour, PieceType.KING)]
        )

    def piece_bitboard(self, colour: Colour, piece_type: PieceType) -> int:
        """
        Return one piece-type mask.

        Args:
            colour (Colour): Piece side or side being queried.
            piece_type (PieceType): Piece kind being queried.

        Returns:
            int: bitboard.

        Complexity:
            O(1).
        """
        return self.bitboards[(colour, piece_type)]

    def occupied_bitboard(self) -> int:
        """
        Return the cached mask of occupied squares.

        Returns:
            int: bitboard.

        Complexity:
            O(1).
        """
        return self._occupied_bitboard

    def empty_bitboard(self) -> int:
        """
        Return the mask of empty in-bounds squares.

        Returns:
            int: bitboard.

        Complexity:
            O(1).
        """
        return self._board_mask ^ self.occupied_bitboard()

    def opponent_bitboard(self, colour: Colour) -> int:
        """
        Return the opposing side's occupied-square mask.

        Args:
            colour (Colour): Piece side or side being queried.

        Returns:
            int: bitboard.

        Complexity:
            O(1).
        """
        return self.colour_bitboard(colour.opponent())

    def squares_in_bitboard(self, bitboard: int) -> Iterator[Square]:
        """
        Yield set-bit squares from least to greatest index.

        Args:
            bitboard (int): Integer bit mask containing selected board squares.

        Returns:
            Iterator[Square]: Square iterator.

        Complexity:
            O(k).
        """
        for idx in self._iter_bits(bitboard):
            yield self._square_from_index(idx)

    def first_square_in_bitboard(self, bitboard: int) -> Optional[Square]:
        """
        Return the least-significant square in a non-empty bitboard.
        First means starting from a1, going across to h1, then a2 and so on

        Args:
            bitboard (int): Integer bit mask containing selected board squares.

        Returns:
            Optional[Square]: Square or None.

        Complexity:
            O(1).
        """
        if bitboard == 0:
            return None
        idx = (bitboard & -bitboard).bit_length() - 1
        return self._square_from_index(idx)

    def bitboard_contains(self, bitboard: int, sq: Square) -> bool:
        """
        Test membership of a square in a bitboard.

        Args:
            bitboard (int): Integer bit mask containing selected board squares.
            sq (Square): Source or target board square.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        return bool(bitboard & self._mask(sq))

    def is_empty(self, sq: Square) -> bool:
        """
        Test whether a square is empty.

        Args:
            sq (Square): Source or target board square.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        return self._entry_at_index(self._index(sq)) is None

    def in_bounds(self, sq: Square) -> bool:
        """
        Test whether a square lies inside the board.

        Args:
            sq (Square): Source or target board square.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(1).
        """
        return 0 <= sq.rank < self.ranks and 0 <= sq.file < self.files

    # ── Iteration helpers ─────────────────────────────────────────────────────

    def all_squares(self) -> Iterator[Square]:
        """
        Yield every board square in rank/file order.

        Returns:
            Iterator[Square]: square iterator.

        Complexity:
            O(N).
        """
        for r in range(self.ranks):
            for f in range(self.files):
                yield Square(r, f)

    def pieces_for(self, colour: Colour) -> Iterator[tuple[Square, Piece]]:
        """
        Yield occupied squares and pieces for one colour.

        Args:
            colour (Colour): Piece side or side being queried.

        Returns:
            Iterator[tuple[Square, Piece]]: iterator of occupied entries.

        Complexity:
            O(P_colour).
        """
        for idx in self._iter_bits(self.colour_bitboard(colour)):
            piece = self._piece_at_index(idx)
            if piece is not None:
                yield self._square_from_index(idx), piece

    def find_piece(self, piece_type: PieceType, colour: Colour) -> Optional[Square]:
        """
        Find the least-indexed piece of a type and colour.

        Args:
            piece_type (PieceType): Piece kind being queried.
            colour (Colour): Piece side or side being queried.

        Returns:
            Optional[Square]: Square or None.

        Complexity:
            O(1).
        """
        return self.first_square_in_bitboard(self.piece_bitboard(colour, piece_type))

    # ── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> "Board":
        """
        Copy the board and apply a move.

        Args:
            move (Move): Move to apply or inspect.

        Returns:
            'Board': new Board.

        Complexity:
            O(N + H).
        """
        new_board = self.copy()
        new_board.make_move(move)
        return new_board

    def make_move(self, move: Move) -> UndoState:
        """
        Apply a move in place and save undo/hash history.

        Args:
            move (Move): Move to apply or inspect.

        Returns:
            UndoState: UndoState.

        Complexity:
            O(1) average.
        """
        prev_hash = self.hash
        from_idx = self._index(move.from_sq)
        to_idx = self._index(move.to_sq)
        piece = self._piece_at_index(from_idx)
        if piece is None:
            raise ValueError(f"No piece on {move.from_sq}")

        for right in self._castling_rights():
            self.hash ^= self._zobrist.ZCASTLE[right]
        if self.en_passant_sq is not None:
            self.hash ^= self._zobrist.ZEP[self._index(self.en_passant_sq)]

        captured_idx: Optional[int] = None
        captured_piece: Optional[Piece] = None

        if move.flag == MoveFlag.EN_PASSANT:
            captured_sq = (
                move.captured_sq
                if isinstance(move, SpecialMove) and move.captured_sq is not None
                else Square(move.from_sq.rank, move.to_sq.file)
            )
            captured_idx = self._index(captured_sq)
            captured_piece = self._piece_at_index(captured_idx)
        elif move.flag not in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            captured_idx = to_idx
            captured_piece = self._piece_at_index(to_idx)

        undo = UndoState(
            move=move,
            moved_piece=piece,
            captured_piece=captured_piece,
            captured_sq=self._square_from_index(captured_idx) if captured_piece is not None else None,
            prev_en_passant_sq=self.en_passant_sq,
            prev_halfmove_clock=self.halfmove_clock,
            prev_fullmove_number=self.fullmove_number,
            prev_turn=self.turn,
            prev_moved_mask=self._moved_mask,
            prev_hash=prev_hash,
        )

        self.en_passant_sq = None
        self._apply_move_no_history(move, from_idx, to_idx, piece, captured_idx)

        is_capture = captured_piece is not None
        is_pawn_move = piece.piece_type == PieceType.PAWN
        from_rank = from_idx // self.files
        to_rank = to_idx // self.files

        if is_pawn_move and abs(to_rank - from_rank) == 2:
            ep_rank = (from_rank + to_rank) // 2
            ep_file = from_idx % self.files
            self.en_passant_sq = Square(ep_rank, ep_file)

        self.halfmove_clock = 0 if (is_capture or is_pawn_move) else self.halfmove_clock + 1

        if self.turn == Colour.BLACK:
            self.fullmove_number += 1

        self.turn = self.turn.opponent()
        self.hash ^= self._zobrist.ZTURN
        if self.en_passant_sq is not None:
            self.hash ^= self._zobrist.ZEP[self._index(self.en_passant_sq)]
        for right in self._castling_rights():
            self.hash ^= self._zobrist.ZCASTLE[right]
        self.zobrist_history.append(self.zobrist_hash())
        return undo

    def unmake_move(self, undo: UndoState) -> None:
        """
        Restore a position from its undo snapshot.

        Args:
            undo (UndoState): Undo snapshot returned by a previous move application.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        move = undo.move
        from_idx = self._index(move.from_sq)
        to_idx = self._index(move.to_sq)

        if self.zobrist_history:
            self.zobrist_history.pop()

        if move.flag in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            self._clear_index(to_idx)
            self._place_piece_at_index(
                from_idx,
                undo.moved_piece.piece_type,
                undo.moved_piece.colour,
                undo.moved_piece.has_moved,
            )

            rank_base = (from_idx // self.files) * self.files
            if move.flag == MoveFlag.CASTLE_KING:
                rook_from_idx = rank_base + self.files - 1
                rook_to_idx = to_idx - 1
            else:
                rook_from_idx = rank_base
                rook_to_idx = to_idx + 1

            self._clear_index(rook_to_idx)
            self._place_piece_at_index(rook_from_idx, PieceType.ROOK, undo.moved_piece.colour, False)
        else:
            self._clear_index(to_idx)
            self._place_piece_at_index(
                from_idx,
                undo.moved_piece.piece_type,
                undo.moved_piece.colour,
                undo.moved_piece.has_moved,
            )
            if undo.captured_piece is not None and undo.captured_sq is not None:
                captured_idx = self._index(undo.captured_sq)
                self._place_piece_at_index(
                    captured_idx,
                    undo.captured_piece.piece_type,
                    undo.captured_piece.colour,
                    undo.captured_piece.has_moved,
                )

        self.turn = undo.prev_turn
        self.en_passant_sq = undo.prev_en_passant_sq
        self.halfmove_clock = undo.prev_halfmove_clock
        self.fullmove_number = undo.prev_fullmove_number
        self._moved_mask = undo.prev_moved_mask
        self.hash = undo.prev_hash

    def _apply_move_no_history(
        self,
        move: Move,
        from_idx: int,
        to_idx: int,
        piece: Piece,
        captured_idx: Optional[int],
    ) -> None:
        """
        Apply piece-placement effects without history updates.

        Args:
            move (Move): Move to apply or inspect.
            from_idx (int): Flat index of the move origin.
            to_idx (int): Flat index of the move destination.
            piece (Piece): Piece involved in the operation.
            captured_idx (Optional[int]): Flat index of the captured square.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        if captured_idx is not None:
            self._clear_index(captured_idx)

        if move.flag in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            self._apply_castle(move.flag, from_idx, to_idx, piece.colour)
            return

        self._clear_index(from_idx)

        if move.flag in (MoveFlag.PROMOTION, MoveFlag.PROMOTION_CAPTURE):
            promo_name = (
                move.promotion_piece
                if isinstance(move, SpecialMove) and move.promotion_piece
                else "QUEEN"
            )
            promo_type = PieceType[promo_name.upper()]
            self._place_piece_at_index(to_idx, promo_type, piece.colour, True)
            return

        self._place_piece_at_index(to_idx, piece.piece_type, piece.colour, True)

    def _apply_castle(self, flag: MoveFlag, from_idx: int, to_idx: int, colour: Colour) -> None:
        """
        Move king and edge rook for castling.

        Args:
            flag (MoveFlag): Move category or operation flag.
            from_idx (int): Flat index of the move origin.
            to_idx (int): Flat index of the move destination.
            colour (Colour): Piece side or side being queried.

        Returns:
            None: No value is returned; the operation updates state in place.

        Complexity:
            O(1).
        """
        rank_base = (from_idx // self.files) * self.files
        if flag == MoveFlag.CASTLE_KING:
            rook_from_idx = rank_base + self.files - 1
            rook_to_idx = to_idx - 1
        else:
            rook_from_idx = rank_base
            rook_to_idx = to_idx + 1

        rook_entry = self._entry_at_index(rook_from_idx)
        self._clear_index(from_idx)
        self._place_piece_at_index(to_idx, PieceType.KING, colour, True)

        if rook_entry is not None:
            rook_type, rook_colour = rook_entry
            self._clear_index(rook_from_idx)
            self._place_piece_at_index(rook_to_idx, rook_type, rook_colour, True)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_fen_position(self) -> str:
        """
        Serialize piece placement only.

        Returns:
            str: FEN placement string.

        Complexity:
            O(N).
        """
        rows = []
        for rank in range(self.ranks - 1, -1, -1):
            empty = 0
            row = ""
            row_start = rank * self.files
            for file in range(self.files):
                idx = row_start + file
                entry = self._entry_at_index(idx)
                if entry is None:
                    empty += 1
                    continue
                if empty:
                    row += str(empty)
                    empty = 0
                piece_type, colour = entry
                row += self._entry_symbol(piece_type, colour)
            if empty:
                row += str(empty)
            rows.append(row)

        return "/".join(rows)

    def to_fen(self) -> str:
        """
        Serialize position and game metadata as FEN.

        Returns:
            str: FEN string.

        Complexity:
            O(N).
        """
        position = self.to_fen_position()
        turn_char = "w" if self.turn == Colour.WHITE else "b"
        ep = self.en_passant_sq.to_algebraic() if self.en_passant_sq else "-"
        castling = self._castling_rights() or "-"
        return f"{position} {turn_char} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        """
        Parse a FEN-like position and infer its dimensions.

        Args:
            fen (str): FEN text describing the position.

        Returns:
            'Board': Parsed Board instance.

        Complexity:
            O(F + N), where F is string length.
        """
        parts = fen.strip().split()
        if not parts:
            raise ValueError("FEN is missing piece placement")

        rows = parts[0].split("/")
        parsed_rows: list[list[tuple[int, PieceType, Colour]]] = []
        row_widths: list[int] = []
        for row in rows:
            file_idx = 0
            pieces: list[tuple[int, PieceType, Colour]] = []
            char_idx = 0
            while char_idx < len(row):
                ch = row[char_idx]
                if "0" <= ch <= "9":
                    run_end = char_idx + 1
                    while run_end < len(row) and "0" <= row[run_end] <= "9":
                        run_end += 1
                    empty_count = int(row[char_idx:run_end])
                    if empty_count == 0:
                        raise ValueError("FEN empty-square counts must be one or more")
                    file_idx += empty_count
                    char_idx = run_end
                    continue

                colour = Colour.WHITE if ch.isupper() else Colour.BLACK
                piece_type = PieceType.from_symbol(ch)
                pieces.append((file_idx, piece_type, colour))
                file_idx += 1
                char_idx += 1

            parsed_rows.append(pieces)
            row_widths.append(file_idx)

        if not rows or row_widths[0] == 0:
            raise ValueError("FEN piece placement must have at least one rank and file")
        if any(width != row_widths[0] for width in row_widths):
            raise ValueError(f"FEN rows have inconsistent widths: {row_widths}")

        board = cls(len(rows), row_widths[0])
        for rank_idx, row_pieces in enumerate(reversed(parsed_rows)):
            for file_idx, piece_type, colour in row_pieces:
                idx = rank_idx * board.files + file_idx
                board._place_piece_at_index(idx, piece_type, colour, False)

        if len(parts) > 1:
            board.turn = Colour.WHITE if parts[1] == "w" else Colour.BLACK
        if len(parts) > 2:
            castling = parts[2]

            def set_has_moved_idx(
                idx: int,
                expected_type: PieceType,
                expected_colour: Colour,
                has_moved: bool,
            ) -> None:
                """
                Set moved status only when the indexed piece matches.

                Args:
                    idx (int): Flat board-square index.
                    expected_type (PieceType): Piece type expected at the square.
                    expected_colour (Colour): Piece colour expected at the square.
                    has_moved (bool): Whether the piece has moved previously.

                Returns:
                    None: No value is returned; the operation updates state in place.

                Complexity:
                    O(1).
                """
                if board._entry_at_index(idx) == (expected_type, expected_colour):
                    board._clear_index(idx)
                    board._place_piece_at_index(idx, expected_type, expected_colour, has_moved)

            white_has_castling = "K" in castling or "Q" in castling
            black_has_castling = "k" in castling or "q" in castling
            king_home_file = board.files // 2

            set_has_moved_idx(king_home_file, PieceType.KING, Colour.WHITE, not white_has_castling)
            set_has_moved_idx(0, PieceType.ROOK, Colour.WHITE, "Q" not in castling)
            set_has_moved_idx(board.files - 1, PieceType.ROOK, Colour.WHITE, "K" not in castling)

            black_rank_base = (board.ranks - 1) * board.files
            set_has_moved_idx(
                black_rank_base + king_home_file,
                PieceType.KING,
                Colour.BLACK,
                not black_has_castling,
            )
            set_has_moved_idx(black_rank_base, PieceType.ROOK, Colour.BLACK, "q" not in castling)
            set_has_moved_idx(
                black_rank_base + board.files - 1,
                PieceType.ROOK,
                Colour.BLACK,
                "k" not in castling,
            )
        if len(parts) > 3 and parts[3] != "-":
            board.en_passant_sq = Square.from_algebraic(parts[3])
        if len(parts) > 4:
            board.halfmove_clock = int(parts[4])
        if len(parts) > 5:
            board.fullmove_number = int(parts[5])

        board.hash = board.recompute_hash()
        return board

    @classmethod
    def standard(cls) -> "Board":
        """
        Build the standard 8x8 chess start.

        Returns:
            'Board': initialized Board.

        Complexity:
            O(1) for its fixed 64 squares.
        """
        board = cls(8, 8)
        back_rank = [
            PieceType.ROOK,
            PieceType.KNIGHT,
            PieceType.BISHOP,
            PieceType.QUEEN,
            PieceType.KING,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
        ]
        for file_idx, piece_type in enumerate(back_rank):
            board._place_piece_at_index(file_idx, piece_type, Colour.WHITE, False)
            board._place_piece_at_index(board.files + file_idx, PieceType.PAWN, Colour.WHITE, False)
            board._place_piece_at_index((board.ranks - 2) * board.files + file_idx, PieceType.PAWN, Colour.BLACK, False)
            board._place_piece_at_index((board.ranks - 1) * board.files + file_idx, piece_type, Colour.BLACK, False)
        board.hash = board.recompute_hash()
        return board

    def _castling_rights(self) -> str:
        """
        Return rights supported by unmoved home pieces.

        Returns:
            str: up to four FEN letters.

        Complexity:
            O(1).
        """
        rights = ""
        king_home_file = self.files // 2
        if self._has_unmoved_piece_at_index(king_home_file, PieceType.KING, Colour.WHITE):
            if self._has_unmoved_piece_at_index(self.files - 1, PieceType.ROOK, Colour.WHITE):
                rights += "K"
            if self._has_unmoved_piece_at_index(0, PieceType.ROOK, Colour.WHITE):
                rights += "Q"

        black_rank_base = (self.ranks - 1) * self.files
        if self._has_unmoved_piece_at_index(
            black_rank_base + king_home_file,
            PieceType.KING,
            Colour.BLACK,
        ):
            if self._has_unmoved_piece_at_index(
                black_rank_base + self.files - 1,
                PieceType.ROOK,
                Colour.BLACK,
            ):
                rights += "k"
            if self._has_unmoved_piece_at_index(black_rank_base, PieceType.ROOK, Colour.BLACK):
                rights += "q"
        return rights

    # ── Hashing (for transposition table) ─────────────────────────────────────

    def recompute_hash(self) -> int:
        """
        Rebuild the hash from pieces and metadata.

        Returns:
            int: 64-bit integer.

        Complexity:
            O(P), where P is piece count.
        """
        h = 0

        for colour in Colour:
            for piece_type in PieceType:
                piece_bb = self.bitboards[(colour, piece_type)]
                while piece_bb:
                    lsb = piece_bb & -piece_bb
                    idx = lsb.bit_length() - 1
                    h ^= self._zobrist.ZPIECE[(colour, piece_type)][idx]
                    piece_bb ^= lsb

        # Side to move
        if self.turn == Colour.BLACK:
            h ^= self._zobrist.ZTURN

        # En passant square
        if self.en_passant_sq is not None:
            h ^= self._zobrist.ZEP[self._index(self.en_passant_sq)]

        # Castling rights
        for right in self._castling_rights():
            h ^= self._zobrist.ZCASTLE[right]

        return h

    def zobrist_hash(self) -> int:
        """
        Return the incrementally maintained position hash.

        Returns:
            int: 64-bit integer.

        Complexity:
            O(1).
        """
        return self.hash

    def __repr__(self) -> str:
        """
        Render the board as a human-readable grid.

        Returns:
            str: Human-readable string.

        Complexity:
            O(N).
        """
        lines = []
        for rank in range(self.ranks - 1, -1, -1):
            row = f"{rank + 1} "
            row_start = rank * self.files
            for file in range(self.files):
                entry = self._entry_at_index(row_start + file)
                if entry is None:
                    row += ". "
                    continue
                piece_type, colour = entry
                row += self._entry_symbol(piece_type, colour) + " "
            lines.append(row)
        lines.append("  " + " ".join(chr(ord("a") + file) for file in range(self.files)))
        lines.append(f"Turn: {self.turn.value}  Move: {self.fullmove_number}")
        return "\n".join(lines)
