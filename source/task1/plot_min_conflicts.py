
import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = (
    PROJECT_ROOT
    / "source"
    / "results"
    / "task1"
)

SUMMARY_FILE = (
    RESULT_DIR / "min_conflicts_summary.csv"
)

FIGURE_DIR = RESULT_DIR / "figures"

FIGURE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def load_summary():
    with SUMMARY_FILE.open(
        newline="",
        encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def plot_metric(rows, field, ylabel, filename):
    strategies = {
        "random": "Standard Min-Conflicts",
        "most_conflicted": "Improved Min-Conflicts"
    }

    plt.figure(figsize=(9, 5))

    for strategy, label in strategies.items():
        group = [
            row for row in rows
            if row["strategy"] == strategy
        ]

        group.sort(
            key=lambda row: int(row["n"])
        )

        x = [
            int(row["n"])
            for row in group
        ]

        y = [
            float(row[field])
            for row in group
        ]

        plt.plot(
            x,
            y,
            marker="o",
            label=label
        )

    plt.xlabel("Board size (N)")
    plt.ylabel(ylabel)
    plt.title(ylabel + " vs Board Size")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / filename,
        dpi=300
    )

    plt.close()


def main():
    rows = load_summary()

    plot_metric(
        rows,
        "success_rate_percent",
        "Success Rate (%)",
        "min_conflicts_success_rate.png"
    )

    plot_metric(
        rows,
        "median_steps_successful_only",
        "Median Successful Steps",
        "min_conflicts_steps.png"
    )

    plot_metric(
        rows,
        "median_time_seconds",
        "Median Execution Time (seconds)",
        "min_conflicts_runtime.png"
    )

    print("All Min-Conflicts charts generated.")
    print(f"Output directory: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
