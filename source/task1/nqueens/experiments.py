
import csv
import platform
import statistics
from pathlib import Path
from typing import Iterable

from .sat_solver import Glucose3NQueensSolver


class Glucose3ExperimentRunner:
    """
    Run repeated N-Queens experiments using Glucose3.

    Raw measurements and summary statistics are saved separately.
    """

    RAW_FIELDS = [
        "n",
        "trial",
        "num_variables",
        "num_clauses",
        "satisfiable",
        "encoding_time_seconds",
        "solver_setup_time_seconds",
        "solve_time_seconds",
        "total_time_seconds",
        "conflicts",
        "decisions",
        "propagations",
        "restarts",
    ]

    def __init__(
        self,
        n_values: Iterable[int],
        repetitions: int = 10
    ):
        self.n_values = list(n_values)

        if not self.n_values:
            raise ValueError("N values cannot be empty.")

        if any(
            not isinstance(n, int)
            or isinstance(n, bool)
            or n < 4
            for n in self.n_values
        ):
            raise ValueError("All N values must be integers >= 4.")

        if self.n_values != sorted(set(self.n_values)):
            raise ValueError(
                "N values must be unique and in ascending order."
            )

        if (
            not isinstance(repetitions, int)
            or isinstance(repetitions, bool)
            or repetitions < 1
        ):
            raise ValueError("Repetitions must be a positive integer.")

        self.repetitions = repetitions

    @staticmethod
    def _get_output_directory() -> Path:
        """Return the Task 1 results directory."""
        project_root = Path(__file__).resolve().parents[3]

        return (
            project_root
            / "source"
            / "results"
            / "task1"
        )

    def _write_raw_results(
        self,
        rows: list[dict],
        output_path: Path
    ) -> None:
        """Save every individual experiment."""
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
        """Calculate statistics for each board size."""
        summary = []

        for n in self.n_values:
            group = [
                row for row in rows
                if row["n"] == n
            ]

            solve_times = [
                row["solve_time_seconds"]
                for row in group
            ]

            def average(field: str) -> float:
                return statistics.mean(
                    row[field] for row in group
                )

            summary.append({
                "n": n,
                "num_variables": group[0]["num_variables"],
                "num_clauses": group[0]["num_clauses"],
                "runs": len(group),

                "mean_solve_time_seconds":
                    statistics.mean(solve_times),

                "median_solve_time_seconds":
                    statistics.median(solve_times),

                "std_solve_time_seconds":
                    statistics.stdev(solve_times)
                    if len(solve_times) > 1
                    else 0.0,

                "mean_encoding_time_seconds":
                    average("encoding_time_seconds"),

                "mean_solver_setup_time_seconds":
                    average("solver_setup_time_seconds"),

                "mean_total_time_seconds":
                    average("total_time_seconds"),

                "mean_conflicts":
                    average("conflicts"),

                "mean_decisions":
                    average("decisions"),

                "mean_propagations":
                    average("propagations"),

                "mean_restarts":
                    average("restarts"),
            })

        return summary

    @staticmethod
    def _write_summary(
        summary: list[dict],
        output_path: Path
    ) -> None:
        """Save aggregated experiment results."""
        if not summary:
            raise ValueError("No summary data to save.")

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

    @staticmethod
    def _write_environment(
        output_path: Path,
        n_values: list[int],
        repetitions: int
    ) -> None:
        """Save the environment used during experiments."""
        information = [
            "GLUCOSE3 EXPERIMENT ENVIRONMENT",
            f"Operating system: {platform.platform()}",
            f"Python version: {platform.python_version()}",
            f"Processor: {platform.processor()}",
            f"Machine architecture: {platform.machine()}",
            f"Logical CPU count: {__import__('os').cpu_count()}",
            f"N values: {n_values}",
            f"Repetitions per N: {repetitions}",
            "Main measurement: solve_time_seconds",
            "Warm-up: one unrecorded solver run",
        ]

        output_path.write_text(
            "\n".join(information) + "\n",
            encoding="utf-8"
        )

    def run(self, output_dir: Path | None = None):
        """Execute all experiments and save the results."""

        if output_dir is None:
            output_dir = self._get_output_directory()
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        solver = Glucose3NQueensSolver()

        # Warm-up run: excluded from recorded measurements.
        print("Running warm-up...")
        solver.solve(self.n_values[0])

        raw_rows = []

        total_runs = (
            len(self.n_values) * self.repetitions
        )

        completed = 0

        for n in self.n_values:
            print(f"\nTesting N = {n}")

            for trial in range(
                1,
                self.repetitions + 1
            ):
                result = solver.solve(n)

                if (
                    not result.satisfiable
                    or result.positions is None
                    or result.board is None
                ):
                    raise RuntimeError(
                        f"No valid solution found for N={n}."
                    )

                stats = result.solver_stats

                row = {
                    "n": n,
                    "trial": trial,
                    "num_variables": result.num_variables,
                    "num_clauses": result.num_clauses,
                    "satisfiable": result.satisfiable,

                    "encoding_time_seconds":
                        result.encoding_time_seconds,

                    "solver_setup_time_seconds":
                        result.solver_setup_time_seconds,

                    "solve_time_seconds":
                        result.solve_time_seconds,

                    "total_time_seconds":
                        result.total_time_seconds,

                    "conflicts": stats.get("conflicts", 0),
                    "decisions": stats.get("decisions", 0),
                    "propagations": stats.get("propagations", 0),
                    "restarts": stats.get("restarts", 0),
                }

                raw_rows.append(row)
                completed += 1

                print(
                    f"Trial {trial}/{self.repetitions} | "
                    f"Solve time: "
                    f"{result.solve_time_seconds:.9f} seconds"
                )

            print(
                f"Completed N={n} | "
                f"CNF clauses: {result.num_clauses}"
            )

        # Save raw data.
        raw_path = output_dir / "glucose3_raw.csv"

        self._write_raw_results(
            raw_rows,
            raw_path
        )

        # Calculate and save summary statistics.
        summary = self._build_summary(raw_rows)

        summary_path = (
            output_dir / "glucose3_summary.csv"
        )

        self._write_summary(
            summary,
            summary_path
        )

        # Save the experimental environment.
        environment_path = (
            output_dir / "glucose3_environment.txt"
        )

        self._write_environment(
            environment_path,
            self.n_values,
            self.repetitions
        )

        print("\n========== EXPERIMENT SUMMARY ==========")

        for item in summary:
            print(
                f"N={item['n']:2d} | "
                f"Variables={item['num_variables']:4d} | "
                f"Clauses={item['num_clauses']:6d} | "
                f"Median={item['median_solve_time_seconds']:.9f}s"
            )

        print("\nAll experiments completed.")
        print(f"Total recorded runs: {completed}")
        print(f"Raw results: {raw_path}")
        print(f"Summary: {summary_path}")
        print(f"Environment: {environment_path}")

        return raw_path, summary_path, environment_path
