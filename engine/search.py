"""
engine/search.py

Negamax search with alpha-beta pruning, move ordering, and transposition table.
Complexity notation: b = branching factor, d = search depth, q = quiescence depth,
L = legal move count, M = candidate moves, and A = king-safety check cost.
"""

from __future__ import annotations
from pathlib import Path
import sys

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if sys.path and sys.path[0] != _ENGINE_DIR:
    if _ENGINE_DIR in sys.path:
        sys.path.remove(_ENGINE_DIR)
    sys.path.insert(0, _ENGINE_DIR)
    sys.modules.pop("evaluate", None)

import time
from infinity_chess.board import Board, _pre_promotion_masks
from infinity_chess.move import Move, MoveFlag, CAPTURE_FLAGS, QUIESCENCE_FLAGS
from infinity_chess.move_generator import MoveGenerator
from evaluate import Evaluator, PIECE_VALUES
from infinity_chess.pieces import Colour, PieceType
from infinity_chess.rules import InfinityChessRules, RuleSet
from config import MATE_SCORE, DELTA_MARGIN, HISTORY_MAX, PROMOTION_HUERISTIC_MAX, HASH_MOVE_SCORE, MVV_LVA_BASE, KILLER_MOVE_SCORE, MATE_KILLER_SCORE, MATE_BOUND
from abbott import is_endgame

TT_EXACT, TT_LOWER, TT_UPPER = 0, 1, 2

# attacker values for move ordering only: the king is capped so Kxp isn't "-89,000"
ORDER_VALUES = {pt: min(v, 1000) for pt, v in PIECE_VALUES.items()}

INF = float("inf")

MAX_PLY = 64
TT_MAX_ENTRIES = 500_000


class _SearchTimeout(Exception):
    """Internal: raised inside the tree when the soft deadline passes, to unwind the search."""


