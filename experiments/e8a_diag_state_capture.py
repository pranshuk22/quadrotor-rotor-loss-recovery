"""E8a diagnostic: why does the state-model offset-free MPC lose the capture at tau = 0?

One run only, no new controller and no parameter change: the OffsetFreeMPC with the "state"
disturbance model and the pre-registered settings of E8a, as capture controller after the spin-up
(2.95 N), on the nominal plant, tau = 0, exact hover start, 10 s (the E8a protocol).

Logged at every controller sample after the hand-over: disturbance estimate d_hat (7 entries), whether
the target was exact, the target input u_s, the commanded thrusts, the measured state. From the
simulation log: n_z and r - r_bar.

Reported (results/tables/e8a_diag_state_capture.md)
  - hand-over time, r - r_bar and n_z at the hand-over;
  - per-component peak |d_hat| over the run and before the first n_z < 0;
  - the time of the first n_z < 0;
  - for each component, the peak |d_hat_i| before the first n_z < 0 divided by the largest one-step
    change |x_i(k+1) - x_i(k)| of the measured state i over the same interval ("share of the motion
    attributed to a constant disturbance"); components with a share above 0.5 are called dominant;
  - the share of samples before the first n_z < 0 with an exact target;
  - a time series from the hand-over to 0.2 s after the first n_z < 0.
This is a single diagnostic run, not a statistical result.
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from rotorfail.control import DelaySupervisor, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import make_state  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import TS  # noqa: E402
from rotorfail.offset_free import OffsetFreeMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

F_SPIN = 2.95
NAMES = ["p", "q", "r", "n_x", "n_y", "z", "v_z"]
UNITS = ["rad/s", "rad/s", "rad/s", "-", "-", "m", "m/s"]


class Recording(OffsetFreeMPC):
    """OffsetFreeMPC that also records the call time and the measured state (logging only)."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.t_log, self.x7_log, self.u_log = [], [], []

    def reset(self, f_now):
        super().reset(f_now)
        for lst in ("t_log", "x7_log", "u_log"):
            if hasattr(self, lst):
                getattr(self, lst).clear()
        if hasattr(self, "d_hat_log"):
            self.d_hat_log.clear()
            self.target_exact.clear()
            self.target_u_log.clear()

    def __call__(self, t, x):
        self.t_log.append(t)
        self.x7_log.append(self.measure(x))
        out = super().__call__(t, x)
        self.u_log.append(out[:3].copy())
        return out


def main():
    eq = relaxed_hover(P)
    c = Recording(P, eq, disturbance="state")
    cap = SpinUpThenLQR(P, c, f_spin=F_SPIN)
    sup = DelaySupervisor(HealthyLQR(P), cap, t_fail=0.0, tau=0.0)
    log = simulate(make_state(), sup, P, 10.0, dt=1e-3, ctrl_period=TS, log_every=5)

    t = np.array(c.t_log)
    d = np.array(c.d_hat_log)
    X = np.array(c.x7_log)
    ex = np.array(c.target_exact)
    us = np.array(c.target_u_log)
    ucmd = np.array(c.u_log)
    t_h = t[0]
    nz = np.interp(t, log.t, log.n[:, 2])
    dr = np.interp(t, log.t, log.w[:, 2] - eq.w[2])
    inv = np.where(log.n[:, 2] < 0)[0]
    t_inv = float(log.t[inv[0]]) if len(inv) else float("nan")
    pre = t < t_inv if len(inv) else np.ones_like(t, bool)

    L = ["# E8a diagnostic: state-model offset-free MPC as capture controller, tau = 0", "",
         "A single diagnostic run (nominal plant, exact hover start, spin-up 2.95 N, tau = 0 ms, 10 s), "
         "with the pre-registered settings of E8a; no parameter was changed. See the docstring of "
         "`experiments/e8a_diag_state_capture.py`. Not a statistical result.", "",
         f"- Hand-over to the controller at t = {t_h:.3f} s; at the hand-over r - r_bar = {dr[0]:+.2f} rad/s, "
         f"n_z = {nz[0]:.2f}.",
         f"- First n_z < 0 at t = {t_inv:.3f} s ({t_inv - t_h:.3f} s after the hand-over)."
         if len(inv) else "- n_z stayed positive.",
         f"- Share of controller samples before that time with an exact target: {np.mean(ex[pre]):.3f} "
         f"({int(np.sum(~ex[pre]))} of {int(np.sum(pre))} inexact).",
         f"- Total samples after the hand-over: {len(t)}; exact targets overall: {np.mean(ex):.3f}.", "",
         "## Disturbance estimate by component", "",
         "d_hat is an offset per state and step, in the unit of the state. Share = peak |d_hat_i| before the "
         "first n_z < 0 divided by the largest one-step change of the measured state i over the same interval.", "",
         "| Component | unit | peak abs. d_hat (whole run) | peak abs. d_hat (before first n_z < 0) | time of that peak (s) "
         "| largest one-step change | share | dominant |", "|---|---|---|---|---|---|---|---|"]
    dX = np.abs(np.diff(X, axis=0))
    dom = []
    for i, nme in enumerate(NAMES):
        pk_all = float(np.max(np.abs(d[:, i])))
        k = int(np.argmax(np.abs(d[pre, i])))
        pk_pre = float(np.abs(d[pre, i])[k])
        step = float(np.max(dX[pre[1:], i])) if np.any(pre[1:]) else float("nan")
        share = pk_pre / step if step > 0 else float("nan")
        if share > 0.5:
            dom.append(nme)
        L.append(f"| {nme} | {UNITS[i]} | {pk_all:.4f} | {pk_pre:.4f} | {t[pre][k]:.3f} | {step:.4f} | {share:.2f} | "
                 f"{'yes' if share > 0.5 else 'no'} |")
    L += ["", f"Dominant components before the first n_z < 0: {', '.join(dom) if dom else 'none'}.", "",
          "## Time series", "",
          "Commanded thrusts and target input u_s are deviations from the relaxed-hover thrusts (N); "
          "the commands are the controller's output (rotor 4 is lost).", "",
          "| t (s) | n_z | r - r_bar (rad/s) | exact target | d_hat (p, q, r, n_x, n_y, z, v_z) | u_s (N) | command (N) |",
          "|---|---|---|---|---|---|---|"]
    t_end = (t_inv + 0.2) if len(inv) else t[-1]
    last = -1.0
    for k in range(len(t)):
        if t[k] > t_end:
            break
        if t[k] - last < 0.025 - 1e-9 and k != 0:
            continue
        last = t[k]
        dstr = ", ".join(f"{v:+.3f}" for v in d[k])
        L.append(f"| {t[k]:.3f} | {nz[k]:.2f} | {dr[k]:+.2f} | {'yes' if ex[k] else 'no'} | {dstr} | "
                 f"{', '.join(f'{v:+.2f}' for v in us[k])} | {', '.join(f'{v:+.2f}' for v in ucmd[k])} |")
    L.append("")
    (ROOT / "results/tables/e8a_diag_state_capture.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
