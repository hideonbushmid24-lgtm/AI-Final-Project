
import random
import pytest

from nqueens.min_conflicts import MinConflictsSolver
from nqueens.validator import NQueensValidator


@pytest.mark.parametrize(
    "n",
    [4, 8, 20]
)
@pytest.mark.parametrize(
    "strategy",
    ["random", "most_conflicted"]
)
def test_min_conflicts_finds_valid_solution(n, strategy):
    rng = random.Random(123 + n)

    initial_positions = [
        rng.randrange(n)
        for _ in range(n)
    ]

    solver = MinConflictsSolver(
        strategy=strategy
    )

    result = solver.solve(
        n=n,
        max_steps=10000,
        max_restarts=5,
        seed=42,
        initial_positions=initial_positions
    )

    assert result.solved is True
    assert result.positions is not None
    assert result.board is not None

    assert NQueensValidator.is_valid_positions(
        result.positions, n
    )

    assert NQueensValidator.is_valid_board(
        result.board
    )

    assert result.steps >= 0
    assert result.restarts >= 0


def test_min_conflicts_accepts_existing_solution():
    solver = MinConflictsSolver(
        strategy="random"
    )

    result = solver.solve(
        n=4,
        initial_positions=[1, 3, 0, 2]
    )

    assert result.solved is True
    assert result.steps == 0
    assert result.restarts == 0


def test_min_conflicts_respects_step_limit():
    solver = MinConflictsSolver(
        strategy="random"
    )

    result = solver.solve(
        n=4,
        max_steps=1,
        max_restarts=0,
        seed=42,
        initial_positions=[0, 0, 0, 0]
    )

    assert result.solved is False
    assert result.steps == 1
    assert result.restarts == 0


def test_invalid_strategy():
    with pytest.raises(ValueError):
        MinConflictsSolver(strategy="unknown")


def test_invalid_board_size():
    solver = MinConflictsSolver()

    with pytest.raises(ValueError):
        solver.solve(n=0)


def test_invalid_initial_positions():
    solver = MinConflictsSolver()

    with pytest.raises(ValueError):
        solver.solve(
            n=4,
            initial_positions=[0, 1, 2]
        )


def test_invalid_step_limit():
    solver = MinConflictsSolver()

    with pytest.raises(ValueError):
        solver.solve(
            n=4,
            max_steps=0
        )
