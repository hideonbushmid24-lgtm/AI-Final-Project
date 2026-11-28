
from .model import (
    Clue,
    Direction,
    KakuroPuzzle,
    KakuroRun,
)

# '#' = blocked/clue cell
# '.' = white cell
# Coordinates are 1-based.

GRID_LAYOUT = (
    "#########",
    "##...#..#",
    "##.......",
    "#..##....",
    "#..#....#",
    "##....#..",
    "#....##..",
    "#.......#",
    "##..#...#",
)

# (row, column): Clue(across_sum, down_sum)
CLUES = {
    # Row 1
    (1, 3): Clue(down=44),
    (1, 4): Clue(down=16),
    (1, 5): Clue(down=9),
    (1, 7): Clue(down=15),
    (1, 8): Clue(down=44),

    # Row 2
    (2, 2): Clue(across=22),
    (2, 6): Clue(across=3, down=11),
    (2, 9): Clue(down=14),

    # Row 3
    (3, 2): Clue(across=28, down=17),

    # Row 4
    (4, 1): Clue(across=14),
    (4, 5): Clue(across=20, down=12),

    # Row 5
    (5, 1): Clue(across=17),
    (5, 4): Clue(across=22, down=29),
    (5, 9): Clue(down=7),

    # Row 6
    (6, 2): Clue(across=28, down=12),
    (6, 7): Clue(across=12),

    # Row 7
    (7, 1): Clue(across=14),
    (7, 6): Clue(down=7),
    (7, 7): Clue(across=6, down=12),

    # Row 8
    (8, 1): Clue(across=39),

    # Row 9
    (9, 2): Clue(across=16),
    (9, 5): Clue(across=8),
}


def build_puzzle() -> KakuroPuzzle:
    """Build all horizontal and vertical runs from the board clues."""

    white_cells = {
        (row, col)
        for row, line in enumerate(GRID_LAYOUT, start=1)
        for col, symbol in enumerate(line, start=1)
        if symbol == "."
    }

    runs = []

    for (row, col), clue in sorted(CLUES.items()):

        if clue.across is not None:
            cells = []
            next_col = col + 1

            while (row, next_col) in white_cells:
                cells.append((row, next_col))
                next_col += 1

            runs.append(
                KakuroRun(
                    run_id=f"A-{row:02d}-{col:02d}",
                    direction=Direction.ACROSS,
                    target_sum=clue.across,
                    cells=tuple(cells),
                )
            )

        if clue.down is not None:
            cells = []
            next_row = row + 1

            while (next_row, col) in white_cells:
                cells.append((next_row, col))
                next_row += 1

            runs.append(
                KakuroRun(
                    run_id=f"D-{row:02d}-{col:02d}",
                    direction=Direction.DOWN,
                    target_sum=clue.down,
                    cells=tuple(cells),
                )
            )

    puzzle = KakuroPuzzle(
        grid_layout=GRID_LAYOUT,
        clues=CLUES,
        runs=tuple(runs),
    )

    puzzle.validate()
    return puzzle
