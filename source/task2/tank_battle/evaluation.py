
from .constants import PlayerId, TERMINAL_UTILITY
from .game_state import GameState


class MaterialEvaluator:
    """
    Basic zero-sum material evaluation.

    The score is calculated from the perspective
    of the player requesting the evaluation.

    The current implementation considers:
        - Tank HP
        - Base HP

    A more advanced heuristic will be added
    in the next milestone.
    """

    def __call__(
        self,
        state: GameState,
        perspective: PlayerId
    ) -> float:

        if not isinstance(perspective, PlayerId):
            raise TypeError("Invalid evaluation perspective.")

        # Terminal states always take priority.
        if state.is_terminal:

            if state.is_draw:
                return 0.0

            if state.winner == perspective:
                return float(TERMINAL_UTILITY)

            return float(-TERMINAL_UTILITY)

        opponent = perspective.opponent

        own_tank_hp = state.tanks[perspective].hp
        own_base_hp = state.bases[perspective].hp

        enemy_tank_hp = state.tanks[opponent].hp
        enemy_base_hp = state.bases[opponent].hp

        own_material = own_tank_hp + own_base_hp
        enemy_material = enemy_tank_hp + enemy_base_hp

        return float(
            own_material - enemy_material
        )
