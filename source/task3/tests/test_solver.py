
import pytest
from source.task3.kakuro.puzzle import build_puzzle
from source.task3.kakuro.demo_puzzle import build_backtracking_demo
from source.task3.kakuro.model import (
    Clue,
    Direction,
    KakuroPuzzle,
    KakuroRun,
)
from source.task3.kakuro.solver import (
    solve,
    validate_solution,
)


def create_ambiguous_puzzle():
    """Create a 2x2 white-cell puzzle with multiple valid solutions."""

    puzzle = KakuroPuzzle(
        grid_layout=(
            "###",
            "#..",
            "#..",
        ),
        clues={
            (1, 2): Clue(down=5),
            (1, 3): Clue(down=5),
            (2, 1): Clue(across=5),
            (3, 1): Clue(across=5),
        },
        runs=(
            KakuroRun(
                "A-02-01",
                Direction.ACROSS,
                5,
                ((2, 2), (2, 3)),
            ),
            KakuroRun(
                "A-03-01",
                Direction.ACROSS,
                5,
                ((3, 2), (3, 3)),
            ),
            KakuroRun(
                "D-01-02",
                Direction.DOWN,
                5,
                ((2, 2), (3, 2)),
            ),
            KakuroRun(
                "D-01-03",
                Direction.DOWN,
                5,
                ((2, 3), (3, 3)),
            ),
        ),
    )

    puzzle.validate()
    return puzzle


def test_solver_finds_a_valid_solution():
    puzzle = create_ambiguous_puzzle()

    result = solve(puzzle)

    assert result.solved is True
    assert validate_solution(puzzle, result.solution)
    assert len(result.solution) == 4
    assert result.nodes_explored >= 1


def test_solver_uses_deterministic_heuristic_order():
    puzzle = create_ambiguous_puzzle()

    result = solve(puzzle)

    first_decision = next(
        event
        for event in result.events
        if event.event_type == "decision"
    )

    # MRV + Degree tie-breaks by coordinates.
    # LCV then tries the lowest-impact value first.
    assert first_decision.cell == (2, 2)
    assert first_decision.value == 1


def test_solver_detects_inconsistent_initial_domains():
    puzzle = create_ambiguous_puzzle()

    result = solve(
        puzzle,
        initial_domains={
            (2, 2): {9},
        },
    )

    assert result.solved is False
    assert result.solution == {}

    assert any(
        event.event_type == "contradiction"
        for event in result.events
    )


def test_solver_does_not_modify_initial_domains():
    puzzle = create_ambiguous_puzzle()

    initial_domains = {
        (2, 2): {1, 2, 3, 4},
    }

    original = {
        cell: set(values)
        for cell, values in initial_domains.items()
    }

    solve(puzzle, initial_domains)

    assert initial_domains == original


def test_solution_validator_rejects_duplicate_digits():
    puzzle = create_ambiguous_puzzle()

    invalid_solution = {
        (2, 2): 1,
        (2, 3): 1,
        (3, 2): 4,
        (3, 3): 4,
    }

    assert validate_solution(puzzle, invalid_solution) is False


def test_solver_rejects_invalid_node_limit():
    puzzle = create_ambiguous_puzzle()

    with pytest.raises(ValueError):
        solve(puzzle, max_nodes=0)


def test_solver_records_solution_event():
    puzzle = create_ambiguous_puzzle()

    result = solve(puzzle)

    assert any(
        event.event_type == "solution"
        for event in result.events
    )

def test_solver_solves_reference_9x9_puzzle():
    puzzle = build_puzzle()

    result = solve(puzzle, max_nodes=100_000)

    assert result.solved is True
    assert len(result.solution) == 48

    assert validate_solution(
        puzzle,
        result.solution,
    )

    assert any(
        event.event_type == "solution"
        for event in result.events
    )

def test_decision_event_contains_domain_snapshot():
    puzzle = create_ambiguous_puzzle()

    result = solve(puzzle)

    decision = next(
        event for event in result.events
        if event.event_type == "decision"
    )

    snapshot = dict(decision.domains_snapshot)

    assert snapshot
    assert snapshot[(2, 2)] == (1, 2, 3, 4)


def test_solver_performs_real_backtracking_on_demo_puzzle():
    puzzle = build_backtracking_demo()

    result = solve(
        puzzle,
        max_nodes=10_000,
    )

    assert result.solved is True
    assert validate_solution(puzzle, result.solution)

    assert result.nodes_explored > 0
    assert result.backtracks > 0

    assert any(
        event.event_type == "decision"
        for event in result.events
    )

    assert any(
        event.event_type == "backtrack"
        for event in result.events
    )

    assert any(
        event.event_type == "solution"
        for event in result.events
    )
