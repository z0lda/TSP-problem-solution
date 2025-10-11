"""
loader.py
CSV load, data validation
"""

import pandas as pd
import numpy as np
import csv
from typing import List, Optional

# CSV-file columns that need to be validated.
REQUIRED_COLUMNS_DEFAULT = [
    'id', 'region', 'municipality', 'settlement',
    'type', 'latitude_dd', 'longitude_dd'
]

def _detect_delimiter(path: str, sample_lines: int = 5) -> str:
    """
    Try to detect CSV delimiter using csv.Sniffer on the first few lines.
    Returns detected delimiter (',' or ';' or '\\t' etc.), or ',' by default.
    """
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        sample = ''.join([next(f) for _ in range(sample_lines)])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[',',';','\\t','|'])
        return dialect.delimiter
    except Exception:
        # fallback to comma
        return ','

def load_path(path: str,
              sep: Optional[str] = ';',
              required_cols: Optional[List[str]] = None,
              convert_to_degrees: bool = False) -> pd.DataFrame:
    """
    Read CSV and validate required columns. If `sep` is provided it will be
    used first; if required columns are missing, the function will attempt to
    auto-detect the delimiter and read again.
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS_DEFAULT

    # try initial read with given sep first
    try:
        df = pd.read_csv(path, sep=sep, dtype={
            'id': object,
            'region': object,
            'municipality': object,
            'settlement': object,
            'type': object,
            'latitude_dd': float,
            'longitude_dd': float
        })
    except Exception as e:
        # if reading with given sep fails, attempt autodetect
        detected = _detect_delimiter(path)
        df = pd.read_csv(path, sep=detected, dtype={
            'id': object,
            'region': object,
            'municipality': object,
            'settlement': object,
            'type': object,
            'latitude_dd': float,
            'longitude_dd': float
        })

    # validate columns
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # try autodetect if we haven't already
        detected = _detect_delimiter(path)
        if sep != detected:
            df = pd.read_csv(path, sep=detected, dtype={
                'id': object,
                'region': object,
                'municipality': object,
                'settlement': object,
                'type': object,
                'latitude_dd': float,
                'longitude_dd': float
            })
            missing = [c for c in required_cols if c not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns in CSV after attempts: {missing}")

    if convert_to_degrees:
        df = df.copy()
        df['latitude'] = df['latitude_dd'] / 100.0
        df['longitude'] = df['longitude_dd'] / 100.0

    return df


def get_points(df: pd.DataFrame,
               lat_col: str = 'latitude_dd',
               lon_col: str = 'longitude_dd',
               convert_to_degrees: bool = False) -> np.ndarray:
    """
    Extract points array.
    :param df: Pandas dataframe
    :param lat_col: latitude
    :param lon_col: longitude
    :param convert_to_degrees:
    :return: matrix with lat and lon in np.float32
    """

    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(f"Columns {lat_col} and {lon_col} must exist in DataFrame")

    # transform np.Dataframe to numpy.darray with only needed columns
    coords = df[[lat_col, lon_col]].to_numpy(dtype=np.float64)
    if convert_to_degrees:
        coords = coords / 100.0

    return coords.astype(np.float32)

def get_ids(df: pd.DataFrame, id_col: str = 'id') -> List:
    """
    returns list of ids using numpy "tolist"
    :param df: pandas dataframe
    :param id_col: column to search
    :return: list of ids
    """

    if id_col not in df.columns:
        raise ValueError(f"Column {id_col} not found in DataFrame")
    return df[id_col].tolist()