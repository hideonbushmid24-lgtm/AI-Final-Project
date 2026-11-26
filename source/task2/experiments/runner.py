
import argparse
import csv
import platform
import random
import re
import statistics
import sys

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from time import perf_counter

from experiments.scenarios import SCENARIO_FACTORIES

from tank_battle.search.minimax import MinimaxAgent
from tank_battle.search.alpha_beta import AlphaBetaAgent

from tank_battle.search.heuristic_agents import (
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
)


# Four search configurations.
ALGORITHM_CLASSES = {
    "Minimax": MinimaxAgent,
    "Alpha-Beta": AlphaBetaAgent,
    "Heuristic Minimax": HeuristicMinimaxAgent,
    "Heuristic Minimax + Alpha-Beta": HeuristicAlphaBetaAgent,
}


def create_agent(algorithm_name, depth):
    """Create an AI agent using the selected configuration."""

    if algorithm_name not in ALGORITHM_CLASSES:
        raise ValueError(
            f"Unknown algorithm: {algorithm_name}"
        )

    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
        raise ValueError("Depth must be a positive integer.")

    agent_class = ALGORITHM_CLASSES[algorithm_name]

    return agent_class(depth=depth)


def run_single_experiment(
    scenario_name,
    algorithm_name,
    depth,
    repetition,
):
    """Run one algorithm once on a fresh scenario."""

    if scenario_name not in SCENARIO_FACTORIES:
        raise ValueError(
            f"Unknown scenario: {scenario_name}"
        )

    if (
        not isinstance(repetition, int)
        or isinstance(repetition, bool)
        or repetition < 0
    ):
        raise ValueError(
            "Repetition must be a non-negative integer. "
            "Repetition 0 is reserved for warm-up."
        )

    # Every run receives a fresh GameState.
    state = SCENARIO_FACTORIES[scenario_name]()

    state.validate()

    agent = create_agent(
        algorithm_name,
        depth
    )

    # Measure the complete search() call.
    start_time = perf_counter()

    result = agent.search(state)

    wall_time = perf_counter() - start_time

    return {
        "scenario": scenario_name,
        "algorithm": algorithm_name,
        "depth_plies": depth,
        "repetition": repetition,

        "starting_player": state.current_player.name,

        "best_action": (
            result.best_action.value
            if result.best_action is not None
            else ""
        ),

        "evaluation_score": result.score,

        "requested_depth": result.requested_depth,
        "actual_depth": result.max_depth_reached,

        "nodes_explored": result.nodes_explored,
        "leaf_nodes": result.leaf_nodes,
        "terminal_nodes": result.terminal_nodes,

        "cutoffs": result.cutoffs,
        "pruned_branches": result.pruned_branches,

        # Time measured inside the search algorithm.
        "search_time_ms": result.elapsed_time_ms,

        # Time measured around the complete search() call.
        "wall_time_ms": wall_time * 1000,
    }


def validate_pairwise_scores(records):
    """
    Check whether Minimax and Alpha-Beta
    return identical scores under the same conditions.
    """

    grouped = defaultdict(dict)

    for record in records:
        key = (
            record["scenario"],
            record["depth_plies"],
            record["repetition"],
        )

        grouped[key][record["algorithm"]] = record

    pairs = [
        ("Minimax", "Alpha-Beta"),
        (
            "Heuristic Minimax",
            "Heuristic Minimax + Alpha-Beta",
        ),
    ]

    for key, algorithms in grouped.items():

        for first, second in pairs:

            if first not in algorithms or second not in algorithms:
                raise ValueError(
                    f"Missing algorithm result for {key}."
                )

            score_a = algorithms[first]["evaluation_score"]
            score_b = algorithms[second]["evaluation_score"]

            difference = abs(score_a - score_b)

            if difference > 1e-9:
                raise AssertionError(
                    f"Score mismatch for {key}: "
                    f"{first}={score_a}, {second}={score_b}"
                )

