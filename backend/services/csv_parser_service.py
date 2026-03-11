"""
CSV parsing service — loads Channel-1 DCRM signatures and normalises 407_B-style files.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List


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
    """
    try:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip", header=1)
        df = df.dropna(axis=1, how="all")
        df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)

        ch1_cols: List[str] = []
        for col in df.columns:
            low = col.lower()
            if ("coil" in low and "c1" in low) or \
               ("travel" in low and "t1" in low) or \
               ("res" in low and "ch1" in low) or \
               ("current" in low and "ch1" in low):
                ch1_cols.append(col)

        if not ch1_cols:
            return None, f"No Channel-1 columns found. Detected: {df.columns.tolist()}"

        vector = df[ch1_cols].fillna(0).values.flatten()
        return vector, None
    except Exception as exc:
        return None, str(exc)


def extract_timeseries(path: str) -> dict:
    """
    Return per-channel lists of values for graph rendering (first 1 000 points).
    """
    try:
        df = pd.read_csv(path, engine="python", on_bad_lines="skip", header=1)
        df = df.dropna(axis=1, how="all")
        df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)
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
            result["coil_current"] = df[col].fillna(0).tolist()[:1000]
        elif "travel" in low and "t1" in low:
            result["contact_travel"] = df[col].fillna(0).tolist()[:1000]
        elif "res" in low and "ch1" in low:
            result["resistance"] = df[col].fillna(0).tolist()[:1000]
        elif "current" in low and "ch1" in low:
            result["dcrm_current"] = df[col].fillna(0).tolist()[:1000]
    return result
