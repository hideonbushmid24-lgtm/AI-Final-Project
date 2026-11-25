
import pytest

from tank_battle.constants import (
    PlayerId,
    Action,
)

from tank_battle.scenario import create_default_scenario
from tank_battle.evaluation import MaterialEvaluator

from tank_battle.search.minimax import MinimaxAgent
from tank_battle.search.alpha_beta import AlphaBetaAgent


@pytest.mark.parametrize(
    "agent_class",
    [MinimaxAgent, AlphaBetaAgent]
)
def test_agent_returns_valid_action(agent_class):
    state = create_default_scenario()

    agent = agent_class(depth=2)

    result = agent.search(state)

    assert isinstance(result.best_action, Action)
    assert result.best_action in Action

    assert result.requested_depth == 2
    assert result.max_depth_reached <= 2

    assert result.nodes_explored > 0
    assert result.leaf_nodes > 0
    assert result.elapsed_time_seconds >= 0


def test_minimax_and_alpha_beta_return_same_score():
    state = create_default_scenario()

    minimax = MinimaxAgent(depth=3)
    alpha_beta = AlphaBetaAgent(depth=3)

    result_minimax = minimax.search(state)
    result_alpha_beta = alpha_beta.search(state)

    assert (
        result_minimax.score
        == result_alpha_beta.score
    )


def test_alpha_beta_explores_no_more_nodes():
    state = create_default_scenario()

    result_minimax = MinimaxAgent(
        depth=3
    ).search(state)

    result_alpha_beta = AlphaBetaAgent(
        depth=3
    ).search(state)

    assert (
        result_alpha_beta.nodes_explored
        <= result_minimax.nodes_explored
    )


def test_alpha_beta_records_cutoffs():
    state = create_default_scenario()

    result = AlphaBetaAgent(
        depth=3
    ).search(state)

    assert result.cutoffs >= 0
    assert result.pruned_branches >= 0


def test_minimax_does_not_modify_original_state():
    state = create_default_scenario()

    original_position = state.tanks[
        PlayerId.PLAYER_1
    ].position

    original_hp = state.tanks[
        PlayerId.PLAYER_1
    ].hp

    MinimaxAgent(depth=2).search(state)

    assert state.tanks[
        PlayerId.PLAYER_1
    ].position == original_position

    assert state.tanks[
        PlayerId.PLAYER_1
    ].hp == original_hp


def test_alpha_beta_does_not_modify_original_state():
    state = create_default_scenario()

    original_position = state.tanks[
        PlayerId.PLAYER_1
    ].position

    AlphaBetaAgent(depth=2).search(state)

    assert state.tanks[
        PlayerId.PLAYER_1
    ].position == original_position


def test_terminal_state_returns_no_action():
    state = create_default_scenario()

    state.bases[
        PlayerId.PLAYER_2
    ].hp = 0

    minimax_result = MinimaxAgent(
        depth=2
    ).search(state)

    alpha_beta_result = AlphaBetaAgent(
        depth=2
    ).search(state)

    assert minimax_result.best_action is None
    assert alpha_beta_result.best_action is None

    assert minimax_result.score == 100000
    assert alpha_beta_result.score == 100000


def test_search_uses_custom_evaluator():
    state = create_default_scenario()

    evaluator = MaterialEvaluator()

    score = evaluator(
        state,
        PlayerId.PLAYER_1
    )

    assert score == 0

    result = MinimaxAgent(
        depth=2,
        evaluator=evaluator
    ).search(state)

    assert result.best_action in Action


@pytest.mark.parametrize(
    "agent_class",
    [MinimaxAgent, AlphaBetaAgent]
)
def test_invalid_search_depth(agent_class):
    with pytest.raises(ValueError):
        agent_class(depth=0)


@pytest.mark.parametrize(
    "agent_class",
    [MinimaxAgent, AlphaBetaAgent]
)
def test_invalid_search_perspective(agent_class):
    state = create_default_scenario()

    agent = agent_class(depth=2)

    with pytest.raises(ValueError):
        agent.search(
            state,
            perspective=PlayerId.PLAYER_2
        )
