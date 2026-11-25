# TASK 2 – TANK BATTLE GAME MODEL

## 1. Problem Description

Tank Battle is a two-player, turn-based adversarial game.

Each player controls one tank and protects one base.
Players can move, shoot, or stay during their turns.

The objective is to defeat the opponent by destroying
their tank or base while keeping their own assets operational.

## 2. Game State

The game state contains:

- Board dimensions and boundaries.
- Positions and health points of both tanks.
- Facing directions of both tanks.
- Positions and health points of both bases.
- Wall positions and remaining health points.
- Active bullets, their directions and owners.
- Current player and cycle information.

Formally:

S = (B, T1, T2, Base1, Base2, W, K, P)

## 3. Players

P = {Player 1, Player 2}

Both players have opposing objectives.

## 4. Actions

A = {
    MOVE_UP,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    FIRE,
    STAY
}

A tank moves one cell per movement action.

A bullet travels up to three cells per completed game cycle.

## 5. Transition Function

The transition function maps a state and an action
to a new state:

S' = T(S, A)

The engine performs:

1. Action validation.
2. Tank movement or bullet creation.
3. Player turn switching.
4. Bullet movement at the cycle boundary.
5. Cell-by-cell collision detection.
6. Health point updates.
7. Terminal state evaluation.

## 6. Terminal States

A player is defeated when either their tank or
their base is destroyed.

The opponent wins when exactly one player is defeated.

A simultaneous defeat is treated as a draw.

## 7. Utility Function

For Player 1:

U(S) = +M, if Player 1 wins
U(S) = -M, if Player 2 wins
U(S) = 0, if the game is a draw

M is a large positive constant.

For non-terminal states, a state evaluation
function is used.

## 8. Adversarial Search Algorithms

The project implements four configurations:

1. Minimax Search.
2. Alpha-Beta Search.
3. Heuristic Minimax Search.
4. Heuristic Minimax Search with Alpha-Beta Pruning.

## 9. Experimental Evaluation

The algorithms are compared using:

- Identical game scenarios.
- Identical initial game states.
- The same search depth where applicable.
- Execution time.
- Number of explored game states.
- Actual search depth.
- Additional pruning and decision statistics.

## 10. Graphical User Interface

The game interface is developed with PyGame.

The system allows players to operate the game
and supports importing external AI Agent implementations.

## 11. Implementation Assumptions

- Board dimensions are configurable.
- A full game cycle contains one action from each player.
- Existing bullets advance after both players complete their actions.
- Bullet collision is checked after every individual cell movement.
- Every collision causes one point of damage.
- A destroyed wall is removed from the board.
- The game terminates when a player's tank or base is destroyed.