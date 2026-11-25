
from tank_battle.scenario import create_default_scenario

from tank_battle.search.minimax import MinimaxAgent
from tank_battle.search.alpha_beta import AlphaBetaAgent


def run_demo(depth: int = 3):
    """Compare Minimax and Alpha-Beta on the same game state."""

    state = create_default_scenario()

    minimax_agent = MinimaxAgent(
        depth=depth
    )

    alpha_beta_agent = AlphaBetaAgent(
        depth=depth
    )

    minimax_result = minimax_agent.search(state)

    alpha_beta_result = alpha_beta_agent.search(state)

    results = [
        minimax_result,
        alpha_beta_result
    ]

    print("=" * 65)
    print("TANK BATTLE - ADVERSARIAL SEARCH DEMO")
    print("=" * 65)

    print(f"Search depth: {depth}")
    print(f"Current player: {state.current_player.name}")

    for result in results:
        print("\nAlgorithm:", result.algorithm)
        print("Best action:", result.best_action)
        print("Evaluation score:", result.score)

        print("Nodes explored:", result.nodes_explored)
        print("Leaf nodes:", result.leaf_nodes)
        print("Terminal nodes:", result.terminal_nodes)

        print("Maximum depth:", result.max_depth_reached)

        print("Cutoffs:", result.cutoffs)
        print("Pruned branches:", result.pruned_branches)

        print(
            f"Execution time: "
            f"{result.elapsed_time_ms:.6f} ms"
        )

    print("\n========== COMPARISON ==========")

    print(
        "Same evaluation score:",
        minimax_result.score == alpha_beta_result.score
    )

    print(
        "Minimax nodes:",
        minimax_result.nodes_explored
    )

    print(
        "Alpha-Beta nodes:",
        alpha_beta_result.nodes_explored
    )

    if minimax_result.nodes_explored > 0:
        reduction = (
            1
            - alpha_beta_result.nodes_explored
            / minimax_result.nodes_explored
        ) * 100

        print(
            f"Node reduction: {reduction:.2f}%"
        )


if __name__ == "__main__":
    run_demo(depth=3)
