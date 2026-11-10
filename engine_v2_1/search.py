"""
engine/search.py

Negamax search with alpha-beta pruning.
Complexity notation: b = branching factor and d = search depth.
"""

from __future__ import annotations
import time
from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag
from infinity_chess.move_generator import MoveGenerator
from engine_v2_1.evaluate import Evaluator, PIECE_VALUES
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet

MATE_SCORE = 100_000_000
INF = float("inf")


class _SearchTimeout(Exception):
    """Internal: raised inside the tree when the soft deadline passes, to unwind the search."""


class _SharedState:
    """
    Counters shared by the root Search and every child Search it spawns.
    (This engine creates a new Search object per node, so per-instance counters
    would never add up.)
    """
    __slots__ = ("nodes", "deadline", "check")

    def __init__(self):
        self.nodes = 0
        self.deadline: float | None = None  # time.perf_counter() timestamp; None = no limit
        self.check = False                  # off during depth 1 so a move is always available


class Search:
    """
    Basic negamax alpha-beta engine.

    Args:
        board (Board): Board position being queried or updated.
        rules (RuleSet | None): Ruleset used to interpret the board.

    Returns:
        Search: Configured search engine; find_best_move returns a move and score.

    Complexity:
        O(b^d).
    """
    def __init__(self, board: Board, rules: RuleSet | None = None):
        """
        Create search state.

        Args:
            board (Board): Board position being queried or updated.
            rules (RuleSet | None): Ruleset used to interpret the board.

        Returns:
            None: Initializes the Search instance.

        Complexity:
            O(1).
        """
        self.board = board
        self.generator = MoveGenerator(board, rules)
        self.evaluator = Evaluator()
        self._shared = _SharedState()
        self.depth_reached = 0  # deepest search that completed (set by find_best_move)

    @property
    def nodes_searched(self) -> int:
        """Nodes visited by the last search, across the whole tree."""
        return self._shared.nodes

    def find_best_move(self, depth: int, time_limit: float | None = None) -> tuple[Move | None, int]:
        """
        Search root moves to a fixed depth.

        Without a time limit this is a single fixed-depth search, exactly as before.
        This engine has no iterative deepening of its own, so when `time_limit`
        (seconds) is given it searches depth 1, 2, 3... up to `depth` individually, abandons the
        iteration that is running when time expires, and returns the move from the
        last completed depth. Depth 1 always completes.

        Args:
            depth (int): Maximum search depth or remaining node depth.
            time_limit (float | None): Soft limit in seconds.

        Returns:
            tuple[Move | None, int]: (Move or None, score); worst-case.
            After the call, `nodes_searched` and `depth_reached` describe the search.

        Complexity:
            O(b^d).
        """
        shared = self._shared
        shared.nodes = 0
        shared.deadline = None if time_limit is None else time.perf_counter() + time_limit
        shared.check = False
        self.depth_reached = 0

        if time_limit is None:
            move, score = self._root_search(depth)
            self.depth_reached = depth
            return move, score

        best_move = None
        best_score = -INF
        for current_depth in range(1, depth + 1):
            shared.check = current_depth > 1
            try:
                move, score = self._root_search(current_depth)
            except _SearchTimeout:
                break
            if move is not None:
                best_move = move
                best_score = score
                self.depth_reached = current_depth

        shared.check = False
        return best_move, best_score

    def _root_search(self, depth: int) -> tuple[Move | None, int]:
        """
        Score each legal root move with a fixed-depth negamax search.

        Args:
            depth (int): Search depth.

        Returns:
            tuple[Move | None, int]: best move and score.

        Complexity:
            O(b^d).
        """
        best_move = None
        best_score = -INF
        alpha, beta = -INF, INF

        for move in self.generator.legal_moves():
            new_board = self.board.apply_move(move)
            child = Search(new_board, self.generator.rules)
            child._shared = self._shared
            score = -child._negamax(depth - 1, -beta, -alpha, 1)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move, best_score

    def _negamax(self, depth: int, alpha: float, beta: float, ply: int) -> int:
        """
        Search a node with negamax alpha-beta.

        Args:
            depth (int): Maximum search depth or remaining node depth.
            alpha (float): Current alpha bound for alpha-beta search.
            beta (float): Current beta bound for alpha-beta search.
            ply (int): Current distance in plies from the search root.

        Returns:
            int: score; worst-case subtree.

        Complexity:
            O(b^d).
        """
        shared = self._shared
        shared.nodes += 1
        if shared.check and time.perf_counter() >= shared.deadline:
            raise _SearchTimeout

        over, result = self.generator.game_over()
        if over:
            if result in ("white", "black"):
                loser = Colour.WHITE if result == "black" else Colour.BLACK
                return -(MATE_SCORE - ply) if self.board.turn == loser else (MATE_SCORE - ply) # To prefer earlier mates
            return 0 # draw

        if depth == 0:
            return self.evaluator.evaluate(self.board)
        
        best_score = -INF

        for move in self.generator.legal_moves():
            new_board = self.board.apply_move(move)
            child = Search(new_board, self.generator.rules)
            child._shared = self._shared
            score = -child._negamax(depth - 1, -beta, -alpha, ply + 1)

            best_score = max(best_score, score)
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        return best_score
