
from typing import Sequence


class NQueensValidator:
    """
    Validate N-Queens solutions.

    A solution is represented by a list where:
    positions[row] = column containing the queen.
    """

    @staticmethod
    def is_valid_positions(
        positions: Sequence[int],
        n: int | None = None
    ) -> bool:
        """Check whether all queens satisfy N-Queens constraints."""

        if n is None:
            n = len(positions)

        if (
            not isinstance(n, int)
            or isinstance(n, bool)
            or n <= 0
        ):
            return False

        if len(positions) != n:
            return False

        for col in positions:
            if (
                not isinstance(col, int)
                or isinstance(col, bool)
                or not 0 <= col < n
            ):
                return False

        # Each column must contain exactly one queen.
        if len(set(positions)) != n:
            return False

        # Queens must not share either diagonal.
        descending_diagonals = [
            row - col
            for row, col in enumerate(positions)
        ]

        ascending_diagonals = [
            row + col
            for row, col in enumerate(positions)
        ]

        if len(set(descending_diagonals)) != n:
            return False

        if len(set(ascending_diagonals)) != n:
            return False

        return True

    @staticmethod
    def positions_to_board(
        positions: Sequence[int]
    ) -> list[list[int]]:
        """Convert queen positions into an N x N board."""

        n = len(positions)

        if not NQueensValidator.is_valid_positions(
            positions, n
        ):
            raise ValueError("Invalid N-Queens solution.")

        board = [
            [0 for _ in range(n)]
            for _ in range(n)
        ]

        for row, col in enumerate(positions):
            board[row][col] = 1

        return board

    @staticmethod
    def is_valid_board(
        board: Sequence[Sequence[int]]
    ) -> bool:
        """Validate a binary N x N chessboard."""

        n = len(board)

        if n == 0:
            return False

        if any(len(row) != n for row in board):
            return False

        positions = []

        for row in board:
            if any(
                value not in (0, 1)
                or isinstance(value, bool)
                for value in row
            ):
                return False

            queen_columns = [
                col
                for col, value in enumerate(row)
                if value == 1
            ]

            if len(queen_columns) != 1:
                return False

            positions.append(queen_columns[0])

        return NQueensValidator.is_valid_positions(
            positions, n
        )
