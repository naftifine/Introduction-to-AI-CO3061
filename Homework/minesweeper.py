import tkinter as tk
from tkinter import messagebox
import random


class Minesweeper:
    def __init__(self, root, rows=9, cols=9, mines=10):
        self.root = root
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.buttons = {}
        self.board = []
        self.revealed = []
        self.flagged = []
        self.game_over = False
        self.first_click = True
        
        self.root.title("Minesweeper")
        self.create_menu()
        self.create_board()
        self.create_buttons()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        
        game_menu.add_command(label="New Game", command=self.reset_game)
        game_menu.add_separator()
        game_menu.add_command(label="Easy (9x9, 10 mines)", 
                              command=lambda: self.change_difficulty(9, 9, 10))
        game_menu.add_command(label="Medium (16x16, 40 mines)", 
                              command=lambda: self.change_difficulty(16, 16, 40))
        game_menu.add_command(label="Hard (30x16, 99 mines)", 
                              command=lambda: self.change_difficulty(16, 30, 99))
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit)
    
    def change_difficulty(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.reset_game()
    
    def create_board(self):
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.revealed = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.flagged = [[False for _ in range(self.cols)] for _ in range(self.rows)]
    
    def place_mines(self, first_row, first_col):
        avoid = set()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = first_row + dr, first_col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    avoid.add((nr, nc))
        
        possible_positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in avoid:
                    possible_positions.append((r, c))
        
        actual_mines = min(self.mines, len(possible_positions))
        mine_positions = random.sample(possible_positions, actual_mines)
        for r, c in mine_positions:
            self.board[r][c] = -1
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.board[nr][nc] == -1:
                                count += 1
                self.board[r][c] = count
    
    def create_buttons(self):
        # Only destroy the game frame, not all frames (preserve AI controls)
        if hasattr(self, 'frame') and self.frame:
            self.frame.destroy()
        
        self.frame = tk.Frame(self.root)
        self.frame.pack(side=tk.BOTTOM, padx=10, pady=10)
        
        btn_size = 3 if self.cols <= 9 else 2
        
        for r in range(self.rows):
            for c in range(self.cols):
                btn = tk.Button(
                    self.frame, 
                    width=btn_size, 
                    height=1,
                    font=('Arial', 10, 'bold'),
                    relief=tk.RAISED
                )
                btn.grid(row=r, column=c)
                btn.bind('<Button-1>', lambda e, row=r, col=c: self.left_click(row, col))
                btn.bind('<Button-3>', lambda e, row=r, col=c: self.right_click(row, col))
                self.buttons[(r, c)] = btn
    
    def left_click(self, row, col):
        if self.game_over:
            return
        
        if self.revealed[row][col]:
            self.chord_reveal(row, col)
            return
        
        if self.flagged[row][col]:
            return
        
        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False
        
        if self.board[row][col] == -1:
            self.game_over = True
            self.reveal_all_mines()
            self.buttons[(row, col)].config(bg='red')
            messagebox.showinfo("Game Over", "BOOM! You hit a mine!")
            return
        
        self.dfs_reveal(row, col)
        
        if self.check_win():
            self.game_over = True
            messagebox.showinfo("Congratulations!", "You won! All mines cleared!")
    
    def chord_reveal(self, row, col):
        value = self.board[row][col]
        
        if value <= 0:
            return
        
        flag_count = 0
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.flagged[nr][nc]:
                        flag_count += 1
                    elif not self.revealed[nr][nc]:
                        neighbors.append((nr, nc))
        
        if flag_count == value:
            for nr, nc in neighbors:
                if self.board[nr][nc] == -1:
                    self.game_over = True
                    self.reveal_all_mines()
                    self.buttons[(nr, nc)].config(bg='red')
                    messagebox.showinfo("Game Over", "BOOM! You hit a mine!")
                    return
                else:
                    self.dfs_reveal(nr, nc)
            
            if self.check_win():
                self.game_over = True
                messagebox.showinfo("Congratulations!", "You won! All mines cleared!")
    

    # DFS to reveal all connected zero-value cells and their neighbors
    def dfs_reveal(self, row, col):
        stack = [(row, col)]
        
        while stack:
            r, c = stack.pop()
            
            if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
                continue
            if self.revealed[r][c] or self.flagged[r][c]:
                continue
            if self.board[r][c] == -1:
                continue
            
            self.revealed[r][c] = True
            self.update_button(r, c)
            
            if self.board[r][c] == 0:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                                stack.append((nr, nc))
    
    def update_button(self, row, col):
        btn = self.buttons[(row, col)]
        value = self.board[row][col]
        
        colors = {
            1: 'blue',
            2: 'green',
            3: 'red',
            4: 'darkblue',
            5: 'darkred',
            6: 'cyan',
            7: 'black',
            8: 'gray'
        }
        
        btn.config(relief=tk.SUNKEN, state=tk.DISABLED)
        
        if value == 0:
            btn.config(text='', bg='lightgray')
        else:
            btn.config(text=str(value), fg=colors.get(value, 'black'), bg='lightgray')
    
    def right_click(self, row, col):
        if self.game_over or self.revealed[row][col]:
            return
        
        btn = self.buttons[(row, col)]
        
        if self.flagged[row][col]:
            self.flagged[row][col] = False
            btn.config(text='', bg='SystemButtonFace')
        else:
            self.flagged[row][col] = True
            btn.config(text='🚩', bg='yellow')
    
    def reveal_all_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    btn = self.buttons[(r, c)]
                    if not self.flagged[r][c]:
                        btn.config(text='💣', bg='lightgray', relief=tk.SUNKEN)
    
    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return False
        return True
    
    def reset_game(self):
        self.game_over = False
        self.first_click = True
        self.create_board()
        self.create_buttons()


def main():
    root = tk.Tk()
    root.resizable(False, False)
    game = Minesweeper(root, rows=9, cols=9, mines=10)
    
    # Import and setup AI controls
    from minesweeper_ai import create_ai_controls
    ai, control_frame = create_ai_controls(game)
    
    # Store reference to recreate AI on reset
    original_reset = game.reset_game
    def new_reset():
        original_reset()
        nonlocal ai
        from minesweeper_ai import MinesweeperAI
        ai = MinesweeperAI(game)
    game.reset_game = new_reset
    
    root.mainloop()


if __name__ == "__main__":
    main()
