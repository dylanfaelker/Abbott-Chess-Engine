"""
engine/search.py

Negamax search with alpha-beta pruning, move ordering, and transposition table.
"""

from __future__ import annotations
from infinity_chess.board import Board
from infinity_chess.move import Move, MoveFlag
from infinity_chess.move_generator import MoveGenerator
from engine.evaluate import Evaluator, PIECE_VALUES
from infinity_chess.pieces import Colour
from infinity_chess.rules import RuleSet

MATE_SCORE = 100_000_000
INF = float("inf")


class Search:
    def __init__(self, board: Board, rules: RuleSet | None = None, isVary: bool = True):
        """Create a search object for a board position and ruleset."""
        self.board = board
        self.generator = MoveGenerator(board, rules)
        self.evaluator = Evaluator(isVary)
        self.transposition_table: dict[int, dict] = {}
        self.killer_moves: list[list] = [[None, None] for _ in range(64)]
        self.nodes_searched = 0
        self.isVary = isVary

    def find_best_move(self, depth: int) -> tuple[Move | None, int]:
        """Run iterative deepening up to depth and return the best move and score."""
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
    #         child = Search(new_board, self.generator.rules, self.isVary)
    #         score = -child._negamax(depth - 1, -INF, INF, 1)
    #         results.append({"move": move, "score": score, "pv": [move,]}) #TODO put in the full principal variation

    #     results.sort(key=lambda r: r["score"], reverse=True)
    #     return results[:top_n]

    def _root_search(self, depth: int) -> tuple[Move | None, int]:
        """Search all legal root moves at a fixed depth."""
        best_move = None
        best_score = -INF
        alpha, beta = -INF, INF

        for move in self._ordered_moves(self.board, 0):
            new_board = self.board.apply_move(move)
            child = Search(new_board, self.generator.rules, self.isVary)
            score = -child._negamax(depth - 1, -beta, -alpha, 1)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

        return best_move, best_score

    def _negamax(self, depth: int, alpha: float, beta: float, ply: int) -> int:
        """Search a position with negamax, alpha-beta, and transposition lookups."""
        self.nodes_searched += 1

        # Checking if position was already computed via transpotion table.
        key = self.board.zobrist_hash()
        tt_entry = self.transposition_table.get(key)
        if tt_entry and tt_entry["depth"] >= depth:
            flag, tt_score = tt_entry["flag"], tt_entry["score"]
            if flag == "exact":              return tt_score
            if flag == "lower" and tt_score >= beta:  return tt_score
            if flag == "upper" and tt_score <= alpha: return tt_score

        over, result = self.generator.game_over()
        if over:
            if result in ("white", "black"):
                loser = Colour.WHITE if result == "black" else Colour.BLACK
                return -(MATE_SCORE - ply) if self.board.turn == loser else (MATE_SCORE - ply) # to prefer earlier mates
            return 0 # draw

        if depth == 0:
            return self._quiescence(alpha, beta)

        original_alpha = alpha
        best_score = -INF
        best_move = None

        for move in self._ordered_moves(self.board, ply):
            new_board = self.board.apply_move(move)
            child = Search(new_board, self.generator.rules, self.isVary)
            child.transposition_table = self.transposition_table
            child.killer_moves = self.killer_moves
            score = -child._negamax(depth - 1, -beta, -alpha, ply + 1)

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, score)

            if alpha >= beta: # beta-cutoff -> killer move
                if move.flag != MoveFlag.CAPTURE: # killer moves are only "quite" moves
                    self.killer_moves[ply][1] = self.killer_moves[ply][0]
                    self.killer_moves[ply][0] = move
                break

        # Updating the transpotion table
        flag = "exact"
        if best_score <= original_alpha: flag = "upper"
        elif best_score >= beta:         flag = "lower"
        self.transposition_table[key] = {"depth": depth, "score": best_score, "flag": flag, "move": best_move}

        return best_score

    def _quiescence(self, alpha: float, beta: float) -> int:
        """Extend leaf search through captures and checks. Combats horizon effect."""
        score = self.evaluator.evaluate(self.board) # stand-pat
        if self.board.turn == Colour.BLACK:
            score = -score

        if score >= beta:  return beta
        alpha = max(alpha, score)

        for move in self._ordered_moves(self.board, 0):

            if move.flag == MoveFlag.CAPTURE:
                new_board = self.board.apply_move(move)
                child = Search(new_board, self.generator.rules, self.isVary)
                s = -child._quiescence(-beta, -alpha)
                if s >= beta:  return beta
                alpha = max(alpha, s)

        return alpha

    def _ordered_moves(self, board: Board, ply: int):
        """Return legal moves sorted by simple tactical and killer-move heuristics."""
        gen = MoveGenerator(board, self.generator.rules)
        moves = gen.legal_moves()
        scored = []

        # Find the best move identified in the previous max depth
        tt_move = None
        key = board.zobrist_hash()
        tt_entry = self.transposition_table.get(key)
        if tt_entry and "move" in tt_entry:
            tt_move = tt_entry["move"]

        for move in moves:
            score = 0

            # Best first Hueristic - found via iterative deepening
            if move == tt_move:
                score = 100_000

            # MVV-LVA Hueristic
            elif move.flag == MoveFlag.CAPTURE:
                victim   = board.get(move.to_sq)
                attacker = board.get(move.from_sq)
                v_val = PIECE_VALUES.get(victim.piece_type, 0)   if victim   else 0
                a_val = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
                score = 10_000 + 10 * v_val - a_val # max 18_900, min 10_100

            # Killer Hueristic
            elif move in self.killer_moves[ply]:
                score = 9_000

            elif move.flag == MoveFlag.PROMOTION:
                score = 8_000

            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for s, m in scored]
