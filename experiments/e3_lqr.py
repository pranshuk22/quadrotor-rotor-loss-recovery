"""E3: LQR designs for the healthy and failed vehicle, and nonlinear verification.

Outputs
  results/tables/e3_lqr.md
  results/figures/e3_failed_lqr_nonlinear.png
  results/figures/e3_healthy_lqr_nonlinear.png
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.analysis import delay_margin  # noqa: E402
from rotorfail.control import FailureLQR, HealthyLQR  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731


def quat_from_n(n):
    """Attitude quaternion whose body-frame 'up' vector R^T e3 equals n (zero 'yaw')."""
    n = np.asarray(n, float) / np.linalg.norm(n)
    e3 = np.array([0.0, 0.0, 1.0])
    v = np.cross(n, e3)
    s, c = np.linalg.norm(v), n @ e3
    if s < 1e-12:
        return np.array([1.0, 0, 0, 0])
    ax, ang = v / s, np.arctan2(s, c)
    return np.concatenate(([np.cos(ang / 2)], np.sin(ang / 2) * ax))


def failed_state(eq, dw=(0, 0, 0), dn=(0, 0, 0), z=0.0):
    x = make_state(d=(0, 0, z), w=eq.w + np.asarray(dw), f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n + np.asarray(dn))
    return x


def poles_text(Acl, k=6):
    ev = np.linalg.eigvals(Acl)
    ev = ev[np.argsort(-ev.real)]
    out, seen = [], set()
    for z in ev:
        key = (round(z.real, 3), round(abs(z.imag), 3))
        if key in seen:
            continue
        seen.add(key)
        out.append(f"{z.real:.2f}" if abs(z.imag) < 1e-6 else f"{z.real:.2f} ± {abs(z.imag):.2f}j")
        if len(out) == k:
            break
    return ", ".join(out)


def main():
    apply_style()
    eq = relaxed_hover(P)
    h = HealthyLQR(P)
    f = FailureLQR(P, eq)
    f_nolag = FailureLQR(P, eq, motor_states=False)

    Ah = h.model.A - h.model.B @ h.K
    Af = f.model.A - f.model.B @ f.K
    Af0 = f_nolag.model.A - f_nolag.model.B @ f_nolag.K
    dm_h = delay_margin(h.model.A, h.model.B, h.K, dt=1e-3, max_delay=0.3)
    dm_f = delay_margin(f.model.A, f.model.B, f.K, dt=1e-3, max_delay=0.3)
    dm_f0 = delay_margin(f_nolag.model.A, f_nolag.model.B, f_nolag.K, dt=1e-3, max_delay=0.3)

    # does the design that ignores motor lag survive the real 15 ms lag?
    from rotorfail.models import add_motor_lag
    lagged = add_motor_lag(f_nolag.model, P.sigma_mot)
    K_ext = np.hstack((f_nolag.K, np.zeros((3, 3))))
    rho_lag = np.max(np.linalg.eigvals(lagged.A - lagged.B @ K_ext).real)

    L = ["# E3: LQR designs", "",
         "| Controller | Model | Weights | Slowest closed-loop poles | Input-delay margin |",
         "|---|---|---|---|---|",
         f"| Healthy LQR | 12-state hover | Bryson: 0.5 m, 1 m/s, 0.2 rad, 2 rad/s; 0.5 N per rotor | "
         f"{poles_text(Ah)} | {dm_h * 1e3:.0f} ms |",
         f"| Failure LQR (M&D weights) | 7-state reduced attitude + altitude + 3 motor states | "
         f"1 on p,q; 20 on n; 0 on r and motor states; 4 on z, 1 on v_z; 1 N⁻² | {poles_text(Af)} | {dm_f * 1e3:.0f} ms |",
         f"| Failure LQR, no motor model | 7-state | same, no motor states | {poles_text(Af0)} | "
         f"{dm_f0 * 1e3:.0f} ms |", "",
         f"Closed loop of the no-motor-model design with the true 15 ms motor lag: max Re(λ) = {rho_lag:.2f} "
         f"({'stable' if rho_lag < 0 else 'UNSTABLE'}). Mueller & D'Andrea report that motor dynamics strongly "
         "affect this system and include them in the design; we do the same.", "",
         "Delay margin: largest pure input delay that keeps the linear closed loop stable "
         "(exact ZOH discretization at 1 ms with a delay line).", ""]

    # ---- nonlinear checks
    # failed vehicle: start at the relaxed hover with attitude/rate error and 1 m altitude error
    x0 = failed_state(eq, dw=(1.0, -1.0, -3.0), dn=(0.08, -0.05, 0.0), z=-1.0)
    log = simulate(x0, f, P, 6.0, dt=5e-4, ctrl_period=1e-3, alive_fn=ALIVE3)
    final_err_n = np.linalg.norm(log.n[-1] - eq.n)
    final_err_w = np.linalg.norm(log.w[-1] - eq.w)
    L += ["## Nonlinear check, failed vehicle", "",
          "Start: relaxed hover + Δω = (1, −1, −3) rad/s, Δn = (0.08, −0.05, ·), 1 m below the set-point; "
          "rotor 4 off; motor lag and thrust limits active.", "",
          f"After 6 s: |n − n̄| = {final_err_n:.1e}, |ω − ω̄| = {final_err_w:.1e} rad/s, "
          f"z = {log.z[-1]:+.3f} m.", ""]

    fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
    t = log.t
    for i, (lab, c) in enumerate(zip(["p", "q", "r"], SERIES)):
        ax[0].plot(t, log.w[:, i], color=c, label=lab)
        ax[0].axhline(eq.w[i], color=c, lw=0.7, alpha=0.6)
    ax[0].set_title("Body rates (thin: equilibrium)")
    ax[0].set_ylabel("rad/s")
    ax[0].legend(loc="center right")
    for i, (lab, c) in enumerate(zip(["n_x", "n_y", "n_z"], SERIES)):
        ax[1].plot(t, log.n[:, i], color=c, label=lab)
        ax[1].axhline(eq.n[i], color=c, lw=0.7, alpha=0.6)
    ax[1].set_title("Reduced attitude n (thin: n̄)")
    ax[1].legend(loc="center right")
    ax[2].plot(t, log.z, color=SERIES[0])
    ax[2].axhline(0, color=REF, lw=0.8)
    ax[2].set_title("Altitude (set-point 0 m)")
    ax[2].set_ylabel("m")
    for a in ax:
        a.set_xlabel("time (s)")
    fig.suptitle("E3 · Failure-mode LQR on the nonlinear model (rotor 4 lost, motor lag, saturation)", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e3_failed_lqr_nonlinear.png")

    # healthy vehicle: tilt + offset
    x0 = make_state(d=(0.5, -0.3, -0.5), euler=(0.25, -0.2, 0.4))
    log = simulate(x0, h, P, 5.0, dt=5e-4, ctrl_period=1e-3)
    L += ["## Nonlinear check, healthy vehicle", "",
          "Start: (0.5, −0.3, −0.5) m offset, Euler (0.25, −0.2, 0.4) rad.",
          f"After 5 s: |position| = {np.linalg.norm(log.x[-1, :3]):.1e} m.", ""]
    fig, ax = plt.subplots(1, 2, figsize=(8, 3.2))
    for i, (lab, c) in enumerate(zip(["x", "y", "z"], SERIES)):
        ax[0].plot(log.t, log.x[:, i], color=c, label=lab)
    ax[0].set_title("Position")
    ax[0].set_ylabel("m")
    ax[0].legend()
    from rotorfail.dynamics import quat_to_rot, rot_to_euler
    eul = np.array([rot_to_euler(quat_to_rot(q)) for q in log.x[:, IDX_Q]])
    for i, (lab, c) in enumerate(zip(["φ", "θ", "ψ"], SERIES)):
        ax[1].plot(log.t, eul[:, i], color=c, label=lab)
    ax[1].set_title("Euler angles")
    ax[1].set_ylabel("rad")
    ax[1].legend()
    for a in ax:
        a.set_xlabel("time (s)")
    fig.suptitle("E3 · Healthy hover LQR on the nonlinear model", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e3_healthy_lqr_nonlinear.png")

    (ROOT / "results/tables/e3_lqr.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
