
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

Coordinate = tuple[int, int]


class Direction(str, Enum):
    ACROSS = "across"
    DOWN = "down"


@dataclass(frozen=True, slots=True)
class Clue:
    """Sum clues associated with a blocked cell."""

    across: int | None = None
    down: int | None = None

    def __post_init__(self) -> None:
        if self.across is None and self.down is None:
            raise ValueError("A clue must contain an across or down sum.")

        for value in (self.across, self.down):
            if value is not None and not 1 <= value <= 45:
                raise ValueError("Kakuro clue sums must be between 1 and 45.")


@dataclass(frozen=True, slots=True)
class KakuroRun:
    """A horizontal or vertical group of white cells."""

    run_id: str
    direction: Direction
    target_sum: int
    cells: tuple[Coordinate, ...]

    def __post_init__(self) -> None:
        length = len(self.cells)

        if not 2 <= length <= 9:
            raise ValueError("A Kakuro run must contain 2 to 9 cells.")

        if len(set(self.cells)) != length:
            raise ValueError("A run cannot contain duplicate cells.")

        if not self.run_id.strip():
            raise ValueError("Run ID cannot be empty.")

        min_sum = length * (length + 1) // 2
        max_sum = length * (19 - length) // 2

        if not min_sum <= self.target_sum <= max_sum:
            raise ValueError(
                f"Impossible sum {self.target_sum} for "
                f"a run of {length} cells. "
                f"Expected {min_sum} to {max_sum}."
            )

        if any(row < 1 or col < 1 for row, col in self.cells):
            raise ValueError("Coordinates must use positive row and column numbers.")

        rows = {row for row, _ in self.cells}
        cols = [col for _, col in self.cells]

        if self.direction == Direction.ACROSS:
            if len(rows) != 1:
                raise ValueError("An across run must stay on one row.")

            if sorted(cols) != list(range(min(cols), max(cols) + 1)):
                raise ValueError("Across run cells must be contiguous.")

        elif self.direction == Direction.DOWN:
            row_values = [row for row, _ in self.cells]

            if len(set(cols)) != 1:
                raise ValueError("A down run must stay in one column.")

            if sorted(row_values) != list(
                range(min(row_values), max(row_values) + 1)
            ):
                raise ValueError("Down run cells must be contiguous.")


@dataclass(frozen=True, slots=True)
class KakuroPuzzle:
    """Complete Kakuro board definition."""

    grid_layout: tuple[str, ...]
    clues: Mapping[Coordinate, Clue]
    runs: tuple[KakuroRun, ...]

    @property
    def size(self) -> int:
        return len(self.grid_layout)

    @property
    def white_cells(self) -> frozenset[Coordinate]:
        return frozenset(
            (row_index, col_index)
            for row_index, row in enumerate(self.grid_layout, start=1)
            for col_index, cell in enumerate(row, start=1)
            if cell == "."
        )

    def validate(self) -> None:
        """Validate the board layout, clues, and run coverage."""

        if not self.grid_layout:
            raise ValueError("Puzzle grid cannot be empty.")

        size = self.size

        if any(len(row) != size for row in self.grid_layout):
            raise ValueError("Puzzle grid must be square.")

        if any(cell not in "#." for row in self.grid_layout for cell in row):
            raise ValueError("Grid cells must be '#' or '.'.")

        white_cells = self.white_cells

        for (row, col), clue in self.clues.items():
            if not (1 <= row <= size and 1 <= col <= size):
                raise ValueError(f"Clue coordinate is outside the board: {(row, col)}")

            if self.grid_layout[row - 1][col - 1] != "#":
                raise ValueError(f"Clue must be on a blocked cell: {(row, col)}")

            if not isinstance(clue, Clue):
                raise TypeError(f"Invalid clue at {(row, col)}.")

        expected_run_count = sum(
            int(clue.across is not None) + int(clue.down is not None)
            for clue in self.clues.values()
        )

        if len(self.runs) != expected_run_count:
            raise ValueError(
                f"Expected {expected_run_count} runs, got {len(self.runs)}."
            )

        coverage = {
            cell: {Direction.ACROSS: 0, Direction.DOWN: 0}
            for cell in white_cells
        }

        run_ids = set()

        for run in self.runs:
            if run.run_id in run_ids:
                raise ValueError(f"Duplicate run ID: {run.run_id}")

            run_ids.add(run.run_id)

            for cell in run.cells:
                if cell not in white_cells:
                    raise ValueError(
                        f"Run {run.run_id} contains a non-white cell: {cell}"
                    )

                coverage[cell][run.direction] += 1

        for cell, directions in coverage.items():
            for direction, count in directions.items():
                if count != 1:
                    raise ValueError(
                        f"Cell {cell} must belong to exactly one "
                        f"{direction.value} run; found {count}."
                    )
