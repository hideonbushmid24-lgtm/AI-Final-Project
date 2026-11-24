
from typing import List


class NQueensCNFEncoder:
    """
    Convert the N-Queens problem into CNF clauses.

    Each board square is represented by one Boolean variable.
    A positive integer represents the variable.
    A negative integer represents its negation.
    """

    def __init__(self, n: int):
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError("N must be a positive integer.")

        self.n = n

    @property
    def num_variables(self) -> int:
        """Return the total number of Boolean variables."""
        return self.n * self.n

    def variable_id(self, row: int, col: int) -> int:
        """
        Map a zero-based board position to a positive SAT variable ID.

        Example for N = 4:
        (0, 0) -> 1
        (0, 1) -> 2
        (1, 0) -> 5
        """
        if not (0 <= row < self.n and 0 <= col < self.n):
            raise ValueError("Board position is out of range.")

        return row * self.n + col + 1

    def expected_clause_count(self) -> int:
        """Calculate the expected number of clauses."""
        n = self.n

        diagonal_pairs = (
            n * (n - 1) * (2 * n - 1)
        ) // 3

        return (
            n
            + n * n * (n - 1)
            + diagonal_pairs
        )

    def encode(self) -> List[List[int]]:
        """Generate the complete CNF formula."""
        clauses = []

        # Constraint 1:
        # At least one queen in every row.
        for row in range(self.n):
            clause = [
                self.variable_id(row, col)
                for col in range(self.n)
            ]
            clauses.append(clause)

        # Constraint 2:
        # At most one queen in every row.
        for row in range(self.n):
            for col1 in range(self.n):
                for col2 in range(col1 + 1, self.n):
                    clauses.append([
                        -self.variable_id(row, col1),
                        -self.variable_id(row, col2)
                    ])

        # Constraint 3:
        # At most one queen in every column.
        for col in range(self.n):
            for row1 in range(self.n):
                for row2 in range(row1 + 1, self.n):
                    clauses.append([
                        -self.variable_id(row1, col),
                        -self.variable_id(row2, col)
                    ])

        # Constraint 4:
        # No two queens can attack each other diagonally.
        # Each pair is generated exactly once.
        for row1 in range(self.n):
            for col1 in range(self.n):
                for row2 in range(row1 + 1, self.n):
                    distance = row2 - row1

                    for col2 in (
                        col1 - distance,
                        col1 + distance
                    ):
                        if 0 <= col2 < self.n:
                            clauses.append([
                                -self.variable_id(row1, col1),
                                -self.variable_id(row2, col2)
                            ])

        # Verify the generated clause count.
        expected = self.expected_clause_count()

        if len(clauses) != expected:
            raise RuntimeError(
                f"Clause count mismatch: "
                f"expected {expected}, got {len(clauses)}"
            )

        return clauses
