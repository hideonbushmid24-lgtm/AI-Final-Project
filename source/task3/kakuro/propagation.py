
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass

from .constraints import DIGITS, iter_valid_assignments
from .model import Coordinate, KakuroPuzzle


@dataclass(frozen=True, slots=True)
class PropagationEvent:
    """One recorded event during constraint propagation."""

    event_type: str
    run_id: str
    cell: Coordinate | None = None
    removed_values: tuple[int, ...] = ()
    remaining_domain: tuple[int, ...] = ()
    message: str = ""


@dataclass(frozen=True, slots=True)
class PropagationResult:
    """Result and trace of a constraint propagation operation."""

    consistent: bool
    domains: dict[Coordinate, set[int]]
    events: tuple[PropagationEvent, ...]


def create_initial_domains(
    puzzle: KakuroPuzzle,
) -> dict[Coordinate, set[int]]:
    """Give every white cell the initial domain {1, ..., 9}."""

    return {
        cell: set(DIGITS)
        for cell in puzzle.white_cells
    }


def propagate_domains(
    puzzle: KakuroPuzzle,
    initial_domains: Mapping[Coordinate, set[int]] | None = None,
) -> PropagationResult:
    """
    Enforce generalized arc consistency on all Kakuro runs.

    A value remains in a variable's domain only if it participates
    in at least one valid assignment of its Across/Down run.

    The process repeats until no domain changes or a contradiction
    is detected. The input domains are never modified.
    """

    puzzle.validate()

    domains = create_initial_domains(puzzle)
    white_cells = puzzle.white_cells

    if initial_domains is not None:
        for cell, values in initial_domains.items():
            if cell not in white_cells:
                raise ValueError(
                    f"Initial domain refers to a non-white cell: {cell}"
                )

            domain = set(values)
            invalid_values = domain - DIGITS

            if invalid_values:
                raise ValueError(
                    f"Invalid values at {cell}: {sorted(invalid_values)}"
                )

            domains[cell] = domain

    runs = puzzle.runs
    events: list[PropagationEvent] = []

    # Find all constraints that contain each variable.
    runs_by_cell: dict[Coordinate, list[int]] = {
        cell: []
        for cell in white_cells
    }

    for run_index, run in enumerate(runs):
        for cell in run.cells:
            runs_by_cell[cell].append(run_index)

    # Start by processing every constraint.
    queue = deque(range(len(runs)))
    queued = set(range(len(runs)))

    while queue:
        run_index = queue.popleft()
        queued.remove(run_index)

        run = runs[run_index]

        # Find values that appear in at least one valid assignment.
        supported_values = {
            cell: set()
            for cell in run.cells
        }

        has_valid_assignment = False

        for assignment in iter_valid_assignments(run, domains):
            has_valid_assignment = True

            for cell, value in zip(run.cells, assignment):
                supported_values[cell].add(value)

        # No assignment satisfies this constraint.
        if not has_valid_assignment:
            events.append(
                PropagationEvent(
                    event_type="contradiction",
                    run_id=run.run_id,
                    message=(
                        f"No valid assignment satisfies run {run.run_id}."
                    ),
                )
            )

            return PropagationResult(
                consistent=False,
                domains=domains,
                events=tuple(events),
            )

        # Remove values that have no supporting assignment.
        for cell in run.cells:
            unsupported = domains[cell] - supported_values[cell]

            if not unsupported:
                continue

            domains[cell] -= unsupported

            events.append(
                PropagationEvent(
                    event_type="domain_pruned",
                    run_id=run.run_id,
                    cell=cell,
                    removed_values=tuple(sorted(unsupported)),
                    remaining_domain=tuple(sorted(domains[cell])),
                    message=(
                        f"Removed {sorted(unsupported)} from {cell}; "
                        f"remaining domain: {sorted(domains[cell])}."
                    ),
                )
            )

            # A changed variable also belongs to another run.
            # That neighboring constraint must be checked again.
            for neighbor_index in runs_by_cell[cell]:
                if neighbor_index == run_index:
                    continue

                if neighbor_index not in queued:
                    queue.append(neighbor_index)
                    queued.add(neighbor_index)

    return PropagationResult(
        consistent=True,
        domains=domains,
        events=tuple(events),
    )
