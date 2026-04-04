import random
import sys
import time
from pathlib import Path

import pygame
import chess

from ai_alphabeta import choose_move_alpha_beta
from ai_mcts import choose_move_mcts


BOARD_SIZE = 8
SQUARE_SIZE = 96
PIECE_SCALE = 0.8
PIECE_SIZE = int(SQUARE_SIZE * PIECE_SCALE)
PANEL_WIDTH = 260
WINDOW_WIDTH = BOARD_SIZE * SQUARE_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = BOARD_SIZE * SQUARE_SIZE
FPS = 60

ASSET_DIR = Path(__file__).parent / "assets"

PIECE_ASSET_MAP = {
    "P": "pawn_white.png",
    "N": "knight_white.png",
    "B": "bishop_white.png",
    "R": "rook_white.png",
    "Q": "queen_white.png",
    "K": "king_white.png",
    "p": "pawn_black.png",
    "n": "knight_black.png",
    "b": "bishop_black.png",
    "r": "rook_black.png",
    "q": "queen_black.png",
    "k": "king_black.png",
}


def load_scaled_image(path: Path, size: tuple[int, int]) -> pygame.Surface:
    image = pygame.image.load(path.as_posix()).convert_alpha()
    return pygame.transform.smoothscale(image, size)


def load_assets() -> dict[str, pygame.Surface]:
    assets: dict[str, pygame.Surface] = {}
    assets["white_square"] = load_scaled_image(ASSET_DIR / "white_square.png", (SQUARE_SIZE, SQUARE_SIZE))
    assets["black_square"] = load_scaled_image(ASSET_DIR / "black_square.png", (SQUARE_SIZE, SQUARE_SIZE))
    assets["dot"] = load_scaled_image(ASSET_DIR / "dot.png", (30, 30))

    for symbol, filename in PIECE_ASSET_MAP.items():
        assets[symbol] = load_scaled_image(ASSET_DIR / filename, (PIECE_SIZE, PIECE_SIZE))
    return assets


def square_to_pixel(square: chess.Square) -> tuple[int, int]:
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)
    x = file_index * SQUARE_SIZE
    y = (7 - rank_index) * SQUARE_SIZE
    return x, y


