"""
CSV parsing service — loads DCRM signatures with smart header detection,
extracts Channel-1 data and statistical features for the model.
"""
import io
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List


def _find_header_row(filepath: str) -> int:
    """
    Scan the CSV for the row that contains the actual column headers.
    DCRM CSVs may have 0–50+ rows of metadata before the data header.
    Returns the 0-based index of the header row (default 1 if not found).
    """
    keywords = ["coil current c1", "contact travel t1", "dcrm res ch1", "dcrm current ch1"]
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                low = line.lower()
                if any(kw in low for kw in keywords):
                    return i
                if i > 100:  # safety limit
                    break
    except Exception:
        pass
    return 1  # fallback


def _load_dataframe(filepath: str) -> pd.DataFrame:
    """
    Load a DCRM CSV into a clean DataFrame with proper header detection.
    Handles both simple CSVs (header on row 1-2) and complex ones with
    metadata blocks (header on row ~46).
    """
    header_row = _find_header_row(filepath)
    # Skip all rows before the header so pandas uses the header as column names
    df = pd.read_csv(
        filepath,
        engine="python",
        on_bad_lines="skip",
        skiprows=range(header_row),  # skip rows 0..header_row-1
        header=0,                     # first non-skipped row = header
    )
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)
    return df


def _find_ch1_columns(df: pd.DataFrame) -> List[str]:
    """Find Channel-1 columns matching the DCRM naming patterns."""
    ch1_cols = []
    for col in df.columns:
        low = col.lower()
        if ("coil" in low and "c1" in low) or \
           ("travel" in low and "t1" in low) or \
           ("res" in low and "ch1" in low) or \
           ("current" in low and "ch1" in low):
            ch1_cols.append(col)
    return ch1_cols


def convert_407b_to_arc_format(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Normalise 407_B-style CSV files so the data header sits on line 2,
    matching the arc_* layout expected by the model.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) < 5:
            return False, "File too short to normalise"
        probe = " ".join(lines[:3]).lower()
        if "close -velocity" not in probe and "open -velocity" not in probe:
            return False, None  # already in arc_* format — nothing to do
        data_section = lines[4:]
        if not data_section:
            return False, "No data rows after metadata"
        header_cells = data_section[0].rstrip("\n").split(",")
        spacer = ",".join([""] * len(header_cells)) + "\n"
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.writelines([spacer] + data_section)
        return True, None
    except Exception as exc:
        return False, str(exc)


def load_signature(path: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Load a DCRM CSV, extract Channel-1 columns and return a 1-D feature vector.
    Uses smart header detection to find the data rows.
    """
    try:
        df = _load_dataframe(path)
        ch1_cols = _find_ch1_columns(df)

        if not ch1_cols:
            return None, f"No Channel-1 columns found. Detected: {df.columns.tolist()}"

        vector = df[ch1_cols].fillna(0).values.flatten()
        return vector, None
    except Exception as exc:
        return None, str(exc)


def extract_features_from_file(path: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Load a DCRM CSV and extract 24 statistical features for the ML model.
    This is the correct feature extraction method that matches the trained model.
    
    Features (6 per channel, 4 channels = 24 total):
      For each of [coil, travel, resistance, current]:
        - mean, std, max, min, IQR (5 features)
        - 1 channel-specific feature (peak index / displacement / etc.)
    """
    try:
        df = _load_dataframe(path)
        
        # Define channels and their column-matching criteria
        channels = {
            'coil':    {'keywords': ['coil', 'c1']},
            'travel':  {'keywords': ['travel', 't1']},
            'res':     {'keywords': ['res', 'ch1']},
            'current': {'keywords': ['current', 'ch1']},
        }
        
        features = []
        
        for key, cfg in channels.items():
            # Find matching column
            col = None
            for c in df.columns:
                c_low = c.lower()
                if all(k in c_low for k in cfg['keywords']):
                    col = c
                    break
            
            if col is not None:
                series = pd.to_numeric(df[col], errors='coerce').fillna(0).values
                if len(series) > 0:
                    # Basic Stats (5 features)
                    features.append(float(np.mean(series)))
                    features.append(float(np.std(series)))
                    features.append(float(np.max(series)))
                    features.append(float(np.min(series)))
                    features.append(float(np.percentile(series, 75) - np.percentile(series, 25)))
                    
                    # Signal-specific feature (1 feature)
                    if key == 'coil':
                        features.append(float(np.argmax(series)))   # Peak time index
                    elif key == 'res':
                        closed_vals = series[series < 7000]
                        features.append(float(np.mean(closed_vals) if len(closed_vals) > 0 else 8000))
                    elif key == 'travel':
                        features.append(float(series[-1] - series[0]))  # Total displacement
                    else:  # current
                        features.append(float(np.sum(series > 1)))  # Duration of activity
                else:
                    features.extend([0.0] * 6)
            else:
                features.extend([0.0] * 6)
        
        if all(f == 0 for f in features):
            return None, f"All features are zero — column matching failed. Columns: {df.columns.tolist()}"
        
        return np.array(features), None
    except Exception as exc:
        return None, str(exc)


def extract_timeseries(path: str) -> dict:
    """
    Return per-channel lists of values for graph rendering (first 1 000 points).
    Uses smart header detection.
    """
    try:
        df = _load_dataframe(path)
    except Exception:
        return {}

    result = {
        "time": list(range(min(len(df), 1000))),
        "coil_current": [],
        "resistance": [],
        "dcrm_current": [],
        "contact_travel": [],
    }
    for col in df.columns:
        low = col.lower()
        if "coil" in low and "c1" in low:
            result["coil_current"] = pd.to_numeric(df[col], errors='coerce').fillna(0).tolist()[:1000]
        elif "travel" in low and "t1" in low:
            result["contact_travel"] = pd.to_numeric(df[col], errors='coerce').fillna(0).tolist()[:1000]
        elif "res" in low and "ch1" in low:
            result["resistance"] = pd.to_numeric(df[col], errors='coerce').fillna(0).tolist()[:1000]
        elif "current" in low and "ch1" in low:
            result["dcrm_current"] = pd.to_numeric(df[col], errors='coerce').fillna(0).tolist()[:1000]
    return result
