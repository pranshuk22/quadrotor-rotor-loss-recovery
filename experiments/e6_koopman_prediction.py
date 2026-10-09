"""E6 (RQ1): failed-regime predictors: analytical M&D model, full-state EDMDc, residual EDMDc.

Truth plant: family A (thrust loss at high body rate, inertia error, slower motors);
held-out family B for generalization. Nominal model: M&D LTI model on nominal parameters.
Data: closed-loop failure-LQR episodes with random command excitation, TS = 5 ms.

Tests H1 (full-state EDMDc spectral radius > 1), H2 (residual best multi-step error),
H4 (data efficiency) and generalization to family B.

Outputs: results/tables/e6_koopman_prediction.md, results/figures/e6_multistep_error.png,
         results/figures/e6_data_efficiency.png, results/figures/e6_full_edmdc_eigs.png
"""
import os

# One BLAS/OpenMP thread per process: the experiments parallelize over runs instead.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import (TS, Dataset, FullEDMDc, NominalModel, ResidualEDMD, generate,  # noqa: E402
                               multistep_errors, nominal_rollout)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import random_family, truth_family  # noqa: E402
from rotorfail.plotting import MUTED, REF, SERIES, apply_style, save  # noqa: E402

EP_LEN = 4.0
HORIZONS = np.array([1, 4, 10, 20, 40, 100, 200, 400, 600])   # steps of 5 ms -> 5 ms ... 3 s


def subset(d: Dataset, n):
    return Dataset(d.x[:n], d.fe[:n], d.u[:n])


def evaluate(models, test, scale):
    rolls = {"Analytical (M&D)": lambda x, f, U: nominal_rollout(models["nom"], x, f, U),
             "Full-state EDMDc": models["full"].rollout,
             "Residual EDMDc (proposed)": models["res"].rollout,
             "No-change baseline": lambda x, f, U: np.repeat(x[None], len(U) + 1, 0)}
    return multistep_errors(rolls, test, HORIZONS, scale, starts_every=40)


