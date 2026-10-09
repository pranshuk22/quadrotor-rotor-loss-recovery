"""V0: model validation report: our simulator vs published numbers and flight data.

Output: results/tables/validation_report.md
The pass/fail versions of these checks are tests/test_physics.py and tests/test_paper_validation.py.
"""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rotorfail.dynamics import make_state, rk4_step  # noqa: E402
from rotorfail.equilibrium import relaxed_hover, single_rotor_hover, two_rotor_hover  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import G, QuadParams  # noqa: E402
from rotorfail.validation import IJRR_CASES, GeneralMulticopter, ijrr_speeds  # noqa: E402


def row(name, ours, paper, unit=""):
    if paper == 0:
        d = f"{ours - paper:+.3f} (abs)"
    else:
        d = f"{(ours - paper) / abs(paper) * 100:+.2f}%"
    return f"| {name} | {ours:.3f} | {paper:.3f} | {d} | {unit} |"


def vec(v):
    return "(" + ", ".join(f"{x:.2f}" for x in v) + ")"


def main():
    L = ["# Model validation report", "",
         "Simulator: `rotorfail/` (Mueller & D'Andrea ICRA 2014 model). Independent implementation of the "
         "IJRR 2016 general model: `rotorfail/validation.py`. Pass/fail tests: `tests/test_physics.py` (analytic "
         "solutions, conservation laws) and `tests/test_paper_validation.py` (published numbers).", ""]

    # ---------------- ICRA 2014
    L += ["## 1. Mueller & D'Andrea, ICRA 2014 (same vehicle and model as our simulator)", "",
          "| Quantity | Ours | Published | Difference | Unit |", "|---|---|---|---|---|"]
    eq = relaxed_hover(P, 0.5)
    L += ["| **One rotor lost, ρ = 0.5** (eqs. 50–53) | | | | |",
          row("f1 = f3", eq.f[0], 2.05, "N"), row("f2", eq.f[1], 1.02, "N"),
          row("p", eq.w[0], 0.0, "rad/s"), row("q", eq.w[1], 5.69, "rad/s"), row("r", eq.w[2], 18.89, "rad/s"),
          row("n_y", eq.n[1], 0.289), row("n_z", eq.n[2], 0.958), row("orbit radius", eq.orbit_radius * 1e3, 8.0, "mm")]
    s2 = two_rotor_hover(P)
    L += ["| **Two opposing rotors lost** (eqs. 57–59) | | | | |",
          row("f1 = f3", s2.f[0], 2.45, "N"), row("propeller speed ω1", s2.prop_speeds[0], -619, "rad/s"),
          row("r", s2.w[2], 30.1, "rad/s")]
    s1 = single_rotor_hover(P)
    L += ["| **Three rotors lost** (eqs. 62–64) | | | | |",
          row("f1", s1.f[0], 5.37, "N"), row("propeller speed ω1", s1.prop_speeds[0], -915, "rad/s"),
          row("p", s1.w[0], 14.7, "rad/s"), row("q", s1.w[1], 0.0, "rad/s"), row("r", s1.w[2], 33.0, "rad/s"),
          row("n_x", s1.n[0], 0.41), row("n_z", s1.n[2], 0.91)]
    rhos = np.linspace(0.3, 1.0, 141)
    sols = [relaxed_hover(P, r) for r in rhos]
    wn = np.array([np.linalg.norm(s.w) for s in sols])
    f1 = np.array([s.f[0] for s in sols])
    L += ["| **Fig. 3 minima** | | | | |",
          row("min |ω|", wn.min(), 19.0, "rad/s"), row("ρ at min |ω|", rhos[wn.argmin()], 0.655),
          row("min f1", f1.min(), 2.04, "N"), row("ρ at min f1", rhos[f1.argmin()], 0.563)]
    # residual of the paper's own eq. (12) at its published equilibrium
    om = P.prop_speeds(np.array([2.05, 1.02, 2.05, 0.0]))
    res12 = (P.kappa_f * om[1] ** 2 * P.l - (P.Izz_T - P.Ixx_T) * 5.69 * 18.89 - P.Izz_P * 5.69 * om.sum())
    L += ["",
          "**Reading.** The two-rotor and single-rotor equilibria are reproduced to every published digit, "
          "including the single-rotor case, which exercises the gyroscopic and propeller-momentum terms with p ≠ 0. "
          "In the one-rotor case, f, r and n_z match, but q and n_y are 6% lower. Substituting the paper's own "
          f"published values into its eq. (12) leaves a roll-torque residual of {res12:+.4f} N·m "
          f"({abs(res12) / (P.l * 1.02) * 100:.0f}% of the rotor-2 torque), so that published case is not an exact "
          "equilibrium of the paper's own model with the stated parameters. We treat it as an inconsistency in that "
          "single published case, not a model error.",
          "", "Also checked analytically (tests): eq. (21) for r̄; eq. (28) for the coupling constant ā equals our "
          "Jacobian entry; eqs. (37)–(39): our controllability rank drops from 7 to 6, with the roll rate p "
          "uncontrollable, exactly when ā = 0.", ""]

    # ---------------- IJRR 2016
    L += ["## 2. Mueller & D'Andrea, IJRR 2016 (same vehicle, more detailed aerodynamics)", "",
          "The IJRR model differs from ICRA 2014 in two ways: propeller thrust uses the speed relative to the "
          "**air** (Ω + r), and the drag torque is **quadratic** in ω on all axes. Our independent implementation "
          "(`rotorfail/validation.py`) solves the rotational equilibrium for the published propeller speeds.", "",
          "| Failure case | Published Ω (rad/s) | Published ω | Ours, published parameters | Ours, I_xx = 2.75e-3 | Vertical force ratio |",
          "|---|---|---|---|---|---|"]
    M0 = GeneralMulticopter()
    M1 = replace(M0, I_B=(2.75e-3, 2.75e-3, 5.2e-3))
    for name, c in IJRR_CASES.items():
        Om = ijrr_speeds(c["Omega"])
        g = np.array(c["w"]) + np.array([1.0, -1.0, 3.0])
        w0, w1 = M0.hover_rates(Om, g), M1.hover_rates(Om, g)
        L.append(f"| {name} | {c['Omega']} | {vec(c['w'])} | {vec(w0)} | {vec(w1)} | {M1.vertical_force_ratio(Om, w1):.3f} |")
    L += ["", "**Reading.** With the published parameters, the hover solutions are within 0–4%. The two high-rate cases "
          "are the most sensitive to the drag and inertia values, which are published to 1–2 significant figures. "
          "One value inside the rounding of the published I_xx = 2.7e-3 (2.75e-3) brings all five cases within 0.7% "
          "in ω and 0.6% in force balance. The two-rotor speed 643 rad/s is explained only by air-relative thrust: "
          "κ_f(643 − 24.5)² = mg/2, while κ_f·643² is 8% too high.", "",
          "**Consequence for our simulator.** The ICRA model we simulate omits air-relative thrust. At the one-rotor "
          "equilibrium (r ≈ 19 rad/s; propeller speeds −565, +399, −565 rad/s) it changes the thrust of rotors 1 and 3 "
          "by about −7% and of rotor 2 by about +10%. That is comparable in size to the uniform thrust loss in our "
          "truth families (`params.truth_family`), but different in structure, because it acts per rotor. Adding "
          "air-relative thrust to the truth plant is a cheap and valuable next step (task K11).", ""]

    # ---------------- Sun et al. 2020
    p = QuadParams(m=0.410, l=0.145, Ixx_T=1.45e-3, Izz_T=2.52e-3, Izz_P=8.0e-6, kappa_f=1.90e-6,
                   kappa_tau=0.01, gamma=1.50e-3, f_min=0.0, f_max=10.0)
    sb = two_rotor_hover(p)
    L += ["## 3. Sun, Wang, Chu & de Visser, T-RO 2020: a second airframe (Parrot Bebop 2)", "",
          "| Quantity | Ours | Eq. (60) with Table III | Published text | Unit |", "|---|---|---|---|---|",
          f"| r̄ (two opposing rotors lost) | {sb.w[2]:.2f} | {p.m * G * p.kappa_tau / p.gamma:.2f} | 26.4 | rad/s |",
          f"| propeller speed ω̄ | {abs(sb.prop_speeds[0]):.0f} | {np.sqrt(p.m * G / (2 * p.kappa_f)):.0f} | 1015 | rad/s |",
          "", "**Reading.** Our solver equals the paper's own closed form exactly. The paper's quoted numbers are about "
          "1.5% below its own formula evaluated with its Table III, which is internal to the paper.", ""]

    # ---------------- flight data
    x = make_state()
    u = np.array([P.weight / 2, 0.0, P.weight / 2, 0.0])
    alive = np.array([True, True, True, False])
    t, dt = 0.0, 1e-3
    while np.linalg.norm(x[10:13]) < 10.0:
        x = rk4_step(x, u, dt, P, alive)
        t += dt
    t_exact = -P.Izz_B / P.gamma * np.log(1 - 10.0 / (P.kappa_tau * P.weight / P.gamma))
    L += ["## 4. Against flight data (where the model is known to be imperfect)", "",
          "| Quantity | Our model | The paper's model | Flight | Source |", "|---|---|---|---|---|",
          f"| Time to |ω| > 10 rad/s on two rotors after propeller 4 is disabled | {t:.2f} s (closed form {t_exact:.2f} s) | not reported | 0.62 s | ICRA 2014, Fig. 4 |",
          f"| Spin rate about n, one rotor lost | {np.linalg.norm(eq.w):.1f} rad/s (ρ = 0.5) | 19.9 rad/s (min-power solution) | 15.8 rad/s | IJRR 2016, Sec. 5.3 |",
          "| Height offset, two rotors, from thrust loss while spinning | not in the nominal model | not in the model | ≈ 2.4 m | ICRA 2014, Sec. V-E |",
          "", "**Reading.** The nominal model spins up about 30% slower than the flight and over-predicts the spin rate by "
          "about 20% (both papers attribute the gaps to unmodelled aerodynamics). These are the reasons the project "
          "(i) keeps a model-mismatch truth plant for RQ1 and (ii) must report the RQ2 delay results with a sensitivity "
          "study on the yaw-drag and thrust parameters (task D7). The empirical delay tolerance in E4 depends on "
          "spin-up speed.", ""]

    (ROOT / "results/tables/validation_report.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
