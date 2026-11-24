
import csv

from nqueens.experiments import Glucose3ExperimentRunner


def test_experiment_runner_creates_result_files(tmp_path):
    runner = Glucose3ExperimentRunner(
        n_values=[4, 5],
        repetitions=2
    )

    raw_path, summary_path, environment_path = (
        runner.run(output_dir=tmp_path)
    )

    assert raw_path.exists()
    assert summary_path.exists()
    assert environment_path.exists()


def test_raw_results_contain_all_trials(tmp_path):
    runner = Glucose3ExperimentRunner(
        n_values=[4, 5],
        repetitions=2
    )

    raw_path, _, _ = runner.run(
        output_dir=tmp_path
    )

    with raw_path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 4

    assert {
        int(row["n"])
        for row in rows
    } == {4, 5}


def test_summary_contains_correct_clause_counts(tmp_path):
    runner = Glucose3ExperimentRunner(
        n_values=[4, 5],
        repetitions=2
    )

    _, summary_path, _ = runner.run(
        output_dir=tmp_path
    )

    with summary_path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    clause_counts = {
        int(row["n"]): int(row["num_clauses"])
        for row in rows
    }

    assert clause_counts == {
        4: 80,
        5: 165
    }

    assert all(
        int(row["runs"]) == 2
        for row in rows
    )
