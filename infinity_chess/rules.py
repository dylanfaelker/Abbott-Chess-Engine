"""
infinity_chess/rules.py

Design:
  - RuleSet is an abstract base class defining the interface the engine uses.
  - StandardRules implements standard chess movement and win conditions.
  - InfinityChessRules implements custom board wrapping movements.

All methods receive a Board and return information — they never mutate state.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterator

from infinity_chess.pieces import Piece, PieceType, Colour
from infinity_chess.move import Square, Move, SpecialMove, MoveFlag
from infinity_chess.board import Board


# ── RuleSet (abstract interface) ──────────────────────────────────────────────

class RuleSet(ABC):
    """
    Abstract base class for all rule sets.

    The engine calls these methods to understand what moves are legal
    and when the game is over.
    """

    @abstractmethod
    def pseudo_legal_moves(self, board: Board, sq: Square, _for_attack_check: bool = False) -> Iterator[Move]:
        """
        Yield all moves a piece on `sq` could make ignoring check.
        'Pseudo-legal' means geometrically valid but not yet filtered for
        leaving your own king in check.
        """
        ...

    @abstractmethod
    def is_in_check(self, board: Board, colour: Colour) -> bool:
        """Return True if `colour`'s king is currently attacked."""
        ...

    @abstractmethod
    def is_square_attacked(self, board: Board, sq: Square, by_colour: Colour) -> bool:
        """Return True if any piece of `by_colour` can capture on `sq`."""
        ...

    @abstractmethod
    def is_checkmate(self, board: Board, colour: Colour) -> bool:
        """Return True if `colour` is in checkmate."""
        ...

    @abstractmethod
    def is_stalemate(self, board: Board, colour: Colour) -> bool:
        """Return True if `colour` is in stalemate."""
        ...

    @abstractmethod
    def is_draw(self, board: Board) -> bool:
        """Return True if the position is a draw by any rule."""
        ...

    @abstractmethod
    def game_over(self, board: Board) -> tuple[bool, Optional[str]]:
        """
        Return (is_over, result_string).
        result_string examples: 'white', 'black', 'draw', or None if not over.
        """
        ...

    def legal_moves(self, board: Board, colour: Colour) -> Iterator[Move]:
        """
        Yield all fully legal moves for `colour` — pseudo-legal filtered
        to exclude moves that leave the king in check.

        This default implementation works for any RuleSet that correctly
        implements pseudo_legal_moves and is_in_check.
        """
        for sq, piece in board.pieces_for(colour):
            for move in self.pseudo_legal_moves(board, sq):
                candidate = board.apply_move(move)
                if not self.is_in_check(candidate, colour):
                    yield move


# ── StandardRules ─────────────────────────────────────────────────────────────

