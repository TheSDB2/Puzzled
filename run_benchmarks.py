"""
Main execution script for Sudoku CSP Solver and Hardware Benchmark Suite

Author: Sylvester Reyes
Test #1: 
=====================================================================================
Target processor: Intel64 Family 6 Model 142 Stepping 11, GenuineIntel
Target RAM     : 15GB
Target OS      : Windows 11
-------------------------------------------------------------------------------------

TEST NAME            | EMPTY BOXES  | TIME (ms)    | BACKTRACKING | STATUS
-------------------------------------------------------------------------------------
 Static Easy Puzzle  | 51           | 53.248       | 4157         | Solved
Random Easy Puzzle   | 35           | 1.1044       | 64           | Solved
Random Medium Puzzle | 48           | 15.6099      | 912          | Solved
Random Hard Puzzle   | 56           | 23.2886      | 1475         | Solved
-------------------------------------------------------------------------------------

test #2:
=====================================================================================
Target processor: Intel64 Family 6 Model 142 Stepping 11, GenuineIntel
Target RAM     : 15GB
Target OS      : Windows 11
-------------------------------------------------------------------------------------

TEST NAME            | EMPTY BOXES  | TIME (ms)    | BACKTRACKING | STATUS
-------------------------------------------------------------------------------------
 Static Easy Puzzle  | 51           | 64.9718      | 4157         | Solved
Random Easy Puzzle   | 35           | 0.5638       | 3            | Solved
Random Medium Puzzle | 47           | 1.8269       | 37           | Solved
Random Hard Puzzle   | 53           | 3.3522       | 159          | Solved
-------------------------------------------------------------------------------------

test #3:
=====================================================================================
                           CSP hardware benchmark profile                            
=====================================================================================
Target processor: Intel64 Family 6 Model 142 Stepping 11, GenuineIntel
Target RAM     : 15GB
Target OS      : Windows 11
-------------------------------------------------------------------------------------

TEST NAME            | EMPTY BOXES  | TIME (ms)    | BACKTRACKING | STATUS
-------------------------------------------------------------------------------------
 Static Easy Puzzle  | 51           | 75.0657      | 4157         | Solved
Random Easy Puzzle   | 37           | 2.7351       | 66           | Solved
Random Medium Puzzle | 43           | 16.0209      | 871          | Solved
Random Hard Puzzle   | 52           | 12.3443      | 381          | Solved
-------------------------------------------------------------------------------------

"""

import time 
import platform

# Attempts to import PySudoku CSP solver
try:
    import psutil
except ImportError:
    psutil_available = False

from test_puzzles import TEST_SUITES

# Metrics helper (empty boxes)
def count_empty_boxes(board):
    """
    Counts the number of unassigned variables (0s) on the board.
    Tracks empty box complexity
    """
    return sum(row.count(0) for row in board)


# Board visulizer 
def print_board(board):
    """
    Prints the 9x9 board in a standard grid format 
    with 3x3 subgrid separators
    """
    for i in range(len(board)):
        if i % 3 == 0 and i !=0:
            print("- - - - - - - - - - - -")
        for j in range(len(board[0])):
            if j % 3 == 0 and j != 0:
                print("|", end=" ")
            if j == 8:
                print(board[i][j])
            else:
                print(str(board[i][j]) + " ", end="")


# CSP solver
def select_unassigned_variable(board):
    """
    Selects an unassigned variable from the board
    """
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] == 0:
                return (i, j)
    return None


# CSP Constraint Propagation
# Brute Force Method 
def is_consistent(board, num, pos):
    """
    CSP constraint check / brute force backtracking
    Validates if assigning 'num' to a given pos is valid 
    Alldiff constraints accross its row, column, and subgrid
    """
    row, col = pos

    # checks row constraints
    for j in range(len(board[0])):
        if board[row][j] == num and col != j:
            return False

    # checks column constraints
    for i in range(len(board)):
        if board[i][col] == num and row != i:
            return False

    # checks subgrid constraints
    subgrid_row = (row // 3) * 3
    subgrid_col = (col // 3) * 3
    for i in range(subgrid_row, subgrid_row + 3):
        for j in range(subgrid_col, subgrid_col + 3):
            if board[i][j] == num and (i, j) != pos:
                return False

    return True

#CSP backtracking search algorithm
# Depth-First Search Method 
def backtracking_search(board):
    """
    Core CSP backtracking search algorithm
    recursively assigns domain values (1-9) to variables
    tracks backtracking frequency, and times execution down to the microsecond
    """
    stats = {"backtrack_count": 0, "recursive_steps": 0}

    def _csp_backtrack(b):
        stats["recursive_steps"] += 1
        var = select_unassigned_variable(b)
        if not var:
            # Goal state reached 
            return True 

        row, col = var
        for num in range(1, 10):
            if is_consistent(b, num, (row, col)):
                b[row][col] = num # assign value

                if _csp_backtrack(b):
                    return True

                # Failure: Triggers backtrack event and resets variable assignment
                stats["backtrack_count"] += 1
                b[row][col] = 0

        return False

    # timer using perf_counter for performance measurements
    start_time = time.perf_counter()
    solved = _csp_backtrack(board)
    end_time = time.perf_counter()

    stats["time_required_ms"] = round((end_time - start_time) * 1000, 4)
    stats["success"] = solved

    return stats


# Hardware benchmarking 
def print_hardware_profile():
    """
    Outputs hardware specification for benchmark 
    (Intel Core i5, 16GB RAM, Windows 11)
    """

    print("=" * 85)
    print(f"{'CSP hardware benchmark profile': ^85}")
    print("=" * 85)
    print(f"Target processor: {platform.processor()}")
    print(f"Target RAM     : {str(psutil.virtual_memory().total // (1024 ** 3))}GB")
    print(f"Target OS      : {platform.system()} {platform.release()}")
    print(f"Python version  : {platform.python_version()}")
    print("-" * 85 + "\n")


# main execution and test suite loop
if __name__ == "__main__":
    print_hardware_profile()

    print(f"{'TEST NAME': <20} | {'EMPTY BOXES': <12} | {'TIME (ms)': <12} | {'BACKTRACKING': <12} | {'STATUS'}")
    print("-" * 85)

    # Loops through each puzzle in the test suite, runs benchmarks, and prints results
    for name, board_data in TEST_SUITES.items():
        board_copy = [row[:] for row in board_data]
        empty_count = count_empty_boxes(board_copy)

        metrics = backtracking_search(board_copy)

        status = "Solved" if metrics["success"] else "Failed"
        print(f"{name: <20} | {empty_count: <12} | {metrics['time_required_ms']: <12} | {metrics['backtrack_count']: <12} | {status}")
    
    print("-" * 85)