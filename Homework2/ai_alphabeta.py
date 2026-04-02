import math
import time
from typing import Optional
from collections import defaultdict

import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

MATE_SCORE = 100000
CHECK_BONUS = 50
CAPTURE_BONUS = 75
MAX_MOVE_TIME_SECONDS = 7

class SearchTimeout(Exception):
    """Raised when search exceeds the time budget."""

def _check_timeout(deadline: float) -> None:
    if time.perf_counter() >= deadline:
        raise SearchTimeout

PAWN_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_PST = [
    0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    5, 10, 10, 10, 10, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
    0,  0,  5,  5,  5,  5,  0, -5,
    -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_PST = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 30, 10,  0,  0, 10, 30, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
]

PST_TABLES = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
    chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST,
    chess.QUEEN: QUEEN_PST,
    chess.KING: KING_PST,
}

def get_pst_value(piece: chess.Piece, square: chess.Square) -> int:
    if piece.piece_type not in PST_TABLES:
        return 0

    pst = PST_TABLES[piece.piece_type]

    if piece.color == chess.BLACK:
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        flipped_square_index = (7 - rank) * 8 + file
    else:
        flipped_square_index = square

    return pst[flipped_square_index]

TT_EXACT, TT_LOWER, TT_UPPER = 0, 1, 2
tt = {}
move_history = defaultdict(int)
killer_moves = defaultdict(list)

def get_move_priority(board: chess.Board, move: chess.Move, depth: int = 0, pv_move: chess.Move = None) -> int:
    if move == pv_move:
        return 2000000

    priority = 0
    if board.is_capture(move):
        victim_piece = board.piece_at(move.to_square)
        attacker_piece = board.piece_at(move.from_square)
        victim_val = PIECE_VALUES.get(victim_piece.piece_type, 100) if victim_piece else 100
        attacker_val = PIECE_VALUES.get(attacker_piece.piece_type, 100) if attacker_piece else 100
        if board.is_en_passant(move):
            victim_val = 100
        mvv_lva_score = victim_val * 10 - attacker_val
        priority += 50000 + mvv_lva_score + CAPTURE_BONUS
    else:
        if depth > 0 and move in killer_moves.get(depth, []):
            priority += 5000
        move_key = move.uci()
        priority += move_history.get(move_key, 0)

    if board.gives_check(move):
        priority += 10000 + CHECK_BONUS

    return priority

def evaluate_pawn_structure(board: chess.Board) -> int:
    score = 0
    w_pawns = board.pieces(chess.PAWN, chess.WHITE)
    b_pawns = board.pieces(chess.PAWN, chess.BLACK)

    w_counts = [0] * 8
    b_counts = [0] * 8
    for s in w_pawns: w_counts[chess.square_file(s)] += 1
    for s in b_pawns: b_counts[chess.square_file(s)] += 1

    for f in range(8):
        if w_counts[f] > 1: score -= 20
        if w_counts[f] > 0 and (f == 0 or w_counts[f-1] == 0) and (f == 7 or w_counts[f+1] == 0):
            score -= 15
        if b_counts[f] > 1: score += 20
        if b_counts[f] > 0 and (f == 0 or b_counts[f-1] == 0) and (f == 7 or b_counts[f+1] == 0):
            score += 15

    for s in w_pawns:
        f, r = chess.square_file(s), chess.square_rank(s)
        if all(b_counts[chk_f] == 0 or not any(chess.square_rank(bs) > r for bs in b_pawns if chess.square_file(bs) == chk_f) for chk_f in [max(0, f-1), f, min(7, f+1)]):
            score += 30 + r * 10

    for s in b_pawns:
        f, r = chess.square_file(s), chess.square_rank(s)
        if all(w_counts[chk_f] == 0 or not any(chess.square_rank(ws) < r for ws in w_pawns if chess.square_file(ws) == chk_f) for chk_f in [max(0, f-1), f, min(7, f+1)]):
            score -= 30 + (7 - r) * 10

    return score

