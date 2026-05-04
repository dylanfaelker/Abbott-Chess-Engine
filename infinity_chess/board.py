"""
infinity_chess/board.py

Board state: the grid, piece positions, and game metadata.

Pure data class
"""

from __future__ import annotations
from typing import Optional, Iterator

from infinity_chess.pieces import Piece, PieceType, Colour, make_piece
from infinity_chess.pieces import W_PAWN, W_KNIGHT, W_BISHOP, W_ROOK, W_QUEEN, W_KING
from infinity_chess.pieces import B_PAWN, B_KNIGHT, B_BISHOP, B_ROOK, B_QUEEN, B_KING
from infinity_chess.move import Square, Move, SpecialMove, MoveFlag


class Board:
    """
    The game board.

    Attributes:
        ranks:           Number of rows (default 8).
        files:           Number of columns (default 8).
        grid:            2D list [rank][file] of Piece | None.
        turn:            Which colour moves next.
        en_passant_sq:   Square a pawn can capture en passant to, or None.
        halfmove_clock:  Moves since last capture or pawn push (for 50-move rule).
        fullmove_number: Increments after Black's move.
        history:         List of all moves played, oldest first.
    """

    def __init__(self, ranks: int = 8, files: int = 8):
        self.ranks = ranks
        self.files = files
        self.grid: list[list[Optional[Piece]]] = [
            [None] * files for _ in range(ranks)
        ]
        self.turn: Colour = Colour.WHITE
        self.en_passant_sq: Optional[Square] = None
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        self.history: list[Move] = []
        self.fen_history: list[str] = []  # piece-placement FEN after each move

    # Custom copy function for cost efficiency
    def copy(self) -> "Board":
        new = Board.__new__(Board)
        new.ranks = self.ranks
        new.files = self.files
        new.grid = [row[:] for row in self.grid]  # shallow copy rows (Pieces are frozen/immutable)
        new.turn = self.turn
        new.en_passant_sq = self.en_passant_sq
        new.halfmove_clock = self.halfmove_clock
        new.fullmove_number = self.fullmove_number
        new.history = self.history[:]
        new.fen_history = self.fen_history[:]
        return new

    # ── Square access ─────────────────────────────────────────────────────────

    def get(self, sq: Square) -> Optional[Piece]:
        return self.grid[sq.rank][sq.file]

    def set(self, sq: Square, piece: Optional[Piece]) -> None:
        self.grid[sq.rank][sq.file] = piece

    def is_empty(self, sq: Square) -> bool:
        return self.get(sq) is None

    def in_bounds(self, sq: Square) -> bool:
        return 0 <= sq.rank < self.ranks and 0 <= sq.file < self.files

    # ── Iteration helpers ─────────────────────────────────────────────────────

    def all_squares(self) -> Iterator[Square]:
        for r in range(self.ranks):
            for f in range(self.files):
                yield Square(r, f)

    def pieces_for(self, colour: Colour) -> Iterator[tuple[Square, Piece]]:
        for sq in self.all_squares():
            piece = self.get(sq)
            if piece and piece.colour == colour:
                yield sq, piece

    def find_piece(self, piece_type: PieceType, colour: Colour) -> Optional[Square]:
        for sq, piece in self.pieces_for(colour):
            if piece.piece_type == piece_type:
                return sq
        return None

    # ── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move: Move) -> "Board":
        """Return a new Board with the move applied. Original is never mutated."""
        new_board = self.copy()
        new_board._apply_move_inplace(move)
        return new_board

    def _apply_move_inplace(self, move: Move) -> None:
        piece = self.get(move.from_sq)
        if piece is None:
            raise ValueError(f"No piece on {move.from_sq}")

        self.en_passant_sq = None

        if move.flag in (MoveFlag.CASTLE_KING, MoveFlag.CASTLE_QUEEN):
            self._apply_castle(move)

        elif move.flag == MoveFlag.EN_PASSANT:
            captured_sq = (move.captured_sq
                           if isinstance(move, SpecialMove) and move.captured_sq
                           else move.to_sq)
            self.set(captured_sq, None)
            self.set(move.to_sq, piece.with_moved())
            self.set(move.from_sq, None)

        elif move.flag == MoveFlag.PROMOTION:
            promo_name = (move.promotion_piece
                          if isinstance(move, SpecialMove) and move.promotion_piece
                          else "QUEEN")
            promo_type = PieceType[promo_name.upper()]
            self.set(move.to_sq, make_piece(promo_type, piece.colour))
            self.set(move.from_sq, None)

        else:
            self.set(move.to_sq, piece.with_moved())
            self.set(move.from_sq, None)

            if piece.piece_type == PieceType.PAWN:
                rank_diff = abs(move.to_sq.rank - move.from_sq.rank)
                if rank_diff == 2:
                    ep_rank = (move.from_sq.rank + move.to_sq.rank) // 2
                    self.en_passant_sq = Square(ep_rank, move.from_sq.file)

        is_capture = move.flag in (MoveFlag.CAPTURE, MoveFlag.EN_PASSANT)
        moved_piece = self.get(move.to_sq)
        is_pawn_move = moved_piece and moved_piece.piece_type == PieceType.PAWN

        self.halfmove_clock = 0 if (is_capture or is_pawn_move) else self.halfmove_clock + 1

        if self.turn == Colour.BLACK:
            self.fullmove_number += 1

        self.turn = self.turn.opponent()
        self.history.append(move)
        self.fen_history.append(self.to_fen_position())

    def _apply_castle(self, move: Move) -> None:
        piece = self.get(move.from_sq)
        self.set(move.to_sq, piece.with_moved())
        self.set(move.from_sq, None)

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
                piece = self.grid[rank][file]
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
 
        # Pieces
        for sq in self.all_squares():
            piece = self.get(sq)
            if piece:
                piece_key = hash((piece.piece_type, piece.colour, sq.rank, sq.file))
                h ^= piece_key * self._ZOBRIST_PIECE_MULTIPLIER
 
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
                piece = self.grid[rank][file]
                row += (piece.symbol() if piece else '.') + ' '
            lines.append(row)
        lines.append("  " + " ".join(chr(ord('a') + f) for f in range(self.files)))
        lines.append(f"Turn: {self.turn.value}  Move: {self.fullmove_number}")
        return "\n".join(lines)
