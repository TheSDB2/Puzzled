# HBPnP Sudoku Solver
# Author: Steven Brashear
"""
=====================================================================================
                       Improved HBPnP Sudoku benchmark profile                       
=====================================================================================
Processor     : Intel64 Family 6 Model 142 Stepping 11, GenuineIntel
Logical CPUs  : 8
Platform      : Windows 11
Python        : 3.14.3
-------------------------------------------------------------------------------------

TEST NAME                | EMPTY BOXES  | TIME (ms)    | BACKTRACKING | STATUS
-----------------------------------------------------------------------------------------------
 Static Easy Puzzle      | 51           | 9.1581       | 0            | Solved
Random Easy Puzzle       | 33           | 7.9906       | 0            | Solved
Random Medium Puzzle     | 47           | 13.8123      | 0            | Solved
Random Hard Puzzle       | 54           | 26.7158      | 0            | Solved
-------------------------------------------------------------------------------------


Test #2:
=====================================================================================
                       Improved HBPnP Sudoku benchmark profile                       
=====================================================================================
Processor     : Intel64 Family 6 Model 142 Stepping 11, GenuineIntel
Logical CPUs  : 8
Platform      : Windows 11
Python        : 3.14.3
-------------------------------------------------------------------------------------

TEST NAME                | EMPTY BOXES  | TIME (ms)    | BACKTRACKING | STATUS
-----------------------------------------------------------------------------------------------
 Static Easy Puzzle      | 51           | 7.4326       | 0            | Solved
Random Easy Puzzle       | 32           | 5.922        | 0            | Solved
Random Medium Puzzle     | 42           | 10.009       | 0            | Solved
Random Hard Puzzle       | 56           | 28.2397      | 0            | Solved

test #3:
=====================================================================================
                       Improved HBPnP Sudoku benchmark profile                       
=====================================================================================
Processor     : Intel64 Family 6 Model 142 Stepping 11, GenuineIntel
Logical CPUs  : 8
Platform      : Windows 11
Python        : 3.14.3
-------------------------------------------------------------------------------------

TEST NAME                | EMPTY BOXES  | TIME (ms)    | BACKTRACKING | STATUS
-----------------------------------------------------------------------------------------------
 Static Easy Puzzle      | 51           | 5.9077       | 0            | Solved
Random Easy Puzzle       | 38           | 4.9832       | 0            | Solved
Random Medium Puzzle     | 42           | 6.65         | 0            | Solved
Random Hard Puzzle       | 58           | 55.931       | 1            | Solved
"""


import time
import platform
import copy
import os

from test_puzzles import TEST_SUITES       ## Commented out, for testing the code

