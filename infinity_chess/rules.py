"""
infinity_chess/rules.py

Design:
  - RuleSet is an abstract base class defining the interface the engine uses.
  - StandardRules implements standard chess movement and win conditions.
  - InfinityChessRules implements custom board wrapping movements.

All methods receive a Board and return information — they never mutate state.
Complexity notation: P = piece count, D = longest ray, M = candidate moves,
A = cost of king-safety checking, L = legal moves, and H = hash-history length.
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

    Returns:
        RuleSet: Interface for a concrete ruleset's move and state queries.

    Complexity:
        Depends on the concrete ruleset implementation.
    """

    @abstractmethod
    def pseudo_legal_moves(self, board: Board, sq: Square, _for_attack_check: bool = False) -> Iterator[Move]:
        """
        Yield all moves a piece on `sq` could make ignoring check.
        'Pseudo-legal' means geometrically valid but not yet filtered for
        leaving your own king in check.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            _for_attack_check (bool): Whether generation is for attack detection.

        Returns:
            Iterator[Move]: Move iterator.
        """
        ...

    @abstractmethod
    def is_in_check(self, board: Board, colour: Colour) -> bool:
        """
        Test whether a side's king is attacked.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.
        """
        ...

    @abstractmethod
    def is_square_attacked(self, board: Board, sq: Square, by_colour: Colour) -> bool:
        """
        Test attacks on a target square.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            by_colour (Colour): Attacking side.

        Returns:
            bool: True when the condition holds; otherwise False.
        """
        ...

    @abstractmethod
    def is_checkmate(self, board: Board, colour: Colour) -> bool:
        """
        Test check plus no legal escape.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.
        """
        ...

    @abstractmethod
    def is_stalemate(self, board: Board, colour: Colour) -> bool:
        """
        Test no check plus no legal move.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.
        """
        ...

    @abstractmethod
    def is_draw(self, board: Board) -> bool:
        """
        Check the configured draw rules.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            bool: True when the condition holds; otherwise False.
        """
        ...

    @abstractmethod
    def game_over(
        self,
        board: Board,
        legal_moves: Optional[list[Move]] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Whether the game is over, and its result.

        Args:
            board (Board): Board position being queried or updated.
        legal_moves (Optional[list[Move]]): Previously generated legal moves,
            when available.

        Returns:
            tuple[bool, Optional[str]]: terminal flag and result as a string. result_string examples: 'white', 'black', 'draw', or None if not over.
        """
        ...

    def legal_moves(self, board: Board, colour: Colour) -> Iterator[Move]:
        """
        Yield all fully legal moves for `colour`. aka pseudo-legal filtered
        to exclude moves that leave the king in check.

        This default implementation works for any RuleSet that correctly
        implements pseudo_legal_moves and is_in_check.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            Iterator[Move]: legal-move iterator.

        Complexity:
            O(M*A), where M is candidate move count and A is check cost.
        """
        for sq, piece in board.pieces_for(colour):
            for move in self.pseudo_legal_moves(board, sq):
                undo = board.make_move(move)
                in_check = self.is_in_check(board, colour)
                board.unmake_move(undo)
                if not in_check:
                    yield move


# ── StandardRules ─────────────────────────────────────────────────────────────

class StandardRules(RuleSet):
    """
    Standard chess rules.

    Returns:
        StandardRules instance: rules for standard chess movement and status checks.

    Complexity:
        O(1) for leapers, O(D) for sliding rays, plus king-safety checks for legal
        moves.
    """

    # ── Public RuleSet interface ───────────────────────────────────────────────

    def pseudo_legal_moves(self, board: Board, sq: Square, _for_attack_check: bool = False) -> Iterator[Move]:
        """
        Dispatch generation for the piece at a square.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            _for_attack_check (bool): Whether generation is for attack detection.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(D).
        """
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
            elif piece.piece_type == PieceType.PAWN:
                yield from self._pawn_moves(board, sq, piece, only_attacks=_for_attack_check)
            else:
                yield from generator(board, sq, piece)

    def is_in_check(self, board: Board, colour: Colour) -> bool:
        """
        Test whether the side's king is attacked.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P*D).
        """
        king_sq = board.find_piece(PieceType.KING, colour)
        if king_sq is None:
            return False  # No king — can't be in check
        return self.is_square_attacked(board, king_sq, colour.opponent())

    def is_square_attacked(self, board: Board, sq: Square, by_colour: Colour) -> bool:
        """
        Test whether a side attacks a target.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            by_colour (Colour): Attacking side.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P*D).
        """
        for attacker_sq, _ in board.pieces_for(by_colour):
            for move in self.pseudo_legal_moves(board, attacker_sq, _for_attack_check=True):
                if move.to_sq == sq:
                    return True
        return False

    def is_checkmate(self, board: Board, colour: Colour) -> bool:
        """
        Examine for check with no legal escape.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(M*A).
        """
        if not self.is_in_check(board, colour):
            return False
        return not any(True for _ in self.legal_moves(board, colour))

    def is_stalemate(self, board: Board, colour: Colour) -> bool:
        """
        Check for no check and no legal moves.

        Args:
            board (Board): Board position being queried or updated.
            colour (Colour): Piece side or side being queried.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(M*A).
        """
        if self.is_in_check(board, colour):
            return False
        return not any(True for _ in self.legal_moves(board, colour))

    def is_draw(self, board: Board) -> bool:
        """
        Check the 50-move, material, and repetition rules.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P+H).
        """
        if board.halfmove_clock >= 100:          # 50-move rule
            return True
        if self._is_insufficient_material(board):
            return True
        if self._is_threefold_repetition(board):
            return True
        return False

    def game_over(
        self,
        board: Board,
        legal_moves: Optional[list[Move]] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Resolve mate, stalemate, and draw.

        Args:
            board (Board): Board position being queried or updated.
        legal_moves (Optional[list[Move]]): Previously generated legal moves,
            when available.

        Returns:
            tuple[bool, Optional[str]]: (over, result).

        Complexity:
            O(M*A) without moves, O(P+H) with them.
        """
        colour = board.turn
        moves = legal_moves if legal_moves is not None else list(self.legal_moves(board, colour))
        if not moves:
            if self.is_in_check(board, colour):
                return True, colour.opponent().value
            return True, "draw"
        if self.is_draw(board):
            return True, "draw"
        return False, None

    # ── Piece movement generators ─────────────────────────────────────────────

    def _pawn_moves(self, board: Board, sq: Square, piece: Piece, only_attacks: bool = False) -> Iterator[Move]:
        """
        Generate pawn moves, including promotion and en passant.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.
            only_attacks (bool): Whether to generate attack squares only.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(1).
        """
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
                    yield from self._promotion_moves(sq, capture_sq, flag=MoveFlag.PROMOTION_CAPTURE)
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
        """
        Yield each promotion choice.

        Args:
            from_sq (Square): Move origin square.
            to_sq (Square): Move destination square.
            flag (MoveFlag): Move category or operation flag.

        Returns:
            Iterator[SpecialMove]: four SpecialMoves.

        Complexity:
            O(1).
        """
        for piece_name in ("QUEEN", "ROOK", "BISHOP", "KNIGHT"):
            yield SpecialMove(from_sq, to_sq, flag,
                              promotion_piece=piece_name)

    def _knight_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        """
        Generate in-bounds knight moves.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(1).
        """
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
        """
        Yield unobstructed bishop/rook/queen rays.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(D) per ray.
        """
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
        """
        Generate adjacent king moves and optional castles.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.
            skip_castling (bool): Whether castling moves should be omitted.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(1) plus attack checks.
        """
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

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.

        Returns:
            Iterator[Move]: castling Move iterator.

        Complexity:
            O(1) plus attack checks.
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
        """
        Check whether the remaining pieces qualify as insufficient material.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(P).
        """
        pieces: list[Piece] = []
        for colour in Colour:
            for _, piece in board.pieces_for(colour):
                pieces.append(piece)
                if len(pieces) > 4:
                    return False
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
        """
        Check whether the current position hash appeared twice earlier.

        Args:
            board (Board): Board position being queried or updated.

        Returns:
            bool: True when the condition holds; otherwise False.

        Complexity:
            O(H).
        """
        current = board.zobrist_hash()
        return board.zobrist_history.count(current) >= 2


