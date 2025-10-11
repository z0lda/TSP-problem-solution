"""
heuristics.py
Nearest Neighbor and 2-opt algorithm realization
"""

from typing import List, Tuple, Optional, Callable
import time
import numpy as np

from .distances import route_length


def nearest_neighbor(start_idx: int, D: np.ndarray) -> List[int]:
    """
    Realization of greedy algorithm 'Nearest Neighbor'

    Desc: start from start_idx, then on every new step go to unvisited point, repeat
    :param start_idx: index to start from
    :param D: pairwise distance matrix
    :return: route
    """

    n = D.shape[0]
    if n == 0:
        return []
    visited = np.zeros(n, dtype=bool)

    # tb sure not to quit the borders of array
    if start_idx < 0 or start_idx >= n:
        start_idx = 0

    route = [int(start_idx)]
    visited[start_idx] = True
    current = start_idx
    for _ in range(n - 1):
        d_row = D[current].copy()
        d_row[visited] = np.inf
        next_idx = int(np.argmin(d_row))
        route.append(next_idx)
        visited[next_idx] = True
        current = next_idx
    return route


def two_opt(route: List[int],
            D: np.ndarray,
            max_iters: int = 1000,
            improve_threshold: float = 1e-9,
            time_limit: Optional[float] = None,
            progress_callback: Optional[Callable] = None) -> Tuple[List[int], float]:
    """
    2-opt local search (first-improvement)
    The function locks the route by adding the first element in the end,
    then applying the method, finding improvement, repeat.
    :param route: the default route
    :param D: pairwise matrix
    :param max_iters: maximum amount of iterations
    :param improve_threshold: the threshold for improving the part of the route
    :param time_limit: optional: limit of function completion time
    :param progress_callback:
    :return: improved route with open length
    """

    if len(route) < 2:
        return route, 0.0

    n = len(route)

    # preparing closed route
    tour = list(route)
    if tour[0] != tour[-1]:
        tour.append(tour[0])
    n_closed = len(tour)

    best = np.asarray(tour, dtype=int)
    best_len = route_length(best, D, closed=False) + D[best[-1], best[0]]

    start_time = time.time()
    improved = True
    iters = 0

    while improved and iters < max_iters:
        improved = False
        iters += 1
        for i in range(1, n_closed - 2):
            # checking time limit
            if time_limit is not None and (time.time() - start_time) > time_limit:
                return best[:-1].tolist(), float(best_len - D[best[-1], best[0]])
            for j in range(i + 1, n_closed - 1):
                a, b = best[i - 1], best[i]
                c, d = best[j], best[(j + 1) % n_closed]
                delta = (D[a, c] + D[b, d]) - (D[a, b] + D[c, d])
                if delta < -improve_threshold:
                    # reversing (applying 2-opt)
                    best[i:j+1] = best[i:j + 1][::-1]
                    best_len += delta
                    improved = True
                    if progress_callback is not None:
                        try:
                            open_len = float(best_len - D[best[-1], best[0]])
                            progress_callback({'route': best[:-1].tolist(),
                                               'length_open': open_len,
                                               'length_closed': float(best_len),
                                               'time': time.time() - start_time})
                        except Exception:
                            pass
                    break
                if improved:
                    break

    open_len = float(best_len - D[best[-1], best[0]])
    return best[:-1].tolist(), open_len
