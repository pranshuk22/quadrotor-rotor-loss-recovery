"""Recovery metrics for failure runs.

Success criterion, fixed before running the sweeps (do not tune afterwards):
  CAPTURE  : over the final 1 s of the run, |n - n_bar| < 0.05 and |w - w_bar| < 2 rad/s
  SAFE     : CAPTURE and altitude loss < 2 m and the vehicle never inverts (n_z > 0)
Altitude loss = z(t_fail) - min_t z(t).
"""
from dataclasses import dataclass

import numpy as np

from .equilibrium import RelaxedHover
from .sim import SimLog

N_TOL = 0.05
W_TOL = 2.0
ALT_LOSS_MAX = 2.0
FINAL_WINDOW = 1.0


@dataclass
class Outcome:
    captured: bool
    safe: bool
    alt_loss: float
    min_nz: float
    t_capture: float      # first time after which the capture tolerances hold (nan if never)
    max_rate: float

    def as_dict(self):
        return self.__dict__.copy()


def evaluate(log: SimLog, eq: RelaxedHover, t_fail: float = 0.0) -> Outcome:
    t = log.t
    dn = np.linalg.norm(log.n - eq.n, axis=1)
    dw = np.linalg.norm(log.w - eq.w, axis=1)
    ok = (dn < N_TOL) & (dw < W_TOL)
    final = t >= t[-1] - FINAL_WINDOW
    captured = bool(np.all(ok[final])) and log.completed
    after = t >= t_fail
    z0 = log.z[after][0]
    alt_loss = float(z0 - np.min(log.z[after]))
    min_nz = float(np.min(log.n[after, 2]))
    if captured:
        bad = np.where(~ok)[0]
        t_cap = float(t[bad[-1] + 1]) if len(bad) else max(float(t[0]), t_fail)
    else:
        t_cap = float("nan")
    safe = captured and alt_loss < ALT_LOSS_MAX and min_nz > 0.0
    max_rate = float(np.max(np.linalg.norm(log.w[after][:, :2], axis=1)))
    return Outcome(captured, safe, alt_loss, min_nz, t_cap - t_fail, max_rate)