# Splits the big grid into smaller 3x3 grids
Subgrid = [
    [(r // 3) * 3 + (c // 3) for c in range(9)]
    for r in range(9)
]

# Seperates all 81 entries into cords for each square to easily find later with solving method
All_Cords = []
All_Cords.extend([[(r, c) for c in range(9)] for r in range(9)])
All_Cords.extend([[(r, c) for r in range(9)] for c in range(9)])
All_Cords.extend([
    [(r, c)
     for r in range(box_row * 3, box_row * 3 + 3)
     for c in range(box_col * 3, box_col * 3 + 3)]
    for box_row in range(3)
    for box_col in range(3)
])

# Looks at the row, column, and 3x3 grid (house) for a given cell, to make a canidates list later
Cell_House = {}
for r in range(9):
    for c in range(9):
        Cell_House[(r, c)] = (
            r,
            c,
            Subgrid[r][c],
        )

# Computes every peer value of a cell (peers are cells that share a house) narrows down the canidates list
Peers = {}
for r in range(9):
    for c in range(9):
        peer_set = set()
        peer_set.update((r, j) for j in range(9) if j != c)
        peer_set.update((i, c) for i in range(9) if i != r)
        box_id = Subgrid[r][c]
        peer_set.update(
            (i, j)
            for i in range(9)
            for j in range(9)
            if Subgrid[i][j] == box_id and (i, j) != (r, c)
        )
        Peers[(r, c)] = peer_set

# Counts the empty spaces
def count_empty_boxes(board):
    return sum(row.count(0) for row in board)

# Prints the board currently being worked on
def print_board(board):
    for r in range(9):
        if r and r % 3 == 0:
            print("-" * 21)

        row_parts = []

        for c in range(9):
            if c and c % 3 == 0:
                row_parts.append("|")

            row_parts.append(str(board[r][c]))

        print(" ".join(row_parts))

# Checks if the board can be solved and is legal
def is_valid_board(board):
    if len(board) != 9 or any(len(row) != 9 for row in board):
        return False

    for row in board:
        values = [v for v in row if v != 0]

        if any(
            not isinstance(v, int) or v < 1 or v > 9
            for v in values
        ):
            return False

        if len(values) != len(set(values)):
            return False

    for c in range(9):
        values = [
            board[r][c]
            for r in range(9)
            if board[r][c] != 0
        ]

        if len(values) != len(set(values)):
            return False

    for unit in All_Cords[18:]:
        values = [
            board[r][c]
            for r, c in unit
            if board[r][c] != 0
        ]

        if len(values) != len(set(values)):
            return False

    return True


# Begin the HBPnP process of looking for different data structures
class SudokuState:

    def __init__(self, board):

        if not is_valid_board(board):
            raise ValueError("The supplied Sudoku board is invalid.")

        self.board = [row[:] for row in board]

        self.filled_count = 81 - count_empty_boxes(self.board)

        # Creates a candidate list for each cell. 
        self.candidates = [
            [set() for _ in range(9)]
            for _ in range(9)
        ]

        # Function proposed in Peer Reviewed Paper, counts how many times a number shows up in peers. 
        self.CountForHiddenSingles = [
            [[0] * 10 for _ in range(9)]
            for _ in range(3)
        ]

        for r in range(9):
            for c in range(9):

                if self.board[r][c] == 0:

                    used = set(self.board[r])

                    used.update(
                        self.board[i][c]
                        for i in range(9)
                    )

                    box_id = Subgrid[r][c]

                    used.update(
                        self.board[i][j]
                        for i in range(9)
                        for j in range(9)
                        if Subgrid[i][j] == box_id
                    )

                    options = set(range(1, 10)) - used

                    if not options:
                        raise ValueError(
                            f"No candidates available for cell "
                            f"({r + 1}, {c + 1})."
                        )

                    self.candidates[r][c] = options

                    for digit in options:
                        self._change_count(r, c, digit, 1)

    # Updates the count of times a digit can show up in a its house if it is being used somewhere else
    def _change_count(self, r, c, digit, amount):

        row_unit, col_unit, box_unit = Cell_House[(r, c)]

        self.CountForHiddenSingles[0][row_unit][digit] += amount
        self.CountForHiddenSingles[1][col_unit][digit] += amount
        self.CountForHiddenSingles[2][box_unit][digit] += amount

    # Removes a digit from all house canidate lists if it is used by a cell
    def remove_candidate(self, r, c, digit):

        if (
            self.board[r][c] != 0
            or digit not in self.candidates[r][c]
        ):
            return True

        self.candidates[r][c].remove(digit)

        self._change_count(r, c, digit, -1)

        return bool(self.candidates[r][c])

    # Places the number into the  cell that it believes is the best fit at the time
    def place_number(self, r, c, digit):

        if self.board[r][c] != 0:
            return self.board[r][c] == digit

        if digit not in self.candidates[r][c]:
            return False

        for candidate in list(self.candidates[r][c]):

            self.candidates[r][c].remove(candidate)

            self._change_count(r, c, candidate, -1)

        self.board[r][c] = digit

        self.filled_count += 1

        for pr, pc in Peers[(r, c)]:

            if self.board[pr][pc] == 0:

                if not self.remove_candidate(pr, pc, digit):
                    return False

        return True

    # Looks to see what digits are already placed in the cell's house
    def unit_used_digits(self, unit_type, unit_index):

        unit = All_Cords[unit_type * 9 + unit_index]

        return {
            self.board[r][c]
            for r, c in unit
            if self.board[r][c] != 0
        }

    # Checks the board to see if there is a rule broken or the current board makes no sense (no canidate, rule broken, etc.)
    def is_contradictory(self):

        for r in range(9):
            for c in range(9):

                if (
                    self.board[r][c] == 0
                    and not self.candidates[r][c]
                ):
                    return True

        for unit_type in range(3):

            for unit_index in range(9):

                used = self.unit_used_digits(
                    unit_type,
                    unit_index
                )

                for digit in range(1, 10):

                    if digit not in used:

                        if (
                            self.CountForHiddenSingles
                            [unit_type][unit_index][digit] == 0
                        ):
                            return True

        return False

    
# Functions to find data structures in the proposed puzzle, as proposed by the Peer Reviewed Paper
    
# Used to fine hidden singles. Digits that can only be placed in one cell of a house, but is not the only canidate for the cell
def find_hidden_single(state):

    for unit_type in range(3):

        for unit_index in range(9):

            used = state.unit_used_digits(
                unit_type,
                unit_index
            )

            unit = All_Cords[unit_type * 9 + unit_index]

            for digit in range(1, 10):

                if digit in used:
                    continue

                if (
                    state.CountForHiddenSingles
                    [unit_type][unit_index][digit] == 1
                ):

                    for r, c in unit:

                        if (
                            state.board[r][c] == 0
                            and digit in state.candidates[r][c]
                        ):
                            return r, c, digit

    return None

# Used to find Lone Pairs. A pair of Digits that show up in exactly two cells, this means you can take that pair out of the other canidate lists in their respective houses
def apply_lone_pair(state):

    for unit in All_Cords:

        pair_cells = {}

        for r, c in unit:

            if (
                state.board[r][c] == 0
                and len(state.candidates[r][c]) == 2
            ):

                key = frozenset(state.candidates[r][c])

                pair_cells.setdefault(key, []).append((r, c))

        for pair, cells in pair_cells.items():

            if len(cells) != 2:
                continue

            pair_digits = set(pair)

            pair_positions = set(cells)

            for r, c in unit:

                if (
                    state.board[r][c] == 0
                    and (r, c) not in pair_positions
                ):

                    for digit in pair_digits:

                        if digit in state.candidates[r][c]:

                            if not state.remove_candidate(
                                r, c, digit
                            ):
                                return True

                            return True

    return False

# Function to call upon the Pencil and Paper method of finding data sturctures in the proposed puzzle using the canidate lists
def pencil_and_paper(state):

    while True:

        if state.is_contradictory():
            return False

        single_found = False

        for r in range(9):

            for c in range(9):

                if (
                    state.board[r][c] == 0
                    and len(state.candidates[r][c]) == 1
                ):

                    digit = next(
                        iter(state.candidates[r][c])
                    )

                    if not state.place_number(r, c, digit):
                        return False

                    single_found = True
                    break

            if single_found:
                break

        if single_found:
            continue

        hidden = find_hidden_single(state)

        if hidden is not None:

            if not state.place_number(*hidden):
                return False

            continue

        if apply_lone_pair(state):
            continue

        return not state.is_contradictory()

# Enables Backtracking as a fallback in case the PnP method finds an incorrect digit. Also prints out statistics of the solve
def backtracking_search(board):

    stats = {
        "backtrack_count": 0,
        "recursive_steps": 0,
        "guess_count": 0,
        "success": False,
        "time_required_ms": 0.0,
    }

    try:
        initial_state = SudokuState(board)

    except ValueError:
        return stats

    # Main solving function to find the solution for the puzzle
    def solve(state):

        stats["recursive_steps"] += 1

        # Apply PnP techniques
        if not pencil_and_paper(state):
            return None

        # Checks if the puzzle is solved
        if state.filled_count == 81:
            return state

        # Focuses on the cell with the smallest candidate list for backtracking, since the more constraints means less of a guess
        best_cell = None
        best_options = None

        for r in range(9):

            for c in range(9):

                if state.board[r][c] == 0:

                    options = state.candidates[r][c]

                    if (
                        best_options is None
                        or len(options) < len(best_options)
                    ):

                        best_cell = (r, c)
                        best_options = options

                    if len(best_options) == 2:
                        break

            if (
                best_options is not None
                and len(best_options) == 2
            ):
                break

        if best_cell is None or not best_options:
            return None

        r, c = best_cell

        stats["guess_count"] += 1

        for digit in sorted(best_options):

            branch = copy.deepcopy(state)

            if branch.place_number(r, c, digit):

                result = solve(branch)

                if result is not None:
                    return result

            stats["backtrack_count"] += 1

        return None

    start_time = time.perf_counter()

    solved_state = solve(initial_state)

    end_time = time.perf_counter()

    stats["time_required_ms"] = round(
        (end_time - start_time) * 1000,
        4
    )

    stats["success"] = solved_state is not None

    if solved_state is not None:

        for r in range(9):
            board[r][:] = solved_state.board[r]

    return stats

# Prints hardware specifications for benchmarking purposes
def print_hardware_profile():

    print("=" * 85)

    print(
        f"{'Improved HBPnP Sudoku benchmark profile': ^85}"
    )

    print("=" * 85)

    print(
        f"Processor     : "
        f"{platform.processor() or 'Not reported by Python'}"
    )

    print(f"Logical CPUs  : {__import__('os').cpu_count()}")

    print(
        f"Platform      : "
        f"{platform.system()} {platform.release()}"
    )

    print(f"Python        : {platform.python_version()}")

    print("-" * 85 + "\n")



# Benchmark Runner   ## Commented Out for Testing Purposes

if __name__ == "__main__":

    print_hardware_profile()

    print(
        f"{'TEST NAME': <24} | "
        f"{'EMPTY BOXES': <12} | "
        f"{'TIME (ms)': <12} | "
        f"{'BACKTRACKING': <12} | "
        f"{'STATUS'}"
    )

    print("-" * 95)

    for name, board_data in TEST_SUITES.items():

        board_copy = [
            row[:]
            for row in board_data
        ]

        empty_count = count_empty_boxes(board_copy)

        metrics = backtracking_search(board_copy)

        status = (
            "Solved"
            if metrics["success"]
            else "Failed"
        )

        print(
            f"{name: <24} | "
            f"{empty_count: <12} | "
            f"{metrics['time_required_ms']: <12} | "
            f"{metrics['backtrack_count']: <12} | "
            f"{status}"
        )
"""
        if metrics["success"]:

            print_board(board_copy)

            print()

    print("-" * 95)
"""


# Testing Code, Runs a 'Easy,' 'Medium,' and 'Hard' Puzzle to test times and completion
"""
if __name__ == "__main__":

    print_hardware_profile()

    test_puzzles = {
        "Easy": [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9]
        ],

        "Medium": [
            [0, 0, 0, 2, 6, 0, 7, 0, 1],
            [6, 8, 0, 0, 7, 0, 0, 9, 0],
            [1, 9, 0, 0, 0, 4, 5, 0, 0],
            [8, 2, 0, 1, 0, 0, 0, 4, 0],
            [0, 0, 4, 6, 0, 2, 9, 0, 0],
            [0, 5, 0, 0, 0, 3, 0, 2, 8],
            [0, 0, 9, 3, 0, 0, 0, 7, 4],
            [0, 4, 0, 0, 5, 0, 0, 3, 6],
            [7, 0, 3, 0, 1, 8, 0, 0, 0]
        ],

        "Hard": [
            [1, 0, 0, 0, 0, 7, 0, 9, 0],
            [0, 3, 0, 0, 2, 0, 0, 0, 8],
            [0, 0, 9, 6, 0, 0, 5, 0, 0],
            [0, 0, 5, 3, 0, 0, 9, 0, 0],
            [0, 1, 0, 0, 8, 0, 0, 0, 2],
            [6, 0, 0, 0, 0, 4, 0, 0, 0],
            [3, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 4, 0, 0, 0, 0, 0, 0, 7],
            [0, 0, 7, 0, 0, 0, 3, 0, 0]
        ]
    }

    print("=" * 75)
    print("HBPnP SUDOKU SOLVER - DIFFICULTY TEST")
    print("=" * 75)

    for name, original_puzzle in test_puzzles.items():

        puzzle = [row[:] for row in original_puzzle]

        print(f"\n{name.upper()} PUZZLE")
        print("-" * 40)

        print("Original Puzzle:")
        print_board(puzzle)

        stats = backtracking_search(puzzle)

        print("\nSolved Puzzle:")

        if stats["success"]:
            print_board(puzzle)
            print("Status: SOLVED")
        else:
            print("Status: FAILED")

        print("\nPerformance:")
        print(f"Time: {stats['time_required_ms']} ms")
        print(f"Recursive Steps: {stats['recursive_steps']}")
        print(f"Guesses: {stats['guess_count']}")
        print(f"Backtracks: {stats['backtrack_count']}")

        print("=" * 75)
"""