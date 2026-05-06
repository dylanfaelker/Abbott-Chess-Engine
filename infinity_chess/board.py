"""
infinity_chess/board.py

Board state: the grid, piece positions, and game metadata.
Backed by bitboards plus move undo support.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Iterator

from infinity_chess.pieces import Piece, PieceType, Colour, make_piece
from infinity_chess.pieces import W_PAWN, W_KNIGHT, W_BISHOP, W_ROOK, W_QUEEN, W_KING
from infinity_chess.pieces import B_PAWN, B_KNIGHT, B_BISHOP, B_ROOK, B_QUEEN, B_KING
from infinity_chess.move import Square, Move, SpecialMove, MoveFlag


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
    is maintained so square lookups stay O(1) without scanning all 12 bitboards.
    """

    def __init__(self, ranks: int = 8, files: int = 8):
        self.ranks = ranks
        self.files = files
        self._board_mask: int = (1 << (ranks * files)) - 1 # Bitboard full of 1s
        self.turn: Colour = Colour.WHITE
        self.en_passant_sq: Optional[Square] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.history: list[Move] = []
        self.fen_history: list[str] = []  # piece-placement FEN after each move

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
        new.history = self.history[:]
        new.fen_history = self.fen_history[:]
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
        """ Iterator for indexes active bits."""
        while bitboard:
            lsb = bitboard & -bitboard
            yield lsb.bit_length() - 1
            bitboard ^= lsb

    def get(self, sq: Square) -> Optional[Piece]:
        entry = self._square_cache[self._index(sq)]
        if entry is None:
            return None
        piece_type, colour = entry
        return _piece_obj(piece_type, colour, bool(self._moved_mask & self._mask(sq)))

    def set(self, sq: Square, piece: Optional[Piece]) -> None:
        idx = self._index(sq)
        mask = 1 << idx
        current = self._square_cache[idx]

        # handle removal of existing piece from square
        if current is not None:
            current_type, current_colour = current
            self.bitboards[(current_colour, current_type)] &= ~mask # removes the existing piece from its bitboard
            self._moved_mask &= ~mask # removes the square from the moved_mask
            self._square_cache[idx] = None

        if piece is None:
            return

        self.bitboards[(piece.colour, piece.piece_type)] |= mask
        if piece.has_moved:
            self._moved_mask |= mask
        self._square_cache[idx] = (piece.piece_type, piece.colour)

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
        return self._square_cache[self._index(sq)] is None

    def in_bounds(self, sq: Square) -> bool:
        return 0 <= sq.rank < self.ranks and 0 <= sq.file < self.files

    # ── Iteration helpers ─────────────────────────────────────────────────────

    def all_squares(self) -> Iterator[Square]:
        for r in range(self.ranks):
            for f in range(self.files):
                yield Square(r, f)

    def pieces_for(self, colour: Colour) -> Iterator[tuple[Square, Piece]]:
        for sq in self.squares_in_bitboard(self.colour_bitboard(colour)):
            piece = self.get(sq)
            if piece is not None:
                yield sq, piece

    def find_piece(self, piece_type: PieceType, colour: Colour) -> Optional[Square]:
        return self.first_square_in_bitboard(self.piece_bitboard(colour, piece_type))

    # ── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> "Board":
        """Return a new Board with the move applied. Original is never mutated."""
        new_board = self.copy()
        new_board.make_move(move)
        return new_board

    def make_move(self, move: Move) -> UndoState:
        piece = self.get(move.from_sq)
        if piece is None:
            raise ValueError(f"No piece on {move.from_sq}")

        captured_sq: Optional[Square] = None
        captured_piece: Optional[Piece] = None

        if move.flag == MoveFlag.EN_PASSANT:
            captured_sq = (
                move.captured_sq
                if isinstance(move, SpecialMove) and move.captured_sq is not None
                else Square(move.from_sq.rank, move.to_sq.file)
            )
            captured_piece = self.get(captured_sq) # This should always be a pawn
        elif move.flag == MoveFlag.CASTLE_KING or move.flag == MoveFlag.CASTLE_QUEEN:
            captured_sq = None
        else:
            captured_sq = move.to_sq
            captured_piece = self.get(move.to_sq)

        undo = UndoState(
            move=move,
            moved_piece=piece,
            captured_piece=captured_piece,
            captured_sq=captured_sq if captured_piece is not None else None,
            prev_en_passant_sq=self.en_passant_sq,
            prev_halfmove_clock=self.halfmove_clock,
            prev_fullmove_number=self.fullmove_number,
            prev_turn=self.turn,
            prev_moved_mask=self._moved_mask,
        )

        self.en_passant_sq = None
        self._apply_move_no_history(move, piece, captured_sq)

        is_capture = captured_piece is not None
        is_pawn_move = piece.piece_type == PieceType.PAWN

        if is_pawn_move and abs(move.to_sq.rank - move.from_sq.rank) == 2:
            ep_rank = (move.from_sq.rank + move.to_sq.rank) // 2
            self.en_passant_sq = Square(ep_rank, move.from_sq.file)

        self.halfmove_clock = 0 if (is_capture or is_pawn_move) else self.halfmove_clock + 1

        if self.turn == Colour.BLACK:
            self.fullmove_number += 1

        self.turn = self.turn.opponent()
        self.history.append(move)
        self.fen_history.append(self.to_fen_position())
        return undo

    def unmake_move(self, undo: UndoState) -> None:
        move = undo.move

        if self.history:
            self.history.pop()
        if self.fen_history:
            self.fen_history.pop()

        if move.flag in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            self.set(move.to_sq, None)
            self.set(move.from_sq, undo.moved_piece)

            rank = move.from_sq.rank
            if move.flag == MoveFlag.CASTLE_KING:
                rook_from = Square(rank, self.files - 1)
                rook_to = Square(rank, move.to_sq.file - 1)
            else:
                rook_from = Square(rank, 0)
                rook_to = Square(rank, move.to_sq.file + 1)

            rook_piece = self.get(rook_to)
            self.set(rook_to, None)
            if rook_piece is not None:
                original_rook = _piece_obj(rook_piece.piece_type, rook_piece.colour, False)
                self.set(rook_from, original_rook)
        else:
            self.set(move.to_sq, None)
            self.set(move.from_sq, undo.moved_piece)
            if undo.captured_piece is not None and undo.captured_sq is not None:
                self.set(undo.captured_sq, undo.captured_piece)

        self.turn = undo.prev_turn
        self.en_passant_sq = undo.prev_en_passant_sq
        self.halfmove_clock = undo.prev_halfmove_clock
        self.fullmove_number = undo.prev_fullmove_number
        self._moved_mask = undo.prev_moved_mask

    def _apply_move_no_history(
        self,
        move: Move,
        piece: Piece,
        captured_sq: Optional[Square],
    ) -> None:
        if captured_sq is not None:
            self.set(captured_sq, None)

        if move.flag in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            self._apply_castle(move, piece)
            return

        self.set(move.from_sq, None)

        if move.flag == MoveFlag.PROMOTION:
            promo_name = (
                move.promotion_piece
                if isinstance(move, SpecialMove) and move.promotion_piece
                else "QUEEN"
            )
            promo_type = PieceType[promo_name.upper()]
            self.set(move.to_sq, _piece_obj(promo_type, piece.colour, True))
            return

        self.set(move.to_sq, piece.with_moved())

    def _apply_castle(self, move: Move, king: Piece) -> None:
        self.set(move.from_sq, None)
        self.set(move.to_sq, king.with_moved())

        rank = move.from_sq.rank
        if move.flag == MoveFlag.CASTLE_KING:
            rook_from = Square(rank, self.files - 1)
            rook_to   = Square(rank, move.to_sq.file - 1)
        else:
            rook_from = Square(rank, 0)
            rook_to   = Square(rank, move.to_sq.file + 1)

        rook = self.get(rook_from)
        if rook:
            self.set(rook_to, rook.with_moved())
            self.set(rook_from, None)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_fen_position(self) -> str:
        """A FEN notation of the position without the extra metadata."""
        rows = []
        for rank in range(self.ranks - 1, -1, -1):
            empty = 0
            row = ""
            for file in range(self.files):
                piece = self.get(Square(rank, file))
                if piece is None:
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    row += piece.symbol()
            if empty:
                row += str(empty)
            rows.append(row)

        return f"{'/'.join(rows)}"


    def to_fen(self) -> str:
        position = self.to_fen_position()

        turn_char = 'w' if self.turn == Colour.WHITE else 'b'
        ep = self.en_passant_sq.to_algebraic() if self.en_passant_sq else '-'
        
        castling = self._castling_rights()
        if not castling:
            castling = "-"

        return f"{position} {turn_char} {castling} {ep} {self.halfmove_clock} {self.fullmove_number}"

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        parts = fen.strip().split()
        board = cls(8, 8)
        rows = parts[0].split('/')
        if len(rows) != 8:
            raise ValueError(f"FEN has {len(rows)} rows, expected 8")

        for rank_idx, row in enumerate(reversed(rows)):
            file_idx = 0
            for ch in row:
                if ch.isdigit():
                    file_idx += int(ch)
                else:
                    colour = Colour.WHITE if ch.isupper() else Colour.BLACK
                    piece_type = PieceType.from_symbol(ch)
                    board.set(Square(rank_idx, file_idx), Piece(piece_type, colour))
                    file_idx += 1

        if len(parts) > 1:
            board.turn = Colour.WHITE if parts[1] == 'w' else Colour.BLACK
        if len(parts) > 2:
            castling = parts[2]

            def set_has_moved(sq: Square, expected_type: PieceType, expected_colour: Colour, has_moved: bool) -> None:
                piece = board.get(sq)
                if piece and piece.piece_type == expected_type and piece.colour == expected_colour:
                    board.set(sq, Piece(expected_type, expected_colour, has_moved=has_moved))

            white_has_castling = 'K' in castling or 'Q' in castling
            black_has_castling = 'k' in castling or 'q' in castling

            set_has_moved(Square(0, 4), PieceType.KING, Colour.WHITE, not white_has_castling)
            set_has_moved(Square(0, 0), PieceType.ROOK, Colour.WHITE, 'Q' not in castling)
            set_has_moved(Square(0, board.files - 1), PieceType.ROOK, Colour.WHITE, 'K' not in castling)

            set_has_moved(Square(board.ranks - 1, 4), PieceType.KING, Colour.BLACK, not black_has_castling)
            set_has_moved(Square(board.ranks - 1, 0), PieceType.ROOK, Colour.BLACK, 'q' not in castling)
            set_has_moved(Square(board.ranks - 1, board.files - 1), PieceType.ROOK, Colour.BLACK, 'k' not in castling)
        if len(parts) > 3 and parts[3] != '-':
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
        back_rank = [W_ROOK, W_KNIGHT, W_BISHOP, W_QUEEN, W_KING, W_BISHOP, W_KNIGHT, W_ROOK]
        for f, piece in enumerate(back_rank):
            board.set(Square(0, f), piece)
            board.set(Square(1, f), W_PAWN)
            board.set(Square(6, f), B_PAWN)
            board.set(Square(7, f), Piece(piece.piece_type, Colour.BLACK))
        return board

    def _castling_rights(self) -> str:
        """Return the active castling rights string (e.g. 'KQk') for the current position."""
        rights = ""
        wk = self.get(Square(0, 4))
        if wk and wk.piece_type == PieceType.KING and wk.colour == Colour.WHITE and not wk.has_moved:
            wkr = self.get(Square(0, self.files - 1))
            if wkr and wkr.piece_type == PieceType.ROOK and wkr.colour == Colour.WHITE and not wkr.has_moved:
                rights += 'K'
            wqr = self.get(Square(0, 0))
            if wqr and wqr.piece_type == PieceType.ROOK and wqr.colour == Colour.WHITE and not wqr.has_moved:
                rights += 'Q'
        bk = self.get(Square(self.ranks - 1, 4))
        if bk and bk.piece_type == PieceType.KING and bk.colour == Colour.BLACK and not bk.has_moved:
            bkr = self.get(Square(self.ranks - 1, self.files - 1))
            if bkr and bkr.piece_type == PieceType.ROOK and bkr.colour == Colour.BLACK and not bkr.has_moved:
                rights += 'k'
            bqr = self.get(Square(self.ranks - 1, 0))
            if bqr and bqr.piece_type == PieceType.ROOK and bqr.colour == Colour.BLACK and not bqr.has_moved:
                rights += 'q'
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
                    sq = self._square_from_index(idx)
                    has_moved = bool(self._moved_mask & lsb)
                    piece_key = hash((piece_type, colour, sq.rank, sq.file, has_moved))
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
            for file in range(self.files):
                piece = self.get(Square(rank, file))
                row += (piece.symbol() if piece else '.') + ' '
            lines.append(row)
        lines.append("  " + " ".join(chr(ord('a') + f) for f in range(self.files)))
        lines.append(f"Turn: {self.turn.value}  Move: {self.fullmove_number}")
        return "\n".join(lines)
