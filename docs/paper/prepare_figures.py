"""Copies the result figures into docs/paper/figures/ without their title rows (internal experiment names).

Usage (repository root): .venv/bin/python docs/paper/prepare_figures.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC, DST = ROOT / "results/figures", ROOT / "docs/paper/figures"
CROP = {"e6_multistep_error.png": 70, "e7_altitude.png": 70, "e8_altitude.png": 70, "e8c_adaptive.png": 62, "e8d_spinup.png": 62}
DST.mkdir(exist_ok=True)
for name, top in CROP.items():
    im = Image.open(SRC / name)
    im.crop((0, top, im.size[0], im.size[1])).save(DST / name)
