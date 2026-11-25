
import pytest

from tank_battle.constants import PlayerId

from tank_battle.scenario import create_default_scenario

from tank_battle.evaluation import (
    HeuristicEvaluator,
    HeuristicWeights,
)

from tank_battle.search.heuristic_agents import (
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
)

from tank_battle.search.minimax import MinimaxAgent
from tank_battle.search.alpha_beta import AlphaBetaAgent


def test_heuristic_is_zero_sum():
    state = create_default_scenario()

    evaluator = HeuristicEvaluator()

    p1_score = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    p2_score = evaluator(
        state,
        PlayerId.PLAYER_2
    )

    assert p1_score == pytest.approx(-p2_score)


def test_initial_scenario_is_balanced():
    state = create_default_scenario()

    evaluator = HeuristicEvaluator()

    score = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    assert score == pytest.approx(0.0, abs=1e-9)


def test_evaluator_rewards_own_tank_hp():
    state = create_default_scenario()

    evaluator = HeuristicEvaluator()

    before = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    state.tanks[PlayerId.PLAYER_1].hp -= 1
    state.tanks[PlayerId.PLAYER_2].hp -= 2

    after = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    assert after > before


def test_evaluator_rewards_own_base_hp():
    state = create_default_scenario()

    evaluator = HeuristicEvaluator()

    before = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    state.bases[PlayerId.PLAYER_1].hp -= 1
    state.bases[PlayerId.PLAYER_2].hp -= 2

    after = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    assert after > before


def test_heuristic_weights_can_be_customized():
    weights = HeuristicWeights(
        tank_hp=20,
        base_hp=30,
        distance=2,
        mobility=2,
        bullet_threat=5
    )

    evaluator = HeuristicEvaluator(weights)

    state = create_default_scenario()

    assert evaluator(
        state,
        PlayerId.PLAYER_1
    ) == pytest.approx(0.0)


def test_terminal_win_has_positive_utility():
    state = create_default_scenario()

    state.bases[
        PlayerId.PLAYER_2
    ].hp = 0

    evaluator = HeuristicEvaluator()

    score = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    assert score == 100000


def test_terminal_loss_has_negative_utility():
    state = create_default_scenario()

    state.bases[
        PlayerId.PLAYER_2
    ].hp = 0

    evaluator = HeuristicEvaluator()

    score = evaluator(
        state,
        PlayerId.PLAYER_2
    )

    assert score == -100000


def test_feature_components_are_available():
    state = create_default_scenario()

    evaluator = HeuristicEvaluator()

    components = evaluator.evaluate_components(
        state,
        PlayerId.PLAYER_1
    )

    assert set(components) == {
        "tank_hp",
        "base_hp",
        "distance",
        "mobility",
        "bullet_threat"
    }

    assert all(
        isinstance(value, float)
        for value in components.values()
    )


def test_heuristic_does_not_modify_game_state():
    state = create_default_scenario()

    original_position = state.tanks[
        PlayerId.PLAYER_1
    ].position

    original_hp = state.tanks[
        PlayerId.PLAYER_1
    ].hp

    HeuristicEvaluator()(
        state,
        PlayerId.PLAYER_1
    )

    assert state.tanks[
        PlayerId.PLAYER_1
    ].position == original_position

    assert state.tanks[
        PlayerId.PLAYER_1
    ].hp == original_hp


@pytest.mark.parametrize(
    "agent_class, expected_name",
    [
        (
            HeuristicMinimaxAgent,
            "Heuristic Minimax"
        ),
        (
            HeuristicAlphaBetaAgent,
            "Heuristic Minimax + Alpha-Beta"
        )
    ]
)
def test_heuristic_agents_return_valid_actions(
    agent_class,
    expected_name
):
    state = create_default_scenario()

    agent = agent_class(depth=2)

    result = agent.search(state)

    assert result.best_action is not None
    assert result.algorithm == expected_name
    assert result.nodes_explored > 0
    assert result.max_depth_reached <= 2


def test_heuristic_minimax_and_alpha_beta_same_score():
    state = create_default_scenario()

    minimax = HeuristicMinimaxAgent(depth=3)
    alpha_beta = HeuristicAlphaBetaAgent(depth=3)

    result_minimax = minimax.search(state)
    result_alpha_beta = alpha_beta.search(state)

    assert result_minimax.score == pytest.approx(
        result_alpha_beta.score
    )


def test_heuristic_alpha_beta_explores_no_more_nodes():
    state = create_default_scenario()

    result_minimax = HeuristicMinimaxAgent(
        depth=3
    ).search(state)

    result_alpha_beta = HeuristicAlphaBetaAgent(
        depth=3
    ).search(state)

    assert (
        result_alpha_beta.nodes_explored
        <= result_minimax.nodes_explored
    )


def test_all_four_algorithms_use_same_state_without_mutation():
    state = create_default_scenario()

    original_positions = {
        player: tank.position
        for player, tank in state.tanks.items()
    }

    agents = [
        MinimaxAgent(depth=2),
        AlphaBetaAgent(depth=2),
        HeuristicMinimaxAgent(depth=2),
        HeuristicAlphaBetaAgent(depth=2)
    ]

    for agent in agents:
        result = agent.search(state)

        assert result.best_action is not None

    current_positions = {
        player: tank.position
        for player, tank in state.tanks.items()
    }

    assert current_positions == original_positions
