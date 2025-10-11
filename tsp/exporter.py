"""
Export helpers for solution files.

Provides functions to write:
- route.csv: sequence of node ids in visiting order
- solution.csv: n-1 lines with pairwise distances between consecutive nodes
- meta.json: metadata about the run

Default CSV format for solution.csv: "from_id;distance"
where `from_id` is either the original id (if ids provided) or the integer index.
"""
import csv
import json
from typing import List, Optional


def export_route_ids(route_indices: List[int],
                     ids: Optional[List] = None,
                     path: str = 'route.csv') -> None:
    """
    Write visiting order to a CSV file (one id per line).
    If `ids` is provided, use ids[index]; otherwise write numeric index.
    """
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';')
        if ids is None:
            for idx in route_indices:
                w.writerow([int(idx)])
        else:
            for idx in route_indices:
                w.writerow([ids[int(idx)]])


def export_solution_distances(route_indices: List[int],
                              D,
                              ids: Optional[List] = None,
                              path: str = 'solution.csv') -> None:
    """
    Write distances between consecutive nodes into solution.csv as n-1 lines.
    Each line: from_id;distance
    """
    if len(route_indices) < 2:
        open(path, 'w', encoding='utf-8').close()
        return
    idx = route_indices
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';')
        for i in range(len(idx) - 1):
            from_idx = idx[i]
            dist = float(D[from_idx, idx[i + 1]])
            left = ids[int(from_idx)] if ids is not None else int(from_idx)
            w.writerow([left, repr(dist)])


def save_meta(meta: dict, path: str = 'meta.json') -> None:
    """
    Save meta information into a JSON file.
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)