"""Common interface for all Tank Battle AI agents."""

from abc import ABC, abstractmethod

from ..constants import Action
from ..game_state import GameState


class AgentError(RuntimeError):
    """Raised when an agent cannot provide a valid action."""


class BaseAgent(ABC):
    """
    Abstract base class for built-in and external agents.

    Every agent receives the current GameState and returns
    one valid Action for state.current_player.
    """

    name = "Base Agent"

    @abstractmethod
    def select_action(self, state: GameState) -> Action:
        """Choose an action for the current player."""
        raise NotImplementedError

    def get_action(self, state: GameState) -> Action:
        """
        Validate the input and normalize the agent output.

        GUI and game controllers should call this method
        instead of calling select_action directly.
        """

        if not isinstance(state, GameState):
            raise TypeError("state must be a GameState.")

        if state.is_terminal:
            raise AgentError(
                "Cannot request an action from a terminal state."
            )

        try:
            action = self.select_action(state)
            return Action(action)
        except (ValueError, TypeError) as exc:
            raise AgentError(
                f"{self.name} returned an invalid action: {exc}"
            ) from exc

    def reset(self) -> None:
        """Optional hook for resetting agent-specific state."""