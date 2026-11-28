
from source.task3.kakuro.constraints import (
    iter_valid_assignments,
    valid_digit_combinations,
)
from source.task3.kakuro.model import (
    Direction,
    KakuroRun,
)


def test_valid_digit_combinations():
    result = valid_digit_combinations(2, 10)

    assert len(result) == 4
    assert (1, 9) in result
    assert (2, 8) in result
    assert (3, 7) in result
    assert (4, 6) in result


def test_combinations_do_not_contain_duplicate_digits():
    result = valid_digit_combinations(3, 15)

    for combination in result:
        assert len(combination) == len(set(combination))
        assert sum(combination) == 15


def test_iter_valid_assignments():
    run = KakuroRun(
        run_id="A-TEST",
        direction=Direction.ACROSS,
        target_sum=10,
        cells=((1, 1), (1, 2)),
    )

    domains = {
        (1, 1): {1, 2, 3, 4},
        (1, 2): {6, 7, 8, 9},
    }

    assignments = list(iter_valid_assignments(run, domains))

    assert assignments == [
        (1, 9),
        (2, 8),
        (3, 7),
        (4, 6),
    ]


def test_assignments_respect_variable_domains():
    run = KakuroRun(
        run_id="A-TEST",
        direction=Direction.ACROSS,
        target_sum=10,
        cells=((1, 1), (1, 2)),
    )

    domains = {
        (1, 1): {1, 4, 6},
        (1, 2): {2, 6, 9},
    }

    assignments = list(iter_valid_assignments(run, domains))

    assert assignments == [(1, 9), (4, 6)]


def test_no_assignment_when_domains_are_incompatible():
    run = KakuroRun(
        run_id="A-TEST",
        direction=Direction.ACROSS,
        target_sum=10,
        cells=((1, 1), (1, 2)),
    )

    domains = {
        (1, 1): {1, 2},
        (1, 2): {3, 4},
    }

    assignments = list(iter_valid_assignments(run, domains))

    assert assignments == []


def test_invalid_digit_domain_is_rejected():
    run = KakuroRun(
        run_id="A-TEST",
        direction=Direction.ACROSS,
        target_sum=10,
        cells=((1, 1), (1, 2)),
    )

    domains = {
        (1, 1): {0, 1},
        (1, 2): {6, 9},
    }

    try:
        list(iter_valid_assignments(run, domains))
        assert False, "Expected ValueError"
    except ValueError:
        pass
