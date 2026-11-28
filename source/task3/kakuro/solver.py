
from collections.abc import Mapping
from dataclasses import dataclass

from .model import Coordinate, KakuroPuzzle
from .propagation import propagate_domains


@dataclass(frozen=True, slots=True)
class SolverEvent:
    """One event recorded during Backtracking Search."""

    event_type: str
    depth: int
    cell: Coordinate | None = None
    value: int | None = None
    run_id: str | None = None
    removed_values: tuple[int, ...] = ()
    remaining_domain: tuple[int, ...] = ()
    message: str = ""
    domains_snapshot: tuple[
        tuple[Coordinate, tuple[int, ...]], ...
    ] = ()

@dataclass(frozen=True, slots=True)
class SolveResult:
    """Solution and search statistics."""

    solved: bool
    solution: dict[Coordinate, int]
    events: tuple[SolverEvent, ...]
    nodes_explored: int
    backtracks: int
    max_depth: int
    limit_reached: bool


def validate_solution(
    puzzle: KakuroPuzzle,
    solution: Mapping[Coordinate, int],
) -> bool:
    """Independently verify a complete Kakuro solution."""

    if set(solution) != set(puzzle.white_cells):
        return False

    if any(
        not isinstance(value, int) or not 1 <= value <= 9
        for value in solution.values()
    ):
        return False

    for run in puzzle.runs:
        values = [solution[cell] for cell in run.cells]

        if sum(values) != run.target_sum:
            return False

        if len(values) != len(set(values)):
            return False

    return True


def build_run_index(
    puzzle: KakuroPuzzle,
) -> dict[Coordinate, list[int]]:
    """Map each cell to the indexes of its Across and Down runs."""

    result = {
        cell: []
        for cell in puzzle.white_cells
    }

    for index, run in enumerate(puzzle.runs):
        for cell in run.cells:
            result[cell].append(index)

    return result


def select_variable_mrv_degree(
    domains: Mapping[Coordinate, set[int]],
    puzzle: KakuroPuzzle,
    runs_by_cell: Mapping[Coordinate, list[int]],
) -> Coordinate:
    """
    Select the next variable using:
    1. MRV: smallest remaining domain.
    2. Degree: most unassigned neighboring variables.
    3. Coordinate order for deterministic tie-breaking.
    """

    unassigned = [
        cell for cell, domain in domains.items()
        if len(domain) > 1
    ]

    if not unassigned:
        raise ValueError("There are no unassigned variables.")

    def ranking(cell: Coordinate) -> tuple[int, int, Coordinate]:
        neighbors = set()

        for run_index in runs_by_cell[cell]:
            run = puzzle.runs[run_index]

            for peer in run.cells:
                if peer != cell and len(domains[peer]) > 1:
                    neighbors.add(peer)

        return (
            len(domains[cell]),
            -len(neighbors),
            cell,
        )

    return min(unassigned, key=ranking)


def order_values_lcv(
    cell: Coordinate,
    domains: Mapping[Coordinate, set[int]],
    puzzle: KakuroPuzzle,
    runs_by_cell: Mapping[Coordinate, list[int]],
) -> list[int]:
    """
    Order candidate values using the Least Constraining Value heuristic.

    Impact is estimated by counting how many neighboring unassigned
    variables would lose the same digit because of the all-different
    constraint in a shared run.
    """

    neighbors = set()

    for run_index in runs_by_cell[cell]:
        for peer in puzzle.runs[run_index].cells:
            if peer != cell and len(domains[peer]) > 1:
                neighbors.add(peer)

    def impact(value: int) -> tuple[int, int]:
        eliminated = sum(
            value in domains[peer]
            for peer in neighbors
        )

        return eliminated, value

    return sorted(domains[cell], key=impact)


