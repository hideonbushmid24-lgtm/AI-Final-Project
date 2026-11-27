"""A simple random agent used for testing and demonstrations."""

import random

from ..constants import Action
from ..game_state import GameState
from ..game_engine import GameEngine

from .base_agent import BaseAgent, AgentError


class RandomAgent(BaseAgent):
    """Choose randomly from the available game actions."""

    name = "Random Agent"

    def __init__(self, seed=None):
        self.random = random.Random(seed)

    def select_action(self, state: GameState) -> Action:
        actions = GameEngine.get_legal_actions(state)

        if not actions:
            raise AgentError(
                "No legal actions are available."
            )

        return self.random.choice(actions)