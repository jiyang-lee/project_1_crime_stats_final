from pathlib import Path
lines = Path('4_streamlit/pages/hotspot.py').read_text(encoding='utf-8').splitlines()
for i in range(160, 230):
    print(f'{i+1}: {lines[i]}')
