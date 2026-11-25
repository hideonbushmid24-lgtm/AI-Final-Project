
from math import inf
from time import perf_counter
from typing import Callable

from ..constants import PlayerId, Action
from ..game_state import GameState
from ..game_engine import GameEngine
from ..evaluation import MaterialEvaluator

from .search_result import SearchResult


Evaluator = Callable[[GameState, PlayerId], float]


class MinimaxAgent:
    """
    Depth-limited Minimax Search.

    The root player's perspective is used for every
    evaluation in the search tree.
    """

    def __init__(
        self,
        depth: int = 2,
        evaluator: Evaluator | None = None
    ):
        if (
            not isinstance(depth, int)
            or isinstance(depth, bool)
            or depth < 1
        ):
            raise ValueError(
                "Search depth must be a positive integer."
            )

        self.depth = depth

        self.evaluator = (
            evaluator
            if evaluator is not None
            else MaterialEvaluator()
        )

        self.engine = GameEngine()

    def search(
        self,
        state: GameState,
        perspective: PlayerId | None = None
    ) -> SearchResult:
        """
        Find the best action using Minimax.

        Depth counts individual player actions (plies).
        """

        if not isinstance(state, GameState):
            raise TypeError("state must be a GameState.")

        if perspective is not None and perspective != state.current_player:
            raise ValueError(
                "Search perspective must match the current player."
        )

        root_player = state.current_player

        if not isinstance(root_player, PlayerId):
            raise ValueError("Invalid search perspective.")

        start_time = perf_counter()

        stats = {
            "nodes": 1,
            "leaves": 0,
            "terminal": 0,
            "max_depth": 0
        }

        def minimax(
            current_state: GameState,
            remaining_depth: int,
            current_depth: int
        ) -> float:

            stats["nodes"] += 1

            stats["max_depth"] = max(
                stats["max_depth"],
                current_depth
            )

            # Terminal state.
            if current_state.is_terminal:
                stats["leaves"] += 1
                stats["terminal"] += 1

                return self.evaluator(
                    current_state,
                    root_player
                )

            # Depth limit.
            if remaining_depth == 0:
                stats["leaves"] += 1

                return self.evaluator(
                    current_state,
                    root_player
                )

            actions = GameEngine.get_legal_actions(
                current_state
            )

            if not actions:
                stats["leaves"] += 1

                return self.evaluator(
                    current_state,
                    root_player
                )

            maximizing = (
                current_state.current_player
                == root_player
            )

            if maximizing:
                best_score = -inf

                for action in actions:

                    child = self.engine.apply_action(
                        current_state,
                        action
                    ).state

                    score = minimax(
                        child,
                        remaining_depth - 1,
                        current_depth + 1
                    )

                    best_score = max(
                        best_score,
                        score
                    )

                return best_score

            else:
                best_score = inf

                for action in actions:

                    child = self.engine.apply_action(
                        current_state,
                        action
                    ).state

                    score = minimax(
                        child,
                        remaining_depth - 1,
                        current_depth + 1
                    )

                    best_score = min(
                        best_score,
                        score
                    )

                return best_score

        # Terminal root state has no available action.
        if state.is_terminal:
            score = self.evaluator(
                state,
                root_player
            )

            stats["nodes"] = 1
            stats["leaves"] = 1
            stats["terminal"] = 1

            elapsed = perf_counter() - start_time

            return SearchResult(
                algorithm="Minimax",
                best_action=None,
                score=score,
                requested_depth=self.depth,
                max_depth_reached=0,
                nodes_explored=1,
                leaf_nodes=1,
                terminal_nodes=1,
                cutoffs=0,
                pruned_branches=0,
                elapsed_time_seconds=elapsed
            )

        root_actions = GameEngine.get_legal_actions(state)

        best_action = None
        best_score = -inf

        # The root is always a maximizing node
        # from the selected player's perspective.
        for action in root_actions:

            child = self.engine.apply_action(
                state,
                action
            ).state

            score = minimax(
                child,
                self.depth - 1,
                1
            )

            if score > best_score:
                best_score = score
                best_action = action

        elapsed = perf_counter() - start_time

        return SearchResult(
            algorithm="Minimax",
            best_action=best_action,
            score=best_score,

            requested_depth=self.depth,
            max_depth_reached=stats["max_depth"],

            nodes_explored=stats["nodes"],
            leaf_nodes=stats["leaves"],
            terminal_nodes=stats["terminal"],

            cutoffs=0,
            pruned_branches=0,

            elapsed_time_seconds=elapsed
        )
