"""E8c (K7): online residual adaptation by recursive least squares.

Question. The offline residual (trained on family A) loses to plain LQR on one plant of E7 (held-out family B without its
thrust loss, +47 % altitude bias). Does adapting its weights online by RLS repair that, on prediction and in closed loop?

Fixed before running (do not tune afterwards)
  - Offline residual: exactly the E6/E7 one (40 family-A episodes of 4 s, seed 11, ridge 1e-3, 91-function dictionary,
    clip at the 99.5 % percentile of the training residuals).
  - RLS on the 91 x 7 weight matrix, one shared 91 x 91 covariance, initialised at W_offline and P0 = p0 I with
    p0 = 1.0; forgetting factor lambda = 0.995 (main, memory about 1 s at 5 ms) and 0.999 (sensitivity); clip scale 1
    (main) and 2 (sensitivity, lambda = 0.995); covariance wind-up guard: rescale P when trace(P) > 10 trace(P0).
  - Causality (`AdaptiveResidual`): at call k the update uses (features at k-1, e_k = x_k - nominal prediction from k-1);
    only then the residual for step k is evaluated.
  - (a) Multi-step prediction: the E6 protocol (horizons 5 ms to 3 s, starts every 40 steps, errors normalised by the
    training standard deviations) on 10 held-out episodes of family B (seed 13) and 10 of family A (seed 12), the adaptive
    models adapting causally along each episode and predicting from each start with the then-current weights.
  - (b) Closed loop, E7 Part 1 on the six plants: LQR, MPC analytical, MPC offline residual, MPC adaptive (0.995),
    MPC adaptive (0.999), MPC adaptive (0.995, clip x2).
  - (c) Adaptive residual + offset-free MPC (state disturbance model, the E8a baseline): offset-free alone, with the
    offline residual, with the adaptive residual (0.995); six plants.
  - (d) Capture after delay (E7 Part 2 protocol, family A and nominal, tau in {0, 10, 20, 30, 40, 60} ms): LQR, MPC offline
    residual, MPC adaptive (0.995), judged against each controller's own steady state.
  - Reported: clip activity, maximum trace(P), number of covariance rescalings and positive-definiteness violations,
    solver times; trace(P) over time (figure). Adaptation runs inside closed loop: closed-loop identification bias is a
    limitation and is not corrected.

Outputs: results/tables/e8c_adaptive_residual.md, results/figures/e8c_adaptive.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import copy
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

from e7_mpc_closed_loop import plants  # noqa: E402
from rq1_common import closed_loop_reference, run_delay, run_regulation  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import (TS, AdaptiveResidual, NominalModel, ResidualEDMD, generate,  # noqa: E402
                               nominal_rollout)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402

HORIZONS = np.array([1, 4, 10, 20, 40, 100, 200, 400, 600])
TAUS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]
P0 = 1.0


def adaptive(res, lam, clip=1.0):
    return AdaptiveResidual(res, p0=P0, lam=lam, clip_scale=clip)


def prediction_errors(res, nom, test, scale, variants):
    """Normalised RMSE vs horizon, adaptation running causally along each test episode."""
    H = int(max(HORIZONS))
    acc = {k: [] for k in ["Analytical (M&D)", "Offline residual"] + list(variants)}
    for X, fe, U in zip(test.x, test.fe, test.u):
        ads = {k: adaptive(res, *v) for k, v in variants.items()}
        for k in range(len(U)):
            for a in ads.values():
                if k >= 1:
                    a.residual(X[k], fe[k], U[k - 1])          # causal update with (k-1 features, e_k)
            if k % 40 == 0 and k <= len(U) - H:
                tgt = X[k:k + H + 1]
                rolls = {"Analytical (M&D)": nominal_rollout(nom, X[k], fe[k], U[k:k + H]),
                         "Offline residual": res.rollout(X[k], fe[k], U[k:k + H])}
                for name, a in ads.items():
                    rolls[name] = a.rollout(X[k], fe[k], U[k:k + H])
                for name, pred in rolls.items():
                    acc[name].append(((pred - tgt) / scale)[HORIZONS])
    out = {}
    for name, E in acc.items():
        E = np.array(E)
        with np.errstate(over="ignore", invalid="ignore"):
            out[name] = np.sqrt(np.nanmean(np.minimum(E ** 2, 1e12), axis=(0, 2)))
    return out


def main():
    apply_style()
    eq = relaxed_hover(P)
    train = generate(truth_family("A"), P, eq, 40, 4.0, seed=11)
    nom = NominalModel.build(P, eq)
    res = ResidualEDMD.fit(train, nom, P)
    scale = np.std(np.vstack(train.x), axis=0)
    test_A = generate(truth_family("A"), P, eq, 10, 4.0, seed=12)
    test_B = generate(truth_family("B"), P, eq, 10, 4.0, seed=13)
    variants = {"Adaptive (0.995)": (0.995, 1.0), "Adaptive (0.999)": (0.999, 1.0), "Adaptive (0.995, clip x2)": (0.995, 2.0)}
    EA = prediction_errors(res, nom, test_A, scale, variants)
    EB = prediction_errors(res, nom, test_B, scale, variants)
    hz = HORIZONS * TS * 1e3
    L = ["# E8c: Online residual adaptation by recursive least squares", "",
         "RLS on the 91 x 7 weights of the offline residual (trained on family A as in E6), shared covariance, P0 = I, "
         "forgetting 0.995 (main) or 0.999, covariance rescaled when trace(P) > 10 trace(P0). Settings fixed in the docstring of "
         "`experiments/e8c_adaptive_residual.py`.", "",
         "## (a) Multi-step prediction error (normalised RMSE, mean over the 7 states), adaptation running along each episode", ""]
    for tag, E in (("family A (training family)", EA), ("family B (held out)", EB)):
        L += [f"### Test episodes of {tag}", "", "| Model | " + " | ".join(f"{h:.0f} ms" for h in hz) + " |", "|---|" + "---|" * len(hz)]
        for name, e in E.items():
            L.append(f"| {name} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
        L.append("")

    # (b) closed loop six plants
    PL = plants()
    names = list(PL)
    specs_b = {"LQR": ("lqr", {}), "MPC, analytical": ("mpc", {}), "MPC, offline residual": ("mpc", dict(residual=res)),
               "MPC, adaptive (0.995)": ("mpc", dict(residual=adaptive(res, 0.995))),
               "MPC, adaptive (0.999)": ("mpc", dict(residual=adaptive(res, 0.999))),
               "MPC, adaptive (0.995, clip x2)": ("mpc", dict(residual=adaptive(res, 0.995, 2.0)))}
    specs_c = {"Offset-free (state d)": ("of", dict(disturbance="state")),
               "Offset-free + offline residual": ("of", dict(residual=res, disturbance="state")),
               "Offset-free + adaptive (0.995)": ("of", dict(residual=adaptive(res, 0.995), disturbance="state"))}
    allspec = {**specs_b, **specs_c}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {(n, pl): ex.submit(run_regulation, (allspec[n], PL[pl])) for n in allspec for pl in names}
        reg = {k: f.result() for k, f in futs.items()}
    L += ["## (b) Closed loop, steady altitude bias (E7 Part 1 protocol, mean altitude over the last 2 s)", "",
          "| Plant | " + " | ".join(specs_b) + " |", "|---|" + "---|" * len(specs_b)]
    for pl in names:
        L.append(f"| {pl} | " + " | ".join(f"{reg[(n, pl)]['z_ss']:+.3f} m" for n in specs_b) + " |")
    L += ["", "Adaptation statistics (run on plant A full / B without thrust loss): fraction of calls with an active clip, maximum trace(P), "
          "rescalings, positive-definiteness violations.", "", "| Controller | plant | clip active | max trace(P) | rescalings | PD violations | median CVXPY ms |", "|---|---|---|---|---|---|---|"]
    for n in ("MPC, adaptive (0.995)", "MPC, adaptive (0.999)", "MPC, adaptive (0.995, clip x2)"):
        for pl in ("A (full)", "B without thrust loss"):
            r = reg[(n, pl)]
            L.append(f"| {n} | {pl} | {r['clip_frac']:.3f} | {r['trace_max']:.1f} | {r['n_resc']} | {r['eig_viol']} | {r['wall_ms']:.1f} |")
    L += ["", "## (c) Adaptive residual combined with offset-free MPC (state disturbance model)", "",
          "| Plant | " + " | ".join(specs_c) + " |", "|---|" + "---|" * len(specs_c)]
    for pl in names:
        L.append(f"| {pl} | " + " | ".join(f"{reg[(n, pl)]['z_ss']:+.3f} m" for n in specs_c) + " |")

    # (d) capture after delay
    specs_d = {"LQR": ("lqr", {}), "MPC, offline residual": ("mpc", dict(residual=res)),
               "MPC, adaptive (0.995)": ("mpc", dict(residual=adaptive(res, 0.995)))}
    plants_d = {"A (full)": truth_family("A"), "nominal": P}
    with ProcessPoolExecutor(max_workers=8) as ex:
        refs = {(n, pl): ex.submit(closed_loop_reference, (specs_d[n], plants_d[pl])) for n in specs_d for pl in plants_d}
        refs = {k: f.result() for k, f in refs.items()}
        futs = {(n, pl, t): ex.submit(run_delay, (specs_d[n], plants_d[pl], t, refs[(n, pl)], None))
                for n in specs_d for pl in plants_d for t in TAUS}
        dl = {k: f.result() for k, f in futs.items()}
    L += ["", "## (d) Capture after a detection delay (exact hover start, spin-up 2.95 N)", "",
          "Alt. loss (m) / min n_z / SAFE; each controller judged against its own steady state on the plant.", ""]
    for pl in plants_d:
        L += [f"### Plant: {pl}", "", "| tau (ms) | " + " | ".join(specs_d) + " |", "|---|" + "---|" * len(specs_d)]
        for t in TAUS:
            cells = []
            for n in specs_d:
                r = dl[(n, pl, t)]
                cells.append(f"{r['alt_loss']:.2f} / {r['min_nz']:.2f} / {'yes' if r['safe'] else 'no'}")
            L.append(f"| {t * 1e3:.0f} | " + " | ".join(cells) + " |")
        L.append("")
    (ROOT / "results/tables/e8c_adaptive_residual.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    for pl, col in (("A (full)", SERIES[0]), ("B without thrust loss", SERIES[1])):
        tr = reg[("MPC, adaptive (0.995)", pl)]["trace"]
        axs[0].plot(np.arange(len(tr)) * TS, tr, color=col, label=pl)
    axs[0].set_xlabel("time (s)")
    axs[0].set_ylabel("trace(P)")
    axs[0].set_title("E8c · covariance trace, adaptive (0.995)")
    axs[0].legend()
    for n, col in zip(("MPC, offline residual", "MPC, adaptive (0.995)"), (SERIES[1], SERIES[0])):
        axs[1].plot(range(len(names)), [reg[(n, pl)]["z_ss"] for pl in names], marker="o", color=col, label=n)
    axs[1].plot(range(len(names)), [reg[("LQR", pl)]["z_ss"] for pl in names], marker="s", color=REF, label="LQR")
    axs[1].set_xticks(range(len(names)))
    axs[1].set_xticklabels([n.replace(" ", "\n", 1) for n in names], fontsize=6)
    axs[1].set_ylabel("steady altitude error (m)")
    axs[1].set_title("E8c · steady altitude error by plant")
    axs[1].legend(fontsize=7)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8c_adaptive.png")


if __name__ == "__main__":
    main()
