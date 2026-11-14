"""
engine/search.py

Negamax search with alpha-beta pruning, move ordering, and transposition table.
Complexity notation: b = branching factor, d = search depth, q = quiescence depth,
L = legal move count, M = candidate moves, and A = king-safety check cost.
"""

from __future__ import annotations
import time
from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag, CAPTURE_FLAGS, QUIESCENCE_FLAGS
from infinity_chess.move_generator import MoveGenerator
from engine.evaluate import Evaluator, PIECE_VALUES
from infinity_chess.pieces import Colour
from infinity_chess.rules import InfinityChessRules, RuleSet

MATE_SCORE = 100_000_000

TT_EXACT, TT_LOWER, TT_UPPER = 0, 1, 2

# attacker values for move ordering only: the king is capped so Kxp isn't "-89,000"
ORDER_VALUES = {pt: min(v, 1000) for pt, v in PIECE_VALUES.items()}

INF = float("inf")


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
        self.transposition_table: dict[int, dict] = {}
        self.killer_moves: list[list] = [[None, None] for _ in range(64)]
        self.nodes_searched = 0
        self.depth_reached = 0                # deepest iteration that completed (set by find_best_move)
        self.deadline: float | None = None    # time.perf_counter() timestamp; None = no time limit
        self._check_deadline = False          # off during depth 1 so a move is always available
        self.isVary = isVary

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
            self._check_deadline = self.deadline is not None and current_depth > 1
            try:
                move, score = self._root_search(current_depth)
            except _SearchTimeout:
                break  # discard the unfinished iteration, keep the last completed one
            if move is not None:
                best_move = move
                best_score = score
                self.depth_reached = current_depth

        self._check_deadline = False
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

        for move in self._ordered_moves(self.board, 0):
            undo = self.board.make_move(move)
            try:
                score = -self._negamax(self.board, depth - 1, -beta, -alpha, 1)
            finally:
                self.board.unmake_move(undo)  # also runs when a timeout unwinds the search

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

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
        if tt_entry and tt_entry["depth"] >= depth:
            flag, tt_score = tt_entry["flag"], tt_entry["score"]
            if flag == TT_EXACT:              return tt_score
            if flag == TT_LOWER and tt_score >= beta:  return tt_score
            if flag == TT_UPPER and tt_score <= alpha: return tt_score

        gen = MoveGenerator(board, self.rules)
        legal_moves = gen.legal_moves()
        over, result = gen.game_over(legal_moves)
        if over:
            if result in ("white", "black"):
                loser = Colour.WHITE if result == "black" else Colour.BLACK
                return -(MATE_SCORE - ply) if board.turn == loser else (MATE_SCORE - ply) # to prefer earlier mates
            return 0 # draw

        if depth == 0:
            return self._quiescence(board, alpha, beta, legal_moves)

        original_alpha = alpha
        best_score = -INF
        best_move = None

        for move in self._ordered_moves(board, ply, legal_moves):
            undo = board.make_move(move)
            try:
                score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            finally:
                board.unmake_move(undo)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

            if alpha >= beta: # beta-cutoff -> killer move
                if move.flag not in CAPTURE_FLAGS: # killer moves are only "quiet" moves
                    self.killer_moves[ply][1] = self.killer_moves[ply][0]
                    self.killer_moves[ply][0] = move
                break

        # Updating the transpotion table
        flag = TT_EXACT
        if best_score <= original_alpha: flag = TT_UPPER
        elif best_score >= beta:         flag = TT_LOWER
        self.transposition_table[key] = {"depth": depth, "score": best_score, "flag": flag, "move": best_move}

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

        score = self.evaluator.evaluate(board) # stand-pat
        if board.turn == Colour.BLACK:
            score = -score

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
            for move in self.rules.pseudo_legal_moves(board, square):
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
        if tt_entry and "move" in tt_entry:
            tt_move = tt_entry["move"]

        for move in legal_moves:
            score = 0

            # Best first Hueristic - found via iterative deepening
            if move == tt_move:
                score = 100_000

            # MVV-LVA Hueristic
            elif move.flag in CAPTURE_FLAGS:
                victim_sq = move.captured_sq or move.to_sq
                victim = board.get(victim_sq)
                attacker = board.get(move.from_sq)
                v_val = PIECE_VALUES.get(victim.piece_type, 0)   if victim   else 0
                a_val = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
                score = 10_000 + 10 * v_val - a_val # max 18_900, min 10_100

            # Killer Hueristic
            elif move in self.killer_moves[ply]:
                score = 9_000

            elif move.flag in (MoveFlag.PROMOTION, MoveFlag.PROMOTION_CAPTURE):
                score = 8_000

            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for s, m in scored]
