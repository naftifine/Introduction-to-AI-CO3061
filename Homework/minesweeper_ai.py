"""
Minesweeper AI Solver
Uses pattern recognition and backtracking with constraint satisfaction.

Patterns implemented (based on minesweeper.online/help/patterns):
1. Basic - If number equals unrevealed neighbors, all are mines; if satisfied, chord
2. 1-2-X Pattern - When you see 1-2-X on a row, X is always a mine
3. 1-1-X Pattern - When 1-1-X from border, third square is safe
4. Reduction - Compare adjacent cells, subset analysis
5. Advanced Logic - Subset deduction for mines and safe cells
6. Last Turn - Endgame logic with remaining mine count
7. Backtracking/CSP - For complex situations
"""

from itertools import combinations
from collections import defaultdict


class MinesweeperAI:
    def __init__(self, game):
        self.game = game
        self.known_mines = set()
        self.known_safe = set()
        self.chord_cells = set()
        self.constraints = []
        
    def get_neighbors(self, row, col):
        """Get all valid neighbor coordinates"""
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
        """Get unrevealed, unflagged neighbor coordinates"""
        unrevealed = []
        for nr, nc in self.get_neighbors(row, col):
            if not self.game.revealed[nr][nc] and not self.game.flagged[nr][nc]:
                unrevealed.append((nr, nc))
        return unrevealed
    
    def get_flagged_neighbors(self, row, col):
        """Get flagged neighbor coordinates"""
        flagged = []
        for nr, nc in self.get_neighbors(row, col):
            if self.game.flagged[nr][nc]:
                flagged.append((nr, nc))
        return flagged
    
    def get_revealed_numbered_cells(self):
        """Get all revealed cells with numbers > 0"""
        cells = []
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if self.game.revealed[r][c] and self.game.board[r][c] > 0:
                    cells.append((r, c))
        return cells
    
    def get_all_unrevealed(self):
        """Get all unrevealed, unflagged cells"""
        cells = []
        for r in range(self.game.rows):
            for c in range(self.game.cols):
                if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                    cells.append((r, c))
        return cells
    
    def get_frontier(self):
        """Get unrevealed cells adjacent to revealed cells"""
        frontier = set()
        for r, c in self.get_revealed_numbered_cells():
            for nr, nc in self.get_unrevealed_neighbors(r, c):
                frontier.add((nr, nc))
        return frontier
    
    def effective_count(self, row, col):
        """Get remaining mines around a cell (total - flagged)"""
        if not self.game.revealed[row][col]:
            return -1
        total_mines = self.game.board[row][col]
        flagged = len(self.get_flagged_neighbors(row, col))
        return total_mines - flagged
    
    # ==================== PATTERN 1: BASIC ====================
    def pattern_basic(self):
        """
        Basic pattern (from minesweepergame.com):
        - When a number touches the same number of squares, those squares must be mines
        - If a number already has all its mines flagged, remaining squares are safe (chord)
        
        Examples:
        - 1 on corner touches 1 square → it's a mine
        - 2 touches 2 squares → both are mines
        - 3 with 3 flags → remaining neighbors are safe
        """
        mines_found = set()
        safe_found = set()
        chord_found = set()
        
        for r, c in self.get_revealed_numbered_cells():
            unrevealed = self.get_unrevealed_neighbors(r, c)
            effective = self.effective_count(r, c)
            
            if len(unrevealed) == 0:
                continue
            
            # All unrevealed squares must be mines (number == unrevealed count)
            if effective == len(unrevealed):
                mines_found.update(unrevealed)
            
            # All mines already flagged, chord click to reveal remaining squares
            elif effective == 0:
                safe_found.update(unrevealed)
                chord_found.add((r, c))
        
        return mines_found, safe_found, chord_found
    
    # ==================== PATTERN 2: 1-2-X PATTERN ====================
    def pattern_1_2_x(self):
        """
        1-2-X Pattern (from minesweepergame.com):
        When you see 1-2-X on a row, the X square is ALWAYS a mine.
        
        Logic: There are 2 mines in 3 squares (because 2 touches 3 squares)
        but there is 1 mine in the first 2 squares (because 1 touches 2 of the 3 squares).
        The 3rd square must contain the other mine.
        
        Also applies to variations like:
        - 1-2-1: Apply from both sides to find 2 mines
        - 1-2-2-1: Apply from both sides
        """
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        for r1, c1 in numbered_cells:
            eff1 = self.effective_count(r1, c1)
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            
            if eff1 != 1 or len(set1) < 2:
                continue
            
            # Look for adjacent "2" cells
            for r2, c2 in self.get_neighbors(r1, c1):
                if not self.game.revealed[r2][c2]:
                    continue
                
                eff2 = self.effective_count(r2, c2)
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                
                if eff2 != 2 or len(set2) < 2:
                    continue
                
                # Check if set1 is subset of set2 (or overlaps significantly)
                overlap = set1 & set2
                if len(overlap) >= 2:
                    # The cells in set2 but not in set1 must be mines
                    # Because: 2 mines in set2, 1 mine in overlap → 1 mine in (set2 - set1)
                    diff = set2 - set1
                    if len(diff) == 1:
                        mines_found.update(diff)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 3: 1-1-X PATTERN ====================
    def pattern_1_1_x(self):
        """
        1-1-X Pattern (from minesweepergame.com):
        When you see 1-1-X on a row starting from a border, the X square is safe.
        
        Logic: The first 1 touches 2 squares, the second 1 touches 3 squares.
        Both clues are true so the mine must be in the subset of 2 squares.
        The third square must be empty.
        
        This is the opposite of 1-2-X (which always has a mine in the third square).
        """
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        for r1, c1 in numbered_cells:
            eff1 = self.effective_count(r1, c1)
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            
            if eff1 != 1 or len(set1) < 1:
                continue
            
            # Look for adjacent "1" cells
            for r2, c2 in self.get_neighbors(r1, c1):
                if not self.game.revealed[r2][c2]:
                    continue
                
                eff2 = self.effective_count(r2, c2)
                set2 = set(self.get_unrevealed_neighbors(r2, c2))
                
                if eff2 != 1:
                    continue
                
                # Check if set1 is proper subset of set2
                if set1 < set2:
                    # The mine is in set1, so (set2 - set1) is safe
                    diff = set2 - set1
                    safe_found.update(diff)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 4: REDUCTION (SUBSET ANALYSIS) ====================
    def pattern_reduction(self):
        """
        Reduction/Subset Pattern (from minesweepergame.com):
        Compare two numbered cells. If one set is a subset of another,
        we can deduce information about the difference.
        
        Examples:
        - If cell A needs 2 mines in 4 squares, and cell B needs 2 mines in 2 of those squares,
          then B's squares are the mines and A's other 2 squares are safe.
        - Subtract known mines from numbers to simplify (reduce) the pattern.
        """
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
                
                # Check if sets overlap
                if not set1 & set2:
                    continue
                
                # If set1 is subset of set2
                if set1 <= set2:
                    diff = set2 - set1
                    diff_mines = eff2 - eff1
                    
                    if diff_mines < 0:
                        continue
                    
                    # All difference cells are mines
                    if diff_mines == len(diff):
                        mines_found.update(diff)
                    # No mines in difference cells
                    elif diff_mines == 0:
                        safe_found.update(diff)
                
                # If set2 is subset of set1
                elif set2 <= set1:
                    diff = set1 - set2
                    diff_mines = eff1 - eff2
                    
                    if diff_mines < 0:
                        continue
                    
                    # All difference cells are mines
                    if diff_mines == len(diff):
                        mines_found.update(diff)
                    # No mines in difference cells
                    elif diff_mines == 0:
                        safe_found.update(diff)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 5: ADVANCED LOGIC (COMPLEX SUBSET) ====================
    def pattern_advanced_logic(self):
        """
        Advanced Logic Pattern:
        Sometimes a mine is in a subset of squares so the remaining squares must be safe.
        This generalizes 1-1-X and handles more complex cases.
        
        Also looks for cases where we can deduce mines by elimination.
        """
        mines_found = set()
        safe_found = set()
        
        numbered_cells = self.get_revealed_numbered_cells()
        
        # Build constraint map for more complex analysis
        for r1, c1 in numbered_cells:
            set1 = set(self.get_unrevealed_neighbors(r1, c1))
            eff1 = self.effective_count(r1, c1)
            
            if len(set1) == 0 or eff1 <= 0:
                continue
            
            # Look at all other numbered cells
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
                
                # If all mines of cell2 MUST be in the overlap
                # then only2 cells are safe
                if eff2 <= len(overlap) and len(only2) > 0:
                    # Check if remaining mines after overlap can fill only1
                    remaining_for_1 = eff1 - eff2
                    if remaining_for_1 >= 0 and remaining_for_1 <= len(only1):
                        # only2 might be safe if eff2 mines fill the overlap
                        if eff2 == len(overlap):
                            # overlap has exactly eff2 mines, so only1 has remaining mines
                            if remaining_for_1 == len(only1):
                                mines_found.update(only1)
                            elif remaining_for_1 == 0:
                                safe_found.update(only1)
                
                # Advanced: check min/max mines in regions
                # Minimum mines in overlap = max(0, eff1 - len(only1), eff2 - len(only2))
                min_in_overlap = max(0, eff1 - len(only1), eff2 - len(only2))
                # Maximum mines in overlap = min(len(overlap), eff1, eff2)
                max_in_overlap = min(len(overlap), eff1, eff2)
                
                if min_in_overlap > max_in_overlap:
                    continue  # Invalid state
                
                # If min == max, we know exactly how many mines in overlap
                if min_in_overlap == max_in_overlap:
                    mines_in_overlap = min_in_overlap
                    
                    # Mines in only1 = eff1 - mines_in_overlap
                    mines_in_only1 = eff1 - mines_in_overlap
                    if mines_in_only1 == len(only1) and only1:
                        mines_found.update(only1)
                    elif mines_in_only1 == 0 and only1:
                        safe_found.update(only1)
                    
                    # Mines in only2 = eff2 - mines_in_overlap
                    mines_in_only2 = eff2 - mines_in_overlap
                    if mines_in_only2 == len(only2) and only2:
                        mines_found.update(only2)
                    elif mines_in_only2 == 0 and only2:
                        safe_found.update(only2)
        
        return mines_found, safe_found
    
    # ==================== PATTERN 6: HIGH COMPLEX (CSP) ====================
    def pattern_high_complex(self):
        """
        High complexity pattern using Constraint Satisfaction.
        Build constraints and find consistent assignments.
        """
        mines_found = set()
        safe_found = set()
        
        # Build constraints: each numbered cell gives a constraint
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
        
        # For each cell in frontier, check if it MUST be mine or MUST be safe
        # by checking all valid assignments
        
        frontier_list = list(frontier)
        
        # Group constraints by shared cells for efficiency
        cell_constraints = defaultdict(list)
        for cells, count in constraints:
            for cell in cells:
                cell_constraints[cell].append((cells, count))
        
        # Check each frontier cell
        for cell in frontier_list:
            can_be_mine = False
            can_be_safe = False
            
            # Get relevant constraints
            relevant_constraints = cell_constraints[cell]
            if not relevant_constraints:
                continue
            
            # Get all cells involved in these constraints
            involved_cells = set()
            for cells, _ in relevant_constraints:
                involved_cells.update(cells)
            
            involved_list = list(involved_cells)
            
            # Try all possible assignments (limit search space)
            if len(involved_list) > 20:
                # Too many cells, skip deep analysis
                continue
            
            # Check if cell can be mine
            if self._check_assignment_possible(involved_list, constraints, cell, True):
                can_be_mine = True
            
            # Check if cell can be safe
            if self._check_assignment_possible(involved_list, constraints, cell, False):
                can_be_safe = True
            
            if can_be_mine and not can_be_safe:
                mines_found.add(cell)
            elif can_be_safe and not can_be_mine:
                safe_found.add(cell)
        
        return mines_found, safe_found
    
    def _check_assignment_possible(self, cells, constraints, target_cell, is_mine):
        """Check if assigning target_cell as mine/safe is consistent"""
        # Filter constraints involving target cell
        relevant_constraints = []
        for cell_tuple, count in constraints:
            if target_cell in cell_tuple:
                relevant_constraints.append((cell_tuple, count))
        
        # Get cells to try
        cells_to_try = set()
        for cell_tuple, _ in relevant_constraints:
            cells_to_try.update(cell_tuple)
        cells_to_try.discard(target_cell)
        cells_list = list(cells_to_try)
        
        if len(cells_list) > 15:
            return True  # Assume possible if too complex
        
        # Try all combinations
        for num_mines in range(len(cells_list) + 1):
            for mine_combo in combinations(cells_list, num_mines):
                mine_set = set(mine_combo)
                if is_mine:
                    mine_set.add(target_cell)
                
                # Check if this assignment satisfies all relevant constraints
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
        Last turn pattern (endgame logic):
        - Count remaining mines and unrevealed cells globally
        - If remaining mines == unrevealed cells, all unrevealed are mines
        - If remaining mines == 0, all unrevealed are safe
        
        This is powerful in the endgame when only a few cells remain.
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
    
    # ==================== BACKTRACKING SOLVER ====================
    def backtracking_solve(self, max_depth=25):
        """
        Use backtracking with constraint propagation to find
        cells that must be mines or must be safe.
        """
        mines_found = set()
        safe_found = set()
        
        frontier = list(self.get_frontier())
        if not frontier or len(frontier) > max_depth:
            # Pick a random safe cell if frontier too large
            return mines_found, safe_found
        
        # Build constraints
        constraints = []
        for r, c in self.get_revealed_numbered_cells():
            unrevealed = tuple(self.get_unrevealed_neighbors(r, c))
            if unrevealed:
                eff = self.effective_count(r, c)
                constraints.append((set(unrevealed), eff))
        
        if not constraints:
            return mines_found, safe_found
        
        # Find all valid solutions
        solutions = []
        self._backtrack(frontier, 0, set(), constraints, solutions, max_solutions=1000)
        
        if not solutions:
            return mines_found, safe_found
        
        # Analyze solutions
        for cell in frontier:
            is_mine_count = sum(1 for sol in solutions if cell in sol)
            
            if is_mine_count == len(solutions):
                mines_found.add(cell)
            elif is_mine_count == 0:
                safe_found.add(cell)
        
        return mines_found, safe_found
    
    def _backtrack(self, cells, idx, current_mines, constraints, solutions, max_solutions):
        """Backtracking helper"""
        if len(solutions) >= max_solutions:
            return
        
        # Check constraints with current assignment
        for cell_set, count in constraints:
            mines_in_set = len(cell_set & current_mines)
            remaining_cells = cell_set - current_mines - set(cells[:idx])
            
            # Too many mines already
            if mines_in_set > count:
                return
            
            # Not enough remaining cells to reach count
            if mines_in_set + len(remaining_cells) < count:
                return
        
        if idx == len(cells):
            # Verify all constraints satisfied
            for cell_set, count in constraints:
                if len(cell_set & current_mines) != count:
                    return
            solutions.append(frozenset(current_mines))
            return
        
        cell = cells[idx]
        
        # Try cell as safe
        self._backtrack(cells, idx + 1, current_mines, constraints, solutions, max_solutions)
        
        # Try cell as mine
        new_mines = current_mines | {cell}
        self._backtrack(cells, idx + 1, new_mines, constraints, solutions, max_solutions)
    
    # ==================== MAIN SOLVER ====================
    def solve_step(self):
        """
        Perform one step of solving.
        Returns: (action, data)
        - ('flag', (row, col)) - Flag a cell
        - ('reveal', (row, col)) - Reveal a cell
        - ('chord', (row, col)) - Chord click on revealed cell
        - ('guess', (row, col)) - Make a guess (risky)
        - ('done', None) - No more moves
        """
        if self.game.game_over:
            return ('done', None)
        
        if self.game.first_click:
            # First click - choose center or random
            r, c = self.game.rows // 2, self.game.cols // 2
            return ('reveal', (r, c))
        
        # Clear known sets
        self.known_mines.clear()
        self.known_safe.clear()
        self.chord_cells.clear()
        
        # Apply basic pattern first (can return chord cells)
        mines, safe, chords = self.pattern_basic()
        self.known_mines.update(mines)
        self.known_safe.update(safe)
        self.chord_cells.update(chords)
        
        # If basic found moves, use them
        if not (mines or safe or chords):
            # Apply other patterns in order of complexity
            patterns = [
                ('1-2-X', self.pattern_1_2_x),
                ('1-1-X', self.pattern_1_1_x),
                ('Reduction', self.pattern_reduction),
                ('Advanced Logic', self.pattern_advanced_logic),
                ('Last Turn', self.pattern_last_turn),
                ('High Complex', self.pattern_high_complex),
            ]
            
            for name, pattern_func in patterns:
                mines, safe = pattern_func()
                self.known_mines.update(mines)
                self.known_safe.update(safe)
                
                # If we found definite moves, execute them
                if mines or safe:
                    break
        
        # Flag known mines first
        for r, c in self.known_mines:
            if not self.game.flagged[r][c]:
                return ('flag', (r, c))
        
        # Use chord click if available (more efficient)
        for r, c in self.chord_cells:
            # Check if there are still unrevealed neighbors
            if self.get_unrevealed_neighbors(r, c):
                return ('chord', (r, c))
        
        # Reveal known safe cells
        for r, c in self.known_safe:
            if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                return ('reveal', (r, c))
        
        # If no definite moves, try backtracking
        mines, safe = self.backtracking_solve()
        
        for r, c in mines:
            if not self.game.flagged[r][c]:
                return ('flag', (r, c))
        
        for r, c in safe:
            if not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                return ('reveal', (r, c))
        
        # No certain moves - make educated guess
        return self._make_guess()
    
    def _make_guess(self):
        """Make an educated guess when no certain move is available"""
        frontier = list(self.get_frontier())
        unrevealed = self.get_all_unrevealed()
        
        if not unrevealed:
            return ('done', None)
        
        # Calculate probability for frontier cells
        if frontier:
            # Count how often each cell is a mine in valid solutions
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
                    # Find cell with lowest mine probability
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
        
        # Prefer corners, then edges, then non-frontier
        non_frontier = [c for c in unrevealed if c not in frontier]
        
        if non_frontier:
            # Choose corner or edge
            corners = [(0, 0), (0, self.game.cols-1), 
                      (self.game.rows-1, 0), (self.game.rows-1, self.game.cols-1)]
            
            for corner in corners:
                if corner in non_frontier:
                    return ('guess', corner)
            
            # Choose any non-frontier
            return ('guess', non_frontier[0])
        
        # Must choose from frontier
        if frontier:
            return ('guess', frontier[0])
        
        return ('done', None)
    
    def auto_solve(self, delay_ms=100, callback=None):
        """
        Automatically solve the game step by step.
        callback: function to call after each step with (action, data, solved)
        Returns: True if won, False if lost
        """
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
            time.sleep(delay_ms / 1000)
        
        return self.game.check_win()


