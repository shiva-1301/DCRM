"""Check column names in all training CSVs."""
import pandas as pd

for f in ['data/healthy_sample.csv', 'data/main_sample.csv', 'data/arc_sample.csv']:
    df = pd.read_csv(f, engine='python', on_bad_lines='skip', header=1)
    df = df.dropna(axis=1, how='all')
    df.columns = df.columns.str.strip().str.replace('\t', ' ', regex=False)
    print(f"\n=== {f} ===")
    print(f"  Columns ({len(df.columns)}): {df.columns.tolist()}")
    print(f"  Rows: {len(df)}")
