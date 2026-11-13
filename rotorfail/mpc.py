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
from .koopman import TS, XI_IDX, NominalModel, ResidualEDMD
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


class LiftedKoopmanMPC:
    """MPC on the full-state Koopman (EDMDc) model, proposal controller 2 (task K5).

    Prediction model: the lifted linear model z+ = A z + B u of `FullEDMDc` (55 lifted states, built
    on xi = [p, q, r, n_x, n_y, v_z, f_est(3)]) plus an altitude state
        alt+ = alt + ts * v_z,       v_z = C[v_z] z + mu[v_z]   (rectangle rule; E6 uses the trapezoid)
    (56 states). The lifted state is centred at the lifted trim z_e = psi(0), for which
    C z_e + mu = 0, so the physical output error is exactly C (z - z_e) and the cost has no linear
    term: the model in centred coordinates is zc+ = A zc + B u + c, c = (A - I) z_e.

    The lifted state is re-computed from the measurement at every control step (zc_0 = psi(xi_k) - z_e),
    never propagated between steps. Stage cost on the physical outputs with the weights of
    `FailureMPC` (mapped to the xi ordering) plus 1e-6 I on the lifted state so the QP is strictly
    convex; terminal cost from the DARE of the 55-state pair (A_aug, B_aug) without the constant coordinate,
    with Q_lift = C' Q C + 1e-6 I (+ altitude weight). The Riccati solution is verified (residual,
    symmetry, positive semi-definiteness, spectral radius of A - B K); if a check fails, no terminal
    cost is used and `terminal` records "none". Same horizon and input box as `FailureMPC`.
    """

    def __init__(self, p: QuadParams, eq: RelaxedHover, model, horizon: int = 20, z_ref: float = 0.0,
                 ts: float = TS, terminal: str = "dare", tol: float = 1e-8):
        self.p, self.eq, self.N, self.ts, self.z_ref = p, eq, horizon, ts, z_ref
        self.model = model
        A, B, C = model.A, model.B, model.C
        nz = A.shape[0]
        self.nz, m = nz, B.shape[1]
        Q10, R = failure_weights()
        idx = [0, 1, 2, 3, 4, 6, 7, 8, 9]          # xi ordering in the 10-state vector (z excluded)
        Qxi = Q10[np.ix_(idx, idx)]
        w_alt = Q10[5, 5]
        self.ze = model.dic(np.zeros(len(model.dic.mu)))[0]
        self.c = (A - np.eye(nz)) @ self.ze
        Aa = np.zeros((nz + 1, nz + 1))
        Aa[:nz, :nz] = A
        Aa[nz, :nz] = ts * C[5]
        Aa[nz, nz] = 1.0
        Ba = np.vstack((B, np.zeros((1, m))))
        ca = np.concatenate((self.c, [0.0]))
        Ql = np.zeros((nz + 1, nz + 1))
        Ql[:nz, :nz] = C.T @ Qxi @ C + 1e-6 * np.eye(nz)
        Ql[nz, nz] = w_alt
        self.Aa, self.Ba, self.Ql, self.R = Aa, Ba, Ql, R
        self.dare = self._terminal(Aa, Ba, Ql, R, terminal, tol)
        PN = self.dare["P"]

        self.z0 = cp.Parameter(nz + 1)
        X = cp.Variable((nz + 1, self.N + 1))
        U = cp.Variable((m, self.N))
        lo = p.f_min - eq.f[:3]
        hi = p.f_max - eq.f[:3]
        cons = [X[:, 0] == self.z0]
        cost = 0
        for j in range(self.N):
            cons += [X[:, j + 1] == Aa @ X[:, j] + Ba @ U[:, j] + ca, U[:, j] >= lo, U[:, j] <= hi]
            cost += cp.quad_form(X[:, j], Ql, assume_PSD=True) + cp.quad_form(U[:, j], R)
        if PN is not None:
            cost += cp.quad_form(X[:, self.N], PN, assume_PSD=True)
        self.prob = cp.Problem(cp.Minimize(cost), cons)
        self.U = U
        self.fe = np.zeros(m)
        self.u_prev = np.zeros(m)
        self.solve_times, self.qp_times = [], []
        self.n_bad, self.max_std = 0, 0.0

    @staticmethod
    def _terminal(Aa, Ba, Ql, R, terminal, tol, exclude_constant=True):
        info = dict(P=None, kind="none", ok=False, residual=np.nan, sym=np.nan, min_eig=np.nan,
                    rho=np.nan, cond=np.nan, error="")
        if terminal != "dare":
            return info
        # The constant coordinate (index 0) is identically zero in centred coordinates and has an
        # eigenvalue of 1 - 2e-9, which makes the full Riccati solution very ill-conditioned:
        # it is excluded from the terminal cost (its P entries are zero).
        keep = np.arange(1 if exclude_constant else 0, Aa.shape[0])
        Ak, Bk, Qk = Aa[np.ix_(keep, keep)], Ba[keep], Ql[np.ix_(keep, keep)]
        try:
            Pk = solve_discrete_are(Ak, Bk, Qk, R)
        except Exception as e:                       # no stabilising solution
            info["error"] = str(e)
            return info
        S = R + Bk.T @ Pk @ Bk
        K = np.linalg.solve(S, Bk.T @ Pk @ Ak)
        res = Ak.T @ Pk @ Ak - Pk - Ak.T @ Pk @ Bk @ K + Qk
        nP = np.linalg.norm(Pk)
        ev = np.linalg.eigvalsh((Pk + Pk.T) / 2)
        info.update(residual=float(np.linalg.norm(res) / nP), sym=float(np.linalg.norm(Pk - Pk.T) / nP),
                    min_eig=float(ev.min() / ev.max()), rho=float(np.max(np.abs(np.linalg.eigvals(Ak - Bk @ K)))),
                    cond=float(np.linalg.cond(Pk)))
        info["ok"] = bool(info["residual"] < tol and info["sym"] < tol and info["min_eig"] > -tol and info["rho"] < 1.0)
        if info["ok"]:
            Pm = np.zeros_like(Aa)
            Pm[np.ix_(keep, keep)] = (Pk + Pk.T) / 2
            info.update(P=Pm, kind="dare")
        return info

    def reset(self, f_now):
        self.fe = np.clip(np.asarray(f_now[:3], float), 0.0, self.p.f_max) - self.eq.f[:3]
        self.u_prev = self.fe.copy()

    def measure(self, x):
        n = quat_to_rot(x[IDX_Q]).T @ E3
        w = x[10:13]
        s = np.array([w[0], w[1], w[2], n[0], n[1], x[2] - self.z_ref, x[5]])
        return s - np.concatenate((self.eq.w, self.eq.n[:2], [0.0, 0.0]))

    def act(self, x7):
        xi = np.concatenate((x7[XI_IDX], self.fe))
        self.max_std = max(self.max_std, float(np.max(np.abs((xi - self.model.dic.mu) / self.model.dic.sd))))
        self.z0.value = np.concatenate((self.model.dic(xi)[0] - self.ze, [x7[5]]))
        t0 = time.perf_counter()
        try:
            self.prob.solve(solver=cp.OSQP, warm_start=True, eps_abs=1e-5, eps_rel=1e-5, max_iter=4000)
        except cp.SolverError:
            pass
        self.solve_times.append(time.perf_counter() - t0)
        st = self.prob.solver_stats.solve_time if self.prob.solver_stats is not None else None
        self.qp_times.append(float(st) if st is not None else float("nan"))
        if self.prob.status != "optimal" or self.U.value is None:
            self.n_bad += 1
        u = self.U.value[:, 0] if self.U.value is not None else self.u_prev
        u = np.clip(u, self.p.f_min - self.eq.f[:3], self.p.f_max - self.eq.f[:3])
        a = 1 - np.exp(-self.ts / self.p.sigma_mot)
        self.fe = self.fe + a * (u - self.fe)
        self.u_prev = u
        return u

    def __call__(self, t, x):
        u = self.act(self.measure(x))
        f = self.eq.f[:3] + u
        return np.array([f[0], f[1], f[2], 0.0])