def create_ai_controls(game):
    """Create AI control panel for the game"""
    import tkinter as tk
    
    ai = MinesweeperAI(game)
    
    # Repack game frame to put AI controls on top
    game.frame.pack_forget()
    
    # Create control frame (pack at top)
    control_frame = tk.Frame(game.root)
    control_frame.pack(side=tk.TOP, pady=5)
    
    # Repack game frame below controls
    game.frame.pack(padx=10, pady=10)
    
    status_label = tk.Label(control_frame, text="AI Ready", font=('Arial', 10))
    status_label.pack()
    
    def on_step():
        if game.game_over:
            status_label.config(text="Game Over")
            return
        
        action, data = ai.solve_step()
        
        if action == 'done':
            status_label.config(text="No more moves")
        elif action == 'flag':
            r, c = data
            game.flagged[r][c] = True
            game.buttons[(r, c)].config(text='🚩', bg='yellow')
            status_label.config(text=f"Flagged ({r}, {c})")
        elif action == 'chord':
            r, c = data
            game.chord_reveal(r, c)
            status_label.config(text=f"Chord ({r}, {c})")
        elif action == 'reveal':
            r, c = data
            game.left_click(r, c)
            status_label.config(text=f"Revealed ({r}, {c})")
        elif action == 'guess':
            r, c = data
            game.left_click(r, c)
            status_label.config(text=f"Guessed ({r}, {c}) ⚠️")
    
    def on_auto():
        def update_status(action, data, solved):
            if action == 'flag':
                status_label.config(text=f"Flagged {data}")
            elif action == 'chord':
                status_label.config(text=f"Chord {data}")
            elif action == 'reveal':
                status_label.config(text=f"Revealed {data}")
            elif action == 'guess':
                status_label.config(text=f"Guessed {data} ⚠️")
        
        result = ai.auto_solve(delay_ms=50, callback=update_status)
        if result:
            status_label.config(text="AI Won!")
        else:
            status_label.config(text="AI Lost")
    
    def on_reset():
        nonlocal ai
        game.reset_game()
        ai = MinesweeperAI(game)
        status_label.config(text="AI Ready")
    
    btn_frame = tk.Frame(control_frame)
    btn_frame.pack()
    
    step_btn = tk.Button(btn_frame, text="AI Step", command=on_step, width=10)
    step_btn.pack(side=tk.LEFT, padx=2)
    
    auto_btn = tk.Button(btn_frame, text="Auto Solve", command=on_auto, width=10)
    auto_btn.pack(side=tk.LEFT, padx=2)
    
    reset_btn = tk.Button(btn_frame, text="Reset", command=on_reset, width=10)
    reset_btn.pack(side=tk.LEFT, padx=2)
    
    return ai, control_frame
