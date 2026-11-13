"""E8d (K8): residual trained on spin-up and capture transients.

Question. The offline residual is trained near the relaxed hover, but capture starts far from it (E9a). Does adding
capture transients to the training data improve prediction and closed-loop capture, and what does it cost near the trim?

Fixed before running (do not tune afterwards)
  - Near-trim data: the E6/E7 set (40 episodes of 4 s on family A, seed 11).
  - Transient data: `generate_capture` on family A, 40 episodes (seed 31), tau ~ U[0, 20] ms, E4 pre-failure
    distribution, spin-up 2.95 N, excited failure LQR after the hand-over, 4 s from the hand-over, command filter
    starting at (f_spin, 0, f_spin); diverged episodes discarded and counted. RULE AMENDED after run 1 (kept in
    results/tables/e8d_run1_discard_rule.md): the first rule (|n_xy deviation| > 0.9) removed 32 of 40 training and 7 of 10 test
    episodes because genuine hand-over states already have a median tilt deviation of 0.87. The rule is now: non-finite, or a
    body-rate norm above 60 rad/s (max_n_dev = 2.0, max_rate = 60).
  - Models (all: 91-function dictionary, ridge 1e-3, 99.5 % clip, standardisation recomputed from the training set used):
      near-trim only (E6), transients only, near-trim + transients, near-trim + transients with row-normalised
      regression (each row divided by the norm of its dictionary row), analytical (no residual).
  - Test data, disjoint seeds: 10 held-out near-trim episodes of family A (seed 12) and 10 held-out transient episodes
    (seed 32, same generator). Prediction error: the E6 protocol (normalised by the near-trim training standard
    deviations, starts every 40 steps, horizons 5 ms to 2 s).
  - Closed loop (E7 Part 2 protocol, family A, exact hover start, spin-up 2.95 N, tau in {0, 10, 20, 30, 40, 60} ms):
    MPC with each residual, judged against its own steady state, plus LQR and analytical MPC.
  - Reported: number of discarded episodes, per-model errors on both test sets.

Outputs: results/tables/e8d_spinup_residual.md, results/figures/e8d_spinup.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from rq1_common import closed_loop_reference, run_delay  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import (TS, Dataset, NominalModel, ResidualEDMD, generate, generate_capture,  # noqa: E402
                               multistep_errors, nominal_rollout)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import MUTED, SERIES, apply_style, save  # noqa: E402

HORIZONS = np.array([1, 4, 10, 20, 40, 100, 200, 400])
TAUS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]


def cat(a: Dataset, b: Dataset):
    return Dataset(a.x + b.x, a.fe + b.fe, a.u + b.u)


def main():
    apply_style()
    eq = relaxed_hover(P)
    PA = truth_family("A")
    nom = NominalModel.build(P, eq)
    near = generate(PA, P, eq, 40, 4.0, seed=11)
    trans, bad_tr = generate_capture(PA, P, eq, 40, 4.0, seed=31, max_n_dev=2.0, max_rate=60.0)
    test_near = generate(PA, P, eq, 10, 4.0, seed=12)
    test_tr, bad_te = generate_capture(PA, P, eq, 10, 4.0, seed=32, max_n_dev=2.0, max_rate=60.0)
    scale = np.std(np.vstack(near.x), axis=0)
    models = {"Near-trim only (E6)": ResidualEDMD.fit(near, nom, P),
              "Transients only": ResidualEDMD.fit(trans, nom, P),
              "Near-trim + transients": ResidualEDMD.fit(cat(near, trans), nom, P),
              "Near-trim + transients, row-normalised": ResidualEDMD.fit(cat(near, trans), nom, P, weighting="row")}

    def evaluate(test):
        rolls = {"Analytical (M&D)": lambda x, f, U: nominal_rollout(nom, x, f, U)}
        rolls.update({k: m.rollout for k, m in models.items()})
        return multistep_errors(rolls, test, HORIZONS, scale, starts_every=40)

    En, Et = evaluate(test_near), evaluate(test_tr)
    hz = HORIZONS * TS * 1e3
    L = ["# E8d: Residual trained on spin-up and capture transients", "",
         f"Training: 40 near-trim episodes (E6 data) and {len(trans.x)} capture-transient episodes "
         f"({bad_tr} discarded; {sum(len(u) for u in trans.u)} samples at {TS * 1e3:.0f} ms, recorded from the hand-over on). "
         f"Test: 10 near-trim episodes (seed 12) and {len(test_tr.x)} transient episodes (seed 32, {bad_te} discarded), "
         "all on family A. Settings fixed in the docstring of `experiments/e8d_spinup_residual.py`.", "",
         "Hand-over states of the transient data (median over episodes): "
         f"|n_xy deviation| = {np.median([np.linalg.norm(X[0][3:5]) for X in trans.x]):.2f}, "
         f"|rate deviation| = {np.median([np.linalg.norm(X[0][:3]) for X in trans.x]):.1f} rad/s.", ""]
    for tag, E in (("held-out near-trim episodes", En), ("held-out transient episodes", Et)):
        L += [f"## Multi-step prediction error on {tag} (normalised RMSE)", "", "| Model | " + " | ".join(f"{h:.0f} ms" for h in hz) + " |",
              "|---|" + "---|" * len(hz)]
        for name, e in E.items():
            L.append(f"| {name} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
        L.append("")
    specs = {"LQR": ("lqr", {}), "MPC, analytical": ("mpc", {})}
    specs.update({f"MPC, {k}": ("mpc", dict(residual=m)) for k, m in models.items() if k != "Transients only"})
    with ProcessPoolExecutor(max_workers=8) as ex:
        refs = {n: ex.submit(closed_loop_reference, (s, PA)) for n, s in specs.items()}
        refs = {n: f.result() for n, f in refs.items()}
        futs = {(n, t): ex.submit(run_delay, (specs[n], PA, t, refs[n], None)) for n in specs for t in TAUS}
        dl = {k: f.result() for k, f in futs.items()}
    L += ["## Capture after a detection delay (family A, exact hover, spin-up 2.95 N): alt. loss (m) / min n_z / SAFE", "",
          "| tau (ms) | " + " | ".join(specs) + " |", "|---|" + "---|" * len(specs)]
    for t in TAUS:
        L.append(f"| {t * 1e3:.0f} | " + " | ".join(
            f"{dl[(n, t)]['alt_loss']:.2f} / {dl[(n, t)]['min_nz']:.2f} / {'yes' if dl[(n, t)]['safe'] else 'no'}" for n in specs) + " |")
    L.append("")
    (ROOT / "results/tables/e8d_spinup_residual.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    cols = {"Analytical (M&D)": MUTED, "Near-trim only (E6)": SERIES[1], "Transients only": SERIES[3],
            "Near-trim + transients": SERIES[0], "Near-trim + transients, row-normalised": SERIES[2]}
    for ax, (tag, E) in zip(axs, (("held-out near-trim", En), ("held-out transients", Et))):
        for name, e in E.items():
            ax.plot(hz, e, marker="o", ms=3, color=cols[name], label=name)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("prediction horizon (ms)")
        ax.set_title(f"E8d · {tag}")
    axs[0].set_ylabel("normalised RMSE")
    axs[0].legend(fontsize=7)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8d_spinup.png")


if __name__ == "__main__":
    main()