def run_benchmark(
    scenario_names=None,
    depths=(2, 3),
    repeats=1,
    verbose=False,
    seed=42,
):
    """
    Run reproducible benchmarks.

    For each scenario and depth:
    - Run every algorithm once as an unmeasured warm-up.
    - Shuffle algorithm order for every measured repetition.
    - Record execution order and random seed.
    """

    if scenario_names is None:
        scenario_names = list(SCENARIO_FACTORIES.keys())
    else:
        scenario_names = list(scenario_names)

    depths = list(depths)

    if not scenario_names:
        raise ValueError("At least one scenario must be selected.")

    unknown_scenarios = [
        name for name in scenario_names
        if name not in SCENARIO_FACTORIES
    ]
    if unknown_scenarios:
        raise ValueError(
            f"Unknown scenarios: {unknown_scenarios}"
        )

    if not depths or any(
        not isinstance(depth, int)
        or isinstance(depth, bool)
        or depth < 1
        for depth in depths
    ):
        raise ValueError("All search depths must be positive integers.")

    if (
        not isinstance(repeats, int)
        or isinstance(repeats, bool)
        or repeats < 1
    ):
        raise ValueError("Repeats must be a positive integer.")

    if not isinstance(seed, int):
        raise ValueError("Seed must be an integer.")

    algorithm_names = list(ALGORITHM_CLASSES.keys())
    rng = random.Random(seed)

    records = []

    for scenario_name in scenario_names:
        for depth in depths:

            # -------------------------------------------------
            # 1. Warm-up: one unmeasured run per algorithm
            # -------------------------------------------------
            warmup_order = algorithm_names.copy()
            rng.shuffle(warmup_order)

            if verbose:
                print(
                    f"\n[WARM-UP] {scenario_name} | "
                    f"Depth {depth}"
                )

            for algorithm_name in warmup_order:
                run_single_experiment(
                    scenario_name=scenario_name,
                    algorithm_name=algorithm_name,
                    depth=depth,
                    repetition=0,
                )

                if verbose:
                    print(f"  Warm-up completed: {algorithm_name}")

            # -------------------------------------------------
            # 2. Measured repetitions
            # -------------------------------------------------
            for repetition in range(1, repeats + 1):

                execution_order = algorithm_names.copy()
                rng.shuffle(execution_order)

                if verbose:
                    print(
                        f"\n[MEASURE] {scenario_name} | "
                        f"Depth {depth} | "
                        f"Repetition {repetition}/{repeats}"
                    )

                for order_index, algorithm_name in enumerate(
                    execution_order,
                    start=1,
                ):
                    record = run_single_experiment(
                        scenario_name=scenario_name,
                        algorithm_name=algorithm_name,
                        depth=depth,
                        repetition=repetition,
                    )

                    # Experimental metadata
                    record["execution_order"] = order_index
                    record["random_seed"] = seed
                    record["warmup_runs_per_algorithm"] = 1

                    records.append(record)

                    if verbose:
                        print(
                            f"  Order {order_index}: {algorithm_name} | "
                            f"Nodes: {record['nodes_explored']} | "
                            f"Time: {record['wall_time_ms']:.3f} ms"
                        )

    # Confirm that paired algorithms produce equivalent scores.
    validate_pairwise_scores(records)

    return records

def build_summary(records):
    """Calculate statistics grouped by scenario, algorithm and depth."""

    grouped = defaultdict(list)

    for record in records:

        key = (
            record["scenario"],
            record["algorithm"],
            record["depth_plies"],
        )

        grouped[key].append(record)

    summaries = []

    for key, group in grouped.items():

        times = [r["wall_time_ms"] for r in group]
        search_times = [r["search_time_ms"] for r in group]
        nodes = [r["nodes_explored"] for r in group]
        leaves = [r["leaf_nodes"] for r in group]
        cutoffs = [r["cutoffs"] for r in group]
        pruned = [r["pruned_branches"] for r in group]
        scores = [r["evaluation_score"] for r in group]

        summary = {
            "scenario": key[0],
            "algorithm": key[1],
            "depth_plies": key[2],
            "runs": len(group),

            "mean_wall_time_ms": statistics.mean(times),
            "median_wall_time_ms": statistics.median(times),
            "stdev_wall_time_ms": (
                statistics.stdev(times)
                if len(times) > 1
                else 0.0
            ),

            "mean_search_time_ms": statistics.mean(search_times),
            "median_search_time_ms": statistics.median(search_times),

            "mean_nodes_explored": statistics.mean(nodes),
            "median_nodes_explored": statistics.median(nodes),

            "mean_leaf_nodes": statistics.mean(leaves),
            "mean_cutoffs": statistics.mean(cutoffs),
            "mean_pruned_branches": statistics.mean(pruned),

            "mean_evaluation_score": statistics.mean(scores),

            "min_wall_time_ms": min(times),
            "max_wall_time_ms": max(times),
        }

        summaries.append(summary)

    return summaries


