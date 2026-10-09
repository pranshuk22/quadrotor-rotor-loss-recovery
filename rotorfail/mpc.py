"""Linear MPC for the failed vehicle (RQ1 controllers 1 and 3).

Prediction model: nominal discrete model (10 states: 7 measured + 3 filtered-command states)
  s_{j+1} = Ad s_j + Bd u_j + d_hat
with d_hat = 0 (analytical MPC) or the residual-Koopman one-step correction evaluated
outside the QP at the current state and held constant over the horizon (measured
disturbance, as in Todde et al. 2026). The QP stays convex.

Cost: sum_j s_j' Q s_j + u_j' R u_j + s_N' P_N s_N (P_N from the discrete Riccati equation),
inputs constrained to the running-motor range [f_min, f_max].
"""
import time

import cvxpy as cp
import numpy as np
from scipy.linalg import solve_discrete_are

from .control import failure_weights
from .dynamics import IDX_Q, E3, quat_to_rot
from .equilibrium import RelaxedHover
from .koopman import TS, NominalModel, ResidualEDMD
from .params import QuadParams


class FailureMPC:
    def __init__(self, p: QuadParams, eq: RelaxedHover, horizon: int = 20,
                 residual: ResidualEDMD | None = None, z_ref: float = 0.0, ts: float = TS):
        self.p, self.eq, self.N, self.ts = p, eq, horizon, ts
        self.nom = NominalModel.build(p, eq, ts)
        self.residual = residual
        self.z_ref = z_ref
        Q, R = failure_weights()
        Ad, Bd = self.nom.Ad, self.nom.Bd
        PN = solve_discrete_are(Ad, Bd, Q, R)
        n, m = Bd.shape
        self.x0 = cp.Parameter(n)
        self.d = cp.Parameter(n)
        X = cp.Variable((n, self.N + 1))
        U = cp.Variable((m, self.N))
        cons = [X[:, 0] == self.x0]
        cost = 0
        lo = p.f_min - eq.f[:3]
        hi = p.f_max - eq.f[:3]
        for j in range(self.N):
            cons += [X[:, j + 1] == Ad @ X[:, j] + Bd @ U[:, j] + self.d,
                     U[:, j] >= lo, U[:, j] <= hi]
            cost += cp.quad_form(X[:, j], Q) + cp.quad_form(U[:, j], R)
        cost += cp.quad_form(X[:, self.N], PN)
        self.prob = cp.Problem(cp.Minimize(cost), cons)
        self.U = U
        self.fe = np.zeros(m)
        self.u_prev = np.zeros(m)
        self.solve_times = []      # wall-clock time of the CVXPY call (includes modelling overhead)
        self.qp_times = []         # time reported by the QP solver itself
        self.d_log = []

    def reset(self, f_now):
        self.fe = np.clip(np.asarray(f_now[:3], float), 0.0, self.p.f_max) - self.eq.f[:3]   # stopped motor: 0 N
        self.u_prev = self.fe.copy()

    def measure(self, x):
        n = quat_to_rot(x[IDX_Q]).T @ E3
        w = x[10:13]
        s = np.array([w[0], w[1], w[2], n[0], n[1], x[2] - self.z_ref, x[5]])
        return s - np.concatenate((self.eq.w, self.eq.n[:2], [0.0, 0.0]))

    def __call__(self, t, x):
        x7 = self.measure(x)
        d = np.zeros(10)
        if self.residual is not None:
            d[:7] = self.residual.residual(x7, self.fe, self.u_prev)
        self.x0.value = np.concatenate((x7, self.fe))
        self.d.value = d
        t0 = time.perf_counter()
        self.prob.solve(solver=cp.OSQP, warm_start=True, eps_abs=1e-5, eps_rel=1e-5, max_iter=4000)
        self.solve_times.append(time.perf_counter() - t0)
        st = self.prob.solver_stats.solve_time
        self.qp_times.append(float(st) if st is not None else float("nan"))
        u = self.U.value[:, 0] if self.U.value is not None else self.u_prev
        u = np.clip(u, self.p.f_min - self.eq.f[:3], self.p.f_max - self.eq.f[:3])
        a = 1 - np.exp(-self.ts / self.p.sigma_mot)
        self.fe = self.fe + a * (u - self.fe)
        self.u_prev = u
        self.d_log.append(d[:7].copy())
        f = self.eq.f[:3] + u
        return np.array([f[0], f[1], f[2], 0.0])
