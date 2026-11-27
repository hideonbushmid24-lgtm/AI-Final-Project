"""Adapters for the existing Tank Battle search algorithms."""

from ..constants import Action
from ..game_state import GameState

from ..search.minimax import MinimaxAgent
from ..search.alpha_beta import AlphaBetaAgent
from ..search.heuristic_agents import (
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent,
)

from .base_agent import BaseAgent, AgentError


class SearchAgentAdapter(BaseAgent):
    """
    Adapt an existing search agent to the common BaseAgent API.

    The underlying search implementation is not modified.
    """

    def __init__(self, search_agent, name=None):
        if not callable(getattr(search_agent, "search", None)):
            raise TypeError(
                "search_agent must provide a callable search() method."
            )

        self.search_agent = search_agent
        self.name = name or type(search_agent).__name__
        self.last_result = None

    def select_action(self, state: GameState) -> Action:
        result = self.search_agent.search(state)

        if result.best_action is None:
            raise AgentError(
                f"{self.name} did not return an action."
            )

        self.last_result = result

        return Action(result.best_action)

    def reset(self) -> None:
        """Clear the last search result."""
        self.last_result = None


def create_search_agent(algorithm: str, depth: int = 2):
    """Create one of the four existing search configurations."""

    factories = {
        "Minimax": MinimaxAgent,
        "Alpha-Beta": AlphaBetaAgent,
        "Heuristic Minimax": HeuristicMinimaxAgent,
        "Heuristic Minimax + Alpha-Beta": HeuristicAlphaBetaAgent,
    }

    if algorithm not in factories:
        raise ValueError(
            f"Unknown search algorithm: {algorithm}"
        )

    search_agent = factories[algorithm](depth=depth)

    return SearchAgentAdapter(
        search_agent=search_agent,
        name=algorithm,
    )


def get_search_algorithm_names() -> tuple[str, ...]:
    """Return the names of all supported search algorithms."""

    return (
        "Minimax",
        "Alpha-Beta",
        "Heuristic Minimax",
        "Heuristic Minimax + Alpha-Beta",
    )