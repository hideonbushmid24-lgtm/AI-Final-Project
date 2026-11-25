
from dataclasses import dataclass
from typing import Any

from .constants import (
    PlayerId,
    Direction,
    Action,
    ACTION_TO_DIRECTION,
    BULLET_SPEED_PER_CYCLE,
    DAMAGE_PER_HIT,
)

from .entities import (
    Position,
    Bullet,
)

from .game_state import GameState, ALL_PLAYERS


class GameRuleError(ValueError):
    """Raised when an action violates the game rules."""


@dataclass(frozen=True)
class GameEvent:
    """Represent an event produced by the game engine."""

    event_type: str
    position: Position | None = None
    player: PlayerId | None = None
    message: str = ""


@dataclass
class TransitionResult:
    """Store the updated state and events of one action."""

    state: GameState
    events: list[GameEvent]


class GameEngine:
    """
    Execute Tank Battle rules and state transitions.

    A complete game cycle contains:
        1. Player 1 action.
        2. Player 2 action.
        3. Bullet movement and collision resolution.

    Bullet movement is processed after both players act.
    Each bullet travels up to three cells per cycle.
    """

    @staticmethod
    def get_legal_actions(
        state: GameState
    ) -> tuple[Action, ...]:
        """
        Return the six available actions.

        Movement into a blocked cell is still an action:
        the tank remains in place, its facing changes,
        and the turn is consumed.
        """

        if state.is_terminal:
            return ()

        return tuple(Action)

    @staticmethod
    def _is_tank_at(
        state: GameState,
        position: Position,
        exclude_player: PlayerId | None = None
    ) -> bool:

        return any(
            tank.is_alive
            and tank.position == position
            and tank.player != exclude_player
            for tank in state.tanks.values()
        )

    @staticmethod
    def _is_base_at(
        state: GameState,
        position: Position
    ) -> bool:

        return any(
            base.is_alive
            and base.position == position
            for base in state.bases.values()
        )

    @classmethod
    def _is_blocked_for_tank(
        cls,
        state: GameState,
        position: Position,
        moving_player: PlayerId
    ) -> bool:

        if not state.is_inside(position):
            return True

        if position in state.walls:
            return True

        if cls._is_tank_at(
            state,
            position,
            exclude_player=moving_player
        ):
            return True

        if cls._is_base_at(state, position):
            return True

        return False

    @staticmethod
    def _get_tank_at(
        state: GameState,
        position: Position
    ):

        for player in ALL_PLAYERS:
            tank = state.tanks[player]

            if tank.is_alive and tank.position == position:
                return tank

        return None

    @staticmethod
    def _get_base_at(
        state: GameState,
        position: Position
    ):

        for player in ALL_PLAYERS:
            base = state.bases[player]

            if base.is_alive and base.position == position:
                return base

        return None

    @classmethod
    def apply_action(
        cls,
        original_state: GameState,
        action: Action | str
    ) -> TransitionResult:
        """
        Apply one player's action without modifying the input state.

        Returns a new GameState and the generated events.
        """

        if not isinstance(original_state, GameState):
            raise TypeError("original_state must be a GameState.")

        if original_state.is_terminal:
            raise GameRuleError(
                "Cannot perform an action after the game has ended."
            )

        try:
            action = Action(action)
        except (ValueError, TypeError):
            raise GameRuleError(
                f"Invalid action: {action}"
            ) from None

        # Work on an independent state copy.
        state = original_state.clone()

        events = []

        player = state.current_player
        tank = state.tanks[player]

        # Movement actions.
        if action in ACTION_TO_DIRECTION:

            direction = ACTION_TO_DIRECTION[action]

            # Facing changes even if movement is blocked.
            tank.facing = direction

            target = tank.position.moved(direction)

            if cls._is_blocked_for_tank(
                state,
                target,
                player
            ):
                events.append(
                    GameEvent(
                        event_type="movement_blocked",
                        position=target,
                        player=player,
                        message="Tank movement was blocked."
                    )
                )

            else:
                tank.position = target

                events.append(
                    GameEvent(
                        event_type="tank_moved",
                        position=target,
                        player=player,
                        message="Tank moved one cell."
                    )
                )

        # Fire action.
        elif action == Action.FIRE:

            bullet = Bullet(
                bullet_id=state.next_bullet_id,
                owner=player,
                position=tank.position,
                direction=tank.facing
            )

            state.next_bullet_id += 1
            state.bullets.append(bullet)

            events.append(
                GameEvent(
                    event_type="bullet_created",
                    position=tank.position,
                    player=player,
                    message="Tank fired a bullet."
                )
            )

        # Stay action.
        elif action == Action.STAY:

            events.append(
                GameEvent(
                    event_type="tank_stayed",
                    position=tank.position,
                    player=player,
                    message="Tank stayed in its position."
                )
            )

        # Switch to the other player.
        state.current_player = player.opponent

        # Completing Player 2's action completes a full cycle.
        if player == PlayerId.PLAYER_2:

            state.cycle_number += 1

            events.append(
                GameEvent(
                    event_type="cycle_completed",
                    message="A game cycle has been completed."
                )
            )

            cls._advance_bullets(state, events)

        state.validate()

        return TransitionResult(
            state=state,
            events=events
        )

    @classmethod
    def _advance_bullets(
        cls,
        state: GameState,
        events: list[GameEvent]
    ) -> None:
        """
        Advance every active bullet by up to three cells.

        Bullets are processed in ascending bullet ID order.
        A bullet is consumed immediately upon collision or
        when it leaves the board.
        """

        remaining_bullets = []

        ordered_bullets = sorted(
            state.bullets,
            key=lambda bullet: bullet.bullet_id
        )

        for bullet in ordered_bullets:

            position = bullet.position
            consumed = False

            for _ in range(BULLET_SPEED_PER_CYCLE):

                next_position = position.moved(
                    bullet.direction
                )

                # Boundary collision.
                if not state.is_inside(next_position):

                    events.append(
                        GameEvent(
                            event_type="bullet_out_of_bounds",
                            position=next_position,
                            player=bullet.owner,
                            message="Bullet left the board."
                        )
                    )

                    consumed = True
                    break

                position = next_position

                # Wall collision.
                wall = state.walls.get(position)

                if wall is not None:

                    wall.hp -= DAMAGE_PER_HIT

                    events.append(
                        GameEvent(
                            event_type="bullet_hit_wall",
                            position=position,
                            player=bullet.owner,
                            message=f"Wall HP: {wall.hp}."
                        )
                    )

                    if wall.is_destroyed:

                        state.walls.pop(position)

                        events.append(
                            GameEvent(
                                event_type="wall_destroyed",
                                position=position,
                                player=bullet.owner,
                                message="Wall was destroyed."
                            )
                        )

                    consumed = True
                    break

                # Tank collision.
                tank = cls._get_tank_at(
                    state,
                    position
                )

                if tank is not None:

                    tank.hp = max(
                        0,
                        tank.hp - DAMAGE_PER_HIT
                    )

                    events.append(
                        GameEvent(
                            event_type="bullet_hit_tank",
                            position=position,
                            player=tank.player,
                            message=f"Tank HP: {tank.hp}."
                        )
                    )

                    consumed = True
                    break

                # Base collision.
                base = cls._get_base_at(
                    state,
                    position
                )

                if base is not None:

                    base.hp = max(
                        0,
                        base.hp - DAMAGE_PER_HIT
                    )

                    events.append(
                        GameEvent(
                            event_type="bullet_hit_base",
                            position=position,
                            player=base.player,
                            message=f"Base HP: {base.hp}."
                        )
                    )

                    consumed = True
                    break

            # Keep bullets that did not collide.
            if not consumed:

                remaining_bullets.append(
                    Bullet(
                        bullet_id=bullet.bullet_id,
                        owner=bullet.owner,
                        position=position,
                        direction=bullet.direction
                    )
                )

                events.append(
                    GameEvent(
                        event_type="bullet_advanced",
                        position=position,
                        player=bullet.owner,
                        message="Bullet advanced this cycle."
                    )
                )

            # Stop processing when a player is defeated.
            if state.is_terminal:

                state.bullets = []

                events.append(
                    GameEvent(
                        event_type="game_over",
                        player=state.winner,
                        message=(
                            "The game ended after a decisive hit."
                            if state.winner is not None
                            else "The game ended in a draw."
                        )
                    )
                )

                return

        state.bullets = remaining_bullets
