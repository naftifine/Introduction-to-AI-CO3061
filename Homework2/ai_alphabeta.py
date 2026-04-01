import math
from typing import Optional

import chess


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

MATE_SCORE = 1_000_000


def evaluate_board(board: chess.Board) -> int:
    """Return score from White's perspective."""
    if board.is_checkmate():
        return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score


def _search(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> int:
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    if maximizing:
        value = -math.inf
        for move in board.legal_moves:
            board.push(move)
            value = max(value, _search(board, depth - 1, alpha, beta, False))
            board.pop()
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return int(value)

    value = math.inf
    for move in board.legal_moves:
        board.push(move)
        value = min(value, _search(board, depth - 1, alpha, beta, True))
        board.pop()
        beta = min(beta, value)
        if beta <= alpha:
            break
    return int(value)


def choose_move_alpha_beta(board: chess.Board, depth: int = 3) -> Optional[chess.Move]:
    """Pick the best move for side to move using alpha-beta pruning."""
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    maximizing = board.turn == chess.WHITE
    best_score = -math.inf if maximizing else math.inf
    best_move = legal_moves[0]

    for move in legal_moves:
        board.push(move)
        score = _search(board, depth - 1, -math.inf, math.inf, not maximizing)
        board.pop()

        if maximizing and score > best_score:
            best_score = score
            best_move = move
        elif not maximizing and score < best_score:
            best_score = score
            best_move = move

    return best_move
