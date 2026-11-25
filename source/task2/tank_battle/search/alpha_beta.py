
from math import inf
from time import perf_counter
from typing import Callable

from ..constants import PlayerId, Action
from ..game_state import GameState
from ..game_engine import GameEngine
from ..evaluation import MaterialEvaluator

from .search_result import SearchResult


Evaluator = Callable[[GameState, PlayerId], float]


class AlphaBetaAgent:
    """
    Depth-limited Minimax with Alpha-Beta Pruning.
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
            "cutoffs": 0,
            "pruned": 0,
            "max_depth": 0
        }

        def alpha_beta(
            current_state: GameState,
            remaining_depth: int,
            current_depth: int,
            alpha: float,
            beta: float
        ) -> float:

            stats["nodes"] += 1

            stats["max_depth"] = max(
                stats["max_depth"],
                current_depth
            )

            if current_state.is_terminal:
                stats["leaves"] += 1
                stats["terminal"] += 1

                return self.evaluator(
                    current_state,
                    root_player
                )

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

                value = -inf

                for index, action in enumerate(actions):

                    child = self.engine.apply_action(
                        current_state,
                        action
                    ).state

                    score = alpha_beta(
                        child,
                        remaining_depth - 1,
                        current_depth + 1,
                        alpha,
                        beta
                    )

                    value = max(value, score)
                    alpha = max(alpha, value)

                    # Alpha-Beta cutoff.
                    if alpha >= beta:

                        stats["cutoffs"] += 1

                        stats["pruned"] += (
                            len(actions) - index - 1
                        )

                        break

                return value

            else:

                value = inf

                for index, action in enumerate(actions):

                    child = self.engine.apply_action(
                        current_state,
                        action
                    ).state

                    score = alpha_beta(
                        child,
                        remaining_depth - 1,
                        current_depth + 1,
                        alpha,
                        beta
                    )

                    value = min(value, score)
                    beta = min(beta, value)

                    # Alpha-Beta cutoff.
                    if alpha >= beta:

                        stats["cutoffs"] += 1

                        stats["pruned"] += (
                            len(actions) - index - 1
                        )

                        break

                return value

        if state.is_terminal:

            score = self.evaluator(
                state,
                root_player
            )

            return SearchResult(
                algorithm="Alpha-Beta",
                best_action=None,
                score=score,

                requested_depth=self.depth,
                max_depth_reached=0,

                nodes_explored=1,
                leaf_nodes=1,
                terminal_nodes=1,

                cutoffs=0,
                pruned_branches=0,

                elapsed_time_seconds=(
                    perf_counter() - start_time
                )
            )

        root_actions = GameEngine.get_legal_actions(state)

        best_action = None
        best_score = -inf

        alpha = -inf
        beta = inf

        # Root is a maximizing node.
        for index, action in enumerate(root_actions):

            child = self.engine.apply_action(
                state,
                action
            ).state

            score = alpha_beta(
                child,
                self.depth - 1,
                1,
                alpha,
                beta
            )

            if score > best_score:
                best_score = score
                best_action = action

            alpha = max(alpha, best_score)

            # Cut off remaining root actions if possible.
            if alpha >= beta:

                stats["cutoffs"] += 1

                stats["pruned"] += (
                    len(root_actions) - index - 1
                )

                break

        elapsed = perf_counter() - start_time

        return SearchResult(
            algorithm="Alpha-Beta",
            best_action=best_action,
            score=best_score,

            requested_depth=self.depth,
            max_depth_reached=stats["max_depth"],

            nodes_explored=stats["nodes"],
            leaf_nodes=stats["leaves"],
            terminal_nodes=stats["terminal"],

            cutoffs=stats["cutoffs"],
            pruned_branches=stats["pruned"],

            elapsed_time_seconds=elapsed
        )