def pixel_to_square(pos: tuple[int, int]) -> chess.Square | None:
    x, y = pos
    if not (0 <= x < BOARD_SIZE * SQUARE_SIZE and 0 <= y < BOARD_SIZE * SQUARE_SIZE):
        return None
    file_index = x // SQUARE_SIZE
    rank_index = 7 - (y // SQUARE_SIZE)
    return chess.square(file_index, rank_index)


def draw_board(screen: pygame.Surface, board: chess.Board, assets: dict[str, pygame.Surface], selected: chess.Square | None, legal_targets: set[chess.Square], font: pygame.font.Font, bot_name: str) -> None:
    for rank in range(BOARD_SIZE):
        for file in range(BOARD_SIZE):
            is_light = (rank + file) % 2 == 0
            square_img = assets["white_square"] if is_light else assets["black_square"]
            x = file * SQUARE_SIZE
            y = rank * SQUARE_SIZE
            screen.blit(square_img, (x, y))

    if selected is not None:
        sx, sy = square_to_pixel(selected)
        overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        overlay.fill((255, 235, 59, 120))
        screen.blit(overlay, (sx, sy))

    for target in legal_targets:
        tx, ty = square_to_pixel(target)
        dot_rect = assets["dot"].get_rect(center=(tx + SQUARE_SIZE // 2, ty + SQUARE_SIZE // 2))
        screen.blit(assets["dot"], dot_rect)

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        px, py = square_to_pixel(square)
        piece_rect = assets[piece.symbol()].get_rect(center=(px + SQUARE_SIZE // 2, py + SQUARE_SIZE // 2))
        screen.blit(assets[piece.symbol()], piece_rect)

    panel_x = BOARD_SIZE * SQUARE_SIZE
    pygame.draw.rect(screen, (31, 33, 43), (panel_x, 0, PANEL_WIDTH, WINDOW_HEIGHT))

    turn_text = "White" if board.turn == chess.WHITE else "Black"
    status = f"Turn: {turn_text}"

    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        status = f"Checkmate: {winner} win"
    elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        status = "Draw"
    elif board.is_check():
        status = f"{turn_text} in check"

    lines = [
        f"Bot: {bot_name}",
        "You play: White",
        status,
        "",
        "Click your piece",
        "to see legal moves.",
    ]

    y = 30
    for line in lines:
        text_surface = font.render(line, True, (241, 243, 248))
        screen.blit(text_surface, (panel_x + 16, y))
        y += 34


def draw_menu(screen: pygame.Surface, font_title: pygame.font.Font, font_btn: pygame.font.Font) -> tuple[pygame.Rect, pygame.Rect]:
    screen.fill((18, 22, 31))

    title = font_title.render("CHESS BOT", True, (245, 245, 245))
    sub = font_btn.render("Chon thuat toan cho bot", True, (196, 204, 219))

    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 130)))
    screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 190)))

    btn_w, btn_h = 340, 70
    alpha_btn = pygame.Rect(0, 0, btn_w, btn_h)
    mcts_btn = pygame.Rect(0, 0, btn_w, btn_h)
    alpha_btn.center = (WINDOW_WIDTH // 2, 300)
    mcts_btn.center = (WINDOW_WIDTH // 2, 400)

    pygame.draw.rect(screen, (56, 99, 214), alpha_btn, border_radius=12)
    pygame.draw.rect(screen, (59, 155, 104), mcts_btn, border_radius=12)

    alpha_text = font_btn.render("Alpha-Beta", True, (255, 255, 255))
    mcts_text = font_btn.render("MCTS", True, (255, 255, 255))

    screen.blit(alpha_text, alpha_text.get_rect(center=alpha_btn.center))
    screen.blit(mcts_text, mcts_text.get_rect(center=mcts_btn.center))

    return alpha_btn, mcts_btn


def choose_menu_option(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    font_title = pygame.font.SysFont("cambria", 66, bold=True)
    font_btn = pygame.font.SysFont("cambria", 36, bold=True)

    while True:
        alpha_btn, mcts_btn = draw_menu(screen, font_title, font_btn)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if alpha_btn.collidepoint(event.pos):
                    return "alpha-beta"
                if mcts_btn.collidepoint(event.pos):
                    return "mcts"

        pygame.display.flip()
        clock.tick(FPS)


def get_move_for_bot(board: chess.Board, bot_name: str) -> chess.Move | None:
    if bot_name == "alpha-beta":
        start = time.perf_counter()
        move = choose_move_alpha_beta(board, depth=4, time_limit=12.0)
        elapsed = time.perf_counter() - start
        print(f"[AlphaBeta d=4] best_move={move} time={elapsed:.2f}s")
        return move

    # Placeholder: MCTS not implemented yet.
    if bot_name == "mcts":
        start = time.perf_counter()
        move = choose_move_mcts(board, time_limit=5.0, max_iterations=10_000)
        elapsed = time.perf_counter() - start
        print(f"[MCTS] best_move={move} time={elapsed:.2f}s")
        return move
    


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Chess with Bot")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    assets = load_assets()
    ui_font = pygame.font.SysFont("cambria", 30)

    bot_name = choose_menu_option(screen, clock)

    board = chess.Board()
    selected_square: chess.Square | None = None
    legal_targets: set[chess.Square] = set()
    human_side = chess.WHITE

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if board.is_game_over() or board.turn != human_side:
                    continue

                clicked = pixel_to_square(event.pos)
                if clicked is None:
                    continue

                piece = board.piece_at(clicked)

                if selected_square is None:
                    if piece and piece.color == human_side:
                        selected_square = clicked
                        legal_targets = {
                            move.to_square
                            for move in board.legal_moves
                            if move.from_square == selected_square
                        }
                    continue

                chosen_move = None
                for move in board.legal_moves:
                    if move.from_square == selected_square and move.to_square == clicked:
                        if move.promotion:
                            chosen_move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
                        else:
                            chosen_move = move
                        break

                if chosen_move is not None:
                    board.push(chosen_move)

                if piece and piece.color == human_side:
                    selected_square = clicked
                    legal_targets = {
                        move.to_square
                        for move in board.legal_moves
                        if move.from_square == selected_square
                    }
                else:
                    selected_square = None
                    legal_targets.clear()

        if not board.is_game_over() and board.turn != human_side:
            bot_move = get_move_for_bot(board, bot_name)
            if bot_move is not None and board.is_legal(bot_move):
                board.push(bot_move)
            elif bot_move is not None:
                print(f"[WARN] Bot returned illegal move: {bot_move}. Skipping move.")
            selected_square = None
            legal_targets.clear()

        draw_board(screen, board, assets, selected_square, legal_targets, ui_font, bot_name)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