class StandardRules(RuleSet):
    """
    Standard chess rules.
    """

    # ── Public RuleSet interface ───────────────────────────────────────────────

    def pseudo_legal_moves(self, board: Board, sq: Square, _for_attack_check: bool = False) -> Iterator[Move]:
        piece = board.get(sq)
        if piece is None:
            return

        dispatch = {
            PieceType.PAWN:   self._pawn_moves,
            PieceType.KNIGHT: self._knight_moves,
            PieceType.BISHOP: self._sliding_moves,
            PieceType.ROOK:   self._sliding_moves,
            PieceType.QUEEN:  self._sliding_moves,
            PieceType.KING:   self._king_moves,
        }

        generator = dispatch.get(piece.piece_type)
        if generator:
            if piece.piece_type == PieceType.KING:
                yield from self._king_moves(board, sq, piece, skip_castling=_for_attack_check)
            if piece.piece_type == PieceType.PAWN:
                yield from self._pawn_moves(board, sq, piece, only_attacks=_for_attack_check)
            else:
                yield from generator(board, sq, piece)

    def is_in_check(self, board: Board, colour: Colour) -> bool:
        king_sq = board.find_piece(PieceType.KING, colour)
        if king_sq is None:
            return False  # No king — can't be in check
        return self.is_square_attacked(board, king_sq, colour.opponent())

    def is_square_attacked(self, board: Board, sq: Square, by_colour: Colour) -> bool:
        for attacker_sq, _ in board.pieces_for(by_colour):
            for move in self.pseudo_legal_moves(board, attacker_sq, _for_attack_check=True):
                if move.to_sq == sq:
                    return True
        return False

    def is_checkmate(self, board: Board, colour: Colour) -> bool:
        if not self.is_in_check(board, colour):
            return False
        return not any(True for _ in self.legal_moves(board, colour))

    def is_stalemate(self, board: Board, colour: Colour) -> bool:
        if self.is_in_check(board, colour):
            return False
        return not any(True for _ in self.legal_moves(board, colour))

    def is_draw(self, board: Board) -> bool:
        if board.halfmove_clock >= 100:          # 50-move rule
            return True
        if self._is_insufficient_material(board):
            return True
        if self._is_threefold_repetition(board):
            return True
        return False

    def game_over(self, board: Board) -> tuple[bool, Optional[str]]:
        colour = board.turn
        if self.is_checkmate(board, colour):
            winner = colour.opponent().value
            return True, winner
        if self.is_stalemate(board, colour):
            return True, "draw"
        if self.is_draw(board):
            return True, "draw"
        return False, None

    # ── Piece movement generators ─────────────────────────────────────────────

    def _pawn_moves(self, board: Board, sq: Square, piece: Piece, only_attacks: bool = False) -> Iterator[Move]:
        direction = 1 if piece.colour == Colour.WHITE else -1
        start_rank = 1 if piece.colour == Colour.WHITE else board.ranks - 2
        promo_rank = board.ranks - 1 if piece.colour == Colour.WHITE else 0

        # Single push
        if not only_attacks:
            one_ahead = sq + (direction, 0)
            if board.in_bounds(one_ahead) and board.is_empty(one_ahead):
                if one_ahead.rank == promo_rank:
                    yield from self._promotion_moves(sq, one_ahead)
                else:
                    yield Move(sq, one_ahead)

                # Double push from starting rank
                if sq.rank == start_rank:
                    two_ahead = sq + (direction * 2, 0)
                    if board.in_bounds(two_ahead) and board.is_empty(two_ahead):
                        yield Move(sq, two_ahead)

        # Captures (diagonal)
        for file_delta in (-1, 1):
            capture_sq = sq + (direction, file_delta)
            if not board.in_bounds(capture_sq):
                continue

            target = board.get(capture_sq)
            if target and target.colour != piece.colour:
                if capture_sq.rank == promo_rank:
                    yield from self._promotion_moves(sq, capture_sq, flag=MoveFlag.CAPTURE)
                else:
                    yield Move(sq, capture_sq, MoveFlag.CAPTURE)

            # En passant
            if capture_sq == board.en_passant_sq:
                captured_pawn_sq = Square(sq.rank, capture_sq.file)
                yield SpecialMove(sq, capture_sq, MoveFlag.EN_PASSANT,
                                  captured_sq=captured_pawn_sq)

    def _promotion_moves(
        self, from_sq: Square, to_sq: Square, flag: MoveFlag = MoveFlag.PROMOTION
    ) -> Iterator[SpecialMove]:
        for piece_name in ("QUEEN", "ROOK", "BISHOP", "KNIGHT"):
            yield SpecialMove(from_sq, to_sq, MoveFlag.PROMOTION,
                              promotion_piece=piece_name)

    def _knight_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, df in offsets:
            target = sq + (dr, df)
            if not board.in_bounds(target):
                continue
            occupant = board.get(target)
            if occupant is None:
                yield Move(sq, target)
            elif occupant.colour != piece.colour:
                yield Move(sq, target, MoveFlag.CAPTURE)

    def _sliding_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        """Handles bishop, rook, and queen by selecting the right ray directions."""
        directions: list[tuple[int, int]] = []

        if piece.piece_type in (PieceType.ROOK, PieceType.QUEEN):
            directions += [(1,0),(-1,0),(0,1),(0,-1)]
        if piece.piece_type in (PieceType.BISHOP, PieceType.QUEEN):
            directions += [(1,1),(1,-1),(-1,1),(-1,-1)]

        for dr, df in directions:
            current = sq + (dr, df)
            while board.in_bounds(current):
                occupant = board.get(current)
                if occupant is None:
                    yield Move(sq, current)
                elif occupant.colour != piece.colour:
                    yield Move(sq, current, MoveFlag.CAPTURE)
                    break
                else:
                    break  # Blocked by own piece
                current = current + (dr, df)

    def _king_moves(self, board: Board, sq: Square, piece: Piece, skip_castling: bool = False) -> Iterator[Move]:
        for dr in (-1, 0, 1):
            for df in (-1, 0, 1):
                if dr == 0 and df == 0:
                    continue
                target = sq + (dr, df)
                if not board.in_bounds(target):
                    continue
                occupant = board.get(target)
                if occupant is None:
                    yield Move(sq, target)
                elif occupant.colour != piece.colour:
                    yield Move(sq, target, MoveFlag.CAPTURE)

        if not skip_castling:
            yield from self._castle_moves(board, sq, piece)

    def _castle_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        """
        Yield castling moves if eligible.
        Conditions: king hasn't moved, rook hasn't moved, squares between
        are empty, king doesn't pass through check.
        """
        if piece.has_moved or self.is_in_check(board, piece.colour):
            return

        rank = sq.rank
        opponent = piece.colour.opponent()

        # Kingside
        rook_sq = Square(rank, board.files - 1)
        rook = board.get(rook_sq)
        if rook and rook.piece_type == PieceType.ROOK and not rook.has_moved:
            path = [Square(rank, sq.file + 1), Square(rank, sq.file + 2)]
            if all(board.is_empty(s) for s in path):
                if not any(self.is_square_attacked(board, s, opponent) for s in path):
                    yield Move(sq, Square(rank, sq.file + 2), MoveFlag.CASTLE_KING)

        # Queenside
        rook_sq = Square(rank, 0)
        rook = board.get(rook_sq)
        if rook and rook.piece_type == PieceType.ROOK and not rook.has_moved:
            path = [Square(rank, sq.file - 1), Square(rank, sq.file - 2)]
            between = [Square(rank, sq.file - 1), Square(rank, sq.file - 2), Square(rank, sq.file - 3)]
            if all(board.is_empty(s) for s in between):
                if not any(self.is_square_attacked(board, s, opponent) for s in path):
                    yield Move(sq, Square(rank, sq.file - 2), MoveFlag.CASTLE_QUEEN)

    # ── Draw helpers ──────────────────────────────────────────────────────────

    def _is_insufficient_material(self, board: Board) -> bool:
        pieces: list[Piece] = [
            board.get(sq) for sq in board.all_squares() if board.get(sq)
        ]
        if len(pieces) == 2: # K vs K
            return True
        if len(pieces) == 3: # K+minor vs K
            minor = {PieceType.BISHOP, PieceType.KNIGHT}
            return any(p.piece_type in minor for p in pieces)
        if len(pieces) == 4: # K+minor vs K+minor
            minor = {PieceType.BISHOP, PieceType.KNIGHT}
            non_kings = [p for p in pieces if p.piece_type != PieceType.KING]
            colours = {p.colour for p in non_kings}
            return (
                len(non_kings) == 2
                and all(p.piece_type in minor for p in non_kings)
                and len(colours) == 2
            )
        return False

    def _is_threefold_repetition(self, board: Board) -> bool:
        current = board.to_fen_position()
        count = getattr(board, 'fen_history', []).count(current)
        return count >= 3


