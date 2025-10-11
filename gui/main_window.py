# gui/main_window.py
import os
import time
import tempfile
from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QVBoxLayout,
                             QHBoxLayout, QLabel, QFileDialog, QComboBox,
                             QSpinBox, QPlainTextEdit, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSlot, QSize
from PyQt5.QtGui import QIcon

from gui.map_widget import MapWidget
from gui.worker import SolverWorker

import tsp.loader as loader
from tsp.distances import build_distance_matrix
from tsp.exporter import export_solution_distances, export_route_ids, save_meta

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSP Solver - GUI")
        self.resize(1100, 780)
        # central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Map widget (top, large)
        self.map_widget = MapWidget()
        main_layout.addWidget(self.map_widget, stretch=5)

        # control panel (bottom)
        controls = QWidget()
        ctrl_layout = QHBoxLayout(controls)

        # left: load / start / stop
        left_col = QVBoxLayout()
        self.btn_load = QPushButton("Load CSV")
        self.btn_load.setIcon(QIcon("gui/ui/icons/files.svg"))
        self.btn_load.setIconSize(QSize(24, 24))
        self.btn_load.clicked.connect(self.on_load)
        left_col.addWidget(self.btn_load)

        self.btn_start = QPushButton("Start")
        self.btn_start.setIcon(QIcon("gui/ui/icons/start.png"))
        self.btn_start.setIconSize(QSize(24, 24))
        self.btn_start.clicked.connect(self.on_start)
        self.btn_start.setEnabled(False)
        left_col.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setIcon(QIcon("gui/ui/icons/stop.png"))
        self.btn_stop.setIconSize(QSize(24, 24))
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_stop.setEnabled(False)
        left_col.addWidget(self.btn_stop)

        ctrl_layout.addLayout(left_col, stretch=1)

        # middle: params
        mid_col = QVBoxLayout()
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method:"))
        self.combo_method = QComboBox()
        self.combo_method.addItems(["nn", "nn+2opt"])
        method_row.addWidget(self.combo_method)
        mid_col.addLayout(method_row)

        maxiters_row = QHBoxLayout()
        maxiters_row.addWidget(QLabel("Max 2-opt iters:"))
        self.spin_iters = QSpinBox()
        self.spin_iters.setRange(1, 100000)
        self.spin_iters.setValue(1000)
        maxiters_row.addWidget(self.spin_iters)
        mid_col.addLayout(maxiters_row)

        timelimit_row = QHBoxLayout()
        timelimit_row.addWidget(QLabel("Time limit (s, 0 = none):"))
        self.spin_time = QSpinBox()
        self.spin_time.setRange(0, 86400)
        self.spin_time.setValue(0)
        timelimit_row.addWidget(self.spin_time)
        mid_col.addLayout(timelimit_row)

        self.check_degrees = QCheckBox("Map in degrees (lat/lon)")
        self.check_degrees.setChecked(True)
        mid_col.addWidget(self.check_degrees)

        ctrl_layout.addLayout(mid_col, stretch=1)

        # right: logs and export buttons
        right_col = QVBoxLayout()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        right_col.addWidget(self.log, stretch=4)

        export_row = QHBoxLayout()
        self.btn_export_solution = QPushButton("Export solution.csv")
        self.btn_export_solution.clicked.connect(self.on_export_solution)
        self.btn_export_solution.setEnabled(False)
        export_row.addWidget(self.btn_export_solution)
        self.btn_export_route = QPushButton("Export route.csv")
        self.btn_export_route.clicked.connect(self.on_export_route)
        self.btn_export_route.setEnabled(False)
        export_row.addWidget(self.btn_export_route)
        right_col.addLayout(export_row)

        ctrl_layout.addLayout(right_col, stretch=2)

        main_layout.addWidget(controls, stretch=2)

        # internal state
        self.df = None
        self.points = None       # numpy (n,2) in dd*100 units or degrees if chosen for map
        self.points_for_calc = None  # points (n,2) used for calculation (no degrees)
        self.ids = None
        self.distance_matrix = None
        self.solver_thread = None
        self.solver_worker = None
        self.last_map_update = 0.0
        self.best_open_len = float('inf')
        self.current_solution = None

    def log_append(self, text: str):
        ts = time.strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{ts}] {text}")

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV files (*.csv);;All files (*)")
        if not path:
            return
        try:
            self.df = loader.load_path(path, sep=';')
        except Exception as e:
            QMessageBox.critical(self, "Load error", f"Failed to load CSV: {e}")
            return
        self.ids = loader.get_ids(self.df)
        # points for calculation — do NOT divide by 100 (as assignment expects)
        pts_calc = loader.get_points(self.df, convert_to_degrees=False)  # float32 with lat_dd, lon_dd
        self.points_for_calc = pts_calc  # used for distances
        # points for map (degrees)
        pts_map = loader.get_points(self.df, convert_to_degrees=True) if self.check_degrees.isChecked() else pts_calc
        self.points = pts_map
        self.log_append(f"Loaded {len(self.df)} rows from {os.path.basename(path)}")
        # precompute matrix lazily? Offer to compute now (or we compute on start)
        self.btn_start.setEnabled(True)
        self.btn_export_solution.setEnabled(False)
        self.btn_export_route.setEnabled(False)
        # show initial map
        self.map_widget.show_points(self.points, ids=self.ids)

    def prepare_distance_matrix(self):
        # compute D from points_for_calc (n,2)
        self.log_append("Building distance matrix (this may take some time)...")
        D = build_distance_matrix(self.points_for_calc)
        self.distance_matrix = D
        self.log_append("Distance matrix ready (shape: %d x %d)" % (D.shape[0], D.shape[1]))

    def on_start(self):
        if self.df is None:
            QMessageBox.warning(self, "No data", "Load CSV first.")
            return
        if self.distance_matrix is None:
            self.prepare_distance_matrix()
        method = self.combo_method.currentText()
        max_iters = self.spin_iters.value()
        time_limit = self.spin_time.value() or None
        params = {'start_idx': 3753, 'max_iters': max_iters}
        # create worker and thread
        self.solver_worker = SolverWorker(distance_matrix=self.distance_matrix,
                                          method=method, params=params, time_limit=time_limit)
        self.solver_thread = QThread()
        self.solver_worker.moveToThread(self.solver_thread)
        self.solver_thread.started.connect(self.solver_worker.run)
        self.solver_worker.progress.connect(self.on_progress)
        self.solver_worker.finished.connect(self.on_finished)
        self.solver_worker.error.connect(self.on_error)
        # UI state
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_load.setEnabled(False)
        self.log_append(f"Starting solver (method={method})...")
        self.best_open_len = float('inf')
        self.current_solution = None
        self.solver_thread.start()

    def on_stop(self):
        # soft stop: request worker to stop via stop() — note two_opt doesn't check it but we can rely on time_limit
        if self.solver_worker is not None:
            self.solver_worker.request_stop()
            self.log_append("Stop requested (worker will stop at next chance).")
            self.btn_stop.setEnabled(False)

    @pyqtSlot(dict)
    def on_progress(self, meta: dict):
        # rate-limit map updates to 1s
        now = time.time()
        self.log_append(f"progress: open={meta.get('length_open'):.3f} closed={meta.get('length_closed'):.3f} time={meta.get('time'):.2f}s")
        if now - self.last_map_update > 1.0:
            route = meta.get('route')
            if route is not None:
                coords = self.points[route]
                self.map_widget.show_route(coords, ids=[self.ids[i] for i in route])
            self.last_map_update = now

    @pyqtSlot(dict)
    def on_finished(self, result: dict):
        self.log_append("Solver finished.")
        self.current_solution = result
        # show final route
        route = result['route']
        if route:
            coords = self.points[route]
            self.map_widget.show_route(coords, ids=[self.ids[i] for i in route])
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_load.setEnabled(True)
        self.btn_export_solution.setEnabled(True)
        self.btn_export_route.setEnabled(True)
        # join thread
        if self.solver_thread is not None:
            self.solver_thread.quit()
            self.solver_thread.wait()
            self.solver_thread = None
            self.solver_worker = None

        # save meta optional
        meta = result.get('meta')
        if meta:
            save_meta(meta, path='meta.json')
            self.log_append("Saved meta.json")

    @pyqtSlot(str)
    def on_error(self, text):
        QMessageBox.critical(self, "Solver error", text)
        self.log_append(f"Solver error: {text}")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_load.setEnabled(True)

    def on_export_solution(self):
        if self.current_solution is None:
            QMessageBox.warning(self, "No solution", "Run solver first.")
            return
        # ask path
        path, _ = QFileDialog.getSaveFileName(self, "Save solution.csv", "solution.csv", "CSV files (*.csv)")
        if not path:
            return
        export_solution_distances(self.current_solution['route'], self.distance_matrix, ids=self.ids, path=path)
        self.log_append(f"Exported solution to {path}")

    def on_export_route(self):
        if self.current_solution is None:
            QMessageBox.warning(self, "No solution", "Run solver first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save route.csv", "route.csv", "CSV files (*.csv)")
        if not path:
            return
        export_route_ids(self.current_solution['route'], ids=self.ids, path=path)
        self.log_append(f"Exported route to {path}")
