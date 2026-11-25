
from copy import deepcopy
from dataclasses import dataclass, field

from .constants import PlayerId
from .entities import (
    Position,
    Tank,
    Base,
    Wall,
    Bullet,
)


ALL_PLAYERS = (
    PlayerId.PLAYER_1,
    PlayerId.PLAYER_2,
)


@dataclass
class GameState:
    """
    Store the complete state of a Tank Battle game.

    All entity dictionaries are indexed by PlayerId,
    except walls, which are indexed by Position.
    """

    width: int
    height: int

    tanks: dict[PlayerId, Tank]
    bases: dict[PlayerId, Base]

    walls: dict[Position, Wall] = field(
        default_factory=dict
    )

    bullets: list[Bullet] = field(
        default_factory=list
    )

    current_player: PlayerId = PlayerId.PLAYER_1
    cycle_number: int = 0
    next_bullet_id: int = 1

    def __post_init__(self):
        self.validate()

    def is_inside(self, position: Position) -> bool:
        """Check whether a position is inside the board."""

        return (
            0 <= position.x < self.width
            and 0 <= position.y < self.height
        )

    def validate(self) -> None:
        """Validate the structural consistency of the game."""

        if (
            not isinstance(self.width, int)
            or isinstance(self.width, bool)
            or self.width <= 0
        ):
            raise ValueError(
                "Board width must be a positive integer."
            )

        if (
            not isinstance(self.height, int)
            or isinstance(self.height, bool)
            or self.height <= 0
        ):
            raise ValueError(
                "Board height must be a positive integer."
            )

        if set(self.tanks) != set(ALL_PLAYERS):
            raise ValueError(
                "The game must contain exactly two tanks."
            )

        if set(self.bases) != set(ALL_PLAYERS):
            raise ValueError(
                "The game must contain exactly two bases."
            )

        if not isinstance(self.current_player, PlayerId):
            raise ValueError("Invalid current player.")

        if (
            not isinstance(self.cycle_number, int)
            or isinstance(self.cycle_number, bool)
            or self.cycle_number < 0
        ):
            raise ValueError("Invalid cycle number.")

        if (
            not isinstance(self.next_bullet_id, int)
            or isinstance(self.next_bullet_id, bool)
            or self.next_bullet_id < 1
        ):
            raise ValueError("Invalid next bullet ID.")

        occupied_positions = set()

        # Validate tanks.
        for player in ALL_PLAYERS:
            tank = self.tanks[player]

            if not isinstance(tank, Tank):
                raise TypeError("Invalid tank object.")

            if tank.player != player:
                raise ValueError(
                    "Tank player ID does not match dictionary key."
                )

            if not self.is_inside(tank.position):
                raise ValueError(
                    "Tank position is outside the board."
                )

            if tank.position in occupied_positions:
                raise ValueError(
                    "Two entities cannot occupy the same cell."
                )

            occupied_positions.add(tank.position)

        # Validate bases.
        for player in ALL_PLAYERS:
            base = self.bases[player]

            if not isinstance(base, Base):
                raise TypeError("Invalid base object.")

            if base.player != player:
                raise ValueError(
                    "Base player ID does not match dictionary key."
                )

            if not self.is_inside(base.position):
                raise ValueError(
                    "Base position is outside the board."
                )

            if base.position in occupied_positions:
                raise ValueError(
                    "Two entities cannot occupy the same cell."
                )

            occupied_positions.add(base.position)

        # Validate walls.
        for position, wall in self.walls.items():

            if not isinstance(position, Position):
                raise TypeError("Invalid wall position key.")

            if not isinstance(wall, Wall):
                raise TypeError("Invalid wall object.")

            if wall.position != position:
                raise ValueError(
                    "Wall position does not match dictionary key."
                )

            if not self.is_inside(position):
                raise ValueError(
                    "Wall position is outside the board."
                )

            if wall.is_destroyed:
                raise ValueError(
                    "Destroyed walls must be removed from the board."
                )

            if position in occupied_positions:
                raise ValueError(
                    "A wall cannot overlap a tank or base."
                )

            occupied_positions.add(position)

        # Validate bullets.
        bullet_ids = set()

        for bullet in self.bullets:

            if not isinstance(bullet, Bullet):
                raise TypeError("Invalid bullet object.")

            if not self.is_inside(bullet.position):
                raise ValueError(
                    "Bullet position is outside the board."
                )

            if bullet.bullet_id in bullet_ids:
                raise ValueError("Duplicate bullet ID.")

            bullet_ids.add(bullet.bullet_id)

        if bullet_ids and self.next_bullet_id <= max(bullet_ids):
            raise ValueError(
                "next_bullet_id must be greater than existing IDs."
            )

    def clone(self) -> "GameState":
        """Create a fully independent copy of the game state."""

        return deepcopy(self)

    @property
    def defeated_players(self) -> tuple[PlayerId, ...]:
        """
        A player is defeated when its tank OR base is destroyed.
        """

        defeated = []

        for player in ALL_PLAYERS:
            tank = self.tanks[player]
            base = self.bases[player]

            if not tank.is_alive or not base.is_alive:
                defeated.append(player)

        return tuple(defeated)

    @property
    def is_terminal(self) -> bool:
        """Check whether the game has ended."""

        return len(self.defeated_players) > 0

    @property
    def is_draw(self) -> bool:
        """Check whether both players are defeated."""

        return len(self.defeated_players) == 2

    @property
    def winner(self) -> PlayerId | None:
        """Return the winner, or None if no unique winner exists."""

        defeated = self.defeated_players

        if len(defeated) != 1:
            return None

        return defeated[0].opponent
