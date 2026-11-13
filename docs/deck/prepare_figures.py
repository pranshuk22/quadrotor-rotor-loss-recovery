"""Crops the title rows (which carry internal experiment labels) from the result figures used on the slides.

Reads results/figures/*.png, writes docs/deck/figures/*.png. The slide builder adds the panel captions as text.
Usage: .venv/bin/python docs/deck/prepare_figures.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC, DST = ROOT / "results/figures", ROOT / "docs/deck/figures"
# rows removed from the top (pixels): the overall title only, or the title and the panel titles
CROP = {
    "e1_rho_sweep.png": 70, "e3_failed_lqr_nonlinear.png": 70, "e6_multistep_error.png": 70,
    "e7_altitude.png": 70, "e8_altitude.png": 70, "e8_full_koopman.png": 70,
    "e6_data_efficiency.png": 66, "e8c_adaptive.png": 62, "e8d_spinup.png": 62, "e8f_ablations.png": 62,
}
DST.mkdir(exist_ok=True)
for name, top in CROP.items():
    im = Image.open(SRC / name)
    w, h = im.size
    im.crop((0, top, w, h)).save(DST / name)
    print(name, (w, h - top))
