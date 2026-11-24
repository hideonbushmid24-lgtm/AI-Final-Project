
import argparse

from nqueens.min_conflicts_experiments import (
    MinConflictsExperimentRunner
)


DEFAULT_N_VALUES = [
    4, 5, 6, 7, 8,
    10, 12, 15, 20,
    30, 40, 50
]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compare Standard and Improved "
            "Min-Conflicts for N-Queens."
        )
    )

    parser.add_argument(
        "--n-values",
        nargs="+",
        type=int,
        default=DEFAULT_N_VALUES,
        help="Board sizes to evaluate."
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=30
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=10000
    )

    parser.add_argument(
        "--max-restarts",
        type=int,
        default=5
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20261124
    )

    args = parser.parse_args()

    runner = MinConflictsExperimentRunner(
        n_values=args.n_values,
        repetitions=args.repetitions,
        max_steps=args.max_steps,
        max_restarts=args.max_restarts,
        base_seed=args.seed
    )

    runner.run()


if __name__ == "__main__":
    main()