def solve(
    puzzle: KakuroPuzzle,
    initial_domains: Mapping[Coordinate, set[int]] | None = None,
    max_nodes: int | None = None,
) -> SolveResult:
    """
    Solve Kakuro using GAC propagation and Backtracking Search.

    Heuristics:
    - MRV
    - Degree
    - LCV

    nodes_explored counts attempted variable-value assignments.
    The input domains are never modified.
    """

    puzzle.validate()

    if max_nodes is not None and max_nodes < 1:
        raise ValueError("max_nodes must be at least 1 or None.")

    runs_by_cell = build_run_index(puzzle)
    events: list[SolverEvent] = []

    stats = {
        "nodes_explored": 0,
        "backtracks": 0,
        "max_depth": 0,
        "limit_reached": False,
    }

    found_solution: dict[Coordinate, int] = {}
    def snapshot_domains(domains):
        return tuple(
            (cell, tuple(sorted(values)))
            for cell, values in sorted(domains.items())
        )

    def record_propagation(
        propagation_events,
        depth: int,
    ) -> None:
        for event in propagation_events:
            events.append(
                SolverEvent(
                    event_type=event.event_type,
                    depth=depth,
                    cell=event.cell,
                    run_id=event.run_id,
                    removed_values=event.removed_values,
                    remaining_domain=event.remaining_domain,
                    message=event.message,
                )
            )

    def backtrack_search(
        current_domains: Mapping[Coordinate, set[int]],
        depth: int,
    ) -> bool:

        stats["max_depth"] = max(stats["max_depth"], depth)

        # First enforce GAC before choosing the next variable.
        propagation = propagate_domains(
            puzzle,
            initial_domains=current_domains,
        )

        record_propagation(propagation.events, depth)

        if not propagation.consistent:
            return False

        domains = propagation.domains

        # All variables are assigned: verify the complete solution.
        if all(len(domain) == 1 for domain in domains.values()):
            candidate = {
                cell: next(iter(domain))
                for cell, domain in domains.items()
            }

            if validate_solution(puzzle, candidate):
                found_solution.update(candidate)

                events.append(
                    SolverEvent(
                        event_type="solution",
                        depth=depth,
                        message="A valid Kakuro solution was found.",
                    )
                )

                return True

            events.append(
                SolverEvent(
                    event_type="invalid_solution",
                    depth=depth,
                    message="The completed assignment failed validation.",
                )
            )

            return False

        # MRV + Degree selects the next variable.
        cell = select_variable_mrv_degree(
            domains,
            puzzle,
            runs_by_cell,
        )

        # LCV orders candidate values.
        candidate_values = order_values_lcv(
            cell,
            domains,
            puzzle,
            runs_by_cell,
        )

        for value in candidate_values:
            if (
                max_nodes is not None
                and stats["nodes_explored"] >= max_nodes
            ):
                stats["limit_reached"] = True

                events.append(
                    SolverEvent(
                        event_type="search_limit",
                        depth=depth,
                        cell=cell,
                        message=(
                            f"Search stopped after "
                            f"{max_nodes} attempted assignments."
                        ),
                    )
                )

                return False

            stats["nodes_explored"] += 1

            events.append(
                SolverEvent(
                    event_type="decision",
                    depth=depth,
                    cell=cell,
                    value=value,
                    remaining_domain=tuple(sorted(domains[cell])),
                    message=f"Assign {value} to variable {cell}.",
                    domains_snapshot=snapshot_domains(domains),
                )
            )

            # Create an independent branch.
            branch_domains = {
                variable: set(domain)
                for variable, domain in domains.items()
            }

            branch_domains[cell] = {value}

            if backtrack_search(branch_domains, depth + 1):
                return True

            # Do not continue exploring after reaching the node limit.
            if stats["limit_reached"]:
                return False

            stats["backtracks"] += 1

            events.append(
                SolverEvent(
                    event_type="backtrack",
                    depth=depth,
                    cell=cell,
                    value=value,
                    message=(
                        f"Assignment {value} at {cell} failed. "
                        "Backtracking to the previous decision."
                    ),
                    domains_snapshot=snapshot_domains(domains),
                )
            )

        return False

    solved = backtrack_search(
        initial_domains or {},
        depth=0,
    )

    return SolveResult(
        solved=solved,
        solution=dict(found_solution),
        events=tuple(events),
        nodes_explored=stats["nodes_explored"],
        backtracks=stats["backtracks"],
        max_depth=stats["max_depth"],
        limit_reached=stats["limit_reached"],
    )
