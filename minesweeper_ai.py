from itertools import combinations
from collections import defaultdict
import tkinter as tk

class MinesweeperAI:
    def __init__(self, game):
        self.game = game
        self.known_mines = set()
        self.known_safe = set()
        self.chord_cells = set()
        self.constraints = []
        
    def get_neighbors(self, row, col):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.game.rows and 0 <= nc < self.game.cols:
                    neighbors.append((nr, nc))
        return neighbors
    
    def get_unrevealed_neighbors(self, row, col):
        unrevealed = []
        for nr, nc in self.get_neighbors(row, col):
            if not self.game.revealed[nr][nc] and not self.game.flagged[nr][nc]:
                unrevealed.append((nr, nc))
        return unrevealed
    
    def get_flagged_neighbors(self, row, col):
        flagged = []
        for nr, nc in self.get_neighbors(row, col):
            if self.game.flagged[nr][nc]:
                flagged.append((nr, nc))
        return flagged
    
    def get_revealed_numbered_cells(self):
        cells = []
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if self.game.revealed[r][c] and self.game.board[r][c] > 0:
                    cells.append((r, c))
        return cells
    
    def get_all_unrevealed(self):
        cells = []
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                    cells.append((r, c))
        return cells
    
    def get_frontier(self):
        frontier = set()
        for r, c in self.get_revealed_numbered_cells():
            for nr, nc in self.get_unrevealed_neighbors(r, c):
                frontier.add((nr, nc))
        return frontier
    
    def effective_count(self, row, col):
        if not self.game.revealed[row][col]:
            return -1
        total_mines = self.game.board[row][col]
        flagged = len(self.get_flagged_neighbors(row, col))
        return total_mines - flagged
    
    # ==================== PATTERN 1: BASIC ====================
    def pattern_basic(self):
        mines_found = set()
        safe_found = set()
        chord_found = set()
        
        for r, c in self.get_revealed_numbered_cells():
            unrevealed = self.get_unrevealed_neighbors(r, c)
            effective = self.effective_count(r, c)
            
            if len(unrevealed) == 0:
                continue
            
            if effective == len(unrevealed):
                mines_found.update(unrevealed)
            elif effective == 0:
                safe_found.update(unrevealed)
                chord_found.add((r, c))
        
        return mines_found, safe_found, chord_found
    
    # ==================== PATTERN 2: 1-2-X ====================
    def pattern_1_2_x(self):
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        for r1, c1 in numbered_cells:
            eff1 = self.effective_count(r1, c1)
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            
            if eff1 != 1 or len(set1) < 2:
                continue
            
            for r2, c2 in self.get_neighbors(r1, c1):
                if not self.game.revealed[r2][c2]:
                    continue
                
                eff2 = self.effective_count(r2, c2)
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                
                if eff2 != 2 or len(set2) < 2:
                    continue
                
                overlap = set1 & set2
                if len(overlap) >= 2:
                    diff = set2 - set1
                    if len(diff) == 1:
                        mines_found.update(diff)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 3: 1-1-X ====================
    def pattern_1_1_x(self):
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        for r1, c1 in numbered_cells:
            eff1 = self.effective_count(r1, c1)
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            
            if eff1 != 1 or len(set1) < 1:
                continue
            
            for r2, c2 in self.get_neighbors(r1, c1):
                if not self.game.revealed[r2][c2]:
                    continue
                
                eff2 = self.effective_count(r2, c2)
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                
                if eff2 != 1:
                    continue
                
                if set1 < set2:
                    diff = set2 - set1
                    safe_found.update(diff)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 4: REDUCTION ====================
    def pattern_reduction(self):
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        for i, (r1, c1) in enumerate(numbered_cells):
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            eff1 = self.effective_count(r1, c1)
            
            if len(set1) == 0 or eff1 < 0:
                continue
            
            for r2, c2 in numbered_cells[i+1:]:
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                eff2 = self.effective_count(r2, c2)
                
                if len(set2) == 0 or eff2 < 0:
                    continue
                
                if not set1 & set2:
                    continue
                
                if set1 <= set2:
                    diff = set2 - set1
                    diff_mines = eff2 - eff1
                    
                    if diff_mines < 0:
                        continue
                    if diff_mines == len(diff):
                        mines_found.update(diff)
                    elif diff_mines == 0:
                        safe_found.update(diff)
                
                elif set2 <= set1:
                    diff = set1 - set2
                    diff_mines = eff1 - eff2
                    
                    if diff_mines < 0:
                        continue
                    if diff_mines == len(diff):
                        mines_found.update(diff)
                    elif diff_mines == 0:
                        safe_found.update(diff)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 5: ADVANCED LOGIC ====================
    def pattern_advanced_logic(self):
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        for r1, c1 in numbered_cells:
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            eff1 = self.effective_count(r1, c1)
            
            if len(set1) == 0 or eff1 <= 0:
                continue
            
            for r2, c2 in numbered_cells:
                if (r1, c1) == (r2, c2):
                    continue
                
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                eff2 = self.effective_count(r2, c2)
                
                if len(set2) == 0:
                    continue
                
                overlap = set1 & set2
                if not overlap:
                    continue
                
                only1 = set1 - set2
                only2 = set2 - set1
                
                if eff2 <= len(overlap) and len(only2) > 0:
                    remaining_for_1 = eff1 - eff2
                    if remaining_for_1 >= 0 and remaining_for_1 <= len(only1):
                        if eff2 == len(overlap):
                            if remaining_for_1 == len(only1):
                                mines_found.update(only1)
                            elif remaining_for_1 == 0:
                                safe_found.update(only1)
                
                min_in_overlap = max(0, eff1 - len(only1), eff2 - len(only2))
                max_in_overlap = min(len(overlap), eff1, eff2)
                
                if min_in_overlap > max_in_overlap:
                    continue
                
                if min_in_overlap == max_in_overlap:
                    mines_in_overlap = min_in_overlap
                    
                    mines_in_only1 = eff1 - mines_in_overlap
                    if mines_in_only1 == len(only1) and only1:
                        mines_found.update(only1)
                    elif mines_in_only1 == 0 and only1:
                        safe_found.update(only1)
                    
                    mines_in_only2 = eff2 - mines_in_overlap
                    if mines_in_only2 == len(only2) and only2:
                        mines_found.update(only2)
                    elif mines_in_only2 == 0 and only2:
                        safe_found.update(only2)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 6: CSP ====================
    def pattern_high_complex(self):
        mines_found = set()
        safe_found = set()
        
        constraints = []
        frontier = self.get_frontier()
        
        if not frontier:
            return mines_found, safe_found
        
        for r, c in self.get_revealed_numbered_cells():
            unrevealed = tuple(self.get_unrevealed_neighbors(r, c))
            if unrevealed:
                eff = self.effective_count(r, c)
                constraints.append((unrevealed, eff))
        
        if not constraints:
            return mines_found, safe_found
        
        frontier_list = list(frontier)
        
        cell_constraints = defaultdict(list)
        for cells, count in constraints:
            for cell in cells:
                cell_constraints[cell].append((cells, count))
        
        for cell in frontier_list:
            can_be_mine = False
            can_be_safe = False
            
            relevant_constraints = cell_constraints[cell]
            if not relevant_constraints:
                continue
            
            involved_cells = set()
            for cells, _ in relevant_constraints:
                involved_cells.update(cells)
            
            involved_list = list(involved_cells)
            
            if len(involved_list) > 20:
                continue
            
            if self._check_assignment_possible(involved_list, constraints, cell, True):
                can_be_mine = True
            
            if self._check_assignment_possible(involved_list, constraints, cell, False):
                can_be_safe = True
            
            if can_be_mine and not can_be_safe:
                mines_found.add(cell)
            elif can_be_safe and not can_be_mine:
                safe_found.add(cell)
        
        return mines_found, safe_found
    
    def _check_assignment_possible(self, cells, constraints, target_cell, is_mine):
        relevant_constraints = []
        for cell_tuple, count in constraints:
            if target_cell in cell_tuple:
                relevant_constraints.append((cell_tuple, count))
        
        cells_to_try = set()
        for cell_tuple, _ in relevant_constraints:
            cells_to_try.update(cell_tuple)
        cells_to_try.discard(target_cell)
        cells_list = list(cells_to_try)
        
        if len(cells_list) > 15:
            return True
        
        for num_mines in range(len(cells_list) + 1):
            for mine_combo in combinations(cells_list, num_mines):
                mine_set = set(mine_combo)
                if is_mine:
                    mine_set.add(target_cell)
                
                valid = True
                for cell_tuple, count in relevant_constraints:
                    mines_in_constraint = sum(1 for c in cell_tuple if c in mine_set)
                    if mines_in_constraint != count:
                        valid = False
                        break
                
                if valid:
                    return True
        
        return False
    
    # ==================== PATTERN 7: LAST TURN ====================
    def pattern_last_turn(self):
        """
        Logic: remaining_mines == unrevealed → all mines
               remaining_mines == 0 → all safe
        """
        mines_found = set()
        safe_found = set()
        
        total_flags = sum(
            1 for r in range(self.game.rows) 
            for c in range(self.game.cols) 
            if self.game.flagged[r][c]
        )
        
        remaining_mines = self.game.mines - total_flags
        unrevealed = self.get_all_unrevealed()
        
        if remaining_mines == 0:
            safe_found.update(unrevealed)
        elif remaining_mines == len(unrevealed):
            mines_found.update(unrevealed)
        
        return mines_found, safe_found
    
    # ==================== BACKTRACKING ====================
    def backtracking_solve(self, max_depth=25):
        mines_found = set()
        safe_found = set()
        
        frontier = list(self.get_frontier())
        if not frontier or len(frontier) > max_depth:
            return mines_found, safe_found
        
        constraints = []
        for r, c in self.get_revealed_numbered_cells():
            unrevealed = tuple(self.get_unrevealed_neighbors(r, c))
            if unrevealed:
                eff = self.effective_count(r, c)
                constraints.append((set(unrevealed), eff))
        
        if not constraints:
            return mines_found, safe_found
        
        solutions = []
        self._backtrack(frontier, 0, set(), constraints, solutions, max_solutions=1000)
        
        if not solutions:
            return mines_found, safe_found
        
        for cell in frontier:
            is_mine_count = sum(1 for sol in solutions if cell in sol)
            
            if is_mine_count == len(solutions):
                mines_found.add(cell)
            elif is_mine_count == 0:
                safe_found.add(cell)
        
        return mines_found, safe_found
    
    def _backtrack(self, cells, idx, current_mines, constraints, solutions, max_solutions):
        if len(solutions) >= max_solutions:
            return
        
        for cell_set, count in constraints:
            mines_in_set = len(cell_set & current_mines)
            remaining_cells = cell_set - current_mines - set(cells[:idx])
            
            if mines_in_set > count:
                return
            if mines_in_set + len(remaining_cells) < count:
                return
        
        if idx == len(cells):
            for cell_set, count in constraints:
                if len(cell_set & current_mines) != count:
                    return
            solutions.append(frozenset(current_mines))
            return
        
        cell = cells[idx]
        self._backtrack(cells, idx + 1, current_mines, constraints, solutions, max_solutions)
        new_mines = current_mines | {cell}
        self._backtrack(cells, idx + 1, new_mines, constraints, solutions, max_solutions)
    
    # ==================== MAIN SOLVER ====================
    def solve_step(self):
        """
        Flow: Basic → 1-2-X → 1-1-X → Reduction → Advanced → Last Turn → CSP → Backtrack → Guess
        Returns: (action, (row, col)) or ('done', None)
        """
        if self.game.game_over:
            return ('done', None)
        
        if self.game.first_click:
            r, c = self.game.rows // 2, self.game.cols // 2
            return ('reveal', (r, c))
        
        self.known_mines.clear()
        self.known_safe.clear()
        self.chord_cells.clear()
        
        # Pattern 1: Basic
        mines, safe, chords = self.pattern_basic()
        self.known_mines.update(mines)
        self.known_safe.update(safe)
        self.chord_cells.update(chords)
        
        # Patterns 2-7 if basic found nothing
        if not (mines or safe or chords):
            patterns = [
                self.pattern_1_2_x,
                self.pattern_1_1_x,
                self.pattern_reduction,
                self.pattern_advanced_logic,
                self.pattern_last_turn,
                self.pattern_high_complex,
            ]
            
            for pattern_func in patterns:
                mines, safe = pattern_func()
                self.known_mines.update(mines)
                self.known_safe.update(safe)
                if mines or safe:
                    break
        
        # Execute: flag → chord → reveal
        for r, c in self.known_mines:
            if not self.game.flagged[r][c]:
                return ('flag', (r, c))
        
        for r, c in self.chord_cells:
            if self.get_unrevealed_neighbors(r, c):
                return ('chord', (r, c))
        
        for r, c in self.known_safe:
            if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                return ('reveal', (r, c))
        
        # Backtracking if patterns failed
        mines, safe = self.backtracking_solve()
        
        for r, c in mines:
            if not self.game.flagged[r][c]:
                return ('flag', (r, c))
        
        for r, c in safe:
            if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                return ('reveal', (r, c))
        
        # Guess if nothing certain
        return self._make_guess()
    
    def _make_guess(self):
        """Guess cell with lowest mine probability"""
        frontier = list(self.get_frontier())
        unrevealed = self.get_all_unrevealed()
        
        if not unrevealed:
            return ('done', None)
        
        # Calculate probability via backtracking
        if frontier:
            constraints = []
            for r, c in self.get_revealed_numbered_cells():
                unrevealed_neighbors = tuple(self.get_unrevealed_neighbors(r, c))
                if unrevealed_neighbors:
                    eff = self.effective_count(r, c)
                    constraints.append((set(unrevealed_neighbors), eff))
            
            if len(frontier) <= 20:
                solutions = []
                self._backtrack(frontier, 0, set(), constraints, solutions, max_solutions=500)
                
                if solutions:
                    min_prob = 1.0
                    best_cell = None
                    
                    for cell in frontier:
                        mine_count = sum(1 for sol in solutions if cell in sol)
                        prob = mine_count / len(solutions)
                        
                        if prob < min_prob:
                            min_prob = prob
                            best_cell = cell
                    
                    if best_cell and min_prob < 0.5:
                        return ('guess', best_cell)
        
        # Prefer non-frontier: corners > edges > any
        non_frontier = [c for c in unrevealed if c not in frontier]
        
        if non_frontier:
            corners = [(0, 0), (0, self.game.cols-1), 
                      (self.game.rows-1, 0), (self.game.rows-1, self.game.cols-1)]
            
            for corner in corners:
                if corner in non_frontier:
                    return ('guess', corner)
            
            return ('guess', non_frontier[0])
        
        if frontier:
            return ('guess', frontier[0])
        
        return ('done', None)
    
    def auto_solve(self, delay_ms=100, callback=None):
        """Auto-solve game with delay between steps"""
        import time
        
        while not self.game.game_over:
            action, data = self.solve_step()
            
            if action == 'done':
                break
            elif action == 'flag':
                r, c = data
                self.game.flagged[r][c] = True
                self.game.buttons[(r, c)].config(text='🚩', bg='yellow')
            elif action == 'chord':
                r, c = data
                self.game.chord_reveal(r, c)
            elif action in ('reveal', 'guess'):
                r, c = data
                self.game.left_click(r, c)
            
            if callback:
                solved = self.game.check_win()
                callback(action, data, solved)
            
            self.game.root.update()
            
            if self.game.game_over:
                break
                
            time.sleep(delay_ms / 1000.0)
        
        return self.game.check_win()


