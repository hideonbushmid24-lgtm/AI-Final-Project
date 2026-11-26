"""Generate experimental evaluation charts for Tank Battle."""

import argparse
import csv
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ALGORITHMS = [
    "Minimax",
    "Alpha-Beta",
    "Heuristic Minimax",
    "Heuristic Minimax + Alpha-Beta",
]

REQUIRED_COLUMNS = {
    "scenario",
    "algorithm",
    "depth_plies",
    "mean_wall_time_ms",
    "mean_nodes_explored",
}


def load_summary(path):
    """Load and validate the summary CSV."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Summary CSV is empty.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Missing CSV columns: {sorted(missing)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("No summary records found.")

    return rows


def build_index(rows):
    """Index rows by scenario, algorithm and search depth."""
    index = {}

    for row in rows:
        key = (
            row["scenario"],
            row["algorithm"],
            int(row["depth_plies"]),
        )

        if key in index:
            raise ValueError(f"Duplicate summary record: {key}")

        index[key] = row

    return index


def average_metric(index, scenarios, algorithm, depth, column):
    """Average a summary metric across all scenarios."""
    values = [
        float(index[(scenario, algorithm, depth)][column])
        for scenario in scenarios
    ]
    return statistics.mean(values)


def save_figure(fig, output_path):
    """Save a figure as a high-resolution PNG."""
    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)
    print(f"Generated: {output_path}")


def plot_average_runtime(index, scenarios, depths, output_dir):
    """Compare average runtime across algorithms and search depths."""
    x_positions = list(range(len(ALGORITHMS)))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))

    for depth_index, depth in enumerate(depths):
        values = [
            average_metric(
                index,
                scenarios,
                algorithm,
                depth,
                "mean_wall_time_ms",
            )
            for algorithm in ALGORITHMS
        ]

        offset = (
            depth_index - (len(depths) - 1) / 2
        ) * bar_width

        positions = [
            position + offset
            for position in x_positions
        ]

        ax.bar(
            positions,
            values,
            bar_width,
            label=f"Depth {depth}",
        )

    ax.set_title("Average Search Runtime by Algorithm")
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Mean Wall Time (ms, logarithmic scale)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        ALGORITHMS,
        rotation=12,
        ha="right",
    )
    ax.set_yscale("log")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    save_figure(
        fig,
        output_dir / "mean_runtime_by_algorithm.png",
    )


def plot_average_nodes(index, scenarios, depths, output_dir):
    """Compare average explored nodes across algorithms."""
    x_positions = list(range(len(ALGORITHMS)))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))

    for depth_index, depth in enumerate(depths):
        values = [
            average_metric(
                index,
                scenarios,
                algorithm,
                depth,
                "mean_nodes_explored",
            )
            for algorithm in ALGORITHMS
        ]

        offset = (
            depth_index - (len(depths) - 1) / 2
        ) * bar_width

        positions = [
            position + offset
            for position in x_positions
        ]

        ax.bar(
            positions,
            values,
            bar_width,
            label=f"Depth {depth}",
        )

    ax.set_title("Average Explored Nodes by Algorithm")
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Mean Nodes Explored")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        ALGORITHMS,
        rotation=12,
        ha="right",
    )
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    save_figure(
        fig,
        output_dir / "mean_nodes_by_algorithm.png",
    )


def plot_runtime_by_scenario(
    index,
    scenarios,
    depth,
    output_dir,
):
    """Compare algorithm runtime across individual scenarios."""
    x_positions = list(range(len(scenarios)))
    bar_width = 0.18

    fig, ax = plt.subplots(figsize=(12, 6))

    for algorithm_index, algorithm in enumerate(ALGORITHMS):
        values = [
            float(
                index[(scenario, algorithm, depth)][
                    "mean_wall_time_ms"
                ]
            )
            for scenario in scenarios
        ]

        offset = (
            algorithm_index - (len(ALGORITHMS) - 1) / 2
        ) * bar_width

        positions = [
            position + offset
            for position in x_positions
        ]

        ax.bar(
            positions,
            values,
            bar_width,
            label=algorithm,
        )

    ax.set_title(
        f"Algorithm Runtime Across Scenarios (Depth {depth})"
    )
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Mean Wall Time (ms, logarithmic scale)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios)
    ax.set_yscale("log")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    save_figure(
        fig,
        output_dir / f"runtime_by_scenario_depth{depth}.png",
    )


def plot_alpha_beta_speedup(
    index,
    scenarios,
    depth,
    output_dir,
):
    """Compare Alpha-Beta speedup against its Minimax baseline."""
    standard_speedups = []
    heuristic_speedups = []

    for scenario in scenarios:
        minimax_time = float(
            index[(scenario, "Minimax", depth)][
                "mean_wall_time_ms"
            ]
        )
        alpha_beta_time = float(
            index[(scenario, "Alpha-Beta", depth)][
                "mean_wall_time_ms"
            ]
        )

        heuristic_time = float(
            index[(scenario, "Heuristic Minimax", depth)][
                "mean_wall_time_ms"
            ]
        )
        heuristic_ab_time = float(
            index[
                (
                    scenario,
                    "Heuristic Minimax + Alpha-Beta",
                    depth,
                )
            ]["mean_wall_time_ms"]
        )

        standard_speedups.append(
            minimax_time / alpha_beta_time
        )
        heuristic_speedups.append(
            heuristic_time / heuristic_ab_time
        )

    x_positions = list(range(len(scenarios)))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(
        [
            position - bar_width / 2
            for position in x_positions
        ],
        standard_speedups,
        bar_width,
        label="Minimax / Alpha-Beta",
    )

    ax.bar(
        [
            position + bar_width / 2
            for position in x_positions
        ],
        heuristic_speedups,
        bar_width,
        label="Heuristic Minimax / Heuristic + Alpha-Beta",
    )

    ax.set_title(
        f"Alpha-Beta Speedup Across Scenarios (Depth {depth})"
    )
    ax.set_xlabel("Scenario")
    ax.set_ylabel("Speedup (times)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    save_figure(
        fig,
        output_dir / f"alpha_beta_speedup_depth{depth}.png",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate Tank Battle experiment charts."
    )
    parser.add_argument(
        "--tag",
        default="final_v1",
        help="Experiment result tag.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[3]
    results_dir = project_root / "source" / "results" / "task2"

    input_path = results_dir / f"{args.tag}_summary_results.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Summary CSV not found: {input_path}"
        )

    rows = load_summary(input_path)
    index = build_index(rows)

    scenarios = sorted({
        row["scenario"] for row in rows
    })
    depths = sorted({
        int(row["depth_plies"]) for row in rows
    })

    for scenario in scenarios:
        for depth in depths:
            for algorithm in ALGORITHMS:
                if (scenario, algorithm, depth) not in index:
                    raise ValueError(
                        "Incomplete summary data: "
                        f"{scenario}, {algorithm}, depth {depth}"
                    )

    output_dir = results_dir / "figures" / args.tag
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_average_runtime(
        index,
        scenarios,
        depths,
        output_dir,
    )

    plot_average_nodes(
        index,
        scenarios,
        depths,
        output_dir,
    )

    target_depth = 3 if 3 in depths else max(depths)

    plot_runtime_by_scenario(
        index,
        scenarios,
        target_depth,
        output_dir,
    )

    plot_alpha_beta_speedup(
        index,
        scenarios,
        target_depth,
        output_dir,
    )

    print("\nChart generation completed.")
    print(f"Input: {input_path}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()