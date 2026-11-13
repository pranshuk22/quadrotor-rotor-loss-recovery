"""Shared helpers for the RQ1 experiments of stage E (E8c to E8g): controller factory from a picklable spec,
the E7 regulation protocol and the E7/E8a capture-after-delay protocol, generalised over the truth plant.

A controller spec is (kind, kwargs) with kind in
  "lqr", "lqri" (LQR + altitude integrator), "mpc" (FailureMPC; kwargs: horizon, residual, weights),
  "of" (OffsetFreeMPC; kwargs: horizon, residual, disturbance).
`residual` objects are deep-copied for every run (adaptive residuals carry state).
"""
import copy
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import TS, initial_state  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.offset_free import FailureLQRIntegral, OffsetFreeMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731
F_SPIN = 2.95


def make_ctrl(spec, eq):
    kind, kw = spec
    kw = dict(kw)
    res = kw.pop("residual", None)
    if res is not None:
        res = copy.deepcopy(res)
        if hasattr(res, "reset"):
            res.reset()
    if kind == "lqr":
        return FailureLQR(P, eq)
    if kind == "lqri":
        return FailureLQRIntegral(P, eq)
    if kind == "mpc":
        return FailureMPC(P, eq, residual=res, **kw)
    if kind == "of":
        return OffsetFreeMPC(P, eq, residual=res, **kw)
    raise ValueError(kind)


def stats(c):
    out = dict(wall_ms=float("nan"), qp_ms=float("nan"), clip_frac=float("nan"), trace_max=float("nan"), n_resc=0, eig_viol=0)
    if hasattr(c, "solve_times") and c.solve_times:
        out["wall_ms"] = float(np.median(c.solve_times) * 1e3)
        out["qp_ms"] = float(np.nanmedian(c.qp_times) * 1e3)
    r = getattr(c, "residual", None)
    if r is not None and hasattr(r, "rls"):
        out["clip_frac"] = r.n_clipped / max(1, r.n_calls)
        out["trace_max"] = max(r.rls.trace_log) if r.rls.trace_log else float("nan")
        out["n_resc"] = r.rls.n_rescaled
        out["eig_viol"] = r.rls.min_eig_violations
    return out


def run_regulation(args):
    """E7 Part 1 protocol: one start 1 m below the set-point, 8 s; steady error over the last 2 s."""
    spec, PT = args
    eq = relaxed_hover(P)
    x0 = initial_state(eq, np.random.default_rng(0))
    x0[2] = -1.0
    c = make_ctrl(spec, eq)
    c.reset(x0[13:16])
    log = simulate(x0, c, PT, 8.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    late = log.t >= 6.0
    r = getattr(c, "residual", None)
    trace = list(r.rls.trace_log) if r is not None and hasattr(r, "rls") else None
    return dict(z_ss=float(np.mean(log.z[late])), z_rms=float(np.sqrt(np.mean(log.z ** 2))),
                upright=bool(log.completed and np.min(log.n[:, 2]) > 0), trace=trace, **stats(c))


def closed_loop_reference(args):
    spec, PT = args
    eq = relaxed_hover(P)
    x = make_state(w=eq.w, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n)
    c = make_ctrl(spec, eq)
    c.reset(eq.f[:3])
    log = simulate(x, c, PT, 12.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    last = log.t >= 11.0
    return SimpleNamespace(n=log.n[last].mean(axis=0), w=log.w[last].mean(axis=0))


def run_delay(args):
    """Capture after a detection delay: healthy LQR for tau, spin-up, then the controller; judged against the
    controller's own closed-loop steady state on the same plant."""
    spec, PT, tau, ref, x0 = args
    eq = relaxed_hover(P)
    c = make_ctrl(spec, eq)
    cap = SpinUpThenLQR(P, c, f_spin=F_SPIN)
    sup = DelaySupervisor(HealthyLQR(P), cap, t_fail=0.0, tau=tau)
    log = simulate(x0 if x0 is not None else make_state(), sup, PT, 10.0, dt=1e-3, ctrl_period=TS, log_every=5)
    o = evaluate(log, ref)
    return dict(tau=tau, alt_loss=float(o.alt_loss), min_nz=float(o.min_nz), captured=bool(o.captured),
                safe=bool(o.safe), **stats(c))
