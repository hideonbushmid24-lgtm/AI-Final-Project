
from dataclasses import dataclass

from .constants import (
    PlayerId,
    Direction,
    DIRECTION_DELTAS,
    TANK_INITIAL_HP,
    BASE_INITIAL_HP,
    WALL_INITIAL_HP,
)


@dataclass(frozen=True, slots=True)
class Position:
    """Represent a cell position on the game board."""

    x: int
    y: int

    def moved(self, direction: Direction):
        """Return a new position after moving one cell."""

        dx, dy = DIRECTION_DELTAS[direction]

        return Position(
            x=self.x + dx,
            y=self.y + dy
        )


def validate_hp(hp: int, maximum: int):
    """Validate health values."""

    if (
        not isinstance(hp, int)
        or isinstance(hp, bool)
        or not 0 <= hp <= maximum
    ):
        raise ValueError(
            f"HP must be between 0 and {maximum}."
        )


@dataclass(slots=True)
class Tank:
    """Represent a player's tank."""

    player: PlayerId
    position: Position
    facing: Direction = Direction.UP
    hp: int = TANK_INITIAL_HP

    def __post_init__(self):
        if not isinstance(self.player, PlayerId):
            raise TypeError("Invalid tank player.")

        if not isinstance(self.position, Position):
            raise TypeError("Invalid tank position.")

        if not isinstance(self.facing, Direction):
            raise TypeError("Invalid tank direction.")

        validate_hp(self.hp, TANK_INITIAL_HP)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass(slots=True)
class Base:
    """Represent a player's protected base."""

    player: PlayerId
    position: Position
    hp: int = BASE_INITIAL_HP

    def __post_init__(self):
        if not isinstance(self.player, PlayerId):
            raise TypeError("Invalid base player.")

        if not isinstance(self.position, Position):
            raise TypeError("Invalid base position.")

        validate_hp(self.hp, BASE_INITIAL_HP)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0


@dataclass(slots=True)
class Wall:
    """Represent a destructible wall cell."""

    position: Position
    hp: int = WALL_INITIAL_HP

    def __post_init__(self):
        if not isinstance(self.position, Position):
            raise TypeError("Invalid wall position.")

        validate_hp(self.hp, WALL_INITIAL_HP)

    @property
    def is_destroyed(self) -> bool:
        return self.hp <= 0


@dataclass(frozen=True, slots=True)
class Bullet:
    """Represent a moving bullet."""

    bullet_id: int
    owner: PlayerId
    position: Position
    direction: Direction

    def __post_init__(self):
        if (
            not isinstance(self.bullet_id, int)
            or isinstance(self.bullet_id, bool)
            or self.bullet_id < 0
        ):
            raise ValueError("Invalid bullet ID.")

        if not isinstance(self.owner, PlayerId):
            raise TypeError("Invalid bullet owner.")

        if not isinstance(self.position, Position):
            raise TypeError("Invalid bullet position.")

        if not isinstance(self.direction, Direction):
            raise TypeError("Invalid bullet direction.")