def evaluate_king_safety(board: chess.Board) -> int:
    score = 0
    wk = board.king(chess.WHITE)
    if wk is not None:
        wk_f, wk_r = chess.square_file(wk), chess.square_rank(wk)
        pawns = sum(1 for s in board.pieces(chess.PAWN, chess.WHITE) if abs(chess.square_file(s)-wk_f) <= 1 and abs(chess.square_rank(s)-wk_r) <= 1)
        if pawns == 0: score -= 30

    bk = board.king(chess.BLACK)
    if bk is not None:
        bk_f, bk_r = chess.square_file(bk), chess.square_rank(bk)
        pawns = sum(1 for s in board.pieces(chess.PAWN, chess.BLACK) if abs(chess.square_file(s)-bk_f) <= 1 and abs(chess.square_rank(s)-bk_r) <= 1)
        if pawns == 0: score += 30
    return score

def evaluate_board(board: chess.Board) -> int:
    score = 0

    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2: score += 30
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2: score -= 30

    for pt, val in PIECE_VALUES.items():
        w_pcs = board.pieces(pt, chess.WHITE)
        b_pcs = board.pieces(pt, chess.BLACK)
        score += len(w_pcs) * val
        score -= len(b_pcs) * val

        pst = PST_TABLES.get(pt)
        if pst:
            for s in w_pcs: score += pst[s]
            for s in b_pcs: score -= pst[(7 - chess.square_rank(s)) * 8 + chess.square_file(s)]

    score += evaluate_pawn_structure(board)
    score += evaluate_king_safety(board)

    if board.turn == chess.WHITE:
        score += len(list(board.legal_moves))
    else:
        score -= len(list(board.legal_moves))

    return score

def quiescence_search(board: chess.Board, alpha: float, beta: float, maximizing: bool, deadline: float) -> int:
    _check_timeout(deadline)
    eval_score = evaluate_board(board)

    if maximizing:
        alpha = max(alpha, eval_score)
        if alpha >= beta: return int(eval_score)
    else:
        beta = min(beta, eval_score)
        if alpha >= beta: return int(eval_score)

    for move in board.legal_moves:
        _check_timeout(deadline)
        if not board.is_capture(move) and not board.gives_check(move):
            continue

        board.push(move)
        try:
            val = quiescence_search(board, alpha, beta, not maximizing, deadline)
        finally:
            board.pop()

        if maximizing:
            alpha = max(alpha, val)
            if alpha >= beta: return int(alpha)
        else:
            beta = min(beta, val)
            if alpha >= beta: return int(beta)

    return int(alpha if maximizing else beta)

