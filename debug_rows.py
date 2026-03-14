with open('data/main_sample.csv', 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if 43 <= i <= 50:
            truncated = line[:150].strip()
            print(f"Row {i}: {truncated}")