class Search:
    """
    Negamax alpha-beta engine with move ordering.

    Args:
        board (Board): Board position being queried or updated.
        rules (RuleSet | None): Ruleset used to interpret the board.
        isVary (bool): Toggle for randomized evaluation variation.

    Returns:
        Search: Configured search engine; find_best_move returns a move and score.

    Complexity:
        O(b^d).
    """
    def __init__(self, board: Board, rules: RuleSet | None = None, isVary: bool = True):
        """
        Create search state.

        Args:
            board (Board): Board position being queried or updated.
            rules (RuleSet | None): Ruleset used to interpret the board.
            isVary (bool): Toggle for randomized evaluation variation.

        Returns:
            None: Initializes the Search instance.

        Complexity:
            O(1).
        """
        self.board = board
        self.rules = rules or InfinityChessRules()
        self.evaluator = Evaluator(isVary)
        self.transposition_table: dict[int, tuple[int, int, int, Move | None]] = {}
        self.killer_moves: list[list] = [[None, None] for _ in range(MAX_PLY)]
        self.mate_killers: list[Move | None] = [None] * MAX_PLY
        n = board.ranks * board.files
        self.history = [0] * (2 * n * n) # # [colour][from][to], flattened
        self.nodes_searched = 0
        self.depth_reached = 0                # deepest iteration that completed (set by find_best_move)
        self.deadline: float | None = None    # time.perf_counter() timestamp; None = no time limit
        self._check_deadline = False          # off during depth 1 so a move is always available
        self.isVary = isVary
        self._root_best: tuple[Move | None, float] = (None, -INF)
        self._root_scores: dict[Move, int] = {}

    def find_best_move(self, depth: int, time_limit: float | None = None) -> tuple[Move | None, int]:
        """
        Search increasing depths for a best move.

        Args:
            depth (int): Maximum search depth or remaining node depth.
            time_limit (float | None): Soft limit in seconds. When it expires the
                unfinished iteration is abandoned and the best move from the last
                completed depth is returned. Depth 1 always completes.

        Returns:
            tuple[Move | None, int]: (Move or None, score); worst-case.
            After the call, `nodes_searched` and `depth_reached` describe the search.

        Complexity:
            O(b^d).
        """
        self.nodes_searched = 0
        self.depth_reached = 0
        self.deadline = None if time_limit is None else time.perf_counter() + time_limit
        best_move = None
        best_score = -INF

        # Iterative deepening
        for current_depth in range(1, depth + 1):
            self._check_deadline = self.deadline is not None
            self._root_best = (None, -INF)
            try:
                move, score = self._root_search(current_depth)
            except _SearchTimeout:
                if self._root_best[0] is not None:
                    best_move, best_score = self._root_best
                break  # discard the unfinished iteration, keep the last completed one
            if move is not None:
                best_move = move
                best_score = score
                self.depth_reached = current_depth

        self._check_deadline = False

        if best_move is None:
            ordered = self._ordered_moves(self.board, 0)
            if ordered:
                best_move, best_score = ordered[0], 0

        return best_move, best_score

    # def analyze(self, depth: int, top_n: int) -> list[dict]:
    #     """Return the top N root moves with their searched scores."""
    #     results = []
    #     for move in self._ordered_moves(self.board, 0):
    #         new_board = self.board.apply_move(move)
    #         score = -self._negamax(new_board, depth - 1, -INF, INF, 1)
    #         results.append({"move": move, "score": score, "pv": [move,]}) #TODO put in the full principal variation

    #     results.sort(key=lambda r: r["score"], reverse=True)
    #     return results[:top_n]

    def _to_tt(self, score, ply):   return score + ply if score >  MATE_BOUND else score - ply if score < -MATE_SCORE + 1000 else score
    def _from_tt(self, score, ply): return score - ply if score >  MATE_BOUND else score + ply if score < -MATE_SCORE + 1000 else score

    def _tt_store(self, key: int, depth: int, score: int, flag: int, move: Move | None) -> None:
        """Entries are tuples: (depth, score, flag, move)."""
        tt = self.transposition_table
        old = tt.get(key)
        if old is not None:
            if depth < old[0]:
                return                  # depth-preferred: never replace a deeper result
            if move is None:
                move = old[3]           # keep the old move as an ordering hint
        elif len(tt) >= TT_MAX_ENTRIES:
            tt.clear()                  # size cap
        tt[key] = (depth, score, flag, move)

    def _root_search(self, depth: int) -> tuple[Move | None, int]:
        """
        Score each legal root move.

        Args:
            depth (int): Maximum search depth or remaining node depth.

        Returns:
            tuple[Move | None, int]: best move and score; worst-case.

        Complexity:
            O(b^d).
        """
        best_move = None
        best_score = -INF
        alpha, beta = -INF, INF

        ordered = self._ordered_moves(self.board, 0)
        if self._root_scores:
            ordered.sort(key=lambda m: self._root_scores.get(m, -INF), reverse=True)

        scores: dict[Move, int] = {}
        for move in self._ordered_moves(self.board, 0):
            undo = self.board.make_move(move)
            try:
                score = -self._negamax(self.board, depth - 1, -beta, -alpha, 1)
            finally:
                self.board.unmake_move(undo)  # also runs when a timeout unwinds the search

            scores[move] = score
            if score > best_score:
                best_score = score
                best_move = move
                self._root_best = (best_move, best_score)
            alpha = max(alpha, score)

        self._root_scores = scores

        if best_move is not None:
            self._tt_store(self.board.zobrist_hash(), depth, best_score, TT_EXACT, best_move)

        return best_move, best_score

    def _negamax(self, board: Board, depth: int, alpha: float, beta: float, ply: int) -> int:
        """
        Search one node with alpha-beta and transpositions.

        Args:
            board (Board): Board position being queried or updated.
            depth (int): Maximum search depth or remaining node depth.
            alpha (float): Current alpha bound for alpha-beta search.
            beta (float): Current beta bound for alpha-beta search.
            ply (int): Current distance in plies from the search root.

        Returns:
            int: score; worst-case subtree.

        Complexity:
            O(b^d).
        """
        self.nodes_searched += 1
        if self._check_deadline and time.perf_counter() >= self.deadline:
            raise _SearchTimeout

        # Checking if position was already computed via transpotion table.
        key = board.zobrist_hash()
        tt_entry = self.transposition_table.get(key)
        if tt_entry is not None and tt_entry[0] >= depth:
            _, tt_score, flag, _ = tt_entry
            tt_score = self._from_tt(tt_score, ply)
            if flag == TT_EXACT:                        return tt_score
            if flag == TT_LOWER and tt_score >= beta:   return tt_score
            if flag == TT_UPPER and tt_score <= alpha:  return tt_score

        if depth == 0:
            if ply < MAX_PLY and self.rules.is_in_check(board, board.turn):
                depth = 1 # check extension: forced to find evasions
            else:
                return self._quiescence(board, alpha, beta)
            
        original_alpha = alpha
        best_score = -INF
        best_move = None

        gen = MoveGenerator(board, self.rules)

        # edge case to handle game thats already won TODO maybe just check in find_best_move if the game is already over
        # opponent_in_check = self.rules.is_in_check(board, Colour.opponent(board.turn))

        # cheap draw checks first
        if self.rules.is_draw(board):
            _, result = gen.game_over() # prioritise mate over 50 move draw
            if result != "draw":
                return -(MATE_SCORE - ply) if self.rules.is_in_check(board, board.turn) else (MATE_SCORE - ply)
            else:
                return 0
            
        colour, legal_found = board.turn, False
        quiets: list[Move] = []
        pseudo_moves = gen.pseudo_legal_moves()
        for move in self._ordered_moves(board, ply, pseudo_moves):
            undo = board.make_move(move)
            try:
                if self.rules.is_in_check(board, colour):
                    continue    # illegal
                legal_found = True
                score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            finally:
                board.unmake_move(undo)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

            if alpha >= beta: # beta-cutoff -> killer move

                if move.flag not in CAPTURE_FLAGS: # killer moves are only "quiet" moves
                    if score >= MATE_BOUND: # Mate killer
                        self.mate_killers[ply] = move
                    elif self.killer_moves[ply][0] != move:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = move

                if move.flag not in QUIESCENCE_FLAGS:              # truly quiet: no capture, no promotion
                    bonus = min(32 * depth * depth, 1200) # 32 scales the memory length (smaller = longer memory)
                    self._update_history(self._hist_index(board, move), bonus)
                    for q in quiets:                               # tried first, failed to cut off
                        self._update_history(self._hist_index(board, q), -bonus)
                
                break

            if move.flag not in QUIESCENCE_FLAGS:
                quiets.append(move)

        if not legal_found: # game over
            return -(MATE_SCORE - ply) if self.rules.is_in_check(board, colour) else 0

        # Updating the transpotion table
        flag = TT_EXACT
        if best_score <= original_alpha: flag = TT_UPPER
        elif best_score >= beta:         flag = TT_LOWER
        self._tt_store(key, depth, self._to_tt(best_score, ply), flag, None if flag == TT_UPPER else best_move)

        return best_score

    def _quiescence(
        self,
        board: Board,
        alpha: float,
        beta: float,
        legal_moves: list[Move] | None = None,
    ) -> int:
        """
        Extend a leaf through tactical captures.

        Args:
            board (Board): Board position being queried or updated.
            alpha (float): Current alpha bound for alpha-beta search.
            beta (float): Current beta bound for alpha-beta search.
            legal_moves (list[Move] | None): Previously generated legal moves, when
            available. Passing this param saved having to find the quiescent legal 
            moves. Otherwise _legal_quiescence_moves() is called.

        Returns:
            int: score; worst-case.

        Complexity:
            O(b^q)
        """
        self.nodes_searched += 1
        if self._check_deadline and time.perf_counter() >= self.deadline:
            raise _SearchTimeout

        score, is_endgame = self.evaluator.evaluate_and_is_endgame(board) # stand-pat
        if board.turn == Colour.BLACK:
            score = -score

        # Delta pruning
        if not is_endgame:
            delta = 0
            for pt in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT, PieceType.PAWN):
                if (board.bitboards[board.turn.opponent(), pt] != 0): 
                    delta = PIECE_VALUES[pt]
                    break

            white_promo_mask, black_promo_mask = _pre_promotion_masks(board.ranks, board.files)
            promo_mask = white_promo_mask if board.turn == Colour.WHITE else black_promo_mask
            if board.bitboards[board.turn, PieceType.PAWN] & promo_mask:
                delta += PIECE_VALUES[PieceType.QUEEN] - PIECE_VALUES[PieceType.PAWN]

            if score + delta + DELTA_MARGIN < alpha:
                return alpha

        if score >= beta:  return beta
        alpha = max(alpha, score)

        if legal_moves is None:
            legal_moves = self._legal_quiescence_moves(board)


        for move in self._ordered_moves(board, 0, legal_moves):

            if move.flag in QUIESCENCE_FLAGS:
                undo = board.make_move(move)
                try:
                    s = -self._quiescence(board, -beta, -alpha)
                finally:
                    board.unmake_move(undo)
                if s >= beta:  return beta
                alpha = max(alpha, s)

        return alpha

    def _legal_quiescence_moves(self, board: Board) -> list[Move]:
        """Return legal tactical moves without generating the full legal list.

        Quiescence only searches captures (including en passant and promotion
        captures) and quiet promotions.  Filtering the pseudo-legal candidates
        before the king-safety check avoids making and unmaking every quiet move
        at each quiescence node.

        Complexity:
            O(C*A), where C is the number of pseudo-legal tactical candidates
            and A is the cost of a king-safety check.
        """
        colour = board.turn
        legal_moves = []

        for square, _piece in board.pieces_for(colour):
            for move in self.rules.pseudo_legal_moves_from(board, square):
                if move.flag not in QUIESCENCE_FLAGS:
                    continue

                undo = board.make_move(move)
                leaves_king_in_check = self.rules.is_in_check(board, colour)
                board.unmake_move(undo)
                if not leaves_king_in_check:
                    legal_moves.append(move)

        return legal_moves

    def _ordered_moves(self, board: Board, ply: int, legal_moves: list[Move] | None = None):
        """
        Sort legal moves by TT, capture, and killer priorities.

        Args:
            board (Board): Board position being queried or updated.
            ply (int): Current distance in plies from the search root.
        legal_moves (list[Move] | None): Previously generated legal moves, when
            available.

        Returns:
            list[Move]: Ordered legal moves.

        Complexity:
            O(L log L), plus O(M*A) if moves must be generated.
        """
        if legal_moves is None:
            gen = MoveGenerator(board, self.rules)
            legal_moves = gen.legal_moves()
        scored = []

        # Find the best move identified in the previous max depth
        tt_move = None
        key = board.zobrist_hash()
        tt_entry = self.transposition_table.get(key)
        tt_move = tt_entry[3] if tt_entry else None

        for move in legal_moves:
            score = 0

            # Best first Hueristic - found via iterative deepening
            if move == tt_move:
                score = HASH_MOVE_SCORE

            # MVV-LVA Hueristic
            elif move.flag in CAPTURE_FLAGS:
                victim_sq = move.captured_sq or move.to_sq
                victim = board.get(victim_sq)
                attacker = board.get(move.from_sq)
                v_val = ORDER_VALUES.get(victim.piece_type, 0)   if victim   else 0
                a_val = ORDER_VALUES.get(attacker.piece_type, 0) if attacker else 0
                score = MVV_LVA_BASE + 10 * v_val - a_val # max 18_900, min 10_000

            # Mate Killer Hueristic
            elif move == self.mate_killers[ply]:
                score = MATE_KILLER_SCORE

            # Killer Hueristic
            elif move == self.killer_moves[ply][0]:
                score = KILLER_MOVE_SCORE
            elif move == self.killer_moves[ply][1]:
                score = KILLER_MOVE_SCORE - 1

            # Promotion Hueristics
            elif move.flag in (MoveFlag.PROMOTION, MoveFlag.PROMOTION_CAPTURE):
                if move.promotion_piece.lower() == "queen":
                    score = PROMOTION_HUERISTIC_MAX
                elif move.promotion_piece.lower() == "rook":
                    score = PROMOTION_HUERISTIC_MAX - 1
                elif move.promotion_piece.lower() == "bishop":
                    score = PROMOTION_HUERISTIC_MAX - 2
                else:
                    score = PROMOTION_HUERISTIC_MAX - 3

            else:
                # History Hueristic
                score = self.history[self._hist_index(board, move)]

                # Advancement Hueristic
                advancement = move.to_sq.rank if board.turn is Colour.WHITE else board.ranks - 1 - move.to_sq.rank
                score += advancement

            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for s, m in scored]

    def _hist_index(self, board: Board, move: Move) -> int:
        n = board.ranks * board.files
        return ((board.turn is Colour.BLACK) * n + board._index(move.from_sq)) * n + board._index(move.to_sq)

    def _update_history(self, idx: int, bonus: int) -> None:
        h = self.history[idx]

        # exponential moving average with scaling decay rate keeps it bounded by [-MAX, MAX]
        self.history[idx] = h + bonus - h * abs(bonus) // HISTORY_MAX # h' = h x (1 - |bonus| / MAX) + bonus
