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
                
                if set1 <= set2:
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
        
        for i, (r1, c1) in enumerate(numbered_cells):
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            eff1 = self.effective_count(r1, c1)
            
            if not set1 or eff1 < 0:
                continue
            
            for j in range(i + 1, len(numbered_cells)):
                r2, c2 = numbered_cells[j]
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                eff2 = self.effective_count(r2, c2)
                
                if not set2 or eff2 < 0:
                    continue
                
                overlap = set1 & set2
                if not overlap:
                    continue
                
                only1 = set1 - set2
                only2 = set2 - set1
                
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
        target_constraints = []
        for cell_tuple, count in constraints:
            if target_cell in cell_tuple:
                target_constraints.append((cell_tuple, count))
        
        cells_to_try = set()
        for cell_tuple, _ in target_constraints:
            cells_to_try.update(cell_tuple)
        cells_to_try.discard(target_cell)
        cells_list = list(cells_to_try)
        
        if len(cells_list) > 15:
            return True
        
        all_relevant_constraints = []
        involved = cells_to_try | {target_cell}
        for cell_tuple, count in constraints:
            if set(cell_tuple) & involved:
                all_relevant_constraints.append((cell_tuple, count))
        
        for num_mines in range(len(cells_list) + 1):
            for mine_combo in combinations(cells_list, num_mines):
                mine_set = set(mine_combo)
                if is_mine:
                    mine_set.add(target_cell)
                
                assigned = cells_to_try | {target_cell}
                valid = True
                for cell_tuple, count in all_relevant_constraints:
                    mines_in_constraint = sum(1 for c in cell_tuple if c in mine_set)
                    unassigned_in_constraint = [c for c in cell_tuple if c not in assigned]
                    
                    if not unassigned_in_constraint:
                        if mines_in_constraint != count:
                            valid = False
                            break
                    else:
                        if mines_in_constraint > count:
                            valid = False
                            break
                        if mines_in_constraint + len(unassigned_in_constraint) < count:
                            valid = False
                            break
                
                if valid:
                    return True
        
        return False
    
    # ==================== PATTERN 7: LAST TURN ====================
    def pattern_last_turn(self):
        """
        Logic: remaining_mines == unrevealed - all mines
               remaining_mines == 0 - all safe
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
    
    # ==================== FRONTIER SPLITTING ====================
    def _get_constraints(self):
        return [(set(unr), self.effective_count(r, c))
                for r, c in self.get_revealed_numbered_cells()
                if (unr := self.get_unrevealed_neighbors(r, c))]

    def _split_frontier(self, frontier, constraints):
        adj = defaultdict(set)
        for cell_set, _ in constraints:
            cells = list(cell_set)
            for i in range(len(cells)):
                for j in range(i + 1, len(cells)):
                    adj[cells[i]].add(cells[j])
                    adj[cells[j]].add(cells[i])

        frontier_set = set(frontier)
        visited = set()
        groups = []
        
        for start in frontier:
            if start in visited:
                continue
            
            component_cells = set()
            stack = [start]
            
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component_cells.add(node)
                
                for nb in adj[node]:
                    if nb not in visited and nb in frontier_set:
                        stack.append(nb)
            
            group_constraints = [
                (cell_set, count)
                for cell_set, count in constraints
                if cell_set & component_cells
            ]
            groups.append((list(component_cells), group_constraints))
            
        return groups

    # ==================== BACKTRACKING ====================
    def backtracking_solve(self, max_group_size=22):
        mines_found = set()
        safe_found = set()
        probs = {}
        
        frontier = list(self.get_frontier())
        constraints = self._get_constraints()
        
        if not frontier or not constraints:
            return mines_found, safe_found, probs

        remaining_mines = self.game.mines - sum(
            1 for r in range(self.game.rows)
            for c in range(self.game.cols)
            if self.game.flagged[r][c]
        )

        groups = self._split_frontier(frontier, constraints)
        
        for group_cells, group_constraints in groups:
            if len(group_cells) > max_group_size:
                continue
            
            solutions = []
            self._backtrack(
                group_cells, 0, set(), group_constraints,
                solutions, max_solutions=2000,
                max_allowed_mines=remaining_mines
            )
            
            if not solutions:
                continue

            for cell in group_cells:
                mine_count = sum(1 for sol in solutions if cell in sol)
                probs[cell] = mine_count / len(solutions)
                
                if mine_count == len(solutions):
                    mines_found.add(cell)
                elif mine_count == 0:
                    safe_found.add(cell)
        
        return mines_found, safe_found, probs
    
    def _backtrack(self, cells, idx, current_mines, constraints,
                   solutions, max_solutions, max_allowed_mines):
        if len(solutions) >= max_solutions:
            return
        
        # Pruning
        if len(current_mines) > max_allowed_mines:
            return

        assigned = set(cells[:idx])
        for cell_set, count in constraints:
            mines_in_set = len(cell_set & current_mines)
            remaining_cells = cell_set - current_mines - assigned
            
            if mines_in_set > count:
                return
            if mines_in_set + len(remaining_cells) < count:
                return
        
        if idx == len(cells):
            if all(len(cell_set & current_mines) == count
                   for cell_set, count in constraints):
                solutions.append(frozenset(current_mines))
            return
        
        cell = cells[idx]
        self._backtrack(cells, idx + 1, current_mines, constraints,
                        solutions, max_solutions, max_allowed_mines)
        self._backtrack(cells, idx + 1, current_mines | {cell}, constraints,
                        solutions, max_solutions, max_allowed_mines)
    
    # ==================== MAIN SOLVER ====================
    def solve_step(self):
        """
        Flow: Chord - Basic - 1-2-X - 1-1-X - Reduction - Advanced - Last Turn - CSP - Backtrack - Guess
        Returns: (action, (row, col)) or ('done', None)
        """
        if self.game.game_over:
            return ('done', None)
        
        if self.game.first_click:
            r, c = self.game.rows // 2, self.game.cols // 2
            return ('reveal', (r, c))
        
        for r, c in self.get_revealed_numbered_cells():
            effective = self.effective_count(r, c)
            if effective == 0 and self.get_unrevealed_neighbors(r, c):
                return ('chord', (r, c))
        
        self.known_mines.clear()
        self.known_safe.clear()
        self.chord_cells.clear()
        
        # ========== Pattern-based strategies ==========
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
        
        # Execute: flag - chord - reveal
        for r, c in self.known_mines:
            if not self.game.flagged[r][c]:
                return ('flag', (r, c))
        
        for r, c in self.chord_cells:
            if self.get_unrevealed_neighbors(r, c):
                return ('chord', (r, c))
        
        for r, c in self.known_safe:
            if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                return ('reveal', (r, c))
        
        mines, safe, probs = self.backtracking_solve()
        
        for r, c in mines:
            if not self.game.flagged[r][c]:
                return ('flag', (r, c))
        
        for r, c in safe:
            if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                return ('reveal', (r, c))
        
        return self._smart_guess(probs)
    
    def _smart_guess(self, probs):
        import random
        
        unrevealed = self.get_all_unrevealed()
        if not unrevealed:
            return ('done', None)
        
        frontier = self.get_frontier()
        non_frontier = [c for c in unrevealed if c not in frontier]
        
        best_frontier_cell = None
        min_frontier_prob = 1.0
        
        if probs:
            best_frontier_cell = min(probs, key=probs.get)
            min_frontier_prob = probs[best_frontier_cell]
        
        if min_frontier_prob >= 0.5 and non_frontier:
            corners = [
                (0, 0), (0, self.game.cols - 1),
                (self.game.rows - 1, 0), (self.game.rows - 1, self.game.cols - 1)
            ]
            for corner in corners:
                if corner in non_frontier:
                    return ('guess', corner)
            return ('guess', random.choice(non_frontier))
        
        if best_frontier_cell and min_frontier_prob < 1.0:
            return ('guess', best_frontier_cell)
        
        if non_frontier:
            return ('guess', random.choice(non_frontier))
        
        if frontier:
            return ('guess', random.choice(list(frontier)))
        
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
                self.game.right_click(r, c)
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
            time.sleep(delay_ms / 1000)
        
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
            game.right_click(r, c)
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
                r, c = data
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
        game.status_label.config(text="Ready", fg=game.COLORS['text_status'] if hasattr(game, 'COLORS') else '#50C878')
        game.btn_step.config(state=tk.NORMAL)
        game.btn_auto.config(state=tk.NORMAL)
    
    game.btn_step.config(command=on_step)
    game.btn_auto.config(command=on_auto)
    game.btn_reset.config(command=on_reset)
    
    return ai
