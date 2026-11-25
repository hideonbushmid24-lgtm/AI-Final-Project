
from ..evaluation import (
    HeuristicEvaluator,
    HeuristicWeights,
)

from ..constants import PlayerId
from ..game_state import GameState

from .minimax import MinimaxAgent
from .alpha_beta import AlphaBetaAgent


class HeuristicMinimaxAgent(MinimaxAgent):
    """Minimax search using an advanced heuristic evaluator."""

    def __init__(
        self,
        depth: int = 2,
        weights: HeuristicWeights | None = None
    ):
        super().__init__(
            depth=depth,
            evaluator=HeuristicEvaluator(weights)
        )

    def search(
        self,
        state: GameState,
        perspective: PlayerId | None = None
    ):
        result = super().search(
            state,
            perspective
        )

        result.algorithm = "Heuristic Minimax"

        return result


class HeuristicAlphaBetaAgent(AlphaBetaAgent):
    """
    Heuristic Minimax combined with Alpha-Beta Pruning.
    """

    def __init__(
        self,
        depth: int = 2,
        weights: HeuristicWeights | None = None
    ):
        super().__init__(
            depth=depth,
            evaluator=HeuristicEvaluator(weights)
        )

    def search(
        self,
        state: GameState,
        perspective: PlayerId | None = None
    ):
        result = super().search(
            state,
            perspective
        )

        result.algorithm = (
            "Heuristic Minimax + Alpha-Beta"
        )

        return result
