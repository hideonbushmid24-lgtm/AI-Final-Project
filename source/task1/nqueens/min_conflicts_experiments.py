
import csv
import os
import platform
import random
import statistics

from pathlib import Path
from typing import Iterable

from nqueens.min_conflicts import MinConflictsSolver


class MinConflictsExperimentRunner:
    """
    Compare Standard and Improved Min-Conflicts.

    Both algorithms receive the same initial assignment
    for each paired experiment.
    """

    STRATEGIES = (
        "random",
        "most_conflicted"
    )

    RAW_FIELDS = [
        "n",
        "trial",
        "strategy",
        "initial_seed",
        "solver_seed",
        "initial_positions",
        "success",
        "steps",
        "restarts",
        "elapsed_time_seconds"
    ]

    def __init__(
        self,
        n_values: Iterable[int],
        repetitions: int = 30,
        max_steps: int = 10000,
        max_restarts: int = 5,
        base_seed: int = 20261124
    ):
        self.n_values = list(n_values)
        self.repetitions = repetitions
        self.max_steps = max_steps
        self.max_restarts = max_restarts
        self.base_seed = base_seed

        if not self.n_values:
            raise ValueError("N values cannot be empty.")

        if any(
            not isinstance(n, int)
            or isinstance(n, bool)
            or n < 4
            for n in self.n_values
        ):
            raise ValueError("All N values must be >= 4.")

        if self.n_values != sorted(set(self.n_values)):
            raise ValueError(
                "N values must be unique and ascending."
            )

        if (
            not isinstance(repetitions, int)
            or isinstance(repetitions, bool)
            or repetitions < 1
        ):
            raise ValueError("Repetitions must be >= 1.")

        if (
            not isinstance(max_steps, int)
            or isinstance(max_steps, bool)
            or max_steps < 1
        ):
            raise ValueError("max_steps must be >= 1.")

        if (
            not isinstance(max_restarts, int)
            or isinstance(max_restarts, bool)
            or max_restarts < 0
        ):
            raise ValueError("max_restarts must be >= 0.")

    @staticmethod
    def _output_directory() -> Path:
        """Locate source/results/task1."""
        project_root = Path(__file__).resolve().parents[3]

        return (
            project_root
            / "source"
            / "results"
            / "task1"
        )

    def _generate_initial_positions(
        self,
        n: int,
        initial_seed: int
    ) -> list[int]:
        """Create one shared initial state for a trial."""
        rng = random.Random(initial_seed)

        return [
            rng.randrange(n)
            for _ in range(n)
        ]

    def _run_one(
        self,
        n: int,
        trial: int,
        strategy: str,
        initial_positions: list[int],
        initial_seed: int
    ) -> dict:
        """Run one algorithm on a supplied initial state."""

        # Different deterministic random streams are used
        # for each strategy's tie-breaking decisions.
        strategy_offset = (
            0 if strategy == "random" else 1
        )

        solver_seed = (
            initial_seed + 100 + strategy_offset
        )

        solver = MinConflictsSolver(
            strategy=strategy
        )

        result = solver.solve(
            n=n,
            max_steps=self.max_steps,
            max_restarts=self.max_restarts,
            seed=solver_seed,
            initial_positions=initial_positions
        )

        return {
            "n": n,
            "trial": trial,
            "strategy": strategy,
            "initial_seed": initial_seed,
            "solver_seed": solver_seed,
            "initial_positions": ";".join(
                str(value)
                for value in initial_positions
            ),
            "success": result.solved,
            "steps": result.steps,
            "restarts": result.restarts,
            "elapsed_time_seconds":
                result.elapsed_time_seconds
        }

    def _write_raw(
        self,
        rows: list[dict],
        output_path: Path
    ):
        with output_path.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self.RAW_FIELDS
            )

            writer.writeheader()
            writer.writerows(rows)

    def _build_summary(
        self,
        rows: list[dict]
    ) -> list[dict]:
        summary = []

        for n in self.n_values:
            for strategy in self.STRATEGIES:

                group = [
                    row for row in rows
                    if row["n"] == n
                    and row["strategy"] == strategy
                ]

                successful = [
                    row for row in group
                    if row["success"]
                ]

                all_steps = [
                    row["steps"] for row in group
                ]

                successful_steps = [
                    row["steps"] for row in successful
                ]

                times = [
                    row["elapsed_time_seconds"]
                    for row in group
                ]

                restarts = [
                    row["restarts"]
                    for row in group
                ]

                success_count = len(successful)
                run_count = len(group)

                summary.append({
                    "n": n,
                    "strategy": strategy,
                    "runs": run_count,
                    "successful_runs": success_count,

                    "success_rate_percent":
                        success_count / run_count * 100,

                    "mean_steps_all_runs":
                        statistics.mean(all_steps),

                    "median_steps_all_runs":
                        statistics.median(all_steps),

                    "mean_steps_successful_only":
                        statistics.mean(successful_steps)
                        if successful_steps else "",

                    "median_steps_successful_only":
                        statistics.median(successful_steps)
                        if successful_steps else "",

                    "mean_time_seconds":
                        statistics.mean(times),

                    "median_time_seconds":
                        statistics.median(times),

                    "mean_restarts":
                        statistics.mean(restarts)
                })

        return summary

    @staticmethod
    def _write_summary(
        summary: list[dict],
        output_path: Path
    ):
        with output_path.open(
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(summary[0].keys())
            )

            writer.writeheader()
            writer.writerows(summary)

    def _write_environment(
        self,
        output_path: Path
    ):
        information = [
            "MIN-CONFLICTS EXPERIMENT ENVIRONMENT",
            f"Operating system: {platform.platform()}",
            f"Python version: {platform.python_version()}",
            f"Processor: {platform.processor()}",
            f"Architecture: {platform.machine()}",
            f"CPU count: {os.cpu_count()}",
            f"N values: {self.n_values}",
            f"Repetitions: {self.repetitions}",
            f"Maximum steps per restart: {self.max_steps}",
            f"Maximum restarts: {self.max_restarts}",
            f"Base seed: {self.base_seed}",
            "Strategies: random, most_conflicted",
            "Both strategies use identical initial assignments."
        ]

        output_path.write_text(
            "\n".join(information) + "\n",
            encoding="utf-8"
        )

    def run(
        self,
        output_dir: Path | None = None
    ):
        """Execute all paired experiments."""

        if output_dir is None:
            output_dir = self._output_directory()
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        raw_rows = []

        total_runs = (
            len(self.n_values)
            * self.repetitions
            * len(self.STRATEGIES)
        )

        completed = 0

        for n in self.n_values:
            print(f"\n========== N = {n} ==========")

            for trial in range(1, self.repetitions + 1):

                initial_seed = (
                    self.base_seed
                    + n * 100000
                    + trial
                )

                initial_positions = (
                    self._generate_initial_positions(
                        n,
                        initial_seed
                    )
                )

                # Each pair receives the same initial assignment.
                for strategy in self.STRATEGIES:

                    result = self._run_one(
                        n=n,
                        trial=trial,
                        strategy=strategy,
                        initial_positions=initial_positions,
                        initial_seed=initial_seed
                    )

                    raw_rows.append(result)
                    completed += 1

                    print(
                        f"{strategy:16s} | "
                        f"Trial {trial:02d}/{self.repetitions} | "
                        f"Success={result['success']} | "
                        f"Steps={result['steps']} | "
                        f"Restarts={result['restarts']} | "
                        f"Time={result['elapsed_time_seconds']:.6f}s"
                    )

        summary = self._build_summary(raw_rows)

        raw_path = output_dir / "min_conflicts_raw.csv"
        summary_path = output_dir / "min_conflicts_summary.csv"
        environment_path = (
            output_dir / "min_conflicts_environment.txt"
        )

        self._write_raw(raw_rows, raw_path)
        self._write_summary(summary, summary_path)
        self._write_environment(environment_path)

        print("\n========== FINAL SUMMARY ==========")

        for row in summary:
            print(
                f"N={row['n']:3d} | "
                f"{row['strategy']:16s} | "
                f"Success={row['success_rate_percent']:.1f}% | "
                f"Median Steps="
                f"{row['median_steps_successful_only']} | "
                f"Median Time="
                f"{row['median_time_seconds']:.6f}s"
            )

        print("\nAll experiments completed.")
        print(f"Total runs: {completed}")
        print(f"Raw: {raw_path}")
        print(f"Summary: {summary_path}")
        print(f"Environment: {environment_path}")

        return raw_path, summary_path, environment_path