def write_csv(records, output_path):
    """Export records to a CSV file."""

    if not records:
        raise ValueError("Cannot export an empty result set.")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys()),
        )

        writer.writeheader()
        writer.writerows(records)


def write_environment(output_path, arguments):
    """Save the experiment environment information."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    information = [
        "TANK BATTLE - EXPERIMENTAL EVALUATION",
        f"Date: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Python version: {sys.version}",
        f"Operating system: {platform.platform()}",
        f"Processor: {platform.processor() or 'Unknown'}",
        f"Architecture: {platform.machine()}",
        f"Scenarios: {', '.join(arguments.scenarios)}",
        f"Search depths: {arguments.depths}",
        f"Repetitions: {arguments.repeats}",
        f"Algorithms: {', '.join(ALGORITHM_CLASSES.keys())}",
        "",
        "Timing notes:",
        "- search_time_ms comes from SearchResult.",
        "- wall_time_ms measures the complete agent.search() call.",
        "- Both measurements exclude Python process startup time.",
    ]

    output_path.write_text(
        "\n".join(information),
        encoding="utf-8",
    )


def parse_arguments():
    """Read command-line configuration."""

    parser = argparse.ArgumentParser(
        description="Tank Battle experimental benchmark."
    )

    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=list(SCENARIO_FACTORIES.keys()),
        default=list(SCENARIO_FACTORIES.keys()),
    )

    parser.add_argument(
        "--depths",
        nargs="+",
        type=int,
        default=[2, 3],
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible algorithm execution order.",
    )

    parser.add_argument(
        "--tag",
        default="pilot",
        help="Output filename tag, e.g. pilot or final.",
    )

    arguments = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_-]+", arguments.tag):
        parser.error("Tag may contain only letters, digits, _ and -.")

    if any(depth < 1 for depth in arguments.depths):
        parser.error("Every depth must be a positive integer.")

    if arguments.repeats < 1:
        parser.error("Repeats must be at least 1.")

    return arguments


def main():
    """Execute the benchmark and export its results."""

    arguments = parse_arguments()

    print("=" * 70)
    print("TANK BATTLE - EXPERIMENTAL EVALUATION")
    print("=" * 70)

    print("Scenarios:", arguments.scenarios)
    print("Depths:", arguments.depths)
    print("Repetitions:", arguments.repeats)
    print("Algorithms:", list(ALGORITHM_CLASSES.keys()))

    start_time = perf_counter()

    records = run_benchmark(
        scenario_names=arguments.scenarios,
        depths=arguments.depths,
        repeats=arguments.repeats,
        verbose=True,
        seed=arguments.seed,
    )

    summaries = build_summary(records)

    # Locate the repository root.
    project_root = Path(__file__).resolve().parents[3]

    output_dir = (
        project_root
        / "source"
        / "results"
        / "task2"
    )

    tag = arguments.tag

    raw_path = output_dir / f"{tag}_raw_results.csv"
    summary_path = output_dir / f"{tag}_summary_results.csv"
    environment_path = output_dir / f"{tag}_environment.txt"

    write_csv(records, raw_path)
    write_csv(summaries, summary_path)
    write_environment(environment_path, arguments)

    elapsed = perf_counter() - start_time

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETED")
    print("=" * 70)

    print("Total experiment runs:", len(records))
    print(f"Total runner time: {elapsed:.3f} seconds")

    print("\nGenerated files:")
    print(raw_path)
    print(summary_path)
    print(environment_path)

    print("\nPairwise score validation: PASSED")


if __name__ == "__main__":
    main()
