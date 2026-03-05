import tkinter as tk
from tkinter import messagebox
import random
from itertools import combinations
from collections import defaultdict
import sys


COLORS = {
    # Nền chính & viền giữa các ô
    'bg':            '#3C3F41',
    'header_bg':     '#2B2B2B',
    'control_bg':    '#2B2B2B',

    # Ô lưới
    'cell_hidden':   '#A0A4A8',  
    'cell_hover':    '#B8BCC0', 
    'cell_revealed': '#505458', 
    'cell_empty':    '#505458',

    'cell_flag':     '#E74C3C',
    'cell_mine_hit': '#B03030', 
    'cell_mine':     '#3A3A3A',

    'n1': '#5CB8FF',  
    'n2': '#50C878',  
    'n3': '#FF6B6B',  
    'n4': '#9B59B6',  
    'n5': '#E67E22',  
    'n6': '#1ABC9C',  
    'n7': '#ECF0F1',  
    'n8': '#95A5A6', 

    'text_light':    '#E0E0E0',
    'text_accent':   '#5CB8FF',
    'text_status':   '#50C878',

    # Nút điều khiển 
    'btn_step':      '#5CB8FF', 'btn_step_h':    '#7CC8FF',
    'btn_auto':      '#50C878', 'btn_auto_h':    '#6FD89A',
    'btn_reset':     '#E67E22', 'btn_reset_h':   '#F0953A',
}

NUM_COLORS = {
    1: COLORS['n1'], 2: COLORS['n2'], 3: COLORS['n3'], 4: COLORS['n4'],
    5: COLORS['n5'], 6: COLORS['n6'], 7: COLORS['n7'], 8: COLORS['n8'],
}


