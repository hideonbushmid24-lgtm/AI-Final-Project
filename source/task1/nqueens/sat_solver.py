
from dataclasses import dataclass
from time import perf_counter

from pysat.solvers import Glucose3

from nqueens.cnf_encoder import NQueensCNFEncoder
from nqueens.validator import NQueensValidator


@dataclass
class SATResult:
    """Store the results returned by Glucose3."""

    n: int
    satisfiable: bool

    positions: list[int] | None
    board: list[list[int]] | None

    num_variables: int
    num_clauses: int

    encoding_time_seconds: float
    solver_setup_time_seconds: float
    solve_time_seconds: float
    total_time_seconds: float

    solver_stats: dict[str, int]


class Glucose3NQueensSolver:
    """
    Solve N-Queens using Glucose3 and a CNF formula.
    """

    def solve(self, n: int) -> SATResult:
        """Generate CNF and solve the N-Queens problem."""

        total_start = perf_counter()

        # Step 1: Generate the CNF formula.
        encode_start = perf_counter()

        encoder = NQueensCNFEncoder(n)
        clauses = encoder.encode()

        encoding_time = (
            perf_counter() - encode_start
        )

        # Step 2: Initialize Glucose3 with CNF clauses.
        setup_start = perf_counter()

        solver = Glucose3(
            bootstrap_with=clauses
        )

        setup_time = (
            perf_counter() - setup_start
        )

        try:
            # Step 3: Ask Glucose3 to solve the formula.
            solve_start = perf_counter()

            satisfiable = solver.solve()

            solve_time = (
                perf_counter() - solve_start
            )

            # Step 4: Collect solver statistics.
            solver_stats = solver.accum_stats()

            # Step 5: Retrieve the Boolean model.
            model = (
                solver.get_model()
                if satisfiable
                else None
            )

        finally:
            # Release native solver resources.
            solver.delete()

        positions = None
        board = None

        # Step 6: Convert the SAT model to queen positions.
        if satisfiable:
            if model is None:
                raise RuntimeError(
                    "SAT solver returned no model."
                )

            true_variables = {
                literal
                for literal in model
                if literal > 0
            }

            positions = []

            for row in range(n):
                queen_columns = [
                    col
                    for col in range(n)
                    if encoder.variable_id(row, col)
                    in true_variables
                ]

                if len(queen_columns) != 1:
                    raise RuntimeError(
                        "The SAT model does not contain "
                        "exactly one queen in each row."
                    )

                positions.append(queen_columns[0])

            # Step 7: Validate the solution independently.
            if not NQueensValidator.is_valid_positions(
                positions, n
            ):
                raise RuntimeError(
                    "Glucose3 returned an invalid solution."
                )

            board = (
                NQueensValidator.positions_to_board(
                    positions
                )
            )

        total_time = perf_counter() - total_start

        return SATResult(
            n=n,
            satisfiable=satisfiable,
            positions=positions,
            board=board,
            num_variables=encoder.num_variables,
            num_clauses=len(clauses),
            encoding_time_seconds=encoding_time,
            solver_setup_time_seconds=setup_time,
            solve_time_seconds=solve_time,
            total_time_seconds=total_time,
            solver_stats=solver_stats or {}
        )
