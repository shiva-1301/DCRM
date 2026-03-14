"""Retrain the model using the corrected feature extraction pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from backend.services.csv_parser_service import extract_features_from_file

DATA_DIR = 'data'
MODEL_PATH = 'dcrm_model.pkl'
SCALER_PATH = 'dcrm_scaler.pkl'

# Collect features from training CSVs
X, y = [], []
for fname, label in [('healthy_sample.csv', 'healthy'), ('main_sample.csv', 'main'), ('arc_sample.csv', 'arc')]:
    path = os.path.join(DATA_DIR, fname)
    features, err = extract_features_from_file(path)
    if err:
        print(f"ERROR extracting {fname}: {err}")
        continue
    print(f"{fname}: {len(features)} features, non-zero={sum(1 for f in features if f != 0)}")
    X.append(features)
    y.append(label)

print(f"\nTotal samples: {len(X)}, Labels: {y}")

# Train
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X_scaled, y)

# Save
joblib.dump(model, MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"\nModel saved: {MODEL_PATH}")
print(f"Scaler saved: {SCALER_PATH}")
print(f"Scaler n_features_in_: {scaler.n_features_in_}")

# Verify predictions for each training file
print("\n=== Verification ===")
for fname, expected in [('healthy_sample.csv', 'healthy'), ('main_sample.csv', 'main'), ('arc_sample.csv', 'arc')]:
    path = os.path.join(DATA_DIR, fname)
    features, _ = extract_features_from_file(path)
    scaled = scaler.transform([features])
    pred = model.predict(scaled)[0]
    proba = model.predict_proba(scaled)[0]
    prob_dict = {cls: round(float(p)*100, 1) for cls, p in zip(model.classes_, proba)}
    match = "OK" if pred == expected else "MISMATCH"
    print(f"  {fname}: predicted={pred}, expected={expected} [{match}]  proba={prob_dict}")