class InfinityChessRules(StandardRules):
    """
    Keeps the standard rules of chess but changes the piece movement to incorporate
    the pac-man style wrapping for infinity chess.
    """
    
    @staticmethod
    def wrap_square(sq: Square) -> Square:
        return Square(sq.rank, sq.file % 8)

    def _pawn_moves(self, board: Board, sq: Square, piece: Piece, only_attacks: bool = False) -> Iterator[Move]:
        direction = 1 if piece.colour == Colour.WHITE else -1
        start_rank = 1 if piece.colour == Colour.WHITE else board.ranks - 2
        promo_rank = board.ranks - 1 if piece.colour == Colour.WHITE else 0

        # Single push
        if not only_attacks:
            one_ahead = sq + (direction, 0)
            if board.in_bounds(one_ahead) and board.is_empty(one_ahead):
                if one_ahead.rank == promo_rank:
                    yield from self._promotion_moves(sq, one_ahead)
                else:
                    yield Move(sq, one_ahead)

                # Double push from starting rank
                if sq.rank == start_rank:
                    two_ahead = sq + (direction * 2, 0)
                    if board.in_bounds(two_ahead) and board.is_empty(two_ahead):
                        yield Move(sq, two_ahead)

        # Captures (diagonal)
        for file_delta in (-1, 1):
            capture_sq = self.wrap_square(sq + (direction, file_delta))
            if not board.in_bounds(capture_sq):
                continue

            target = board.get(capture_sq)
            if target and target.colour != piece.colour:
                if capture_sq.rank == promo_rank:
                    yield from self._promotion_moves(sq, capture_sq, flag=MoveFlag.CAPTURE)
                else:
                    yield Move(sq, capture_sq, MoveFlag.CAPTURE)

            # En passant
            if capture_sq == board.en_passant_sq:
                captured_pawn_sq = Square(sq.rank, capture_sq.file)
                yield SpecialMove(sq, capture_sq, MoveFlag.EN_PASSANT,
                                  captured_sq=captured_pawn_sq)

    def _knight_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, df in offsets:
            target = self.wrap_square(sq + (dr, df))
            if not board.in_bounds(target):
                continue
            occupant = board.get(target)
            if occupant is None:
                yield Move(sq, target)
            elif occupant.colour != piece.colour:
                yield Move(sq, target, MoveFlag.CAPTURE)

    def _sliding_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        """Handles bishop, rook, and queen by selecting the right ray directions."""
        directions: list[tuple[int, int]] = []

        if piece.piece_type in (PieceType.ROOK, PieceType.QUEEN):
            directions += [(1,0),(-1,0),(0,1),(0,-1)]
        if piece.piece_type in (PieceType.BISHOP, PieceType.QUEEN):
            directions += [(1,1),(1,-1),(-1,1),(-1,-1)]

        for dr, df in directions:
            current = self.wrap_square(sq + (dr, df))
            while board.in_bounds(current):
                occupant = board.get(current)
                if occupant is None:
                    yield Move(sq, current)
                elif occupant.colour != piece.colour:
                    yield Move(sq, current, MoveFlag.CAPTURE)
                    break
                else:
                    break  # Blocked by own piece. Will also block the infinite loop when you run into yourself via wrapping
                current = current + (dr, df)

    def _king_moves(self, board: Board, sq: Square, piece: Piece, skip_castling: bool = False) -> Iterator[Move]:
        for dr in (-1, 0, 1):
            for df in (-1, 0, 1):
                if dr == 0 and df == 0:
                    continue
                target = self.wrap_square(sq + (dr, df))
                if not board.in_bounds(target):
                    continue
                occupant = board.get(target)
                if occupant is None:
                    yield Move(sq, target)
                elif occupant.colour != piece.colour:
                    yield Move(sq, target, MoveFlag.CAPTURE)

        if not skip_castling:
            yield from self._castle_moves(board, sq, piece)
