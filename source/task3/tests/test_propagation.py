
import pytest

from source.task3.kakuro.model import (
    Clue,
    Direction,
    KakuroPuzzle,
    KakuroRun,
)
from source.task3.kakuro.puzzle import build_puzzle
from source.task3.kakuro.propagation import (
    create_initial_domains,
    propagate_domains,
)


def create_small_puzzle():
    """Create a 3x3 Kakuro puzzle with a unique solution."""

    return KakuroPuzzle(
        grid_layout=(
            "###",
            "#..",
            "#..",
        ),
        clues={
            (1, 2): Clue(down=4),
            (1, 3): Clue(down=3),
            (2, 1): Clue(across=3),
            (3, 1): Clue(across=4),
        },
        runs=(
            KakuroRun(
                "A-02-01",
                Direction.ACROSS,
                3,
                ((2, 2), (2, 3)),
            ),
            KakuroRun(
                "A-03-01",
                Direction.ACROSS,
                4,
                ((3, 2), (3, 3)),
            ),
            KakuroRun(
                "D-01-02",
                Direction.DOWN,
                4,
                ((2, 2), (3, 2)),
            ),
            KakuroRun(
                "D-01-03",
                Direction.DOWN,
                3,
                ((2, 3), (3, 3)),
            ),
        ),
    )


def test_initial_domains_contain_digits_one_to_nine():
    puzzle = create_small_puzzle()
    domains = create_initial_domains(puzzle)

    assert len(domains) == 4

    for domain in domains.values():
        assert domain == set(range(1, 10))


def test_propagation_reduces_domains_to_unique_solution():
    puzzle = create_small_puzzle()

    result = propagate_domains(
        puzzle,
        initial_domains={
            (2, 2): {1},
        },
    )

    assert result.consistent is True

    assert result.domains == {
        (2, 2): {1},
        (2, 3): {2},
        (3, 2): {3},
        (3, 3): {1},
    }

    assert len(result.events) > 0
    assert all(
        event.event_type == "domain_pruned"
        for event in result.events
    )


def test_propagation_detects_contradiction():
    puzzle = create_small_puzzle()

    result = propagate_domains(
        puzzle,
        initial_domains={
            (2, 2): {2},
        },
    )

    assert result.consistent is False

    assert any(
        event.event_type == "contradiction"
        for event in result.events
    )


def test_initial_domains_are_not_modified():
    puzzle = create_small_puzzle()

    initial_domains = {
        (2, 2): {1},
    }

    original = {
        cell: set(values)
        for cell, values in initial_domains.items()
    }

    propagate_domains(puzzle, initial_domains)

    assert initial_domains == original


def test_non_white_cell_domain_is_rejected():
    puzzle = create_small_puzzle()

    with pytest.raises(ValueError):
        propagate_domains(
            puzzle,
            initial_domains={
                (1, 1): {1},
            },
        )


def test_invalid_digit_is_rejected():
    puzzle = create_small_puzzle()

    with pytest.raises(ValueError):
        propagate_domains(
            puzzle,
            initial_domains={
                (2, 2): {0},
            },
        )


def test_reference_board_has_no_immediate_contradiction():
    puzzle = build_puzzle()
    result = propagate_domains(puzzle)

    assert result.consistent is True
    assert set(result.domains) == set(puzzle.white_cells)

    for domain in result.domains.values():
        assert domain
        assert domain.issubset(set(range(1, 10)))
