
from tank_battle.scenario import create_default_scenario

from tank_battle.search.minimax import MinimaxAgent

from tank_battle.search.alpha_beta import (
    AlphaBetaAgent
)

from tank_battle.search.heuristic_agents import (
    HeuristicMinimaxAgent,
    HeuristicAlphaBetaAgent
)


def run_demo(depth: int = 3):
    """Compare all four search configurations."""

    state = create_default_scenario()

    agents = [
        MinimaxAgent(depth=depth),
        AlphaBetaAgent(depth=depth),
        HeuristicMinimaxAgent(depth=depth),
        HeuristicAlphaBetaAgent(depth=depth)
    ]

    results = []

    print("=" * 75)
    print("TANK BATTLE - FOUR SEARCH CONFIGURATIONS")
    print("=" * 75)

    print("Search depth:", depth)
    print("Current player:", state.current_player.name)

    for agent in agents:

        result = agent.search(state)
        results.append(result)

        print("\nAlgorithm:", result.algorithm)
        print("Best action:", result.best_action)
        print("Evaluation score:", result.score)

        print("Nodes explored:", result.nodes_explored)
        print("Leaf nodes:", result.leaf_nodes)

        print("Search depth:", result.max_depth_reached)
        print("Cutoffs:", result.cutoffs)
        print("Pruned branches:", result.pruned_branches)

        print(
            f"Execution time: "
            f"{result.elapsed_time_ms:.6f} ms"
        )

    print("\n========== FINAL COMPARISON ==========")

    baseline_score = results[0].score
    heuristic_score = results[2].score

    print(
        "Standard Minimax vs Alpha-Beta:",
        results[0].score == results[1].score
    )

    print(
        "Heuristic Minimax vs Heuristic Alpha-Beta:",
        results[2].score == results[3].score
    )

    print(
        "Material vs Heuristic evaluation:",
        baseline_score,
        heuristic_score
    )

    print("\nAll four searches completed.")


if __name__ == "__main__":
    run_demo(depth=3)
