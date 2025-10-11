#  tsp/solver.py
import time
import numpy as np
from typing import Any, Optional, Callable, Dict

from .distances import build_distance_matrix, route_length
from .heuristics import nearest_neighbor, two_opt

def _compute_distance_matrix(points: np.ndarray, distance_fn: Optional[Callable] = None) -> np.ndarray:
    if distance_fn is None:
        return build_distance_matrix(points)
    n = points.shape[0]
    D = np.empty((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            d = float(distance_fn(points[i], points[j]))
            D[i, j] = d
            D[j, i] = d
    return D.astype(np.float32)

def solve_tsp(items: Any = None,
              distance_fn: Optional[Callable] = None,
              distance_matrix: Optional[np.ndarray] = None,
              method: str = 'nn+2opt',
              params: Optional[Dict] = None,
              time_limit: Optional[float] = None,
              progress_callback: Optional[Callable] = None) -> dict:
    """
    Deterministic TSP solver wrapper.
    - items: np.ndarray (n,k) OR None if distance_matrix provided
    - distance_matrix: full pairwise distances (n x n) or None
    - method: 'nn' or 'nn+2opt'
    - params: {'start_idx': int, 'max_iters': int}
    - time_limit: global time limit in seconds (optional)
    - progress_callback: called with progress dicts
    """
    t0 = time.time()
    if params is None:
        params = {}

    # Prepare D
    if distance_matrix is None:
        if items is None:
            raise ValueError("Either items or distance_matrix must be provided")
        points = np.asarray(items)
        if points.ndim != 2:
            raise ValueError("items must be a 2D array with shape (n,k)")
        D = _compute_distance_matrix(points, distance_fn=distance_fn)
    else:
        D = np.asarray(distance_matrix)

    # basic sanity checks on D
    if D.ndim != 2 or D.shape[0] != D.shape[1]:
        raise ValueError("distance_matrix must be a square 2D array")

    n = D.shape[0]
    # default start: Krasnoyarsk id index 3753 (safety fallback to 0)
    default_start = int(params.get('start_idx', 3753))
    if default_start < 0 or default_start >= n:
        start_idx = 0
    else:
        start_idx = default_start

    best_route = None
    best_open_len = float('inf')
    best_closed_len = float('inf')

    # -------------------------
    # Method: nearest neighbor
    # -------------------------
    if method == 'nn':
        try:
            route = nearest_neighbor(start_idx, D)
        except Exception as e:
            raise RuntimeError(f"nearest_neighbor failed: {e}")

        # safety: validate route
        if route is None or len(route) == 0:
            raise RuntimeError("nearest_neighbor returned empty route")

        # compute lengths
        open_len = float(route_length(route, D, closed=False))
        closed_len = float(open_len + D[route[-1], route[0]]) if len(route) > 0 else 0.0
        best_route = route
        best_open_len = open_len
        best_closed_len = closed_len
        if progress_callback is not None:
            progress_callback({'route': best_route,
                               'length_open': best_open_len,
                               'length_closed': best_closed_len,
                               'time': time.time() - t0})

    # -------------------------
    # Method: NN + 2-opt
    # -------------------------
    elif method == 'nn+2opt':
        try:
            route = nearest_neighbor(start_idx, D)
        except Exception as e:
            raise RuntimeError(f"nearest_neighbor failed: {e}")

        if route is None or len(route) == 0:
            raise RuntimeError("nearest_neighbor returned empty route")

        open_len = float(route_length(route, D, closed=False))
        closed_len = float(open_len + D[route[-1], route[0]])
        best_route = route
        best_open_len = open_len
        best_closed_len = closed_len
        if progress_callback is not None:
            progress_callback({'route': best_route,
                               'length_open': best_open_len,
                               'length_closed': best_closed_len,
                               'time': time.time() - t0})

        rem_time = None
        if time_limit is not None:
            rem_time = max(0.0, time_limit - (time.time() - t0))
        max_iters = int(params.get('max_iters', 1000))
        # run two_opt (itself may honor time_limit)
        try:
            new_route, new_open_len = two_opt(route, D, max_iters=max_iters,
                                              time_limit=rem_time, progress_callback=progress_callback)
        except Exception as e:
            raise RuntimeError(f"two_opt failed: {e}")

        if new_route is not None and len(new_route) > 0:
            new_closed_len = float(new_open_len + D[new_route[-1], new_route[0]])
            if new_open_len < best_open_len:
                best_route = new_route
                best_open_len = new_open_len
                best_closed_len = new_closed_len
        # else keep original

    else:
        raise ValueError(f"Unknown method '{method}' — allowed: 'nn', 'nn+2opt'")

    # prepare distances list (n-1)
    if best_route is None or len(best_route) == 0:
        distances = []
    else:
        idx = np.asarray(best_route, dtype=int)
        if idx.size >= 2:
            distances = D[idx[:-1], idx[1:]].tolist()
        else:
            distances = []

    meta = {
        'method': method,
        'n': n,
        'time_seconds': time.time() - t0,
        'best_open_length': float(best_open_len),
        'best_closed_length': float(best_closed_len),
        'start_idx': int(start_idx)
    }

    return {'route': best_route, 'lengths': distances, 'meta': meta}
