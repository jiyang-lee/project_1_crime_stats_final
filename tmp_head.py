from pathlib import Path
lines = Path('4_streamlit/pages/hotspot.py').read_text(encoding='utf-8').splitlines()
for i in range(1, 30):
    print(f"{i}: {lines[i-1]}")
