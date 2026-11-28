
import pytest

from source.task3.kakuro.model import Direction, KakuroRun
from source.task3.kakuro.puzzle import build_puzzle


def test_reference_board_dimensions_and_white_cells():
    puzzle = build_puzzle()

    assert puzzle.size == 9
    assert len(puzzle.white_cells) == 48


def test_reference_board_has_fourteen_runs_each_direction():
    puzzle = build_puzzle()

    across_runs = [
        run for run in puzzle.runs
        if run.direction == Direction.ACROSS
    ]

    down_runs = [
        run for run in puzzle.runs
        if run.direction == Direction.DOWN
    ]

    assert len(across_runs) == 14
    assert len(down_runs) == 14


def test_every_white_cell_has_one_across_and_one_down_run():
    puzzle = build_puzzle()

    for cell in puzzle.white_cells:
        across_count = sum(
            run.direction == Direction.ACROSS and cell in run.cells
            for run in puzzle.runs
        )

        down_count = sum(
            run.direction == Direction.DOWN and cell in run.cells
            for run in puzzle.runs
        )

        assert across_count == 1
        assert down_count == 1


def test_all_reference_run_sums_are_feasible():
    puzzle = build_puzzle()

    for run in puzzle.runs:
        length = len(run.cells)
        min_sum = length * (length + 1) // 2
        max_sum = length * (19 - length) // 2

        assert min_sum <= run.target_sum <= max_sum


def test_run_rejects_impossible_sum():
    with pytest.raises(ValueError):
        KakuroRun(
            run_id="A-TEST",
            direction=Direction.ACROSS,
            target_sum=2,
            cells=((1, 2), (1, 3)),
        )
