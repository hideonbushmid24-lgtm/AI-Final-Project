
import pytest

from tank_battle.constants import (
    PlayerId,
    Direction,
    Action,
    DIRECTION_DELTAS,
    TANK_INITIAL_HP,
    BASE_INITIAL_HP,
    WALL_INITIAL_HP,
    BULLET_SPEED_PER_CYCLE,
)

from tank_battle.entities import (
    Position,
    Tank,
    Base,
    Wall,
    Bullet,
)


def test_player_opponent():
    assert (
        PlayerId.PLAYER_1.opponent
        == PlayerId.PLAYER_2
    )

    assert (
        PlayerId.PLAYER_2.opponent
        == PlayerId.PLAYER_1
    )


def test_direction_deltas():
    assert DIRECTION_DELTAS[Direction.UP] == (0, -1)
    assert DIRECTION_DELTAS[Direction.DOWN] == (0, 1)
    assert DIRECTION_DELTAS[Direction.LEFT] == (-1, 0)
    assert DIRECTION_DELTAS[Direction.RIGHT] == (1, 0)


def test_all_six_actions_exist():
    assert len(Action) == 6


def test_position_movement():
    position = Position(5, 5)

    assert position.moved(Direction.UP) == Position(5, 4)
    assert position.moved(Direction.DOWN) == Position(5, 6)
    assert position.moved(Direction.LEFT) == Position(4, 5)
    assert position.moved(Direction.RIGHT) == Position(6, 5)


def test_tank_default_hp():
    tank = Tank(
        player=PlayerId.PLAYER_1,
        position=Position(1, 1)
    )

    assert tank.hp == TANK_INITIAL_HP
    assert tank.is_alive is True


def test_base_default_hp():
    base = Base(
        player=PlayerId.PLAYER_1,
        position=Position(1, 0)
    )

    assert base.hp == BASE_INITIAL_HP
    assert base.is_alive is True


def test_wall_default_hp():
    wall = Wall(
        position=Position(3, 3)
    )

    assert wall.hp == WALL_INITIAL_HP
    assert wall.is_destroyed is False


def test_bullet_properties():
    bullet = Bullet(
        bullet_id=1,
        owner=PlayerId.PLAYER_1,
        position=Position(2, 2),
        direction=Direction.RIGHT
    )

    assert bullet.bullet_id == 1
    assert bullet.owner == PlayerId.PLAYER_1
    assert bullet.position == Position(2, 2)


@pytest.mark.parametrize(
    "entity_factory",
    [
        lambda: Tank(
            PlayerId.PLAYER_1,
            Position(0, 0),
            hp=-1
        ),
        lambda: Tank(
            PlayerId.PLAYER_1,
            Position(0, 0),
            hp=7
        ),
        lambda: Base(
            PlayerId.PLAYER_1,
            Position(0, 0),
            hp=10
        ),
        lambda: Wall(
            Position(0, 0),
            hp=4
        ),
    ]
)
def test_invalid_entity_hp(entity_factory):
    with pytest.raises(ValueError):
        entity_factory()


def test_bullet_speed_constant():
    assert BULLET_SPEED_PER_CYCLE == 3
