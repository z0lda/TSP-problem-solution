
"""
Small utilities used across the package: validation, timers,
and a simple progress printer.
"""


from contextlib import contextmanager
import time
from typing import List
import sys


def validate_route_indices(route: List[int], n: int) -> bool:
    """
    Validate that `route` is a permutation of 0..n-1.
    Returns True when route contains exactly n unique indices in [0, n-1].
    """
    if len(route) != n:
        return False
    s = set(route)
    if len(s) != n:
        return False
    if min(route) < 0 or max(route) >= n:
        return False
    return True


@contextmanager
def timer(label: str = ''):
    """Context manager for timing code blocks."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print(f"{label} time: {t1 - t0:.3f}s", file=sys.stderr)


def simple_progress_printer():
    """
    Return a simple callback that prints progress updates.
    Callback receives a dict: {'route', 'length_open', 'length_closed', 'time'}
    """
    def cb(meta):
        try:
            print(f"[progress] time={meta.get('time', 0):.2f}s open={meta.get('length_open'):.3f} closed={meta.get('length_closed'):.3f}")
        except Exception:
            pass
    return cb
