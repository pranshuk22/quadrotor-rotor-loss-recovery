"""E8g (K11): truth plants with air-relative thrust and quadratic drag (families A+ and B+).

Question. Do the conclusions (E6 prediction, E7/E8a regulation) survive when the truth plant contains the two
remaining IJRR 2016 effects: thrust from the propeller speed relative to the air and quadratic drag?

Fixed before running (do not tune afterwards)
  - Plants: A+ = A + air-relative thrust + quadratic drag (Kd = (0.7, 0.7, 1.4) e-4 N m s^2/rad^2, replaces the linear yaw drag);
    B+ = B + the same effects. Controllers are designed on the nominal model, as in E6 to E8a.
  - (a) Prediction (E6 protocol, horizons 5 ms to 3 s, starts every 40 steps, normalised by the training standard deviations):
    models trained on 40 episodes of 4 s on A+ (seed 111): analytical, full-state EDMDc, residual EDMDc; tested on 10 episodes of A+
    (seed 112) and of B+ (seed 113). Extra rows: the residual trained on family A (E6 data) tested on A+ and B+.
  - (b) Regulation (E7 Part 1 protocol) on A+ (full), A+ without thrust loss, nominal + effects only, B+ (full, held out),
    B+ without thrust loss: LQR, MPC analytical, MPC residual (trained on A+), offset-free MPC (state d), LQR + integrator.
  - The physics tests with the effects off and the bit-identity of the default dynamics are in tests/test_truth_effects.py.
  - E6/E7 are re-run after the code change and their tables diffed (see the commit message of the regenerated tables).

Outputs: results/tables/e8g_realistic_plant.md, results/figures/e8g_plants.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from shared import run_regulation  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import (TS, FullEDMDc, NominalModel, ResidualEDMD, generate, multistep_errors,  # noqa: E402
                               nominal_rollout)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402

HORIZONS = np.array([1, 4, 10, 20, 40, 100, 200, 400, 600])


def plants():
    Ap, Bp = truth_family("A+"), truth_family("B+")
    return {"A+ (full)": Ap, "A+ without thrust loss": replace(Ap, thrust_loss=0.0),
            "nominal + effects only": replace(P, air_relative=True, quad_drag=Ap.quad_drag, gamma=0.0),
            "B+ (full, held out)": Bp, "B+ without thrust loss": replace(Bp, thrust_loss=0.0)}


def main():
    apply_style()
    eq = relaxed_hover(P)
    nom = NominalModel.build(P, eq)
    Ap, Bp = truth_family("A+"), truth_family("B+")
    train = generate(Ap, P, eq, 40, 4.0, seed=111)
    test_Ap = generate(Ap, P, eq, 10, 4.0, seed=112)
    test_Bp = generate(Bp, P, eq, 10, 4.0, seed=113)
    scale = np.std(np.vstack(train.x), axis=0)
    res = ResidualEDMD.fit(train, nom, P)
    full = FullEDMDc.fit(train)
    res_A = ResidualEDMD.fit(generate(truth_family("A"), P, eq, 40, 4.0, seed=11), nom, P)
    rolls = {"Analytical (M&D)": lambda x, f, U: nominal_rollout(nom, x, f, U), "Full-state EDMDc (A+)": full.rollout,
             "Residual EDMDc (A+)": res.rollout, "Residual EDMDc (trained on A, E6)": res_A.rollout}
    hz = HORIZONS * TS * 1e3
    L = ["# E8g: Truth plants with air-relative thrust and quadratic drag (A+, B+)", "",
         f"Training: {len(train.x)} episodes of 4 s on A+ (seed 111). Test: 10 episodes of A+ (seed 112) and of B+ (seed 113). "
         "Settings fixed in the docstring of `experiments/e8g_realistic_plant.py`.", "",
         f"Full-state EDMDc trained on A+: {int(np.sum(np.abs(full.eigs()) > 1 + 1e-9))} of {full.A.shape[0]} eigenvalues outside the unit circle, "
         f"spectral radius {np.max(np.abs(full.eigs())):.4f}.", ""]
    for tag, test in (("A+", test_Ap), ("B+ (held out)", test_Bp)):
        E = multistep_errors(rolls, test, HORIZONS, scale, starts_every=40)
        L += [f"## Multi-step prediction error on {tag} (normalised RMSE)", "", "| Model | " + " | ".join(f"{h:.0f} ms" for h in hz) + " |",
              "|---|" + "---|" * len(hz)]
        for n, e in E.items():
            L.append(f"| {n} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
        L.append("")
    PL = plants()
    specs = {"LQR": ("lqr", {}), "MPC, analytical": ("mpc", {}), "MPC, residual (A+)": ("mpc", dict(residual=res)),
             "Offset-free MPC (state d)": ("of", dict(disturbance="state")), "LQR + integrator": ("lqri", {})}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {(n, pl): ex.submit(run_regulation, (s, PL[pl])) for n, s in specs.items() for pl in PL}
        reg = {k: f.result() for k, f in futs.items()}
    L += ["## Steady altitude bias (E7 Part 1 protocol; mean altitude over the last 2 s; 'diverged' if the run ended inverted or non-finite)", "",
          "| Plant | " + " | ".join(specs) + " |", "|---|" + "---|" * len(specs)]
    for pl in PL:
        cells = []
        for n in specs:
            r = reg[(n, pl)]
            cells.append(f"{r['z_ss']:+.3f} m" if r["upright"] and abs(r["z_ss"]) < 100 else "diverged")
        L.append(f"| {pl} | " + " | ".join(cells) + " |")
    L.append("")
    (ROOT / "results/tables/e8g_realistic_plant.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(figsize=(8, 3.8))
    names = list(PL)
    for k, n in enumerate(specs):
        ys = [reg[(n, pl)]["z_ss"] if reg[(n, pl)]["upright"] and abs(reg[(n, pl)]["z_ss"]) < 100 else np.nan for pl in names]
        ax.plot(range(len(names)), ys, marker="o", color=SERIES[k % 8], label=n)
    ax.axhline(0, color=REF, lw=0.8)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace(" ", "\n", 1) for n in names], fontsize=7)
    ax.set_ylabel("steady altitude error (m)")
    ax.set_title("E8g · regulation on A+ and B+")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8g_plants.png")


if __name__ == "__main__":
    main()
