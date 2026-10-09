"""E2: structural analysis of the healthy and failed linear models.

Open-loop eigenvalues, controllability (Krylov rank, PBH, Gramian) and
observability for several sensor sets, with the unobservable directions.

Output: results/tables/e2_structure.md
"""
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import null_space

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rotorfail.analysis import (ctrb, gramian_summary, obsv, pbh_controllability,  # noqa: E402
                                pbh_observability, scaled_rank)
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.models import failed_linear, healthy_linear  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402


def C_rows(states, names):
    C = np.zeros((len(names), len(states)))
    for i, s in enumerate(names):
        C[i, states.index(s)] = 1.0
    return C


HEALTHY_SENSORS = {
    "S1 gyro (p,q,r)": ["p", "q", "r"],
    "S2 gyro + position": ["p", "q", "r", "x", "y", "z"],
    "S3 gyro + position + magnetometer (psi)": ["p", "q", "r", "x", "y", "z", "psi"],
    "S4 gyro + attitude (phi,theta,psi)": ["p", "q", "r", "phi", "theta", "psi"],
}
FAILED_SENSORS = {
    "F1 gyro (p,q,r)": ["p", "q", "r"],
    "F2 gyro + tilt estimate (n_x,n_y)": ["p", "q", "r", "n_x", "n_y"],
    "F3 gyro + altitude (baro)": ["p", "q", "r", "z"],
    "F4 gyro + tilt + altitude": ["p", "q", "r", "n_x", "n_y", "z"],
}


def fmt_eigs(ev):
    ev = sorted(ev, key=lambda z: (round(z.real, 6), round(abs(z.imag), 6)))
    out = []
    for z in ev:
        if abs(z.imag) < 1e-9:
            out.append(f"{z.real:.3f}")
        elif z.imag > 0:
            out.append(f"{z.real:.3f} ± {z.imag:.3f}j")
    return ", ".join(out)


def unobservable_states(A, C, states):
    O = obsv(A, C)
    norms = np.linalg.norm(O, axis=0)
    norms[norms == 0] = 1
    N = null_space(O / norms, rcond=1e-9)
    if N.shape[1] == 0:
        return "none"
    weight = np.sum(N ** 2, axis=1)
    return ", ".join(s for s, w in zip(states, weight) if w > 1e-6)


def section(title, model, sensors, T_gram):
    A, B = model.A, model.B
    n = A.shape[0]
    L = [f"## {title}", "",
         f"States ({n}): {', '.join(model.states)}; inputs: {', '.join(model.inputs)}", "",
         f"**Open-loop eigenvalues:** {fmt_eigs(np.linalg.eigvals(A))}", "",
         f"**Controllability:** rank [B AB ... A^{n-1}B] = {scaled_rank(ctrb(A, B))} / {n} "
         "(columns normalized before the SVD).", ""]
    L += ["PBH test, min singular value of [λI − A, B̃] per mode (scaled; > 0 means controllable):", "",
          "| Mode λ | σ_min | Controllable |", "|---|---|---|"]
    seen = set()
    for lam, smin, ok in pbh_controllability(A, B):
        key = (round(lam.real, 4), round(abs(lam.imag), 4))
        if key in seen:
            continue
        seen.add(key)
        lam_s = f"{lam.real:.3f}" if abs(lam.imag) < 1e-9 else f"{lam.real:.3f} ± {abs(lam.imag):.3f}j"
        L.append(f"| {lam_s} | {smin:.2e} | {'yes' if ok else 'NO'} |")
    g = gramian_summary(A, B, T_gram)
    L += ["", f"Controllability Gramian W({T_gram} s): λ_min = {g['lambda_min']:.2e}, "
          f"λ_max = {g['lambda_max']:.2e}, condition number = {g['cond']:.2e}.", ""]
    L += ["**Observability by sensor set:**", "",
          "| Sensor set | rank O | Unobservable states | λ_min W_o(1 s) | cond W_o |",
          "|---|---|---|---|---|"]
    for name, rows in sensors.items():
        C = C_rows(model.states, rows)
        r = scaled_rank(obsv(A, C))
        go = gramian_summary(A.T, C.T, T_gram)
        lam = f"{go['lambda_min']:.1e}" if r == n else "0 (unobs.)"
        cond = f"{go['cond']:.1e}" if r == n else "∞"
        L.append(f"| {name} | {r} / {n} | {unobservable_states(A, C, model.states)} | {lam} | {cond} |")
    L.append("")
    return L


def main():
    eq = relaxed_hover(P)
    h = healthy_linear(P)
    f = failed_linear(P, eq)
    L = ["# E2: Structural analysis", "",
         "Models are numerical Jacobians of the exact nonlinear equations (see `rotorfail/models.py`).", ""]
    L += section("Healthy quadrotor at hover", h, HEALTHY_SENSORS, 1.0)
    L += section("Failed quadrotor (rotor 4 lost) at the relaxed hover, ρ = 0.5", f, FAILED_SENSORS, 1.0)
    L += ["## Notes", "",
          "- Healthy model: the classic result. Gyro + position leaves yaw ψ unobservable at hover "
          "(heading enters the translational dynamics only at second order), so a heading sensor is needed.",
          "- Failed model: the rate dynamics do not depend on n, so gyro-only leaves the reduced attitude "
          "and the altitude unobservable.",
          "- Failed model, F3: because the relaxed hover is *tilted* (n̄_y ≠ 0), vertical acceleration depends "
          "on tilt to first order (∂v̇_z/∂n_y ≠ 0). This coupling does not exist at a level hover, and it makes "
          "the full reduced attitude observable from gyro + barometer alone (F3). The Gramian columns show how "
          "weak this observability is compared with a direct tilt measurement (F4): it is a structural "
          "property, not a practical estimator design. It is a candidate for the observability part of the "
          "project (to be checked against the estimation literature).",
          "- Controllability of the reduced attitude from three rotors reproduces Mueller & D'Andrea "
          "(not a contribution).", ""]
    out = ROOT / "results/tables/e2_structure.md"
    out.write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
