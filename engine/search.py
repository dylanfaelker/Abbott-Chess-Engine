"""
engine/search.py

Negamax search with alpha-beta pruning, move ordering, and transposition table.
Complexity notation: b = branching factor, d = search depth, q = quiescence depth,
L = legal move count, M = candidate moves, and A = king-safety check cost.
"""

from __future__ import annotations
from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag, SpecialMove
from infinity_chess.move_generator import MoveGenerator
from engine.evaluate import Evaluator, PIECE_VALUES
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet

MATE_SCORE = 100_000_000
INF = float("inf")


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
        self.rules = rules
        self.evaluator = Evaluator(isVary)
        self.transposition_table: dict[int, dict] = {}
        self.killer_moves: list[list] = [[None, None] for _ in range(64)]
        self.nodes_searched = 0
        self.isVary = isVary

    def find_best_move(self, depth: int) -> tuple[Move | None, int]:
        """
        Search increasing depths for a best move.

        Args:
            depth (int): Maximum search depth or remaining node depth.

        Returns:
            tuple[Move | None, int]: (Move or None, score); worst-case.

        Complexity:
            O(b^d).
        """
        self.nodes_searched = 0
        best_move = None
        best_score = -INF

        # Iterative deepening
        for current_depth in range(1, depth + 1):
            move, score = self._root_search(current_depth)
            if move is not None:
                best_move = move
                best_score = score

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
            score = -self._negamax(self.board, depth - 1, -beta, -alpha, 1)
            self.board.unmake_move(undo)

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

        # Checking if position was already computed via transpotion table.
        key = board.zobrist_hash()
        tt_entry = self.transposition_table.get(key)
        if tt_entry and tt_entry["depth"] >= depth:
            flag, tt_score = tt_entry["flag"], tt_entry["score"]
            if flag == "exact":              return tt_score
            if flag == "lower" and tt_score >= beta:  return tt_score
            if flag == "upper" and tt_score <= alpha: return tt_score

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
            score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.unmake_move(undo)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

            if alpha >= beta: # beta-cutoff -> killer move
                if move.flag not in (MoveFlag.CAPTURE, MoveFlag.EN_PASSANT, MoveFlag.PROMOTION_CAPTURE): # killer moves are only "quiet" moves
                    self.killer_moves[ply][1] = self.killer_moves[ply][0]
                    self.killer_moves[ply][0] = move
                break

        # Updating the transpotion table
        flag = "exact"
        if best_score <= original_alpha: flag = "upper"
        elif best_score >= beta:         flag = "lower"
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
            available.

        Returns:
            int: score; worst-case.

        Complexity:
            O(b^q)
        """
        score = self.evaluator.evaluate(board) # stand-pat
        if board.turn == Colour.BLACK:
            score = -score

        if score >= beta:  return beta
        alpha = max(alpha, score)

        for move in self._ordered_moves(board, 0, legal_moves):

            if move.flag in (MoveFlag.CAPTURE, MoveFlag.EN_PASSANT, MoveFlag.PROMOTION_CAPTURE):
                undo = board.make_move(move)
                s = -self._quiescence(board, -beta, -alpha)
                board.unmake_move(undo)
                if s >= beta:  return beta
                alpha = max(alpha, s)

        return alpha

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
            elif move.flag in (MoveFlag.CAPTURE, MoveFlag.EN_PASSANT, MoveFlag.PROMOTION_CAPTURE):
                victim_sq = move.to_sq
                if isinstance(move, SpecialMove):
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
