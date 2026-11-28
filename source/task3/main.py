
from collections import Counter
from time import perf_counter

from source.task3.kakuro.puzzle import build_puzzle
from source.task3.kakuro.solver import solve, validate_solution


def print_solution(puzzle, solution):
    """Display the solved Kakuro board."""

    print("\nSolved Kakuro board:")
    print("-" * (puzzle.size * 4))

    for row_index, row in enumerate(puzzle.grid_layout, start=1):
        output = []

        for col_index, symbol in enumerate(row, start=1):
            if symbol == "#":
                output.append("###")
            else:
                value = solution.get((row_index, col_index), 0)
                output.append(f"{value:3d}")

        print(" ".join(output))

    print("-" * (puzzle.size * 4))


def main():
    puzzle = build_puzzle()

    print("=" * 55)
    print("KAKURO CSP SOLVER")
    print("=" * 55)

    print(f"Board size       : {puzzle.size} x {puzzle.size}")
    print(f"White variables  : {len(puzzle.white_cells)}")
    print(f"Across runs      : {sum(r.direction.value == 'across' for r in puzzle.runs)}")
    print(f"Down runs        : {sum(r.direction.value == 'down' for r in puzzle.runs)}")

    print("\nStarting Backtracking Search...")

    start_time = perf_counter()

    result = solve(
        puzzle,
        max_nodes=100_000,
    )

    elapsed = perf_counter() - start_time

    print("\n" + "=" * 55)
    print("SOLVER RESULTS")
    print("=" * 55)

    print(f"Solved           : {result.solved}")
    print(f"Nodes explored   : {result.nodes_explored}")
    print(f"Backtracks       : {result.backtracks}")
    print(f"Maximum depth    : {result.max_depth}")
    print(f"Search time      : {elapsed:.6f} seconds")
    print(f"Search limit     : {result.limit_reached}")

    event_counts = Counter(
        event.event_type for event in result.events
    )

    print("\nSearch event statistics:")

    for event_type, count in sorted(event_counts.items()):
        print(f"  {event_type:20s}: {count}")

    if result.solved:
        valid = validate_solution(puzzle, result.solution)

        print(f"\nIndependent validation: {valid}")

        if valid:
            print_solution(puzzle, result.solution)
        else:
            print("ERROR: The returned solution is invalid.")

    elif result.limit_reached:
        print("\nSearch stopped because the node limit was reached.")

    else:
        print("\nNo valid solution was found.")

    print("\n" + "=" * 55)


if __name__ == "__main__":
    main()
