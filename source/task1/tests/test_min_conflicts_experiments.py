
import csv

from nqueens.min_conflicts_experiments import (
    MinConflictsExperimentRunner
)


def test_experiment_runner_creates_output_files(tmp_path):
    runner = MinConflictsExperimentRunner(
        n_values=[4, 5],
        repetitions=2,
        max_steps=1000,
        max_restarts=2,
        base_seed=123
    )

    raw_path, summary_path, environment_path = (
        runner.run(output_dir=tmp_path)
    )

    assert raw_path.exists()
    assert summary_path.exists()
    assert environment_path.exists()


def test_experiment_runner_records_both_strategies(tmp_path):
    runner = MinConflictsExperimentRunner(
        n_values=[4, 5],
        repetitions=2,
        max_steps=1000,
        max_restarts=2
    )

    raw_path, _, _ = runner.run(
        output_dir=tmp_path
    )

    with raw_path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    # 2 values of N x 2 repetitions x 2 strategies.
    assert len(rows) == 8

    strategies = {
        row["strategy"] for row in rows
    }

    assert strategies == {
        "random",
        "most_conflicted"
    }


def test_experiment_runner_uses_paired_initial_states(tmp_path):
    runner = MinConflictsExperimentRunner(
        n_values=[4],
        repetitions=3,
        max_steps=1000,
        max_restarts=2
    )

    raw_path, _, _ = runner.run(
        output_dir=tmp_path
    )

    with raw_path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    for trial in range(1, 4):
        pair = [
            row for row in rows
            if int(row["trial"]) == trial
        ]

        assert len(pair) == 2

        assert (
            pair[0]["initial_positions"]
            == pair[1]["initial_positions"]
        )

        assert (
            pair[0]["initial_seed"]
            == pair[1]["initial_seed"]
        )


def test_experiment_summary_contains_expected_fields(tmp_path):
    runner = MinConflictsExperimentRunner(
        n_values=[4],
        repetitions=2,
        max_steps=1000,
        max_restarts=2
    )

    _, summary_path, _ = runner.run(
        output_dir=tmp_path
    )

    with summary_path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2

    for row in rows:
        assert "success_rate_percent" in row
        assert "mean_steps_successful_only" in row
        assert "median_time_seconds" in row
        assert "mean_restarts" in row
