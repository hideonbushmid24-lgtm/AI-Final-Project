
from collections import deque
from dataclasses import dataclass

from .constants import (
    PlayerId,
    Direction,
    DIRECTION_DELTAS,
    TERMINAL_UTILITY,
)

from .game_state import GameState


@dataclass(frozen=True)
class HeuristicWeights:
    """Weights used by the heuristic evaluation function."""

    tank_hp: float = 12.0
    base_hp: float = 18.0
    distance: float = 1.5
    mobility: float = 1.0
    bullet_threat: float = 4.0


class MaterialEvaluator:
    """
    Basic evaluation based on tank and base HP.

    This evaluator is retained as the baseline
    for the two non-heuristic search algorithms.
    """

    def __call__(
        self,
        state: GameState,
        perspective: PlayerId
    ) -> float:

        if not isinstance(perspective, PlayerId):
            raise TypeError("Invalid evaluation perspective.")

        if state.is_terminal:

            if state.is_draw:
                return 0.0

            if state.winner == perspective:
                return float(TERMINAL_UTILITY)

            return float(-TERMINAL_UTILITY)

        opponent = perspective.opponent

        own_material = (
            state.tanks[perspective].hp
            + state.bases[perspective].hp
        )

        enemy_material = (
            state.tanks[opponent].hp
            + state.bases[opponent].hp
        )

        return float(own_material - enemy_material)


