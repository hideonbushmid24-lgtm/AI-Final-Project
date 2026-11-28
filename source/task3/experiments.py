
import csv
import os
import platform
import statistics
import sys

from collections import Counter
from datetime import datetime
from pathlib import Path
from time import perf_counter

from .kakuro.demo_puzzle import build_backtracking_demo
from .kakuro.propagation import propagate_domains
from .kakuro.puzzle import build_puzzle
from .kakuro.solver import solve, validate_solution


# =========================================================
# Experiment configuration
# =========================================================

REPETITIONS = 30
WARMUP_RUNS = 3
MAX_NODES = 100_000

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "source" / "results" / "task3"


# =========================================================
# Utility functions
# =========================================================

def solution_signature(solution):
    """Create a deterministic representation of a solution."""

    return "|".join(
        f"{row},{col}={value}"
        for (row, col), value in sorted(solution.items())
    )


def measure_once(puzzle, scenario, operation, run_number):
    """Execute one measurement and collect solver statistics."""

    start_time = perf_counter()

    if operation == "propagation":
        result = propagate_domains(puzzle)

        elapsed_ms = (
            perf_counter() - start_time
        ) * 1000

        events = result.events

        complete_assignment = (
            result.consistent
            and all(
                len(domain) == 1
                for domain in result.domains.values()
            )
        )

        solution = {}

        if complete_assignment:
            solution = {
                cell: next(iter(domain))
                for cell, domain in result.domains.items()
            }

        consistent = result.consistent
        success = complete_assignment
        solved = complete_assignment

        solution_valid = (
            validate_solution(puzzle, solution)
            if complete_assignment
            else None
        )

        nodes_explored = 0
        backtracks = 0
        max_depth = 0

    elif operation == "full_solver":
        result = solve(
            puzzle,
            max_nodes=MAX_NODES,
        )

        elapsed_ms = (
            perf_counter() - start_time
        ) * 1000

        events = result.events
        solution = result.solution

        consistent = ""
        success = result.solved
        solved = result.solved

        solution_valid = (
            validate_solution(puzzle, solution)
            if result.solved
            else False
        )

        complete_assignment = result.solved
        nodes_explored = result.nodes_explored
        backtracks = result.backtracks
        max_depth = result.max_depth

    else:
        raise ValueError(f"Unknown operation: {operation}")

    event_counts = Counter(
        event.event_type
        for event in events
    )

    values_pruned = sum(
        len(event.removed_values)
        for event in events
        if event.event_type == "domain_pruned"
    )

    signature = (
        solution_signature(solution)
        if solution_valid is True
        else ""
    )

    return {
        "scenario": scenario,
        "operation": operation,
        "run": run_number,
        "wall_time_ms": round(elapsed_ms, 8),
        "variables": len(puzzle.white_cells),
        "success": success,
        "solved": solved,
        "consistent": consistent,
        "solution_valid": (
            solution_valid
            if solution_valid is not None
            else ""
        ),
        "complete_assignment": complete_assignment,
        "nodes_explored": nodes_explored,
        "backtracks": backtracks,
        "max_depth": max_depth,
        "event_count": len(events),
        "domain_pruned_events": event_counts["domain_pruned"],
        "values_pruned": values_pruned,
        "decisions": event_counts["decision"],
        "contradictions": event_counts["contradiction"],
        "solution_signature": signature,
    }


# =========================================================
# Benchmark execution
# =========================================================

