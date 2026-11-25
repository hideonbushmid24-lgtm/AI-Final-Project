
from dataclasses import dataclass

from ..constants import Action


@dataclass
class SearchResult:
    """
    Store the output and performance metrics of a search.
    """

    algorithm: str
    best_action: Action | None
    score: float

    requested_depth: int
    max_depth_reached: int

    nodes_explored: int
    leaf_nodes: int
    terminal_nodes: int

    cutoffs: int
    pruned_branches: int

    elapsed_time_seconds: float

    @property
    def elapsed_time_ms(self) -> float:
        return self.elapsed_time_seconds * 1000
