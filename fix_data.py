import os

samples = {
    "data/healthy_sample.csv": "graph_plotter/HYDERABAD SS_409_61970C_16-11-2024_16-31-24_DCRM_20-11-2024_15-12-24.csv",
    "data/main_sample.csv": "graph_plotter/HYDERABAD SS_409_61970C_16-11-2024_16-49-25_DCRM_20-11-2024_15-13-07.csv",
    "data/arc_sample.csv": "graph_plotter/HYDERABAD SS_409_61970C_16-11-2024_17-48-41_DCRM_20-11-2024_15-13-54.csv"
}

for dest, src in samples.items():
    try:
        with open(src, 'r', encoding='utf-8', errors='ignore') as s:
            content = s.read()
        with open(dest, 'w', encoding='utf-8', newline='') as d:
            d.write('.\n') # Blank/metadata row
            d.write(content)
        print(f"✅ Created {dest}")
    except Exception as e:
        print(f"❌ Error creating {dest}: {e}")
