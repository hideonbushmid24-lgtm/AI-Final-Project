
import argparse

from nqueens.experiments import Glucose3ExperimentRunner


def main():
    parser = argparse.ArgumentParser(
        description="Run N-Queens Glucose3 experiments."
    )

    parser.add_argument(
        "--n-min",
        type=int,
        default=4,
        help="Minimum board size (default: 4)."
    )

    parser.add_argument(
        "--n-max",
        type=int,
        default=20,
        help="Maximum board size (default: 20)."
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=10,
        help="Number of runs for each N (default: 10)."
    )

    args = parser.parse_args()

    if args.n_min < 4:
        parser.error("The minimum N must be >= 4.")

    if args.n_max < args.n_min:
        parser.error("The maximum N must be >= minimum N.")

    if args.repetitions < 1:
        parser.error("Repetitions must be >= 1.")

    n_values = range(
        args.n_min,
        args.n_max + 1
    )

    runner = Glucose3ExperimentRunner(
        n_values=n_values,
        repetitions=args.repetitions
    )

    runner.run()


if __name__ == "__main__":
    main()
