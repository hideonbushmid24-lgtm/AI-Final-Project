# Min-Conflicts Experimental Analysis

## Experimental Configuration

- Board sizes: 4, 5, 6, 7, 8, 10, 12, 15, 20, 30, 40, 50.
- Repetitions: 30 per configuration.
- Algorithms: Standard and Improved Min-Conflicts.
- Maximum steps: 10,000 per restart.
- Maximum restarts: 5.
- Total runs: 720.

## Experimental Results

Both algorithms achieved a 100% success rate
across all tested board sizes.

The Improved Min-Conflicts heuristic achieved
a lower median number of search steps in 9 out
of 12 tested board sizes.

It also achieved a lower median execution time
in 7 out of 12 tested board sizes.

However, the heuristic did not consistently
outperform the standard approach.

## Discussion

The results suggest that selecting the most
conflicted variable can reduce the search effort
for many board sizes.

Nevertheless, its performance depends on the
initial state and board size.

Additional computational cost may occur when
the improved heuristic evaluates conflict counts.

Therefore, the proposed heuristic is effective
in many tested cases but is not universally
superior to standard Min-Conflicts.

## Conclusion

Both approaches successfully solved all tested
instances under the configured search budget.

The improved heuristic demonstrated promising
results in terms of median search steps, although
its runtime advantage was not consistent.