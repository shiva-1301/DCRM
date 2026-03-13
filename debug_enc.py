
path = r'c:\Users\Shivadhanu\OneDrive\Desktop\DCRM\data\dcrm_info.md'
try:
    with open(path, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    print(f"First 20 bytes: {data[:20]}")
    
    # Try common encodings
    for enc in ['utf-8', 'utf-16', 'utf-16-le', 'cp1252', 'latin-1']:
        try:
            data.decode(enc)
            print(f"✅ Decodable as: {enc}")
        except UnicodeDecodeError:
            print(f"❌ NOT decodable as: {enc}")

except Exception as e:
    print(f"Error: {e}")
