# gui/map_widget.py
import os
import math
import tempfile
import folium
import numpy as np
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

class MapWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tmpfile = None
        self._last_bounds = None

    def _write_map(self, m: folium.Map):
        # write to a temp file and load
        fd, path = tempfile.mkstemp(suffix=".html", prefix="tsp_map_")
        os.close(fd)
        m.save(path)
        self.load(QUrl.fromLocalFile(path))
        # remember path to allow later cleanup (not strictly necessary)
        self._tmpfile = path

    def show_points(self, points: np.ndarray, ids=None):
        # points: (n,2) lat/lon in degrees or scaled units (if not deg)
        if points.size == 0:
            return
        # determine center
        lats = points[:,0].astype(float)
        lons = points[:,1].astype(float)
        center = [float(lats.mean()), float(lons.mean())]
        m = folium.Map(location=center, zoom_start=6, control_scale=True)
        # add a few markers (sparse)
        n = len(points)
        for i in range(0, n):
            label = str(ids[i]) if ids is not None else str(i)
            folium.CircleMarker(location=[float(lats[i]), float(lons[i])],
                                radius=2, popup=label, fill=True).add_to(m)
        self._write_map(m)

    def show_route(self, coords: np.ndarray, ids=None):
        # coords: (k,2) lat lon in degrees
        if coords is None or len(coords) == 0:
            return
        lats = coords[:,0].astype(float)
        lons = coords[:,1].astype(float)
        center = [float(lats.mean()), float(lons.mean())]
        m = folium.Map(location=center, zoom_start=6, control_scale=True)
        # add polyline
        points = [[float(lat), float(lon)] for lat, lon in zip(lats, lons)]
        folium.PolyLine(points, color='blue', weight=3, opacity=0.8).add_to(m)
        # add start marker
        folium.Marker(points[0], popup="Start", icon=folium.Icon(color='green')).add_to(m)
        # add end marker
        folium.Marker(points[-1], popup="End", icon=folium.Icon(color='red')).add_to(m)
        self._write_map(m)
