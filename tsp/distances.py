"""
distances.py
Create distance matrix and distance_fn
"""

from typing import Sequence, Optional
import numpy as np
from scipy.spatial import distance


def euclid_distance(p1: Sequence[float], p2: Sequence[float]) -> float:
    """
    Calculate euclidian distance between two points
    Accepts 1d sequences like (x,y)
    :param p1: point1
    :param p2: point2
    :return: euclidian distance between two points
    """

    p1 = np.asarray(p1, dtype=np.float64)
    p2 = np.asarray(p2, dtype=np.float64)
    return float(np.linalg.norm(p1 - p2))


def build_distance_matrix(points: np.ndarray,
                          dtype: Optional[np.dtype] = np.float32) -> np.ndarray:
    """
    Build full pairwise Euclidean distance matrix using scipy.spatial.distance.cdist.
    Returns a symmetric matrix with zeros on diagonal.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] < 1:
        raise ValueError("points must be a 2D array of shape (n, k)")
    D = distance.cdist(points, points, metric='euclidean')
    if dtype is not None:
        D = D.astype(dtype)
    return D

def route_length(route: Sequence[int],
                 D: np.ndarray,
                 closed: bool = False) -> float:
    """
    Calculate length of a given route
    :param route: sequence of indices of points
    :param D: pairwise distance matrix
    :param closed: if True, include distance from last to first (close the route)
    :return: total route length
    """

    if len(route) < 2:
        return 0.0

    # get indexes
    idx = np.asarray(route, dtype=np.int64)

    # sum distances between consecutive pairs
    dist_sum = D[idx[:-1], idx[1:]].sum()
    if closed and len(route) > 1:
        dist_sum += D[idx[-1], idx[0]]
    return float(dist_sum)

def validate_distance_matrix(D: np.ndarray, atol: float = 1e-6) -> bool:
    """Sanity-check distance matrix: square, zero diagonal, symmetric and non-negative."""
    D = np.asarray(D)
    if D.ndim != 2 or D.shape[0] != D.shape[1]:
        return False
    if not np.allclose(np.diag(D), 0.0, atol=atol):
        return False
    if not np.allclose(D, D.T, atol=atol):
        return False
    if np.any(D < -atol):
        return False
    return True