class HeuristicEvaluator:
    """
    Advanced zero-sum heuristic evaluation.

    Features:
        1. Tank HP difference.
        2. Base HP difference.
        3. Path distance to opponent assets.
        4. Tank mobility difference.
        5. Active bullet threat.

    All features are calculated from the perspective
    of one player.
    """

    def __init__(
        self,
        weights: HeuristicWeights | None = None
    ):
        self.weights = (
            weights
            if weights is not None
            else HeuristicWeights()
        )

    def __call__(
        self,
        state: GameState,
        perspective: PlayerId
    ) -> float:

        if not isinstance(perspective, PlayerId):
            raise TypeError("Invalid evaluation perspective.")

        if state.is_terminal:

            if state.is_draw:
                return 0.0

            if state.winner == perspective:
                return float(TERMINAL_UTILITY)

            return float(-TERMINAL_UTILITY)

        components = self.evaluate_components(
            state,
            perspective
        )

        return float(sum(components.values()))

    def evaluate_components(
        self,
        state: GameState,
        perspective: PlayerId
    ) -> dict[str, float]:
        """Return individual heuristic feature scores."""

        if state.is_terminal:
            return {
                "terminal": self(state, perspective)
            }

        opponent = perspective.opponent

        own_tank = state.tanks[perspective]
        enemy_tank = state.tanks[opponent]

        own_base = state.bases[perspective]
        enemy_base = state.bases[opponent]

        weights = self.weights

        # 1. Tank health difference.
        tank_score = (
            own_tank.hp - enemy_tank.hp
        ) * weights.tank_hp

        # 2. Base health difference.
        base_score = (
            own_base.hp - enemy_base.hp
        ) * weights.base_hp

        # 3. Distance advantage.
        own_distance = self._distance_to_opponent_assets(
            state,
            perspective
        )

        enemy_distance = self._distance_to_opponent_assets(
            state,
            opponent
        )

        distance_score = (
            enemy_distance - own_distance
        ) * weights.distance

        # 4. Mobility advantage.
        own_mobility = self._count_mobility(
            state,
            perspective
        )

        enemy_mobility = self._count_mobility(
            state,
            opponent
        )

        mobility_score = (
            own_mobility - enemy_mobility
        ) * weights.mobility

        # 5. Bullet threat.
        bullet_score = (
            self._bullet_pressure(state, perspective)
            * weights.bullet_threat
        )

        return {
            "tank_hp": tank_score,
            "base_hp": base_score,
            "distance": distance_score,
            "mobility": mobility_score,
            "bullet_threat": bullet_score
        }

    @staticmethod
    def _distance_to_opponent_assets(
        state: GameState,
        player: PlayerId
    ) -> int:
        """
        Calculate the shortest reachable path from a tank
        to a cell adjacent to the nearest opponent asset.

        BFS explores four-directional movement.

        Walls, living tanks and living bases block movement.
        """

        tank = state.tanks[player]

        if not tank.is_alive:
            return state.width * state.height

        opponent = player.opponent

        targets = []

        enemy_tank = state.tanks[opponent]
        enemy_base = state.bases[opponent]

        if enemy_tank.is_alive:
            targets.append(enemy_tank.position)

        if enemy_base.is_alive:
            targets.append(enemy_base.position)

        if not targets:
            return 0

        blocked = set(state.walls.keys())

        # Other living tanks are obstacles.
        for other_player, other_tank in state.tanks.items():

            if (
                other_player != player
                and other_tank.is_alive
            ):
                blocked.add(other_tank.position)

        # All living bases are obstacles.
        for base in state.bases.values():

            if base.is_alive:
                blocked.add(base.position)

        # Find walkable cells adjacent to opponent assets.
        goals = set()

        for target in targets:

            for direction in DIRECTION_DELTAS:
                candidate = target.moved(direction)

                if (
                    state.is_inside(candidate)
                    and candidate not in blocked
                ):
                    goals.add(candidate)

        start = tank.position

        if start in goals:
            return 0

        queue = deque([(start, 0)])
        visited = {start}

        while queue:

            current, distance = queue.popleft()

            for direction in DIRECTION_DELTAS:

                neighbor = current.moved(direction)

                if not state.is_inside(neighbor):
                    continue

                if neighbor in blocked:
                    continue

                if neighbor in visited:
                    continue

                next_distance = distance + 1

                if neighbor in goals:
                    return next_distance

                visited.add(neighbor)

                queue.append(
                    (neighbor, next_distance)
                )

        # No reachable adjacent target cell.
        return state.width * state.height

    @staticmethod
    def _count_mobility(
        state: GameState,
        player: PlayerId
    ) -> int:
        """Count immediately available tank movement cells."""

        tank = state.tanks[player]

        if not tank.is_alive:
            return 0

        blocked = set(state.walls.keys())

        for other_player, other_tank in state.tanks.items():

            if (
                other_player != player
                and other_tank.is_alive
            ):
                blocked.add(other_tank.position)

        for base in state.bases.values():

            if base.is_alive:
                blocked.add(base.position)

        available = 0

        for direction in DIRECTION_DELTAS:

            candidate = tank.position.moved(direction)

            if not state.is_inside(candidate):
                continue

            if candidate in blocked:
                continue

            available += 1

        return available

    @staticmethod
    def _bullet_pressure(
        state: GameState,
        perspective: PlayerId
    ) -> float:
        """
        Estimate active bullet threats.

        A bullet contributes:
            +1/distance if its first target belongs
            to the opponent.

            -1/distance if its first target belongs
            to the perspective player.

        Walls stop the bullet ray.

        The metric is directional and independent
        of the bullet owner, because friendly fire
        is permitted by the current game rules.
        """

        score = 0.0

        max_steps = state.width + state.height

        for bullet in state.bullets:

            position = bullet.position

            for distance in range(1, max_steps + 1):

                position = position.moved(
                    bullet.direction
                )

                if not state.is_inside(position):
                    break

                # A wall blocks the bullet ray.
                if position in state.walls:
                    break

                target_player = None

                for player, tank in state.tanks.items():

                    if (
                        tank.is_alive
                        and tank.position == position
                    ):
                        target_player = player
                        break

                if target_player is None:

                    for player, base in state.bases.items():

                        if (
                            base.is_alive
                            and base.position == position
                        ):
                            target_player = player
                            break

                if target_player is None:
                    continue

                if target_player == perspective:
                    score -= 1.0 / distance
                else:
                    score += 1.0 / distance

                # Stop at the first encountered entity.
                break

        return score
