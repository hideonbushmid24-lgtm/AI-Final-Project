
import pytest

from nqueens.sat_solver import Glucose3NQueensSolver
from nqueens.validator import NQueensValidator


@pytest.mark.parametrize(
    "n",
    [1, 4, 5, 6, 8]
)
def test_sat_solver_finds_valid_solution(n):
    solver = Glucose3NQueensSolver()

    result = solver.solve(n)

    assert result.satisfiable is True
    assert result.positions is not None
    assert result.board is not None

    assert len(result.positions) == n
    assert NQueensValidator.is_valid_positions(
        result.positions, n
    )

    assert NQueensValidator.is_valid_board(
        result.board
    )


@pytest.mark.parametrize(
    "n",
    [2, 3]
)
def test_unsatisfiable_n_queens(n):
    solver = Glucose3NQueensSolver()

    result = solver.solve(n)

    assert result.satisfiable is False
    assert result.positions is None
    assert result.board is None


def test_sat_solver_returns_correct_clause_count():
    solver = Glucose3NQueensSolver()

    result = solver.solve(4)

    assert result.num_variables == 16
    assert result.num_clauses == 80


def test_solver_execution_times_are_non_negative():
    solver = Glucose3NQueensSolver()

    result = solver.solve(8)

    assert result.encoding_time_seconds >= 0
    assert result.solver_setup_time_seconds >= 0
    assert result.solve_time_seconds >= 0
    assert result.total_time_seconds >= 0


def test_solver_returns_statistics():
    solver = Glucose3NQueensSolver()

    result = solver.solve(8)

    assert isinstance(result.solver_stats, dict)
    assert "conflicts" in result.solver_stats
    assert "decisions" in result.solver_stats
    assert "propagations" in result.solver_stats
