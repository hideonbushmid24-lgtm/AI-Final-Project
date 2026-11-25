
from enum import Enum, IntEnum


class PlayerId(IntEnum):
    PLAYER_1 = 1
    PLAYER_2 = 2

    @property
    def opponent(self):
        if self == PlayerId.PLAYER_1:
            return PlayerId.PLAYER_2

        return PlayerId.PLAYER_1


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Action(str, Enum):
    MOVE_UP = "MOVE_UP"
    MOVE_DOWN = "MOVE_DOWN"
    MOVE_LEFT = "MOVE_LEFT"
    MOVE_RIGHT = "MOVE_RIGHT"
    FIRE = "FIRE"
    STAY = "STAY"


# Screen coordinates:
# x increases to the right.
# y increases downward.

DIRECTION_DELTAS = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
}


ACTION_TO_DIRECTION = {
    Action.MOVE_UP: Direction.UP,
    Action.MOVE_DOWN: Direction.DOWN,
    Action.MOVE_LEFT: Direction.LEFT,
    Action.MOVE_RIGHT: Direction.RIGHT,
}


TANK_INITIAL_HP = 6
BASE_INITIAL_HP = 9
WALL_INITIAL_HP = 3

DAMAGE_PER_HIT = 1

TANK_MOVE_DISTANCE = 1
BULLET_SPEED_PER_CYCLE = 3

GAME_WIDTH = 13
GAME_HEIGHT = 13

TERMINAL_UTILITY = 100_000
