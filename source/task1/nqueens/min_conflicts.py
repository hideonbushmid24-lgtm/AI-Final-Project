
import random
from dataclasses import dataclass
from time import perf_counter
from typing import Sequence

from nqueens.validator import NQueensValidator


@dataclass
class MinConflictsResult:
    """Store the result of a Min-Conflicts search."""

    n: int
    strategy: str
    solved: bool

    positions: list[int] | None
    board: list[list[int]] | None

    steps: int
    restarts: int
    elapsed_time_seconds: float


class MinConflictsSolver:
    """
    Solve N-Queens using Min-Conflicts.

    Representation:
        positions[row] = column containing the queen.

    Strategies:
        random:
            Select a random conflicted row.

        most_conflicted:
            Select a row whose queen has the largest
            number of attacking queens.
    """

    VALID_STRATEGIES = (
        "random",
        "most_conflicted"
    )

    def __init__(self, strategy: str = "random"):
        if strategy not in self.VALID_STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy}. "
                f"Expected one of {self.VALID_STRATEGIES}."
            )

        self.strategy = strategy

    @staticmethod
    def _validate_input(
        n: int,
        max_steps: int,
        max_restarts: int,
        initial_positions: Sequence[int] | None
    ) -> None:
        if (
            not isinstance(n, int)
            or isinstance(n, bool)
            or n < 1
        ):
            raise ValueError("N must be a positive integer.")

        if (
            not isinstance(max_steps, int)
            or isinstance(max_steps, bool)
            or max_steps < 1
        ):
            raise ValueError("max_steps must be >= 1.")

        if (
            not isinstance(max_restarts, int)
            or isinstance(max_restarts, bool)
            or max_restarts < 0
        ):
            raise ValueError("max_restarts must be >= 0.")

        if initial_positions is not None:
            if len(initial_positions) != n:
                raise ValueError(
                    "Initial positions must contain N values."
                )

            for col in initial_positions:
                if (
                    not isinstance(col, int)
                    or isinstance(col, bool)
                    or not 0 <= col < n
                ):
                    raise ValueError(
                        "Every initial column must be in [0, N-1]."
                    )

    @staticmethod
    def _build_counts(positions: list[int]):
        """
        Build conflict counters for columns and diagonals.
        """

        n = len(positions)

        column_counts = [0] * n
        diagonal_down = [0] * (2 * n - 1)
        diagonal_up = [0] * (2 * n - 1)

        offset = n - 1

        for row, col in enumerate(positions):
            column_counts[col] += 1

            diagonal_down[
                row - col + offset
            ] += 1

            diagonal_up[
                row + col
            ] += 1

        return (
            column_counts,
            diagonal_down,
            diagonal_up
        )

    @staticmethod
    def _count_conflicts(
        row: int,
        positions: list[int],
        column_counts: list[int],
        diagonal_down: list[int],
        diagonal_up: list[int],
        offset: int
    ) -> int:
        """Count attacking queens for a selected queen."""

        col = positions[row]

        return (
            column_counts[col] - 1
            + diagonal_down[row - col + offset] - 1
            + diagonal_up[row + col] - 1
        )

    def _select_variable(
        self,
        conflicted_rows: list[int],
        conflict_counts: dict[int, int],
        rng: random.Random
    ) -> int:
        """
        Select a conflicted row using the configured strategy.
        """

        if self.strategy == "random":
            return rng.choice(conflicted_rows)

        # Improved heuristic:
        # Select the queen involved in the most conflicts.
        maximum = max(
            conflict_counts[row]
            for row in conflicted_rows
        )

        candidates = [
            row
            for row in conflicted_rows
            if conflict_counts[row] == maximum
        ]

        # Random tie-breaking prevents deterministic bias.
        return rng.choice(candidates)

    @staticmethod
    def _make_result(
        n: int,
        strategy: str,
        solved: bool,
        positions: list[int] | None,
        steps: int,
        restarts: int,
        elapsed_time: float
    ) -> MinConflictsResult:

        board = None

        if solved and positions is not None:
            board = NQueensValidator.positions_to_board(
                positions
            )

        return MinConflictsResult(
            n=n,
            strategy=strategy,
            solved=solved,
            positions=positions,
            board=board,
            steps=steps,
            restarts=restarts,
            elapsed_time_seconds=elapsed_time
        )

    def solve(
        self,
        n: int,
        max_steps: int = 10000,
        max_restarts: int = 5,
        seed: int | None = None,
        initial_positions: Sequence[int] | None = None
    ) -> MinConflictsResult:
        """
        Solve N-Queens with randomized initial states.

        max_steps:
            Maximum number of moves per restart.

        max_restarts:
            Maximum number of additional random restarts.

        initial_positions:
            Optional shared initial assignment for fair comparison.
        """

        self._validate_input(
            n,
            max_steps,
            max_restarts,
            initial_positions
        )

        rng = random.Random(seed)

        start_time = perf_counter()

        total_steps = 0
        restarts_used = 0

        for restart_index in range(max_restarts + 1):

            # Use the same initial assignment for the first run
            # when comparing different selection strategies.
            if (
                restart_index == 0
                and initial_positions is not None
            ):
                positions = list(initial_positions)

            else:
                positions = [
                    rng.randrange(n)
                    for _ in range(n)
                ]

            (
                column_counts,
                diagonal_down,
                diagonal_up
            ) = self._build_counts(positions)

            offset = n - 1

            for step in range(max_steps + 1):

                conflict_counts = {}

                for row in range(n):
                    conflicts = self._count_conflicts(
                        row,
                        positions,
                        column_counts,
                        diagonal_down,
                        diagonal_up,
                        offset
                    )

                    if conflicts > 0:
                        conflict_counts[row] = conflicts

                # A solution has no conflicts.
                if not conflict_counts:
                    elapsed = perf_counter() - start_time

                    return self._make_result(
                        n=n,
                        strategy=self.strategy,
                        solved=True,
                        positions=list(positions),
                        steps=total_steps,
                        restarts=restarts_used,
                        elapsed_time=elapsed
                    )

                if step == max_steps:
                    break

                conflicted_rows = list(
                    conflict_counts.keys()
                )

                # Step 1: Select a conflicted variable.
                row = self._select_variable(
                    conflicted_rows,
                    conflict_counts,
                    rng
                )

                old_col = positions[row]

                # Step 2: Temporarily remove its queen.
                column_counts[old_col] -= 1

                diagonal_down[
                    row - old_col + offset
                ] -= 1

                diagonal_up[
                    row + old_col
                ] -= 1

                # Step 3: Calculate conflicts for every candidate.
                scores = []

                for col in range(n):
                    score = (
                        column_counts[col]
                        + diagonal_down[row - col + offset]
                        + diagonal_up[row + col]
                    )

                    scores.append(score)

                minimum = min(scores)

                # Step 4: Select a minimum-conflict value.
                best_columns = [
                    col
                    for col, score in enumerate(scores)
                    if score == minimum
                ]

                new_col = rng.choice(best_columns)

                # Step 5: Place the queen at the selected value.
                positions[row] = new_col

                column_counts[new_col] += 1

                diagonal_down[
                    row - new_col + offset
                ] += 1

                diagonal_up[
                    row + new_col
                ] += 1

                total_steps += 1

            # Restart with a new random assignment if necessary.
            if restart_index < max_restarts:
                restarts_used += 1

        elapsed = perf_counter() - start_time

        # Failure within the search budget does not prove UNSAT.
        return self._make_result(
            n=n,
            strategy=self.strategy,
            solved=False,
            positions=None,
            steps=total_steps,
            restarts=restarts_used,
            elapsed_time=elapsed
        )
