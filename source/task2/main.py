
from tank_battle.constants import Action, PlayerId
from tank_battle.game_engine import GameEngine
from tank_battle.scenario import create_default_scenario


def print_game_state(state):
    """Display a text representation of the game board."""

    board = [
        ["." for _ in range(state.width)]
        for _ in range(state.height)
    ]

    for position in state.walls:
        board[position.y][position.x] = "#"

    for player in (PlayerId.PLAYER_1, PlayerId.PLAYER_2):
        base = state.bases[player]
        tank = state.tanks[player]

        if base.is_alive:
            board[base.position.y][base.position.x] = (
                "B1" if player == PlayerId.PLAYER_1 else "B2"
            )

        if tank.is_alive:
            board[tank.position.y][tank.position.x] = (
                "T1" if player == PlayerId.PLAYER_1 else "T2"
            )

    for bullet in state.bullets:
        marker = "*" if bullet.owner == PlayerId.PLAYER_1 else "+"
        board[bullet.position.y][bullet.position.x] = marker

    print(f"\nCycle: {state.cycle_number}")
    print(f"Current player: {state.current_player.name}")

    for row in board:
        print(" ".join(f"{cell:>2}" for cell in row))

    print("\nPlayer 1:")
    print(
        "Tank HP:",
        state.tanks[PlayerId.PLAYER_1].hp
    )
    print(
        "Base HP:",
        state.bases[PlayerId.PLAYER_1].hp
    )

    print("\nPlayer 2:")
    print(
        "Tank HP:",
        state.tanks[PlayerId.PLAYER_2].hp
    )
    print(
        "Base HP:",
        state.bases[PlayerId.PLAYER_2].hp
    )


def main():
    engine = GameEngine()

    state = create_default_scenario()

    print("========== INITIAL GAME STATE ==========")
    print_game_state(state)

    # Player 1 moves up.
    result = engine.apply_action(
        state,
        Action.MOVE_UP
    )

    state = result.state

    print("\n========== PLAYER 1 MOVES ==========")
    print_game_state(state)

    # Player 2 stays.
    result = engine.apply_action(
        state,
        Action.STAY
    )

    state = result.state

    print("\n========== CYCLE COMPLETED ==========")
    print_game_state(state)

    print("\n========== GAME EVENTS ==========")

    for event in result.events:
        print(
            f"{event.event_type}: {event.message}"
        )


if __name__ == "__main__":
    main()
