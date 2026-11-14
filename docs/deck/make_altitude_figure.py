"""Slide figure: altitude regulation of four controllers on two plants (large lines, readable legend).

Re-runs only the regulation part of experiments/e8_offset_free.py (same data, seeds and controllers) for the four
controllers shown, so the curves are those of results/figures/e8_altitude.png without the other four.
Usage (repository root): .venv/bin/python docs/deck/make_altitude_figure.py
Output: docs/deck/figures/e8_altitude_selected.png
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments")]
os.environ.setdefault("OMP_NUM_THREADS", "1")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from e8_offset_free import run_regulation  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import NominalModel, ResidualEDMD, generate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style  # noqa: E402

CTRLS = [("LQR", "LQR", SERIES[0], "-", 3.4), ("MPC, residual Koopman", "Residual Koopman MPC", SERIES[2], "-", 2.4),
         ("MPC, offset-free (state d)", "Offset-free MPC (state model)", SERIES[1], "--", 2.4),
         ("LQR + integrator", "LQR + integrator", SERIES[6], "-", 2.4)]
PLANTS = [("A (full)", "Plant A (residual trained here)"), ("B (full, held out)", "Plant B (held out)")]

if __name__ == "__main__":
    apply_style()
    eq = relaxed_hover(P)
    res = ResidualEDMD.fit(generate(truth_family("A"), P, eq, 40, 4.0, seed=11), NominalModel.build(P, eq), P)
    jobs = [(c[0], pl[0], res) for pl in PLANTS for c in CTRLS]
    with ProcessPoolExecutor(max_workers=8) as ex:
        out = list(ex.map(run_regulation, jobs))
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.5), sharey=True)
    for a, (pl, title) in zip(ax, PLANTS):
        for name, label, col, ls, lw in CTRLS:
            r = next(r for r in out if r["ctrl"] == name and r["plant"] == pl)
            a.plot(r["t"], r["z"], color=col, ls=ls, lw=lw, label=label)
        a.axhline(0, color=REF, lw=0.8)
        a.set_title(title, fontsize=14, fontweight="bold")
        a.set_xlabel("time (s)", fontsize=13)
        a.tick_params(labelsize=12)
    ax[0].set_ylabel("altitude (m), set-point 0", fontsize=13)
    ax[0].legend(loc="lower right", fontsize=12)
    fig.tight_layout()
    fig.savefig(ROOT / "docs/deck/figures/e8_altitude_selected.png", dpi=200)
    print("ok")
