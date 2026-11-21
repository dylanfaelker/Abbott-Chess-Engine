from infinity_chess.board import Board
from infinity_chess.pieces import Colour, PieceType
from config import PIECE_VALUES

def is_endgame(board: Board) -> bool:
    """
    Determines if the board is in the endgame.

    Args:
        board (Board): Board position being queried or updated.

    Returns:
        bool: whether or not it is the endgame.

    Complexity:
        O(P).
    """
    total_mat = 0
    for colour in Colour:
        for piece_type in PieceType:
            if piece_type == PieceType.KING or piece_type == PieceType.PAWN:
                continue
            value = PIECE_VALUES.get(piece_type, 0)
            bb = board.bitboards[colour, piece_type]
            total_mat += value * bb.bit_count()
    return total_mat <= 28 