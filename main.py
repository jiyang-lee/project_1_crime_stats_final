from pathlib import Path
import os
import runpy
import sys


APP_DIR = Path(__file__).resolve().parent / "4_streamlit"
APP_MAIN = APP_DIR / "main.py"

if __name__ == "__main__":
    # Ensure Streamlit pages and local imports resolve like direct app execution.
    app_dir_str = str(APP_DIR)
    if app_dir_str not in sys.path:
        sys.path.insert(0, app_dir_str)
    os.chdir(APP_DIR)
    runpy.run_path(str(APP_MAIN), run_name="__main__")
