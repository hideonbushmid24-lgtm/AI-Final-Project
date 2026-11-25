
from .constants import (
    PlayerId,
    Direction,
)

from .entities import (
    Position,
    Tank,
    Base,
    Wall,
)

from .game_state import GameState


def create_default_scenario() -> GameState:
    """
    Create a 13 x 13 Tank Battle scenario.

    Player 1 starts near the bottom-left.
    Player 2 starts near the top-right.
    Both players have one tank and one base.
    """

    width = 13
    height = 13

    tanks = {
        PlayerId.PLAYER_1: Tank(
            player=PlayerId.PLAYER_1,
            position=Position(1, 10),
            facing=Direction.UP
        ),

        PlayerId.PLAYER_2: Tank(
            player=PlayerId.PLAYER_2,
            position=Position(11, 2),
            facing=Direction.DOWN
        )
    }

    bases = {
        PlayerId.PLAYER_1: Base(
            player=PlayerId.PLAYER_1,
            position=Position(1, 12)
        ),

        PlayerId.PLAYER_2: Base(
            player=PlayerId.PLAYER_2,
            position=Position(11, 0)
        )
    }

    wall_positions = []

    # Upper-left and upper-right obstacles.
    for x in (3, 4, 5, 7, 8, 9):
        wall_positions.append(Position(x, 4))

    # Lower-left and lower-right obstacles.
    for x in (3, 4, 5, 7, 8, 9):
        wall_positions.append(Position(x, 8))

    # Central obstacles.
    for y in (5, 6, 7):
        wall_positions.append(Position(6, y))

    walls = {
        position: Wall(position=position)
        for position in wall_positions
    }

    return GameState(
        width=width,
        height=height,
        tanks=tanks,
        bases=bases,
        walls=walls,
        current_player=PlayerId.PLAYER_1
    )
