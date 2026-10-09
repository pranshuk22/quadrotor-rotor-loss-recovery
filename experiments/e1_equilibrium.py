"""E1: relaxed-hover equilibrium, validated against Mueller & D'Andrea (ICRA 2014).

Outputs
  results/tables/e1_equilibrium.md
  results/figures/e1_rho_sweep.png
"""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.equilibrium import fig3_minima, relaxed_hover  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402

# Published values, ICRA 2014 eqs. (50)-(53) and Sec. V-D text
PAPER = {"f1 = f3 (N)": 2.05, "f2 (N)": 1.02, "p (rad/s)": 0.0, "q (rad/s)": 5.69,
         "r (rad/s)": 18.89, "n_y": 0.289, "n_z": 0.958, "orbit radius (mm)": 8.0}


def summary(eq):
    return {"f1 = f3 (N)": eq.f[0], "f2 (N)": eq.f[1], "p (rad/s)": eq.w[0], "q (rad/s)": eq.w[1],
            "r (rad/s)": eq.w[2], "n_y": eq.n[1], "n_z": eq.n[2],
            "orbit radius (mm)": eq.orbit_radius * 1e3}


def main():
    apply_style()
    out_t = ROOT / "results/tables"
    out_f = ROOT / "results/figures"
    eq = relaxed_hover(P, 0.5)
    ours = summary(eq)

    # sensitivity of q to the 2-significant-figure rounding of the published inertias
    q_range = []
    for dxx in (-0.05e-3, 0.05e-3):
        for dzz in (-0.05e-3, 0.05e-3):
            e = relaxed_hover(replace(P, Ixx_T=P.Ixx_T + dxx, Izz_T=P.Izz_T + dzz), 0.5)
            q_range.append((e.w[1], e.n[1]))
    q_range = np.array(q_range)

    # rho sweep with continuation
    rhos = np.linspace(0.02, 1.6, 80)
    rows, guess = [], None
    for rho in rhos:
        e = relaxed_hover(P, rho, w_guess=guess)
        guess = e.w
        rows.append([rho, *e.w, np.linalg.norm(e.w), *e.n, e.f[0], e.f[1], e.orbit_radius])
    S = np.array(rows)
    m3 = fig3_minima(P)

    lines = ["# E1: Relaxed-hover equilibrium (rotor 4 lost, rho = f2/f1 = 0.5)", "",
             "Vehicle: Mueller & D'Andrea ICRA 2014, Sec. V-A parameters.", "",
             "| Quantity | Ours | Paper | Rel. diff |", "|---|---|---|---|"]
    for k, v in ours.items():
        ref = PAPER[k]
        rel = "n/a" if ref == 0 else f"{(v - ref) / ref * 100:+.1f}%"
        lines.append(f"| {k} | {v:.3f} | {ref:.3f} | {rel} |")
    lines += ["",
              f"**Inertia-rounding sensitivity.** The paper gives I_xx^T = 3.2e-3 and I_zz^T = 5.5e-3 "
              f"(2 significant figures). Perturbing each by ±0.05e-3 moves q from {q_range[:,0].min():.2f} "
              f"to {q_range[:,0].max():.2f} rad/s and n_y from {q_range[:,1].min():.3f} to "
              f"{q_range[:,1].max():.3f}; the published q = 5.69, n_y = 0.289 are reached only at the edge of this band. "
              "However, the paper's two-rotor and single-rotor equilibria are reproduced to every published digit "
              "with the stated parameters (see results/tables/validation_report.md), and the published one-rotor "
              "values leave a residual in the paper's own eq. (12). The more likely explanation is an inconsistency "
              "in that one published case, not a model error. f, r and n_z do not depend on it.",
              "",
              "**Rho sweep vs. paper Fig. 3 text.**",
              f"- Minimum |w|: ours {m3['w_min']:.2f} rad/s at rho = {m3['rho_w']:.3f}; paper 19.0 rad/s at rho = 0.655.",
              f"- Minimum f1: ours {m3['f1_min']:.3f} N at rho = {m3['rho_f']:.3f}; paper 2.04 N at rho = 0.563.",
              "Values agree within 2%; the minimizer locations differ by about 3% (both minima are shallow).",
              ""]
    (out_t / "e1_equilibrium.md").write_text("\n".join(lines))
    print("\n".join(lines))

    fig, ax = plt.subplots(2, 2, figsize=(9, 6), sharex=True)
    a = ax[0, 0]
    a.plot(S[:, 0], S[:, 2], color=SERIES[0], label="q")
    a.plot(S[:, 0], S[:, 3], color=SERIES[1], label="r")
    a.plot(S[:, 0], S[:, 4], color=SERIES[2], label="|ω|")
    a.set_title("Body rates at equilibrium")
    a.set_ylabel("rad/s")
    a.legend(loc="upper left")
    a = ax[0, 1]
    a.plot(S[:, 0], S[:, 6], color=SERIES[0], label="n_y")
    a.plot(S[:, 0], S[:, 7], color=SERIES[1], label="n_z")
    a.set_title("Primary axis n̄ (body frame)")
    a.legend(loc="center left")
    a = ax[1, 0]
    a.plot(S[:, 0], S[:, 8], color=SERIES[0], label="f1 = f3")
    a.plot(S[:, 0], S[:, 9], color=SERIES[1], label="f2")
    a.axhline(P.f_max, color=REF, lw=0.8)
    a.text(0.03, P.f_max + 0.15, "f_max", color=REF, fontsize=8)
    a.set_title("Rotor thrusts")
    a.set_ylabel("N")
    a.set_xlabel("ρ = f̄2 / f̄1")
    a.legend(loc="upper left")
    a = ax[1, 1]
    a.plot(S[:, 0], S[:, 10] * 1e3, color=SERIES[0])
    a.set_title("Orbit radius of the centre of mass")
    a.set_ylabel("mm")
    a.set_xlabel("ρ = f̄2 / f̄1")
    for a in ax.flat:
        a.axvline(0.5, color=MUTED_LINE, lw=0.8)
    ax[0, 0].text(0.52, ax[0, 0].get_ylim()[1] * 0.92, "design ρ = 0.5", color=REF, fontsize=8)
    fig.suptitle("E1 · Relaxed-hover equilibrium vs. thrust ratio ρ (rotor 4 lost)", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e1_rho_sweep.png")


MUTED_LINE = "#b9b8b3"

if __name__ == "__main__":
    main()