class InfinityChessRules(StandardRules):
    """
    Apply chess rules with horizontal file wrapping for piece movement.

    Returns:
        InfinityChessRules instance: rules for wrapped piece movement.

    Complexity:
        O(1) for leapers; wrapped sliding moves are bounded by O(ranks*files).
    """
    
    @staticmethod
    def wrap_square(sq: Square, board: Board) -> Square:
        """
        Wrap a file coordinate to the board width.

        Args:
            sq (Square): Source or target board square.
            board (Board): Board position being queried or updated.

        Returns:
            Square: wrapped Square.

        Complexity:
            O(1).
        """
        return Square(sq.rank, sq.file % board.files)

    def _pawn_moves(self, board: Board, sq: Square, piece: Piece, only_attacks: bool = False) -> Iterator[Move]:
        """
        Generate pawn moves with horizontal wrap on captures.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.
            only_attacks (bool): Whether to generate attack squares only.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(1).
        """
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
            capture_sq = self.wrap_square(sq + (direction, file_delta), board)
            if not board.in_bounds(capture_sq):
                continue

            target = board.get(capture_sq)
            if target and target.colour != piece.colour:
                if capture_sq.rank == promo_rank:
                    yield from self._promotion_moves(sq, capture_sq, flag=MoveFlag.PROMOTION_CAPTURE)
                else:
                    yield Move(sq, capture_sq, MoveFlag.CAPTURE)

            # En passant
            if capture_sq == board.en_passant_sq:
                captured_pawn_sq = Square(sq.rank, capture_sq.file)
                yield SpecialMove(sq, capture_sq, MoveFlag.EN_PASSANT,
                                  captured_sq=captured_pawn_sq)

    def _knight_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        """
        Generate knight moves with horizontal wrap.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(1).
        """
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, df in offsets:
            target = self.wrap_square(sq + (dr, df), board)
            if not board.in_bounds(target):
                continue
            occupant = board.get(target)
            if occupant is None:
                yield Move(sq, target)
            elif occupant.colour != piece.colour:
                yield Move(sq, target, MoveFlag.CAPTURE)

    def _sliding_moves(self, board: Board, sq: Square, piece: Piece) -> Iterator[Move]:
        """
        Yield wrapped sliding rays until blocked or cycled.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(D), bounded by board squares.
        """
        directions: list[tuple[int, int]] = []

        if piece.piece_type in (PieceType.ROOK, PieceType.QUEEN):
            directions += [(1,0),(-1,0),(0,1),(0,-1)]
        if piece.piece_type in (PieceType.BISHOP, PieceType.QUEEN):
            directions += [(1,1),(1,-1),(-1,1),(-1,-1)]

        seen = 0
        for dr, df in directions:
            current = self.wrap_square(sq + (dr, df), board)
            while board.in_bounds(current):
                target_bit = board._mask(current)
                is_new_target = not seen & target_bit
                seen |= target_bit

                occupant = board.get(current)
                if occupant is None:
                    if is_new_target:
                        yield Move(sq, current)
                elif occupant.colour != piece.colour:
                    if is_new_target:
                        yield Move(sq, current, MoveFlag.CAPTURE)
                    break
                else:
                    break  # Blocked by own piece. Will also block the infinite loop when you run into yourself via wrapping
                current = self.wrap_square(current + (dr, df), board)

    def _king_moves(self, board: Board, sq: Square, piece: Piece, skip_castling: bool = False) -> Iterator[Move]:
        """
        Generate adjacent king moves with horizontal wrap and optional castles.

        Args:
            board (Board): Board position being queried or updated.
            sq (Square): Source or target board square.
            piece (Piece): Piece involved in the operation.
            skip_castling (bool): Whether castling moves should be omitted.

        Returns:
            Iterator[Move]: Move iterator.

        Complexity:
            O(1) plus attack checks.
        """
        for dr in (-1, 0, 1):
            for df in (-1, 0, 1):
                if dr == 0 and df == 0:
                    continue
                target = self.wrap_square(sq + (dr, df), board)
                if not board.in_bounds(target):
                    continue
                occupant = board.get(target)
                if occupant is None:
                    yield Move(sq, target)
                elif occupant.colour != piece.colour:
                    yield Move(sq, target, MoveFlag.CAPTURE)

        if not skip_castling:
            yield from self._castle_moves(board, sq, piece)
