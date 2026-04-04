import math
import time

import chess
from ai_alphabeta import evaluate_board, PIECE_VALUES


CPUCT         = 1.5
TOP_K         = 20
EVAL_SCALE    = 2000.0
ROLLOUT_DEPTH = 4


def _see_ok(board: chess.Board, move: chess.Move) -> bool:
    if not board.is_capture(move):
        return True
    victim = board.piece_at(move.to_square)
    aggr   = board.piece_at(move.from_square)
    if victim is None or aggr is None:
        return True
    v_val = PIECE_VALUES.get(victim.piece_type, 0)
    a_val = PIECE_VALUES.get(aggr.piece_type, 0)
    if v_val >= a_val:
        return True
    board2 = board.copy()
    board2.push(move)
    return not board2.is_attacked_by(board2.turn, move.to_square)


_CENTER_BONUS = [0] * 64
for _sq in range(64):
    _f = chess.square_file(_sq)
    _r = chess.square_rank(_sq)
    _center_f = min(abs(_f - 3), abs(_f - 4))
    _center_r = min(abs(_r - 3), abs(_r - 4))
    _CENTER_BONUS[_sq] = max(0, 3 - _center_f) * 5 + max(0, 3 - _center_r) * 5

def _prior(board: chess.Board, move: chess.Move) -> float:
    score = 0.0

    if move.promotion:
        score += 900.0
        return score

    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        aggr   = board.piece_at(move.from_square)
        v_val  = PIECE_VALUES.get(victim.piece_type, 100) if victim else 100
        a_val  = PIECE_VALUES.get(aggr.piece_type,   100) if aggr   else 100
        if _see_ok(board, move):
            score += 200.0 + v_val - a_val * 0.1
        else:
            score -= 300.0
        return score

    if board.gives_check(move):
        score += 100.0

    score += _CENTER_BONUS[move.to_square]

    piece = board.piece_at(move.from_square)
    if piece:
        board2 = board.copy()
        board2.push(move)
        if board2.is_attacked_by(board2.turn, move.to_square):
            a_val = PIECE_VALUES.get(piece.piece_type, 0)
            score -= a_val * 0.3   

    return score


def _fast_move(board: chess.Board) -> chess.Move:
    """Chọn nước nhanh cho rollout (không gọi evaluate_board)."""
    moves = list(board.legal_moves)
    best_m = moves[0]
    best_s = -99999.0
    for m in moves:
        s = _prior(board, m)
        if s > best_s:
            best_s = s
            best_m = m
    return best_m


def _rollout(start: chess.Board) -> chess.Board:
    b = start.copy()
    for _ in range(ROLLOUT_DEPTH):
        if b.is_game_over():
            break
        b.push(_fast_move(b))
    return b


class MCTSNode:
    __slots__ = ("board_state", "move", "parent", "children",
                 "untried_moves", "prior_scores", "wins", "visits")

    def __init__(self, board: chess.Board,
                 move: chess.Move | None = None,
                 parent: "MCTSNode | None" = None) -> None:
        self.board_state = board.copy()
        self.move        = move
        self.parent      = parent
        self.children: list["MCTSNode"] = []
        self.wins   = 0.0
        self.visits = 0

        moves  = list(board.legal_moves)
        scored = sorted(moves, key=lambda m: _prior(board, m), reverse=True)[:TOP_K]
        self.untried_moves = list(scored)

        raw   = [max(0.01, _prior(board, m) + 400) for m in scored]
        total = sum(raw) or 1.0
        self.prior_scores: dict[chess.Move, float] = {
            m: r / total for m, r in zip(scored, raw)
        }

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def is_terminal(self) -> bool:
        return self.board_state.is_game_over()

    def puct(self, parent_visits: int) -> float:
        q = self.wins / self.visits if self.visits else 0.0
        p = self.parent.prior_scores.get(self.move, 0.01) if self.parent else 0.01
        u = CPUCT * p * math.sqrt(parent_visits) / (1 + self.visits)
        return q + u

    def best_child(self) -> "MCTSNode":
        return max(self.children, key=lambda c: c.puct(self.visits))

    def most_visited_child(self) -> "MCTSNode":
        return max(self.children, key=lambda c: c.visits)


def _select(node: MCTSNode) -> MCTSNode:
    while not node.is_terminal():
        if not node.is_fully_expanded():
            return node
        node = node.best_child()
    return node


def _expand(node: MCTSNode) -> MCTSNode:
    move      = node.untried_moves.pop(0)
    new_board = node.board_state.copy()
    new_board.push(move)
    child = MCTSNode(new_board, move=move, parent=node)
    node.children.append(child)
    return child


def _simulate(node: MCTSNode, root_color: chess.Color) -> float:
    board = node.board_state

    if board.is_game_over():
        return _terminal_reward(board, root_color)

    after = _rollout(board)

    if after.is_game_over():
        return _terminal_reward(after, root_color)

    raw        = float(evaluate_board(after))
    clamped    = max(-EVAL_SCALE, min(EVAL_SCALE, raw))
    normalized = clamped / EVAL_SCALE
    return normalized if root_color == chess.WHITE else -normalized


def _terminal_reward(board: chess.Board, root_color: chess.Color) -> float:
    result = board.result()
    if result == "1-0":
        return  1.0 if root_color == chess.WHITE else -1.0
    if result == "0-1":
        return  1.0 if root_color == chess.BLACK else -1.0
    return 0.0


def _backpropagate(node: MCTSNode, reward: float) -> None:
    cur: MCTSNode | None = node
    while cur is not None:
        cur.visits += 1
        cur.wins   += reward
        reward      = -reward
        cur         = cur.parent


def choose_move_mcts(
    board: chess.Board,
    time_limit: float   = 5.0,
    max_iterations: int = 10_000,
) -> chess.Move | None:
    legal = list(board.legal_moves)
    if not legal:
        return None
    if len(legal) == 1:
        return legal[0]

    root_color = board.turn
    root       = MCTSNode(board)
    deadline   = time.perf_counter() + time_limit
    iterations = 0

    while iterations < max_iterations and time.perf_counter() < deadline:
        leaf = _select(root)
        if not leaf.is_terminal() and not leaf.is_fully_expanded():
            leaf = _expand(leaf)
        reward = _simulate(leaf, root_color)
        _backpropagate(leaf, reward)
        iterations += 1

    if not root.children:
        return max(legal, key=lambda m: _prior(board, m))

    best = root.most_visited_child()
    print(
        f"[MCTS] iter={iterations}  best={best.move}  "
        f"visits={best.visits}  Q={best.wins/best.visits:+.3f}"
    )
    return best.move