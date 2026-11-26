
import pytest

from experiments.runner import (
    ALGORITHM_CLASSES,
    run_benchmark,
    validate_pairwise_scores,
    build_summary,
)


@pytest.fixture(scope="module")
def sample_records():
    """Run a small benchmark for testing."""

    return run_benchmark(
        scenario_names=["S2_Open"],
        depths=[2],
        repeats=1,
    )


def test_benchmark_runs_all_four_algorithms(sample_records):

    assert len(sample_records) == 4

    algorithms = {
        record["algorithm"]
        for record in sample_records
    }

    assert algorithms == set(ALGORITHM_CLASSES.keys())


def test_pairwise_scores_are_consistent(sample_records):

    # This function raises an error if corresponding
    # Minimax and Alpha-Beta scores do not match.
    validate_pairwise_scores(sample_records)


def test_summary_contains_statistics(sample_records):

    summaries = build_summary(sample_records)

    assert len(summaries) == 4

    for summary in summaries:

        assert summary["runs"] == 1

        assert summary["mean_wall_time_ms"] >= 0
        assert summary["mean_search_time_ms"] >= 0

        assert summary["mean_nodes_explored"] > 0


def test_invalid_depth_is_rejected():

    with pytest.raises(ValueError):

        run_benchmark(
            scenario_names=["S2_Open"],
            depths=[0],
            repeats=1,
        )


def test_invalid_repetitions_are_rejected():

    with pytest.raises(ValueError):

        run_benchmark(
            scenario_names=["S2_Open"],
            depths=[2],
            repeats=0,
        )
def test_benchmark_records_execution_order_and_seed():
    records = run_benchmark(
        scenario_names=["S2_Open"],
        depths=[2],
        repeats=2,
        seed=123,
    )

    # 1 scenario x 1 depth x 2 repetitions x 4 algorithms
    assert len(records) == 8

    assert all(record["random_seed"] == 123 for record in records)
    assert all(
        record["warmup_runs_per_algorithm"] == 1
        for record in records
    )

    for repetition in (1, 2):
        repetition_records = [
            record for record in records
            if record["repetition"] == repetition
        ]

        assert len(repetition_records) == 4
        assert sorted(
            record["execution_order"]
            for record in repetition_records
        ) == [1, 2, 3, 4]


def test_benchmark_execution_order_is_reproducible():
    first_run = run_benchmark(
        scenario_names=["S2_Open"],
        depths=[2],
        repeats=2,
        seed=42,
    )

    second_run = run_benchmark(
        scenario_names=["S2_Open"],
        depths=[2],
        repeats=2,
        seed=42,
    )

    first_order = [
        (
            record["repetition"],
            record["algorithm"],
            record["execution_order"],
        )
        for record in first_run
    ]

    second_order = [
        (
            record["repetition"],
            record["algorithm"],
            record["execution_order"],
        )
        for record in second_run
    ]

    assert first_order == second_order