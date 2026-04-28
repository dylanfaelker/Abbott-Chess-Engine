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
from engine.evaluate import Evaluator

app = Flask(__name__)
CORS(app, origins=["https://dylanfaelker.com", "http://localhost:3000"])

@app.route("/health", methods=["GET"])
def health():
    """Wake-up call to ping Render"""
    return jsonify({"status": "ok"}), 200


#TODO handle drawing 3 fold repition if bot is still winning in second best move. Would this even be an issue if search depth is above 3.

@app.route("/move", methods=["POST"])
def get_move():
    """
    Get the engine's best move for a given position.
 
    Request body:
        fen   (str):  FEN string of the current position
        depth (int):  Search depth (default: 2, max: 8). Higher = stronger but slower.
 
    Response:
        move  (str):  Best move in UCI format e.g. "e2e4", "e7e8q"
        eval  (float): Centipawn evaluation from the perspective of the side to move
        depth (int):  Depth actually searched
    """
    data = request.get_json()
 
    if not data or "fen" not in data:
        return jsonify({"error": "Missing required field: fen"}), 400
 
    fen = data["fen"]
    depth = int(data.get("depth", 2))
    depth = max(1, min(depth, 8))
 
    try:
        board = Board.from_fen(data["fen"])
    except ValueError:
        return jsonify({"error": "Invalid FEN string"}), 400
 
    gen = MoveGenerator(board, InfinityChessRules())
    over, result = gen.game_over()
    if over:
        return jsonify({"error": "Game is already over", "result": result}), 400
 
    try:
        searcher = Search(board)
        best_move, score = searcher.find_best_move(depth)

        if best_move is None:
            return jsonify({"error": "No legal moves available"}), 400
 
        return jsonify({
            "move": best_move.to_uci(),
            "eval": score / 100.0,
            "depth": depth,
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