def create_ai_controls(game):    
    ai = MinesweeperAI(game)
    
    def on_step():
        if game.game_over:
            game.status_label.config(text="Game Over")
            return
        
        # Khóa nút để chống spam click
        game.btn_step.config(state=tk.DISABLED)
        game.btn_auto.config(state=tk.DISABLED)
        game.root.update()

        action, data = ai.solve_step()
        
        if action == 'done':
            game.status_label.config(text="No moves left")
        elif action == 'flag':
            r, c = data
            game.flagged[r][c] = True
            game.buttons[(r, c)].config(text='🚩', fg='#E74C3C', bg='#A0A4A8', relief=tk.RAISED, bd=3)
            game.flags_count += 1
            game.mines_label.config(text=f"💣 {game.mines - game.flags_count}")
            game.status_label.config(text=f"Flag ({r}, {c})")
        elif action == 'chord':
            r, c = data
            game.chord_reveal(r, c)
            game.status_label.config(text=f"Chord ({r}, {c})")
        elif action == 'reveal':
            r, c = data
            game.left_click(r, c)
            game.status_label.config(text=f"Reveal ({r}, {c})")
        elif action == 'guess':
            r, c = data
            game.left_click(r, c)
            game.status_label.config(text=f"Guess ({r}, {c})")
        if not game.game_over and game.check_win():
            game._trigger_win()
            
        # Mở lại nút
        if not game.game_over:
            game.btn_step.config(state=tk.NORMAL)
            game.btn_auto.config(state=tk.NORMAL)
    
    def on_auto():
        game.auto_solving = True
        game.btn_step.config(state=tk.DISABLED)
        game.btn_auto.config(state=tk.DISABLED)
        game.status_label.config(text="AI Thinking...", fg='#0984E3')
        
        def update_status(action, data, solved):
            if action == 'flag':
                # Re-style cờ cho giống UI mới
                r, c = data
                game.buttons[(r, c)].config(text='🚩', fg='#E74C3C', bg='#A0A4A8', relief=tk.RAISED, bd=3)
                game.flags_count += 1
                game.mines_label.config(text=f"💣 {game.mines - game.flags_count}")
                game.status_label.config(text=f"Flag ({r}, {c})")
            elif action == 'chord':
                game.status_label.config(text=f"Chord {data}")
            elif action == 'reveal':
                game.status_label.config(text=f"Reveal {data}")
            elif action == 'guess':
                game.status_label.config(text=f"Guess {data}")
        
        result = ai.auto_solve(delay_ms=50, callback=update_status)
        if result and not game.game_over:
            game._trigger_win()

    def on_reset():
        nonlocal ai
        game.reset_game()
        ai = MinesweeperAI(game)
        game.status_label.config(text="Ready", fg='#50C878')
        game.btn_step.config(state=tk.NORMAL)
        game.btn_auto.config(state=tk.NORMAL)
    
    game.btn_step.config(command=on_step)
    game.btn_auto.config(command=on_auto)
    game.btn_reset.config(command=on_reset)
    
    return ai
