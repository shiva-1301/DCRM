"""
Standalone training script — run this from the project root to train/retrain the model
using all CSV files in the data/ folder.

Usage:
    python ml/training/train_model.py
"""
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import glob
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

# Import ML utilities
from ml.utils.features import extract_features

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "model")
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "dcrm_training_dataset.npz")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)


def load_signature(path):
    import pandas as pd
    try:
        # Read CSV with header on line 2
        df = pd.read_csv(path, engine="python", on_bad_lines="skip", header=1)
        
        # Remove empty spacer columns
        df = df.dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace("\t", " ", regex=False)
        
        # Use centralized feature extraction
        return extract_features(df), None
    except Exception as e:
        return None, str(e)


def main():
    X, y = [], []
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    print(f"Found {len(files)} CSV files in {DATA_DIR}")
    for fp in files:
        fn = os.path.basename(fp).lower()
        label = "healthy" if "healthy" in fn else "main" if "main" in fn else "arc" if "arc" in fn else None
        if label is None:
            print(f"  ⚠ Skipping {fp} — no label in filename")
            continue
        vec, err = load_signature(fp)
        if err or vec is None or vec.size == 0:
            print(f"  ⚠ Skipping {fp} — {err}")
            continue
        X.append(vec)
        y.append(label)
        print(f"  ✓ {os.path.basename(fp)} → {label}")

    if not X:
        print("❌ No usable training data found.")
        sys.exit(1)

    # Statistical features are already fixed length! No more manual alignment.
    X_aligned = np.array(X)

    # Save dataset
    np.savez(DATASET_PATH, X=np.array(X_aligned, dtype=object), y=np.array(y, dtype=object))

    # Train
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_aligned)
    model = RandomForestClassifier(n_estimators=300, random_state=42)

    if len(set(y)) > 1 and len(X) >= 5:
        scores = cross_val_score(model, X_scaled, y, cv=min(5, len(X)), scoring="accuracy")
        print(f"\n📊 Cross-val accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

    model.fit(X_scaled, y)
    joblib.dump(model, os.path.join(MODEL_DIR, "dcrm_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "dcrm_scaler.pkl"))
    print(f"\n✅ Model trained with {len(X)} samples and saved to {MODEL_DIR}")


if __name__ == "__main__":
    main()
