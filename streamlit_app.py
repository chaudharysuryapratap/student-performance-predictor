"""Streamlit Community Cloud entry point."""

from pathlib import Path
from runpy import run_path

run_path(str(Path(__file__).resolve().parent / "app/main.py"), run_name="__main__")
