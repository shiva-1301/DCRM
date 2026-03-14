import sys
sys.path.insert(0, '.')
from backend.services.csv_parser_service import _load_dataframe, extract_features_from_file

for name in ['healthy_sample', 'main_sample', 'arc_sample']:
    path = f'data/{name}.csv'
    print(f"=== {name} ===")
    try:
        df = _load_dataframe(path)
        print(f"Shape: {df.shape}")
        # Show all column names
        for c in df.columns:
            low = c.lower()
            match = ""
            if "coil" in low and "c1" in low:
                match = " <-- COIL"
            elif "travel" in low and "t1" in low:
                match = " <-- TRAVEL"
            elif "res" in low and "ch1" in low:
                match = " <-- RES"
            elif "current" in low and "ch1" in low:
                match = " <-- CURRENT"
            if match:
                print(f"  Col: '{c}'{match}")
    except Exception as e:
        print(f"  Error: {e}")
    
    features, err = extract_features_from_file(path)
    if err:
        print(f"  Feature Error: {err}")
    else:
        print(f"  Features ({len(features)}): {features.tolist()}")
        print(f"  Non-zero: {sum(1 for f in features if f != 0)}")
    print()