def _search(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool, original_depth: int, deadline: float) -> int:
    _check_timeout(deadline)

    if board.is_checkmate():
        if board.turn == chess.WHITE:
            return -(MATE_SCORE - original_depth + depth)
        else:
            return MATE_SCORE - original_depth + depth

    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return 0

    if depth <= 0:
        return quiescence_search(board, alpha, beta, maximizing, deadline)

    orig_alpha, orig_beta = alpha, beta
    tt_key = board._transposition_key()
    tt_entry = tt.get(tt_key)
    pv_move = None

    if tt_entry:
        tt_depth, tt_val, tt_flag, tt_best = tt_entry
        pv_move = tt_best
        if tt_depth >= depth:
            if tt_flag == TT_EXACT: return tt_val
            if tt_flag == TT_LOWER and tt_val >= beta: return tt_val
            if tt_flag == TT_UPPER and tt_val <= alpha: return tt_val

    if depth >= 3 and not board.is_check():
        board.push(chess.Move.null())
        try:
            null_val = _search(board, depth - 1 - 2, alpha, beta, not maximizing, original_depth, deadline)
        finally:
            board.pop()

        if maximizing:
            if null_val >= beta: return int(beta)
        else:
            if null_val <= alpha: return int(alpha)

    legal_moves = sorted(board.legal_moves, key=lambda m: get_move_priority(board, m, depth, pv_move), reverse=True)
    best_move = None

    if maximizing:
        best_value = -math.inf
        for idx, move in enumerate(legal_moves):
            _check_timeout(deadline)
            board.push(move)
            try:
                if depth >= 3 and idx >= 4 and not board.is_capture(move) and not board.gives_check(move):
                    val = _search(board, depth - 2, alpha, alpha + 1, False, original_depth, deadline)
                    if val > alpha:
                        val = _search(board, depth - 1, alpha, beta, False, original_depth, deadline)
                else:
                    val = _search(board, depth - 1, alpha, beta, False, original_depth, deadline)
            finally:
                board.pop()

            if val > best_value:
                best_value = val
                best_move = move
            alpha = max(alpha, val)

            if alpha >= beta:
                if not board.is_capture(move):
                    if move not in killer_moves[depth]:
                        killer_moves[depth].insert(0, move)
                        if len(killer_moves[depth]) > 2:
                            killer_moves[depth].pop()
                break

        tt_flag = TT_EXACT
        if best_value <= orig_alpha: tt_flag = TT_UPPER
        elif best_value >= orig_beta: tt_flag = TT_LOWER
        tt[tt_key] = (depth, best_value, tt_flag, best_move)
        return int(best_value)
    else:
        best_value = math.inf
        for idx, move in enumerate(legal_moves):
            _check_timeout(deadline)
            board.push(move)
            try:
                if depth >= 3 and idx >= 4 and not board.is_capture(move) and not board.gives_check(move):
                    val = _search(board, depth - 2, beta - 1, beta, True, original_depth, deadline)
                    if val < beta:
                        val = _search(board, depth - 1, alpha, beta, True, original_depth, deadline)
                else:
                    val = _search(board, depth - 1, alpha, beta, True, original_depth, deadline)
            finally:
                board.pop()

            if val < best_value:
                best_value = val
                best_move = move
            beta = min(beta, val)

            if alpha >= beta:
                if not board.is_capture(move):
                    if move not in killer_moves[depth]:
                        killer_moves[depth].insert(0, move)
                        if len(killer_moves[depth]) > 2:
                            killer_moves[depth].pop()
                break

        tt_flag = TT_EXACT
        if best_value <= orig_alpha: tt_flag = TT_UPPER
        elif best_value >= orig_beta: tt_flag = TT_LOWER
        tt[tt_key] = (depth, best_value, tt_flag, best_move)
        return int(best_value)

def choose_move_alpha_beta(board: chess.Board, depth: Optional[int] = None, max_depth: int = 4, time_limit: float = 12.0) -> Optional[chess.Move]:
    if depth is not None: max_depth = depth
    time_limit = min(time_limit, MAX_MOVE_TIME_SECONDS)

    if len(tt) > 500000: tt.clear()

    legal_moves = list(board.legal_moves)
    if not legal_moves: return None

    best_move = legal_moves[0]
    start_time = time.perf_counter()
    deadline = start_time + max(0.05, time_limit)

    for current_depth in range(1, max_depth + 1):
        if time.perf_counter() >= deadline: break

        legal_moves = sorted(legal_moves, key=lambda m: get_move_priority(board, m, current_depth, best_move), reverse=True)
        maximizing = board.turn == chess.WHITE
        best_score = -math.inf if maximizing else math.inf
        current_best_move = legal_moves[0]
        depth_completed = True

        try:
            for move in legal_moves:
                _check_timeout(deadline)
                board.push(move)
                try:
                    score = _search(board, current_depth - 1, -math.inf, math.inf, not maximizing, current_depth, deadline)
                finally:
                    board.pop()

                move_key = move.uci()
                if (maximizing and score > best_score) or (not maximizing and score < best_score):
                    move_history[move_key] += 1
                    best_score = score
                    current_best_move = move
        except SearchTimeout:
            depth_completed = False

        if not depth_completed: break
        best_move = current_best_move

    return best_move
