"""
infinity_chess/board.py

Board state: the grid, piece positions, and game metadata.
Backed by bitboards plus move undo support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterator

from infinity_chess.move import Move, MoveFlag, SpecialMove, Square
from infinity_chess.pieces import Colour, Piece, PieceType


_PIECE_CACHE: dict[tuple[PieceType, Colour, bool], Piece] = {}


def _piece_obj(piece_type: PieceType, colour: Colour, has_moved: bool) -> Piece:
    key = (piece_type, colour, has_moved)
    piece = _PIECE_CACHE.get(key)
    if piece is None:
        piece = Piece(piece_type, colour, has_moved=has_moved)
        _PIECE_CACHE[key] = piece
    return piece


@dataclass(frozen=True)
class UndoState:
    move: Move
    moved_piece: Piece
    captured_piece: Optional[Piece]
    captured_sq: Optional[Square]
    prev_en_passant_sq: Optional[Square]
    prev_halfmove_clock: int
    prev_fullmove_number: int
    prev_turn: Colour
    prev_moved_mask: int


class Board:
    """
    The game board.

    Bitboards are the source of truth for piece placement. A flat occupancy cache
    is maintained so public square lookups stay O(1) without scanning all 12
    piece bitboards.
    """

    def __init__(self, ranks: int = 8, files: int = 8):
        self.ranks = ranks
        self.files = files
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
        self._moved_mask: int = 0
        self._square_cache: list[Optional[tuple[PieceType, Colour]]] = [None] * (ranks * files)

    def copy(self) -> "Board":
        new = Board.__new__(Board)
        new.ranks = self.ranks
        new.files = self.files
        new._board_mask = self._board_mask
        new.turn = self.turn
        new.en_passant_sq = self.en_passant_sq
        new.halfmove_clock = self.halfmove_clock
        new.fullmove_number = self.fullmove_number
        new.zobrist_history = self.zobrist_history[:]
        new.bitboards = self.bitboards.copy()
        new._moved_mask = self._moved_mask
        new._square_cache = self._square_cache[:]
        return new

    def _index(self, sq: Square) -> int:
        return sq.rank * self.files + sq.file

    def _mask(self, sq: Square) -> int:
        return 1 << self._index(sq)

    def _square_from_index(self, idx: int) -> Square:
        return Square(idx // self.files, idx % self.files)

    @staticmethod
    def _iter_bits(bitboard: int) -> Iterator[int]:
        """ Iterator for indexes of active bits."""
        while bitboard:
            lsb = bitboard & -bitboard
            yield lsb.bit_length() - 1
            bitboard ^= lsb

    @staticmethod
    def _entry_symbol(piece_type: PieceType, colour: Colour) -> str:
        symbol = piece_type.symbol()
        return symbol.upper() if colour == Colour.WHITE else symbol

    def _entry_at_index(self, idx: int) -> Optional[tuple[PieceType, Colour]]:
        return self._square_cache[idx]

    def _piece_at_index(self, idx: int) -> Optional[Piece]:
        entry = self._square_cache[idx]
        if entry is None:
            return None
        piece_type, colour = entry
        has_moved = bool(self._moved_mask & (1 << idx))
        return _piece_obj(piece_type, colour, has_moved)

    def _clear_index(self, idx: int) -> None:
        entry = self._square_cache[idx]
        if entry is None:
            return
        piece_type, colour = entry
        mask = 1 << idx
        self.bitboards[(colour, piece_type)] &= ~mask
        self._moved_mask &= ~mask
        self._square_cache[idx] = None

    def _place_piece_at_index(
        self,
        idx: int,
        piece_type: PieceType,
        colour: Colour,
        has_moved: bool,
    ) -> None:
        mask = 1 << idx
        self.bitboards[(colour, piece_type)] |= mask
        if has_moved:
            self._moved_mask |= mask
        else:
            self._moved_mask &= ~mask
        self._square_cache[idx] = (piece_type, colour)

    def _replace_index(self, idx: int, piece: Optional[Piece]) -> None:
        self._clear_index(idx)
        if piece is not None:
            self._place_piece_at_index(idx, piece.piece_type, piece.colour, piece.has_moved)

    def _has_unmoved_piece_at_index(self, idx: int, piece_type: PieceType, colour: Colour) -> bool:
        entry = self._square_cache[idx]
        if entry != (piece_type, colour):
            return False
        return not bool(self._moved_mask & (1 << idx))

    def get(self, sq: Square) -> Optional[Piece]:
        return self._piece_at_index(self._index(sq))

    def set(self, sq: Square, piece: Optional[Piece]) -> None:
        self._replace_index(self._index(sq), piece)

    def colour_bitboard(self, colour: Colour) -> int:
        """Return all occupied squares for one side."""
        return (
            self.bitboards[(colour, PieceType.PAWN)]
            | self.bitboards[(colour, PieceType.KNIGHT)]
            | self.bitboards[(colour, PieceType.BISHOP)]
            | self.bitboards[(colour, PieceType.ROOK)]
            | self.bitboards[(colour, PieceType.QUEEN)]
            | self.bitboards[(colour, PieceType.KING)]
        )

    def piece_bitboard(self, colour: Colour, piece_type: PieceType) -> int:
        """Return the bitboard for one colour/piece-type pair."""
        return self.bitboards[(colour, piece_type)]

    def occupied_bitboard(self) -> int:
        """Return all occupied squares on the board."""
        return self.colour_bitboard(Colour.WHITE) | self.colour_bitboard(Colour.BLACK)

    def empty_bitboard(self) -> int:
        """Return all empty squares inside the board bounds."""
        return self._board_mask ^ self.occupied_bitboard()

    def opponent_bitboard(self, colour: Colour) -> int:
        """Return all occupied squares for the opposing side."""
        return self.colour_bitboard(colour.opponent())

    def squares_in_bitboard(self, bitboard: int) -> Iterator[Square]:
        """Yield squares contained in a bitboard, least-significant bit first."""
        for idx in self._iter_bits(bitboard):
            yield self._square_from_index(idx)

    def first_square_in_bitboard(self, bitboard: int) -> Optional[Square]:
        """
        Return the least-significant square in a non-empty bitboard.
        First means starting from a1, going across to h1, then a2 and so on
        """
        if bitboard == 0:
            return None
        idx = (bitboard & -bitboard).bit_length() - 1
        return self._square_from_index(idx)

    def bitboard_contains(self, bitboard: int, sq: Square) -> bool:
        """Return True if the bitboard contains the given square."""
        return bool(bitboard & self._mask(sq))

    def is_empty(self, sq: Square) -> bool:
        return self._entry_at_index(self._index(sq)) is None

    def in_bounds(self, sq: Square) -> bool:
        return 0 <= sq.rank < self.ranks and 0 <= sq.file < self.files

    # ── Iteration helpers ─────────────────────────────────────────────────────

    def all_squares(self) -> Iterator[Square]:
        for r in range(self.ranks):
            for f in range(self.files):
                yield Square(r, f)

    def pieces_for(self, colour: Colour) -> Iterator[tuple[Square, Piece]]:
        for idx in self._iter_bits(self.colour_bitboard(colour)):
            piece = self._piece_at_index(idx)
            if piece is not None:
                yield self._square_from_index(idx), piece

    def find_piece(self, piece_type: PieceType, colour: Colour) -> Optional[Square]:
        return self.first_square_in_bitboard(self.piece_bitboard(colour, piece_type))

    # ── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> "Board":
        """Return a new Board with the move applied. Original is never mutated."""
        new_board = self.copy()
        new_board.make_move(move)
        return new_board

    def make_move(self, move: Move) -> UndoState:
        from_idx = self._index(move.from_sq)
        to_idx = self._index(move.to_sq)
        piece = self._piece_at_index(from_idx)
        if piece is None:
            raise ValueError(f"No piece on {move.from_sq}")

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
        self.zobrist_history.append(self.zobrist_hash())
        return undo

    def unmake_move(self, undo: UndoState) -> None:
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

    def _apply_move_no_history(
        self,
        move: Move,
        from_idx: int,
        to_idx: int,
        piece: Piece,
        captured_idx: Optional[int],
    ) -> None:
        if captured_idx is not None:
            self._clear_index(captured_idx)

        if move.flag in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            self._apply_castle(move.flag, from_idx, to_idx, piece.colour)
            return

        self._clear_index(from_idx)

        if move.flag == MoveFlag.PROMOTION:
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
        """A FEN notation of the position without the extra metadata."""
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
        position = self.to_fen_position()
        turn_char = "w" if self.turn == Colour.WHITE else "b"
        ep = self.en_passant_sq.to_algebraic() if self.en_passant_sq else "-"
        castling = self._castling_rights() or "-"
        return f"{position} {turn_char} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
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

        return board

    @classmethod
    def standard(cls) -> "Board":
        """Return a board in the standard chess starting position."""
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
        return board

    def _castling_rights(self) -> str:
        """Return the active castling rights string (e.g. 'KQk') for the current position."""
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

    _ZOBRIST_PIECE_MULTIPLIER = 0x2320966b7560cd4c
    _ZOBRIST_TURN_KEY         = 0x685e6f47d3d50ebd
    _ZOBRIST_EP_MULTIPLIER    = 0x329f754e8d3eeb7d
    _ZOBRIST_CASTLING_KEYS = {
        'K': 0xa74de7cd7f596f2d,
        'Q': 0x2f1b3144324b8b3f,
        'k': 0x9ef981efebe4f71a,
        'q': 0x5b9bc9438dbbeb34,
    }

    def zobrist_hash(self) -> int:
        h = 0
 
        for colour in Colour:
            for piece_type in PieceType:
                piece_bb = self.bitboards[(colour, piece_type)]
                while piece_bb:
                    lsb = piece_bb & -piece_bb
                    idx = lsb.bit_length() - 1
                    rank = idx // self.files
                    file = idx % self.files
                    has_moved = bool(self._moved_mask & lsb)
                    piece_key = hash((piece_type, colour, rank, file, has_moved))
                    h ^= piece_key * self._ZOBRIST_PIECE_MULTIPLIER
                    piece_bb ^= lsb
 
        # Side to move
        if self.turn == Colour.BLACK:
            h ^= self._ZOBRIST_TURN_KEY
 
        # En passant file
        if self.en_passant_sq:
            h ^= hash((self.en_passant_sq.rank, self.en_passant_sq.file)) * self._ZOBRIST_EP_MULTIPLIER
 
        # Castling rights
        for right in self._castling_rights():
            h ^= self._ZOBRIST_CASTLING_KEYS[right]
 
        return h & 0xFFFFFFFFFFFFFFFF

    def __repr__(self) -> str:
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
