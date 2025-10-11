# gui/worker.py
from PyQt5.QtCore import QObject, pyqtSignal
import time

from tsp.solver import solve_tsp

class SolverWorker(QObject):
    progress = pyqtSignal(dict)   # emits progress dict
    finished = pyqtSignal(dict)   # emits final result: {'route','lengths','meta'}
    error = pyqtSignal(str)

    def __init__(self, items=None, distance_matrix=None, method='nn+2opt', params=None, time_limit=None):
        super().__init__()
        self.items = items
        self.distance_matrix = distance_matrix
        self.method = method
        self.params = params or {}
        self.time_limit = time_limit
        self._stop_requested = False

    def request_stop(self):
        # note: this is cooperative; existing two_opt checks only time_limit,
        # so user-initiated stop will not be immediate unless two_opt checks for it.
        self._stop_requested = True

    def run(self):
        try:
            # forwarder for progress callback
            def cb(meta):
                # if stop requested, we won't forcibly abort here; but we can emit progress
                self.progress.emit(meta)
            res = solve_tsp(items=self.items,
                            distance_matrix=self.distance_matrix,
                            method=self.method,
                            params=self.params,
                            time_limit=self.time_limit,
                            progress_callback=cb)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))