class Minesweeper:
    # constructor
    def __init__(self, root, rows=9, cols=9, mines=10):
        self.root = root
        self.rows = rows
        self.cols = cols
        self.mines = mines
        
        self.buttons = {} # giao diện nút bấm
        self.board = [] # dữ liệu logic bàn cờ
        self.revealed = [] # ô đã được mở chưa
        self.flagged = [] # ô có đang bị cắm cờ không
        
        self.game_over = False # Trạng thái game
        self.first_click = True # mìn sẽ được thiết lập sau click đầu tiên
        self.flags_count = 0 # Số cờ đã cắm 
        self.auto_solving = False # Tự động giải
        self.ai = None 

        self.root.title("Minesweeper")
        self.root.configure(bg=COLORS['bg'])
        self.root.resizable(False, False)

        self._build_menu()
        self._build_ui()
        self._create_board()
        self._create_buttons()

    # Tạo thanh menu top
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game Difficulty", menu=game_menu)
        
        game_menu.add_command(label="Easy (5x5, 5 mines)", command=lambda: self._change_diff(5, 5, 5))
        game_menu.add_command(label="Medium (9x9, 10 mines)", command=lambda: self._change_diff(9, 9, 10))
        game_menu.add_command(label="Hard (16x16, 40 mines)", command=lambda: self._change_diff(16, 16, 40))
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit)

    # Tạo bố cục: 3 phần (header, grid, control)
    def _build_ui(self):
        # header: tiêu đề và thông số
        hdr = tk.Frame(self.root, bg=COLORS['header_bg'], pady=15)
        hdr.pack(fill=tk.X)

        tk.Label(hdr, text="MINESWEEPER", font=('Segoe UI Black', 22, 'bold'),
                 fg=COLORS['text_accent'], bg=COLORS['header_bg']).pack()

        info = tk.Frame(hdr, bg=COLORS['header_bg'])
        info.pack(pady=(10, 0))

        self.mines_label = tk.Label( # hiển thị số mìn còn lại
            info, text=f"💣 {self.mines}",
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['text_light'], bg=COLORS['header_bg']
        )
        self.mines_label.pack(side=tk.LEFT, padx=20)

        self.status_label = tk.Label( # trạng thái game hiện tại
            info, text="Ready",
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['text_status'], bg=COLORS['header_bg']
        )
        self.status_label.pack(side=tk.LEFT, padx=20)

        self.size_label = tk.Label( # kích thước bàn cờ
            info, text=f"📐 {self.rows}x{self.cols}",
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['text_light'], bg=COLORS['header_bg']
        )
        self.size_label.pack(side=tk.LEFT, padx=20)

        # grid: khung chứa các ô
        self.grid_frame = tk.Frame(self.root, bg=COLORS['bg'], padx=15, pady=15)
        self.grid_frame.pack()

        # control: container cho các nút bấm AI (Sẽ được nhúng từ create_ai_controls)
        ctrl = tk.Frame(self.root, bg=COLORS['control_bg'], pady=15)
        ctrl.pack(fill=tk.X)

        row1 = tk.Frame(ctrl, bg=COLORS['control_bg'])
        row1.pack()

        self.btn_step = self._btn(row1, "AI Step", COLORS['btn_step'], COLORS['btn_step_h'], None)
        self.btn_step.pack(side=tk.LEFT, padx=5)
        
        self.btn_auto = self._btn(row1, "Auto Solve", COLORS['btn_auto'], COLORS['btn_auto_h'], None)
        self.btn_auto.pack(side=tk.LEFT, padx=5)
        
        self.btn_reset = self._btn(row1, "Reset", COLORS['btn_reset'], COLORS['btn_reset_h'], None)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

    # Cấu hình các nút điều khiển
    def _btn(self, parent, text, bg, hover, cmd):
        b = tk.Button(parent, text=text, font=('Helvetica', 11, 'bold'),
                      fg='#1A1A1A', bg=bg, activebackground=hover,
                      activeforeground='#1A1A1A', relief=tk.RAISED,
                      padx=16, pady=6, cursor='hand2', bd=2)
        b.config(command=cmd)
        b.bind('<Enter>', lambda e, w=b, c=hover: w.config(bg=c) if w['state'] != 'disabled' else None)
        b.bind('<Leave>', lambda e, w=b, c=bg: w.config(bg=c) if w['state'] != 'disabled' else None)
        return b

    # Khởi tạo dữ liệu bảng
    def _create_board(self):
        self.board = [[0]*self.cols for _ in range(self.rows)] # khởi tạo giá trị 0 cho toàn bộ ô
        self.revealed = [[False]*self.cols for _ in range(self.rows)] # chưa ô nào được mở
        self.flagged = [[False]*self.cols for _ in range(self.rows)] # chưa ô nào bị cắm cờ
        self.flags_count = 0 # số cờ đếm được = 0

    # Đặt mìn (sau khi click ô đầu tiên)
    def _place_mines(self, fr, fc): # fr, fc là tọa độ ô đầu tiên được click
        avoid = set()
        for dr in range(-1, 2): # duyệt 3x3 quanh ô đầu tiên vừa click
            for dc in range(-1, 2):
                nr, nc = fr + dr, fc + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    avoid.add((nr, nc)) # lưu các ô xung quanh (bao gồm cả ô đầu tiên) vào set avoid

        candidates = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in avoid] # tạo danh sách các ô có thể đặt mìn (không nằm trong tập avoid)
        # chọn ngẫu nhiên vị trí đặt mìn
        # dùng random.sample thay vì random.randint để tránh chọn trùng vị trí
        for r, c in random.sample(candidates, min(self.mines, len(candidates))): 
            self.board[r][c] = -1

        # đuyệt lại toàn bộ bàn cờ để tính số mìn xung quanh mỗi ô
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1: continue # nếu là mìn thì bỏ qua

                count = 0  # Biến đếm số mìn xung quanh
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        # Bỏ qua ô trung tâm (khi độ lệch = 0)
                        if dr == 0 and dc == 0:
                            continue
                            
                        # Tính tọa độ hàng xóm
                        hang_xom_r = r + dr
                        hang_xom_c = c + dc
                        
                        # Kiểm tra xem hàng xóm có nằm trong bàn cờ không
                        if 0 <= hang_xom_r < self.rows and 0 <= hang_xom_c < self.cols:
                            
                            # Nếu hàng xóm là mìn (-1)
                            if self.board[hang_xom_r][hang_xom_c] == -1:
                                count = count + 1  # Cộng thêm 1 vào tổng

                self.board[r][c] = count


    # Tạo lưới ô
    def _create_buttons(self):
        # Lấy container grid chính
        self.frame = self.grid_frame
        
        # Xóa lưới cũ (reset)
        for w in self.frame.winfo_children():
            w.destroy()
        self.buttons.clear()

        pad = (12, 6) if self.cols <= 9 else (8, 4)
        fs = 15 if self.cols <= 9 else 11

        for r in range(self.rows):
            for c in range(self.cols):
                # Các ô ban đầu đều có màu xám sáng, viền nổi (chưa mở)
                lbl = tk.Label(self.grid_frame, text='',
                               font=('Helvetica', fs, 'bold'),
                               bg=COLORS['cell_hidden'], fg='#2D3436',
                               relief=tk.RAISED, bd=3,
                               width=2, anchor='center',
                               padx=pad[0], pady=pad[1],
                               cursor='hand2')
                lbl.grid(row=r, column=c, padx=1, pady=1)

                lbl.bind('<Button-1>', lambda e, rr=r, cc=c: self.left_click(rr, cc))
                lbl.bind('<Button-2>', lambda e, rr=r, cc=c: self.right_click(rr, cc))
                lbl.bind('<Button-3>', lambda e, rr=r, cc=c: self.right_click(rr, cc))
                self.buttons[(r, c)] = lbl


    # Xử lý click chuột trái
    def left_click(self, row, col):
        # nếu game đã kết thúc hoặc ô đang bị cắm cờ -> không làm gì cả
        if self.game_over or self.flagged[row][col]: return

        # nếu ô đã được mở -> thực hiện chord
        if self.revealed[row][col]:
            self._chord(row, col)
            return

        # nếu là lần click đầu tiên -> đặt mìn
        if self.first_click:
            self._place_mines(row, col)
            self.first_click = False

        # nếu click vào mìn -> game over
        if self.board[row][col] == -1:
            self.game_over = True
            self.auto_solving = False
            self._show_mines()  
            self.buttons[(row, col)].config(text='💣', bg=COLORS['cell_mine_hit'],
                                             fg='white', relief=tk.FLAT, bd=1)
            self.status_label.config(text="BOOM!", fg=COLORS['cell_flag'])
            messagebox.showinfo("Game Over", "BOOM! You hit a mine!")
            return

        self.dfs_reveal(row, col)
        if self._check_win(): self._trigger_win()

    # Xử lý click chuột phải (cắm/gỡ cờ)
    def right_click(self, row, col):
        # nếu game đã kết thúc hoặc ô đã được mở -> không làm gì cả
        if self.game_over or self.revealed[row][col]: return
        b = self.buttons[(row, col)]
        
        if self.flagged[row][col]:
            self.flagged[row][col] = False
            self.flags_count -= 1
            b.config(text='', bg=COLORS['cell_hidden'], relief=tk.RAISED, bd=3)
        else:
            self.flagged[row][col] = True
            self.flags_count += 1
            b.config(text='🚩', fg=COLORS['cell_flag'], bg=COLORS['cell_hidden'],
                     relief=tk.RAISED, bd=3)
            
        self.mines_label.config(text=f"💣 {self.mines - self.flags_count}")

    # Thuật toán DFS 
    def dfs_reveal(self, row, col):
        stack = [(row, col)]
        in_stack = {(row, col)}

        while stack:
            r, c = stack.pop() # lấy ô cuối cùng trong stack (LIFO)
            
            if self.revealed[r][c] or self.flagged[r][c] or self.board[r][c] == -1:
                continue

            self.revealed[r][c] = True
            self._update_cell(r, c)

            if self.board[r][c] == 0:
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if dr == 0 and dc == 0: continue

                        # nr: neighbor row, nc: neighbor col
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            # những ô chưa mở và chưa cắm cờ
                            if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                                if (nr, nc) not in in_stack:
                                    stack.append((nr, nc))
                                    in_stack.add((nr, nc))

    # mở chùm
    # nếu số cờ xung quanh bằng số hiển thị trên ô -> mở tất cả ô xung quanh
    # nếu cắm cờ sai -> mở nhầm ô mìn -> game over
    def _chord(self, row, col):
        val = self.board[row][col]
        if val <= 0: return
        
        flags, nbrs = 0, []
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0: continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.flagged[nr][nc]: flags += 1 # nếu có cắm cờ -> +1 vào biến flags
                    elif not self.revealed[nr][nc]: nbrs.append((nr, nc)) # thêm vào danh sách các ô cần mở
                        
        if flags == val:
            for nr, nc in nbrs:
                if self.board[nr][nc] == -1:
                    self.game_over = True
                    self.auto_solving = False
                    self._show_mines()  

                    self.buttons[(nr, nc)].config(text='💣', bg=COLORS['cell_mine_hit'],
                                                   fg='white', relief=tk.FLAT, bd=1)
                    self.status_label.config(text="BOOM!", fg=COLORS['cell_flag'])
                    messagebox.showinfo("Game Over", "BOOM! You hit a mine!")
                    return

                self.dfs_reveal(nr, nc)
    def chord_reveal(self, row, col):
        self._chord(row, col)

    def _trigger_win(self):
        self.game_over = True
        self.auto_solving = False
        self.status_label.config(text="YOU WIN!", fg=COLORS['text_status'])
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1 and not self.flagged[r][c]:
                    self.buttons[(r, c)].config(text='🚩', fg=COLORS['cell_flag'],
                                                bg=COLORS['cell_hidden'])
        self.mines_label.config(text="💣 0")
        messagebox.showinfo("Congratulations!", "You won! All mines cleared!")

    def _update_cell(self, r, c):
        b = self.buttons[(r, c)]
        v = self.board[r][c]

        b.config(relief=tk.FLAT, bd=1, bg=COLORS['cell_revealed'], cursor='arrow')
        if v == 0:
            b.config(text='', bg=COLORS['cell_empty'])
        else:
            b.config(text=str(v), fg=NUM_COLORS.get(v, 'white'))

    def _show_mines(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1 and not self.flagged[r][c]:
                    self.buttons[(r, c)].config(text='💣', bg=COLORS['cell_mine'],
                                                fg='white', relief=tk.FLAT, bd=1)
                elif self.flagged[r][c] and self.board[r][c] != -1:
                    self.buttons[(r, c)].config(text='❌', bg=COLORS['cell_revealed'], fg='red')
                    
    def reveal_all_mines(self):
        self._show_mines()

    def check_win(self):
        return self._check_win()

    def reset_game(self):
        self._on_reset()

    def _check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return False
        return True

    def get_neighbors(self, row, col):
        return [(row+dr, col+dc) for dr in range(-1, 2) for dc in range(-1, 2)
                if (dr != 0 or dc != 0) and 0 <= row+dr < self.rows and 0 <= col+dc < self.cols]

    def _change_diff(self, rows, cols, mines):
        self.rows, self.cols, self.mines = rows, cols, mines
        self._on_reset()

    def _on_reset(self):
        self.game_over = False
        self.auto_solving = False
        self.first_click = True
        
        self._create_board()
        self._create_buttons()
        self.status_label.config(text="Ready", fg=COLORS['text_status'])
        self.size_label.config(text=f"📐 {self.rows}x{self.cols}")
        self.mines_label.config(text=f"💣 {self.mines}")
def main():
    root = tk.Tk()
    root.resizable(False, False)
    game = Minesweeper(root, rows=9, cols=9, mines=10)
    
    # Import and setup friend's AI controls
    from minesweeper_ai import create_ai_controls
    ai = create_ai_controls(game)
    
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
