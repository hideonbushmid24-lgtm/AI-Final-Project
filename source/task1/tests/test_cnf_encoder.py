
import pytest

from nqueens.cnf_encoder import NQueensCNFEncoder


@pytest.mark.parametrize(
    "n, expected_clauses",
    [
        (4, 80),
        (5, 165),
        (6, 296),
        (7, 483),
        (8, 736),
    ]
)
def test_cnf_clause_count(n, expected_clauses):
    encoder = NQueensCNFEncoder(n)

    clauses = encoder.encode()

    assert encoder.num_variables == n * n
    assert len(clauses) == expected_clauses


def test_variable_ids_are_unique():
    n = 4
    encoder = NQueensCNFEncoder(n)

    ids = [
        encoder.variable_id(row, col)
        for row in range(n)
        for col in range(n)
    ]

    assert len(ids) == n * n
    assert sorted(ids) == list(range(1, n * n + 1))


def test_all_literals_are_in_valid_range():
    n = 4
    encoder = NQueensCNFEncoder(n)

    clauses = encoder.encode()

    for clause in clauses:
        assert len(clause) > 0

        for literal in clause:
            assert 1 <= abs(literal) <= n * n


def test_invalid_board_size():
    with pytest.raises(ValueError):
        NQueensCNFEncoder(0)


def test_invalid_variable_position():
    encoder = NQueensCNFEncoder(4)

    with pytest.raises(ValueError):
        encoder.variable_id(4, 0)
