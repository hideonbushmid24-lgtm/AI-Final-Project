# TASK 2 – ADVERSARIAL SEARCH ALGORITHMS

## 1. Minimax Search

Minimax is an adversarial search algorithm used
in two-player zero-sum games.

It assumes that both players make optimal decisions.

- MAX tries to maximize the utility.
- MIN tries to minimize the utility.

The algorithm recursively explores possible
actions until reaching a terminal state
or the predefined search depth.

The evaluation function assigns a value
to each leaf state.

### Minimax Formula

V(s) = Eval(s), if s is a leaf.

V(s) = max V(T(s,a)), if MAX.

V(s) = min V(T(s,a)), if MIN.

## 2. Alpha-Beta Pruning

Alpha-Beta Pruning optimizes Minimax Search
by removing branches that cannot influence
the final optimal decision.

Alpha represents the best value guaranteed
to MAX.

Beta represents the best value guaranteed
to MIN.

A branch can be pruned when:

Alpha >= Beta.

### Advantages

- Reduces the number of explored states.
- Preserves the optimal Minimax result.
- Can support deeper search under the same
  computational budget.

## 3. Baseline Evaluation Function

The initial evaluation function considers
the remaining HP of each player's tank and base.

Eval(S, P) =

(TankHP(P) + BaseHP(P))
-
(TankHP(Opponent) + BaseHP(Opponent))

Terminal states receive a large positive
or negative utility.

## 4. Performance Metrics

The implementation records:

- Selected action.
- Evaluation score.
- Explored nodes.
- Leaf nodes.
- Terminal nodes.
- Actual search depth.
- Alpha-Beta cutoffs.
- Pruned immediate branches.
- Execution time.

## 5. Experimental Comparison

Minimax and Alpha-Beta are evaluated using:

- The same initial game state.
- The same evaluation function.
- The same search depth.
- The same action ordering.

The comparison focuses on the number of explored
states and computational time.