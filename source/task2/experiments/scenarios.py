from tank_battle.constants import (
    PlayerId,
    Direction,
    GAME_WIDTH,
    GAME_HEIGHT,
)

from tank_battle.entities import (
    Position,
    Tank,
    Base,
    Wall,
    Bullet,
)

from tank_battle.game_state import GameState

from tank_battle.scenario import (
    create_default_scenario as _create_default_scenario,
)


def create_default_scenario() -> GameState:
    """Create the existing default scenario."""
    return _create_default_scenario()


def create_open_scenario() -> GameState:
    """Create an open map without walls."""

    tanks = {
        PlayerId.PLAYER_1: Tank(
            player=PlayerId.PLAYER_1,
            position=Position(2, 6),
            facing=Direction.RIGHT,
        ),
        PlayerId.PLAYER_2: Tank(
            player=PlayerId.PLAYER_2,
            position=Position(10, 6),
            facing=Direction.LEFT,
        ),
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            player=PlayerId.PLAYER_1,
            position=Position(1, 12),
        ),
        PlayerId.PLAYER_2: Base(
            player=PlayerId.PLAYER_2,
            position=Position(11, 0),
        ),
    }

    return GameState(
        width=GAME_WIDTH,
        height=GAME_HEIGHT,
        tanks=tanks,
        bases=bases,
        walls={},
        current_player=PlayerId.PLAYER_1,
    )


def create_obstacle_scenario() -> GameState:
    """Create a maze-like map with an open central corridor."""

    tanks = {
        PlayerId.PLAYER_1: Tank(
            player=PlayerId.PLAYER_1,
            position=Position(1, 10),
            facing=Direction.UP,
        ),
        PlayerId.PLAYER_2: Tank(
            player=PlayerId.PLAYER_2,
            position=Position(11, 2),
            facing=Direction.DOWN,
        ),
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            player=PlayerId.PLAYER_1,
            position=Position(1, 12),
        ),
        PlayerId.PLAYER_2: Base(
            player=PlayerId.PLAYER_2,
            position=Position(11, 0),
        ),
    }

    wall_positions = []

    # Vertical obstacles with gaps at y = 6.
    wall_positions.extend(
        Position(4, y)
        for y in range(1, 12)
        if y != 6
    )

    wall_positions.extend(
        Position(8, y)
        for y in range(1, 12)
        if y != 6
    )

    # Horizontal obstacles.
    for y in (4, 8):
        for x in (5, 6, 7):
            wall_positions.append(Position(x, y))

    walls = {
        position: Wall(position=position)
        for position in wall_positions
    }

    return GameState(
        width=GAME_WIDTH,
        height=GAME_HEIGHT,
        tanks=tanks,
        bases=bases,
        walls=walls,
        current_player=PlayerId.PLAYER_1,
    )


def create_combat_scenario() -> GameState:
    """
    Create a close-range combat scenario.

    Both tanks face each other.
    Two bullets are already moving toward opposing tanks.
    """

    tanks = {
        PlayerId.PLAYER_1: Tank(
            player=PlayerId.PLAYER_1,
            position=Position(3, 6),
            facing=Direction.RIGHT,
        ),
        PlayerId.PLAYER_2: Tank(
            player=PlayerId.PLAYER_2,
            position=Position(9, 6),
            facing=Direction.LEFT,
        ),
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            player=PlayerId.PLAYER_1,
            position=Position(1, 12),
        ),
        PlayerId.PLAYER_2: Base(
            player=PlayerId.PLAYER_2,
            position=Position(11, 0),
        ),
    }

    wall_positions = [
        Position(5, 4),
        Position(7, 4),
        Position(5, 8),
        Position(7, 8),
    ]

    walls = {
        position: Wall(position=position)
        for position in wall_positions
    }

    bullets = [
        Bullet(
            bullet_id=1,
            owner=PlayerId.PLAYER_1,
            position=Position(6, 6),
            direction=Direction.RIGHT,
        ),
        Bullet(
            bullet_id=2,
            owner=PlayerId.PLAYER_2,
            position=Position(5, 6),
            direction=Direction.LEFT,
        ),
    ]

    return GameState(
        width=GAME_WIDTH,
        height=GAME_HEIGHT,
        tanks=tanks,
        bases=bases,
        walls=walls,
        bullets=bullets,
        current_player=PlayerId.PLAYER_1,
        next_bullet_id=3,
    )


# Each factory creates a new GameState.
SCENARIO_FACTORIES = {
    "S1_Default": create_default_scenario,
    "S2_Open": create_open_scenario,
    "S3_Obstacle": create_obstacle_scenario,
    "S4_Combat": create_combat_scenario,
}


def create_all_scenarios() -> dict[str, GameState]:
    """Create fresh instances of all four scenarios."""

    return {
        name: factory()
        for name, factory in SCENARIO_FACTORIES.items()
    }