def run_experiments():
    """Run all benchmark scenarios and save raw measurements."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    scenarios = {
        "reference_9x9": build_puzzle(),
        "backtracking_demo": build_backtracking_demo(),
    }

    operations = (
        "propagation",
        "full_solver",
    )

    raw_results = []

    total_runs = (
        len(scenarios)
        * len(operations)
        * REPETITIONS
    )

    print("=" * 65)
    print("KAKURO CSP EXPERIMENTAL EVALUATION")
    print("=" * 65)

    print(f"Repetitions : {REPETITIONS}")
    print(f"Warmups     : {WARMUP_RUNS}")
    print(f"Total runs  : {total_runs}")

    for scenario_name, puzzle in scenarios.items():

        print(f"\nScenario: {scenario_name}")
        print(f"Variables: {len(puzzle.white_cells)}")

        for operation in operations:

            print(f"\n  Operation: {operation}")

            # Warmup executions are excluded from measurements.
            for _ in range(WARMUP_RUNS):
                measure_once(
                    puzzle,
                    scenario_name,
                    operation,
                    0,
                )

            # Actual measurements.
            for run_number in range(1, REPETITIONS + 1):

                row = measure_once(
                    puzzle,
                    scenario_name,
                    operation,
                    run_number,
                )

                raw_results.append(row)

                if run_number % 10 == 0:
                    print(
                        f"    Completed {run_number}/{REPETITIONS}"
                    )

    raw_path = OUTPUT_DIR / "raw_benchmark.csv"

    with raw_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(raw_results[0].keys()),
        )

        writer.writeheader()
        writer.writerows(raw_results)

    return raw_results


# =========================================================
# Statistical summary
# =========================================================

def summarize_results(raw_results):
    """Calculate descriptive statistics for each workload."""

    summary_rows = []

    groups = {}

    for row in raw_results:
        key = (
            row["scenario"],
            row["operation"],
        )

        groups.setdefault(key, []).append(row)

    for (scenario, operation), rows in groups.items():

        times = [
            row["wall_time_ms"]
            for row in rows
        ]

        solved_runs = sum(
            bool(row["solved"])
            for row in rows
        )

        consistency_rows = [
                row for row in rows
                if row["consistent"] != ""
            ]

        consistent_runs = sum(
                bool(row["consistent"])
                for row in consistency_rows
            )

        validation_attempts = [
            row for row in rows
            if row["solution_valid"] != ""
        ]

        valid_solutions = sum(
            row["solution_valid"] is True
            for row in validation_attempts
        )

        signatures = {
            row["solution_signature"]
            for row in rows
            if row["solution_signature"]
        }

        def average(field):
            return statistics.mean(
                row[field] for row in rows
            )

        summary_rows.append({
            "scenario": scenario,
            "operation": operation,
            "runs": len(rows),
            "solved_runs": solved_runs,
            "solve_rate_percent": round(
                solved_runs / len(rows) * 100,
                4,
            ),
            "consistency_checks": len(consistency_rows),
            "consistent_runs": consistent_runs,
            "consistency_rate_percent": (
                round(
                    consistent_runs / len(consistency_rows) * 100,
                    4,
                )
                if consistency_rows
                else ""
            ),
            "valid_solutions": valid_solutions,
            "validation_attempts": len(validation_attempts),
            "valid_solution_rate_percent": (
                round(
                    valid_solutions / len(validation_attempts) * 100,
                    4,
                )
                if validation_attempts
                else ""
            ),
            "distinct_solutions_observed": len(signatures),
            "mean_time_ms": round(statistics.mean(times), 8),
            "median_time_ms": round(statistics.median(times), 8),
            "std_time_ms": round(statistics.pstdev(times), 8),
            "min_time_ms": round(min(times), 8),
            "max_time_ms": round(max(times), 8),
            "mean_nodes": round(average("nodes_explored"), 4),
            "mean_backtracks": round(average("backtracks"), 4),
            "mean_max_depth": round(average("max_depth"), 4),
            "mean_domain_pruned_events": round(
                average("domain_pruned_events"), 4
            ),
            "mean_values_pruned": round(
                average("values_pruned"), 4
            ),
            "mean_decisions": round(average("decisions"), 4),
            "mean_contradictions": round(
                average("contradictions"), 4
            ),
        })

    summary_path = OUTPUT_DIR / "benchmark_summary.csv"

    with summary_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(summary_rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    return summary_rows


# =========================================================
# Environment information
# =========================================================

def save_environment_info():
    """Save reproducibility information about the machine."""

    try:
        import pygame
        pygame_version = pygame.version.ver
    except ImportError:
        pygame_version = "Not installed"

    lines = [
        "KAKURO CSP BENCHMARK ENVIRONMENT",
        "=" * 45,
        f"Date: {datetime.now().astimezone().isoformat()}",
        f"Operating system: {platform.platform()}",
        f"System: {platform.system()}",
        f"Machine architecture: {platform.machine()}",
        f"Processor: {platform.processor() or 'Not reported'}",
        f"Logical CPU count: {os.cpu_count()}",
        f"Python version: {sys.version}",
        f"Python executable: {sys.executable}",
        f"Pygame version: {pygame_version}",
        f"Repetitions: {REPETITIONS}",
        f"Warmup runs: {WARMUP_RUNS}",
        f"Maximum search nodes: {MAX_NODES}",
    ]

    environment_path = OUTPUT_DIR / "environment.txt"

    environment_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return environment_path


# =========================================================
# Main
# =========================================================

def main():
    raw_results = run_experiments()

    summary_rows = summarize_results(
        raw_results
    )

    environment_path = save_environment_info()

    print("\n" + "=" * 65)
    print("BENCHMARK SUMMARY")
    print("=" * 65)

    
    for row in summary_rows:
        print(
            f"\n{row['scenario']} / {row['operation']}"
        )

        print(
            f"  Solve rate       : "
            f"{row['solve_rate_percent']}% "
            f"({row['solved_runs']}/{row['runs']})"
        )

        if row["consistency_checks"] != "":
            print(
                f"  Consistency rate : "
                f"{row['consistency_rate_percent']}% "
                f"({row['consistent_runs']}/{row['consistency_checks']})"
            )

        if row["validation_attempts"] > 0:
            print(
                f"  Valid solutions  : "
                f"{row['valid_solutions']}/"
                f"{row['validation_attempts']} "
                f"({row['valid_solution_rate_percent']}%)"
            )
        else:
            print(
                "  Valid solutions  : Not applicable"
            )

        print(
            f"  Mean time        : {row['mean_time_ms']:.6f} ms"
        )

        print(
            f"  Median time      : {row['median_time_ms']:.6f} ms"
        )

        print(
            f"  Std time         : {row['std_time_ms']:.6f} ms"
        )

        print(
            f"  Mean nodes       : {row['mean_nodes']}"
        )

        print(
            f"  Mean backtracks  : {row['mean_backtracks']}"
        )

        print(
            f"  Unique solutions : "
            f"{row['distinct_solutions_observed']}"
        )
      
if __name__ == "__main__":
    main()
