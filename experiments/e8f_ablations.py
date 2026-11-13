"""E8f (K9): ablations of the residual Koopman model and its MPC.

Fixed before running (do not tune afterwards)
  Data: family A training set of the E6/E7 experiments (40 episodes of 4 s, seed 11); test sets: 10 episodes of A (seed 12) and of
  B (seed 13); a separate validation set of 10 episodes of A (seed 14) is used only to choose the ridge parameter.
  1. Dictionary degree 1, 2 (published), 3 for the residual (sizes 13, 91, 455; ridge 1e-3): test errors on A and B at horizons
     5 ms to 3 s and the condition number of the regularised Gram matrix.
  2. Ridge lambda in {1e-6, 1e-4, 1e-3, 1e-2, 1e-1}: chosen on the validation split by the mean normalised RMSE over the horizons
     {100, 200, 400} ms (the three horizons with 20, 40 and 80 steps), reported on the test splits for all values.
  3. Sampling period TS in {2, 5, 10} ms: data, nominal model and residual rebuilt at that period (generate(ts=...));
     prediction errors at the physical horizons {20, 100, 500, 1000} ms; closed-loop regulation (E7 Part 1 protocol) on A (full) and
     B without thrust loss with LQR, MPC analytical and MPC residual, controller period ts and a horizon of 0.1 s
     (round(0.1 / ts) steps).
  4. Sensor noise: Gaussian on the measurements (rates 0.05 rad/s, tilt 0.005 rad as a small rotation so |n| = 1, z 0.02 m,
     v_z 0.05 m/s), on the training data (noise seed 9500) and on the controller inputs (noise seeds 9510 to 9512, one per
     controller instance). Prediction: clean-trained and noise-trained residual on noisy test episodes (A seed 12 and B seed 13 with noise
     seed 9600). Closed loop: E7 Part 1 on A (full), B (full) and nominal + A's thrust loss with LQR, MPC analytical, MPC residual
     (clean-trained), MPC residual (noise-trained), offset-free MPC (state d). The errors-in-variables bias of the fit with noisy regressors
     is reported, not corrected.

Outputs: results/tables/e8f_ablations.md, results/figures/e8f_ablations.png
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

from e7_mpc_closed_loop import plants  # noqa: E402
from shared import run_regulation  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import (MeasurementNoise, NominalModel, ResidualEDMD, generate, multistep_errors,  # noqa: E402
                               nominal_rollout)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import MUTED, SERIES, apply_style, save  # noqa: E402

HORIZONS = np.array([1, 4, 10, 20, 40, 100, 200, 400, 600])
LAMBDAS = (1e-6, 1e-4, 1e-3, 1e-2, 1e-1)
VAL_H = np.array([20, 40, 80])


def errs(model_rolls, test, hz, scale):
    return multistep_errors(model_rolls, test, hz, scale, starts_every=40)


def main():
    apply_style()
    eq = relaxed_hover(P)
    nom = NominalModel.build(P, eq)
    PA, PB = truth_family("A"), truth_family("B")
    train = generate(PA, P, eq, 40, 4.0, seed=11)
    tA, tB, val = generate(PA, P, eq, 10, 4.0, seed=12), generate(PB, P, eq, 10, 4.0, seed=13), generate(PA, P, eq, 10, 4.0, seed=14)
    scale = np.std(np.vstack(train.x), axis=0)
    hz_ms = HORIZONS * 5.0
    L = ["# E8f: Ablations", "", "Settings fixed in the docstring of `experiments/e8f_ablations.py`. Errors are normalised RMSE (mean over the 7 states).", ""]

    # 1. degree
    L += ["## 1. Dictionary degree (residual EDMDc, ridge 1e-3)", "", "| Degree | dictionary size | cond(Gram) | test | " + " | ".join(f"{h:.0f} ms" for h in hz_ms) + " |",
          "|---|---|---|---|" + "---|" * len(hz_ms)]
    base = {"Analytical (M&D)": lambda x, f, U: nominal_rollout(nom, x, f, U)}
    deg_models = {}
    for deg in (1, 2, 3):
        m = ResidualEDMD.fit(train, nom, P, degree=deg)
        deg_models[deg] = m
        F = np.array([np.concatenate((X[k][[0, 1, 2, 3, 4, 6]], fe[k], U[k])) for X, fe, U in zip(train.x, train.fe, train.u) for k in range(len(U))])
        Psi = m.dic(F)
        cond = float(np.linalg.cond(Psi.T @ Psi + 1e-3 * np.eye(Psi.shape[1])))
        for tag, test in (("A", tA), ("B", tB)):
            e = errs({"r": m.rollout}, test, HORIZONS, scale)["r"]
            L.append(f"| {deg} | {m.dic.size} | {cond:.1e} | {tag} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
    for tag, test in (("A", tA), ("B", tB)):
        e = errs(base, test, HORIZONS, scale)["Analytical (M&D)"]
        L.append(f"| analytical | - | - | {tag} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
    L.append("")

    # 2. ridge
    L += ["## 2. Ridge parameter (chosen on the validation split by the mean error at 100, 200 and 400 ms)", "",
          "| lambda | validation (mean) | test A: 100 ms / 500 ms / 1 s | test B: 100 ms / 500 ms / 1 s |", "|---|---|---|---|"]
    vals = {}
    sel = [5, 6, 7]
    for lam in LAMBDAS:
        m = ResidualEDMD.fit(train, nom, P, lam=lam)
        ev = errs({"r": m.rollout}, val, HORIZONS, scale)["r"]
        ea, eb = (errs({"r": m.rollout}, t, HORIZONS, scale)["r"] for t in (tA, tB))
        vals[lam] = float(np.mean(ev[sel]))
        L.append(f"| {lam:g} | {vals[lam]:.3f} | " + " / ".join(f"{ea[i]:.3f}" for i in (5, 6, 7)) + " | " + " / ".join(f"{eb[i]:.3f}" for i in (5, 6, 7)) + " |")
    best = min(vals, key=vals.get)
    L += ["", f"Chosen on validation: lambda = {best:g} (published: 1e-3).", ""]

    # 3. TS
    L += ["## 3. Sampling period", ""]
    physical = {"20 ms": 0.02, "100 ms": 0.1, "500 ms": 0.5, "1000 ms": 1.0}
    L += ["| TS | test | " + " | ".join(physical) + " |", "|---|---|" + "---|" * len(physical)]
    ts_models = {}
    for ts in (0.002, 0.005, 0.010):
        nom_t = NominalModel.build(P, eq, ts)
        tr = generate(PA, P, eq, 40, 4.0, seed=11, ts=ts)
        m = ResidualEDMD.fit(tr, nom_t, P)
        ts_models[ts] = m
        hz = np.array([int(round(h / ts)) for h in physical.values()])
        sc = np.std(np.vstack(tr.x), axis=0)
        for tag, pt, seed in (("A", PA, 12), ("B", PB, 13)):
            te = generate(pt, P, eq, 10, 4.0, seed=seed, ts=ts)
            rolls = {"analytical": lambda x, f, U, n=nom_t: nominal_rollout(n, x, f, U), "residual": m.rollout}
            e = multistep_errors(rolls, te, hz, sc, starts_every=int(round(0.2 / ts)))
            for k, v in e.items():
                L.append(f"| {ts * 1e3:.0f} ms | {tag}, {k} | " + " | ".join(f"{x:.3f}" for x in v) + " |")
    L.append("")
    PLd = {"A (full)": PA, "B without thrust loss": replace(PB, thrust_loss=0.0)}
    jobs = {}
    for ts, m in ts_models.items():
        h = int(round(0.1 / ts))
        specs = {"LQR": ("lqr", dict(ts=ts)), "MPC analytical": ("mpc", dict(ts=ts, horizon=h)),
                 "MPC residual": ("mpc", dict(ts=ts, horizon=h, residual=m))}
        for n, s in specs.items():
            for pl in PLd:
                jobs[(ts, n, pl)] = (s, PLd[pl])
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {k: ex.submit(run_regulation, v) for k, v in jobs.items()}
        reg_ts = {k: f.result() for k, f in futs.items()}
    L += ["Closed loop (steady altitude error, E7 Part 1 protocol, controller period = TS, horizon 0.1 s):", "",
          "| TS | plant | LQR | MPC analytical | MPC residual |", "|---|---|---|---|---|"]
    for ts in (0.002, 0.005, 0.010):
        for pl in PLd:
            L.append(f"| {ts * 1e3:.0f} ms | {pl} | " + " | ".join(f"{reg_ts[(ts, n, pl)]['z_ss']:+.3f} m" for n in ("LQR", "MPC analytical", "MPC residual")) + " |")
    L.append("")

    # 4. noise
    ns = MeasurementNoise()
    trn = generate(PA, P, eq, 40, 4.0, seed=11, noise=ns, noise_seed=9500)
    res_clean = ResidualEDMD.fit(train, nom, P)
    res_noisy = ResidualEDMD.fit(trn, nom, P)
    tAn = generate(PA, P, eq, 10, 4.0, seed=12, noise=ns, noise_seed=9600)
    tBn = generate(PB, P, eq, 10, 4.0, seed=13, noise=ns, noise_seed=9600)
    L += ["## 4. Sensor noise", "", "Prediction on noisy test episodes (normalised RMSE):", "",
          "| Model | test | " + " | ".join(f"{h:.0f} ms" for h in hz_ms) + " |", "|---|---|" + "---|" * len(hz_ms)]
    for name, m in (("Residual, clean-trained", res_clean), ("Residual, noise-trained", res_noisy)):
        for tag, te in (("A noisy", tAn), ("B noisy", tBn)):
            e = errs({"r": m.rollout}, te, HORIZONS, scale)["r"]
            L.append(f"| {name} | {tag} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
    for tag, te in (("A noisy", tAn), ("B noisy", tBn)):
        e = errs(base, te, HORIZONS, scale)["Analytical (M&D)"]
        L.append(f"| Analytical (M&D) | {tag} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
    L.append("")
    PL = plants()
    pl_names = ["A (full)", "B (full, held out)", "nominal + A's thrust loss only"]
    specs = {"LQR": ("lqr", dict(noise=ns, noise_seed=9510)), "MPC analytical": ("mpc", dict(noise=ns, noise_seed=9511)),
             "MPC residual (clean-trained)": ("mpc", dict(residual=res_clean, noise=ns, noise_seed=9512)),
             "MPC residual (noise-trained)": ("mpc", dict(residual=res_noisy, noise=ns, noise_seed=9513)),
             "Offset-free MPC (state d)": ("of", dict(disturbance="state", noise=ns, noise_seed=9514))}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {(n, pl): ex.submit(run_regulation, (s, PL[pl])) for n, s in specs.items() for pl in pl_names}
        reg_n = {k: f.result() for k, f in futs.items()}
    L += ["Closed loop with noisy controller inputs (steady altitude error, E7 Part 1 protocol):", "",
          "| Plant | " + " | ".join(specs) + " |", "|---|" + "---|" * len(specs)]
    for pl in pl_names:
        L.append(f"| {pl} | " + " | ".join(f"{reg_n[(n, pl)]['z_ss']:+.3f} m" if reg_n[(n, pl)]["upright"] else "diverged" for n in specs) + " |")
    L.append("")
    (ROOT / "results/tables/e8f_ablations.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, (tag, te) in zip(axs, (("A", tA), ("B", tB))):
        for k, deg in enumerate((1, 2, 3)):
            e = errs({"r": deg_models[deg].rollout}, te, HORIZONS, scale)["r"]
            ax.plot(hz_ms, e, marker="o", ms=3, color=SERIES[k], label=f"degree {deg}")
        ax.plot(hz_ms, errs(base, te, HORIZONS, scale)["Analytical (M&D)"], color=MUTED, label="analytical")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("horizon (ms)")
        ax.set_title(f"E8f · dictionary degree, test {tag}")
    axs[0].set_ylabel("normalised RMSE")
    axs[0].legend(fontsize=8)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8f_ablations.png")


if __name__ == "__main__":
    main()