def main():
    apply_style()
    eq = relaxed_hover(P)
    PA, PB = truth_family("A"), truth_family("B")
    train = generate(PA, P, eq, 40, EP_LEN, seed=11)
    test_A = generate(PA, P, eq, 10, EP_LEN, seed=12)
    test_B = generate(PB, P, eq, 10, EP_LEN, seed=13)
    nom = NominalModel.build(P, eq)
    scale = np.std(np.vstack(train.x), axis=0)

    full = FullEDMDc.fit(train)
    res = ResidualEDMD.fit(train, nom, P)
    ev = full.eigs()
    n_unstable = int(np.sum(np.abs(ev) > 1 + 1e-9))
    models = {"nom": nom, "full": full, "res": res}
    EA = evaluate(models, test_A, scale)
    EB = evaluate(models, test_B, scale)

    # domain-randomized training (one random truth plant per episode); B stays outside the ranges
    train_R = generate(random_family, P, eq, 40, EP_LEN, seed=21)
    full_R, res_R = FullEDMDc.fit(train_R), ResidualEDMD.fit(train_R, nom, P)
    ev_R = full_R.eigs()
    models_R = {"nom": nom, "full": full_R, "res": res_R}
    EA_R = evaluate(models_R, test_A, scale)
    EB_R = evaluate(models_R, test_B, scale)

    hz_ms = HORIZONS * TS * 1e3
    L = ["# E6 (RQ1): Koopman predictors in the failed regime", "",
         f"Training: {len(train.x)} episodes × {EP_LEN:.0f} s on truth family A "
         f"({sum(len(u) for u in train.u)} samples at {TS*1e3:.0f} ms). Test: 10 held-out episodes "
         "of family A and 10 of family B (unseen mismatch magnitudes).", "",
         "Dictionary: constant + 9 standardized states/filtered inputs + all degree-2 monomials "
         f"(lifted dimension {full.A.shape[0]}). Ridge regression.", "",
         "## H1: spectrum of the full-state EDMDc operator", "",
         f"Trained on family A: {n_unstable} of {len(ev)} eigenvalues have |λ| > 1; spectral radius "
         f"{np.max(np.abs(ev)):.4f}. Trained on randomized families: "
         f"{int(np.sum(np.abs(ev_R) > 1 + 1e-9))} of {len(ev_R)}; spectral radius {np.max(np.abs(ev_R)):.4f}.", "",
         "## Multi-step open-loop prediction error (normalized RMSE, mean over the 7 states)", ""]
    for title, (Ea, Eb) in (("Models trained on family A only", (EA, EB)),
                            ("Models trained on domain-randomized families (B outside the ranges)", (EA_R, EB_R))):
        L += [f"### {title}", "", "| Model, test set | " + " | ".join(f"{h:.0f} ms" for h in hz_ms) + " |",
              "|---|" + "---|" * len(hz_ms)]
        for tag, E in (("A", Ea), ("B (held out)", Eb)):
            for name, e in E.items():
                L.append(f"| {name}, family {tag} | " + " | ".join(f"{v:.3f}" for v in e) + " |")
        L.append("")

    # per-state error at 0.5 s, family A
    from rotorfail.koopman import MEAS
    idx = int(np.where(HORIZONS == 100)[0][0])
    L += ["Normalization: each state divided by its standard deviation in the training data.", ""]

    # data efficiency
    sizes = [2, 5, 10, 20, 40]
    eff = {"Full-state EDMDc": [], "Residual EDMDc (proposed)": []}
    for n in sizes:
        sub = subset(train, n)
        m = {"nom": nom, "full": FullEDMDc.fit(sub), "res": ResidualEDMD.fit(sub, nom, P)}
        E = evaluate(m, test_A, scale)
        for k in eff:
            eff[k].append(E[k][idx])
    L += ["## H4: data efficiency (error at 0.5 s horizon, family A test)", "",
          "| Training episodes | " + " | ".join(str(s) for s in sizes) + " |", "|---|" + "---|" * len(sizes)]
    for k, v in eff.items():
        L.append(f"| {k} | " + " | ".join(f"{x:.3f}" for x in v) + " |")
    L.append(f"| Analytical (M&D), no data | " + " | ".join(f"{EA['Analytical (M&D)'][idx]:.3f}" for _ in sizes) + " |")
    L.append("")
    (ROOT / "results/tables/e6_koopman_prediction.md").write_text("\n".join(L))
    print("\n".join(L))

    # figures
    colors = {"Analytical (M&D)": SERIES[1], "Full-state EDMDc": SERIES[2],
              "Residual EDMDc (proposed)": SERIES[0], "No-change baseline": MUTED}
    fig, axs = plt.subplots(2, 2, figsize=(11, 7), sharey=True, sharex=True)
    panels = [(axs[0, 0], "trained on A · test A", EA), (axs[0, 1], "trained on A · test B (held out)", EB),
              (axs[1, 0], "randomized training · test A", EA_R), (axs[1, 1], "randomized training · test B (held out)", EB_R)]
    ax = axs[:, 0]
    for a, tag, E in panels:
        for name, e in E.items():
            a.plot(hz_ms, e, marker="o", ms=3.5, color=colors[name], label=name,
                   lw=1.2 if name == "No-change baseline" else 1.8)
        a.set_xscale("log")
        a.set_yscale("log")
        a.set_title(tag)
    for a in axs[1]:
        a.set_xlabel("prediction horizon (ms)")
    for a in axs[:, 0]:
        a.set_ylabel("normalized RMSE")
    axs[0, 0].legend(loc="upper left", fontsize=8)
    fig.suptitle("E6 · Open-loop multi-step prediction, failed quadrotor (rotor 4 lost)", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e6_multistep_error.png")

    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    for k, v in eff.items():
        ax.plot(sizes, v, marker="o", color=colors[k], label=k)
    ax.axhline(EA["Analytical (M&D)"][idx], color=colors["Analytical (M&D)"], lw=1.2, label="Analytical (M&D), no data")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("training episodes (4 s each)")
    ax.set_ylabel("normalized RMSE at 0.5 s")
    ax.set_title("E6 · Data efficiency")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e6_data_efficiency.png")

    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), color=REF, lw=0.8)
    inside = np.abs(ev) <= 1 + 1e-9
    ax.scatter(ev[inside].real, ev[inside].imag, s=14, color=SERIES[0], label="|λ| ≤ 1")
    ax.scatter(ev[~inside].real, ev[~inside].imag, s=22, color=SERIES[1], marker="x", label="|λ| > 1")
    ax.set_aspect("equal")
    ax.set_title(f"E6 · Full-state EDMDc eigenvalues\n({n_unstable} of {len(ev)} outside the unit circle)")
    ax.set_xlabel("Re λ")
    ax.set_ylabel("Im λ")
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e6_full_edmdc_eigs.png")


if __name__ == "__main__":
    main()
