"""Flask API for chess-engine health checks and move searches."""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from infinity_chess.board import Board
from infinity_chess.game import Game
from infinity_chess.move import Square, Move
from infinity_chess.move_generator import MoveGenerator
from infinity_chess.rules import InfinityChessRules
from engine.search import Search
from engine_v2_1.search import Search as Search_v2_1
from engine_v2_2.search import Search as Search_v2_2
from engine_v2_3.search import Search as Search_v2_3
from engine_v2_4.search import Search as Search_v2_4
from engine_v2_5.search import Search as Search_v2_5
from engine_v2_6.search import Search as Search_v2_6
from engine_v2_7.search import Search as Search_v2_7

app = Flask(__name__)
CORS(app, origins=["https://www.dylanfaelker.com", "http://localhost:3000"])

@app.route("/health", methods=["GET"])
def health():
    """
    Report service health.

    Returns:
        tuple[Response, int]: JSON status response and HTTP 200.

    Complexity:
        O(1).
    """
    return jsonify({"status": "ok"}), 200


@app.route("/move", methods=["POST"])
def get_move():
    """
    Get the engine's best move for a given position.

    Request body:
        fen    (str):       FEN string of the current position
        depth  (int):       Search depth (default: 2, max: 8). Higher = stronger but slower.
        time_limit (float): Optional soft limit in seconds (max 10). With no depth, searches as deep as the time allows.
        engine (str):       Engine version (defaults to latest engine).

    Response:
        move   (str):   Best move in UCI format e.g. "e2e4", "e7e8q"
        eval   (float): Centipawn evaluation from the perspective of the side to move
        depth  (int):   Depth actually searched
        engine (str):   Actual engine used

    Returns:
        tuple[Response, int]: JSON response with the move and evaluation, or an
            error response with its HTTP status.

    Complexity:
        dominated by selected engine search, approximately O(b^d) without pruning,
    where b is branching factor and d is search depth.
    """
    data = request.get_json()
 
    if not data or "fen" not in data:
        return jsonify({"error": "Missing required field: fen"}), 400
 
    fen = data["fen"]

    depth = int(data.get("depth", 64))
    depth = max(1, min(depth, 64))
    time_limit = int(data.get("time_limit", 1))
    time_limit = max(0, min(time_limit, 10))
 
    try:
        board = Board.from_fen(fen)
    except ValueError:
        return jsonify({"error": "Invalid FEN string"}), 400
    
    # Choosing the engine
    engine = data.get("engine", "latest")
    if engine == "v2.1":
        searcher = Search_v2_1(board, InfinityChessRules())
    elif engine == "v2.2":
        searcher = Search_v2_2(board, InfinityChessRules())
    elif engine == "v2.3":
        searcher = Search_v2_3(board, InfinityChessRules())
    elif engine == "v2.4":
        searcher = Search_v2_4(board, InfinityChessRules())
    elif engine == "v2.5":
        searcher = Search_v2_5(board, InfinityChessRules())
    elif engine == "v2.6":
        searcher = Search_v2_6(board, InfinityChessRules())
    elif engine == "v2.7":
        searcher = Search_v2_7(board, InfinityChessRules())
    else:
        searcher = Search(board, InfinityChessRules())
 
    gen = MoveGenerator(board, InfinityChessRules())
    over, result = gen.game_over()
    if over:
        return jsonify({"error": "Game is already over", "result": result}), 400
 
    try:
        best_move, score = searcher.find_best_move(depth, time_limit)

        if best_move is None:
            return jsonify({"error": "No legal moves available"}), 400
 
        return jsonify({
            "move": best_move.to_uci(),
            "eval": score / 100.0,
            "depth": searcher.depth_reached,
            "engine": engine,
        }), 200
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Engine error", "detail": str(e)}), 500

# @app.route("/legal-moves", methods=["POST"])
# def legal_moves():
#     """
#     Return all legal moves for a given position.
 
#     Request body:
#         fen    (str):          FEN string
#         square (str, optional): If provided, return only moves from that square e.g. "e2"
 
#     Response:
#         moves (list[str]): Legal moves in UCI format
#         count (int):       Number of legal moves
#     """

# @app.route("/evaluate", methods=["POST"])
# def evaluate():
#     """
#     Return a static evaluation of a position (no search — instant).
#     Useful for live advantage meters.
 
#     Request body:
#         fen (str): FEN string
 
#     Response:
#         eval       (float): Score in pawns from white's perspective
#         game_over  (bool):  Whether the game is over
#         outcome    (str):   "checkmate", "stalemate", "draw", or null
#     """

# @app.route("/analyze", methods=["POST"])
# def analyze():
#     """
#     Return the top N moves with scores and the principal variation.
#     More expensive than /move — use for post-game analysis features.
 
#     Request body:
#         fen   (str): FEN string
#         depth (int): Search depth (default: 4)
#         top_n (int): Number of top moves to return (default: 3)
 
#     Response:
#         moves (list): Each entry has:
#             move (str):           Move in UCI format
#             eval (float):         Score in pawns
#             pv   (list[str]):     Principal variation (expected line of play)
#     """



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
