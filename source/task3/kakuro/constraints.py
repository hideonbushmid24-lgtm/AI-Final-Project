
from collections.abc import Iterator, Mapping
from itertools import combinations

from .model import Coordinate, KakuroRun


DIGITS = frozenset(range(1, 10))


def valid_digit_combinations(
    length: int,
    target_sum: int,
) -> tuple[tuple[int, ...], ...]:
    """
    Generate all distinct-digit combinations whose sum equals target_sum.

    The order of digits does not matter in this function.
    Example: length=2, target_sum=10 includes (1, 9), (2, 8), ...
    """

    if not 1 <= length <= 9:
        raise ValueError("Combination length must be between 1 and 9.")

    return tuple(
        combination
        for combination in combinations(range(1, 10), length)
        if sum(combination) == target_sum
    )


def iter_valid_assignments(
    run: KakuroRun,
    domains: Mapping[Coordinate, set[int]],
) -> Iterator[tuple[int, ...]]:
    """
    Generate valid ordered assignments for a Kakuro run.

    Every returned tuple:
    - follows the cell order in run.cells;
    - uses values from the corresponding variable domains;
    - contains no repeated digit;
    - sums exactly to run.target_sum.
    """

    missing_cells = [
        cell for cell in run.cells
        if cell not in domains
    ]

    if missing_cells:
        raise ValueError(f"Missing domains for cells: {missing_cells}")

    cell_domains = []

    for cell in run.cells:
        domain = set(domains[cell])

        if not domain.issubset(DIGITS):
            raise ValueError(
                f"Invalid digit domain at {cell}: {domain}"
            )

        if not domain:
            return

        cell_domains.append(domain)

    # Assign variables with smaller domains first.
    variable_order = sorted(
        range(len(run.cells)),
        key=lambda index: len(cell_domains[index]),
    )

    assignment = [0] * len(run.cells)

    def backtrack(
        depth: int,
        used_digits: set[int],
        current_sum: int,
    ) -> Iterator[tuple[int, ...]]:

        if depth == len(variable_order):
            if current_sum == run.target_sum:
                yield tuple(assignment)
            return

        variable_index = variable_order[depth]

        for digit in sorted(cell_domains[variable_index] - used_digits):
            next_sum = current_sum + digit

            if next_sum > run.target_sum:
                continue

            next_used = used_digits | {digit}
            remaining_indices = variable_order[depth + 1:]
            remaining_count = len(remaining_indices)

            if remaining_count:
                available_digits = set().union(
                    *(cell_domains[index] for index in remaining_indices)
                ) - next_used

                if len(available_digits) < remaining_count:
                    continue

                sorted_available = sorted(available_digits)

                minimum_possible = sum(
                    sorted_available[:remaining_count]
                )

                maximum_possible = sum(
                    sorted_available[-remaining_count:]
                )

                if next_sum + minimum_possible > run.target_sum:
                    continue

                if next_sum + maximum_possible < run.target_sum:
                    continue

            assignment[variable_index] = digit

            yield from backtrack(
                depth + 1,
                next_used,
                next_sum,
            )

            assignment[variable_index] = 0

    yield from backtrack(
        depth=0,
        used_digits=set(),
        current_sum=0,
    )
