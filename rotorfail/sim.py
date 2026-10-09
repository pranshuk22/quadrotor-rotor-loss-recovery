"""Fixed-step simulation with a zero-order-hold digital controller."""
from dataclasses import dataclass

import numpy as np

from .dynamics import E3, IDX_Q, quat_to_rot, rk4_step
from .params import QuadParams


@dataclass
class SimLog:
    t: np.ndarray
    x: np.ndarray
    u: np.ndarray
    n: np.ndarray     # reduced attitude R^T e3 at each sample

    @property
    def w(self):
        return self.x[:, 10:13]

    @property
    def z(self):
        return self.x[:, 2]


def simulate(x0, controller, p: QuadParams, T: float, dt: float = 5e-4,
             ctrl_period: float = 1e-3, alive_fn=None, motor_lag: bool = True,
             log_every: int = 4, stop_fn=None) -> SimLog:
    """Integrate with RK4 at dt; the controller is sampled every ctrl_period (ZOH).

    alive_fn(t) -> bool[4] gives which rotors produce thrust at time t.
    stop_fn(t, x) -> bool ends the run early (e.g. crash / divergence).
    """
    if alive_fn is None:
        alive_fn = getattr(controller, "alive", lambda t: np.ones(4, bool))
    n_steps = int(round(T / dt))
    ctrl_every = max(1, int(round(ctrl_period / dt)))
    x = np.array(x0, float)
    u = controller(0.0, x)
    ts, xs, us, ns = [], [], [], []
    for k in range(n_steps + 1):
        t = k * dt
        if k % ctrl_every == 0:
            u = controller(t, x)
        if k % log_every == 0:
            ts.append(t)
            xs.append(x.copy())
            us.append(np.array(u, float))
            ns.append(quat_to_rot(x[IDX_Q]).T @ E3)
            if stop_fn is not None and stop_fn(t, x):
                break
        if k < n_steps:
            x = rk4_step(x, u, dt, p, alive_fn(t), motor_lag)
            if not np.all(np.isfinite(x)):
                break
    return SimLog(np.array(ts), np.array(xs), np.array(us), np.array(ns))
