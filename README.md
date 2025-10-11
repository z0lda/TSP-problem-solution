# TSP Solver: Решатель задачи коммивояжера для городов Сибири

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-yellow)](https://www.pyqtgraph.org/)
[![Folium](https://img.shields.io/badge/Folium-0.12%2B-green)](https://python-visualization.github.io/folium/)

## Описание

Этот проект реализует **графический интерфейс (GUI)** для приближённого решения **задачи коммивояжера (TSP)** — NP-полной задачи оптимизации маршрутов. Программа работает с данными о городах и поселениях **Сибирского федерального округа** (около 6137 точек), загружаемыми из CSV-файла с координатами (latitude/longitude в формате dd*100).

### Ключевые особенности
- **Алгоритмы**: 
  - **Nearest Neighbor (NN)**: Жадный алгоритм для начального маршрута.
  - **2-opt**: Локальный поиск для улучшения (first-improvement, детерминированный).
- **Визуализация**: Интерактивная карта на базе Folium (встраивается в PyQt5 via QWebEngineView). Поддержка отображения всех точек (density=1) или спарсинга для производительности.
- **Экспорт**: route.csv (последовательность ID), solution.csv (дистанции между последовательными точками), meta.json (метаданные: время, длины).
- **GUI**: Кнопки Load/Start/Stop, параметры (метод, итерации 2-opt, time_limit), чекбокс для градусов, логи, экспорт.

Проект демонстрирует применение теории (DFS/BFS-подобные обходы, MST-подобные улучшения) к реальным данным. Результаты: NN ~105k км, NN+2opt ~100k км (экономия ~5%).

## Установка

### Требования
- Python 3.8+
- Библиотеки: `pip install PyQt5 folium pandas numpy scipy`

### Клонирование и запуск
```bash
  git clone <https://github.com/z0lda/TSP-problem-solution> tsp-solver
  cd tsp-solver
  
    pip install -r requirements.txt  # Если есть
    python gui/main.py  # Или python -m gui.main_window
```

## Использование

1. **Загрузка данных**:
   - Нажмите "Load CSV" и выберите файл (формат: id;region;municipality;settlement;type;latitude_dd;longitude_dd).
   - Пример: Данные Сибири (~6137 строк). Чекбокс "Map in degrees" — для отображения в реальных координатах (делит на 100).

2. **Настройка**:
   - Метод: "nn" (быстрый, ~0.2с) или "nn+2opt" (улучшенный, самостоятельный выбор времени или итераций).
   - Max 2-opt iters: 1000 (по умолчанию).
   - Time limit: 0 (без лимита) или секунды.
   - Marker density: 1 (все точки).

3. **Запуск**:
   - Нажмите "Start". Прогресс в логах (open/closed length, время). Карта обновляется каждую секунду.
   - "Stop" — прерывает (кооперативно, проверяет time_limit).

4. **Экспорт**:
   - После завершения: "Export solution.csv" (from_id;distance, n-1 строк).
   - "Export route.csv" (ID по порядку).
   - meta.json: Автосохранение (n, time, lengths).

### Пример вывода
- **meta.json** (NN+2opt):
  ```json
  {
    "method": "nn+2opt",
    "n": 6137,
    "time_seconds": 60.01,
    "best_open_length": 104128.35,
    "best_closed_length": 104141.35,
    "start_idx": 3753
  }
  ```
- **solution.csv** (фрагмент):
  ```
  3753;5.099
  2533;10.630
  ...
  ```

## Структура кода

```
tsp-solver/
├── gui/
│   ├── main_window.py     # Главное окно PyQt5
│   ├── map_widget.py      # Folium в QWebEngineView
│   ├── ui/                # Иконки
│   │   ├── start.png
│   │   ├── stop.png
│   │   └── files.png
│   └── worker.py          # QThread для solver (progress/finished)
├── tsp/
│   ├── __init__.py        # Экспорты
│   ├── loader.py          # Загрузка CSV, валидация
│   ├── distances.py       # Евклидова матрица D, route_length
│   ├── heuristics.py      # NN, 2-opt
│   ├── solver.py          # solve_tsp (wrapper)
│   ├── exporter.py        # CSV/JSON вывод
│   └── utils.py           # Валидация, timer
└── main.py                # Entry point: app = QApplication; window.show()
```

## Лицензия
MIT License. Автор: Vakhlyuev Vadim