
from .model import (
    Clue,
    Direction,
    KakuroPuzzle,
    KakuroRun,
)


GRID_LAYOUT = (
    "####",
    "#...",
    "#...",
    "#...",
)

CLUES = {
    # Vertical clues
    (1, 2): Clue(down=14),
    (1, 3): Clue(down=10),
    (1, 4): Clue(down=19),

    # Horizontal clues
    (2, 1): Clue(across=12),
    (3, 1): Clue(across=16),
    (4, 1): Clue(across=15),
}


def build_backtracking_demo() -> KakuroPuzzle:
    """Build a small Kakuro puzzle that exercises backtracking."""

    runs = (
        KakuroRun(
            run_id="A-02-01",
            direction=Direction.ACROSS,
            target_sum=12,
            cells=((2, 2), (2, 3), (2, 4)),
        ),
        KakuroRun(
            run_id="A-03-01",
            direction=Direction.ACROSS,
            target_sum=16,
            cells=((3, 2), (3, 3), (3, 4)),
        ),
        KakuroRun(
            run_id="A-04-01",
            direction=Direction.ACROSS,
            target_sum=15,
            cells=((4, 2), (4, 3), (4, 4)),
        ),
        KakuroRun(
            run_id="D-01-02",
            direction=Direction.DOWN,
            target_sum=14,
            cells=((2, 2), (3, 2), (4, 2)),
        ),
        KakuroRun(
            run_id="D-01-03",
            direction=Direction.DOWN,
            target_sum=10,
            cells=((2, 3), (3, 3), (4, 3)),
        ),
        KakuroRun(
            run_id="D-01-04",
            direction=Direction.DOWN,
            target_sum=19,
            cells=((2, 4), (3, 4), (4, 4)),
        ),
    )

    puzzle = KakuroPuzzle(
        grid_layout=GRID_LAYOUT,
        clues=CLUES,
        runs=runs,
    )

    puzzle.validate()
    return puzzle
