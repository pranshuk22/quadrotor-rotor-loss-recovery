"""Copies the result figures into docs/report/figures/ without their title rows.

The title rows carry the internal experiment names; the captions in the report describe each figure instead.
Usage (repository root): .venv/bin/python docs/report/prepare_figures.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC, DST = ROOT / "results/figures", ROOT / "docs/report/figures"
CROP = {  # pixel rows removed from the top
    "e1_rho_sweep.png": 70, "e3_failed_lqr_nonlinear.png": 70, "e3_healthy_lqr_nonlinear.png": 70,
    "e6_multistep_error.png": 70, "e6_full_edmdc_eigs.png": 92, "e6_data_efficiency.png": 66,
    "e7_altitude.png": 70, "e8_altitude.png": 70, "e8_full_koopman.png": 70,
    "e8c_adaptive.png": 62, "e8d_spinup.png": 62, "e8e_horizon.png": 62, "e8f_ablations.png": 62, "e8g_plants.png": 62,
}
DST.mkdir(exist_ok=True)
for name, top in CROP.items():
    im = Image.open(SRC / name)
    im.crop((0, top, im.size[0], im.size[1])).save(DST / name)
