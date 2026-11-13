"""Offset-free control of the failed vehicle (baselines for the residual Koopman MPC, task K6).

OffsetFreeMPC
    Linear MPC with a constant-disturbance model, a steady-state Kalman filter and a
    target calculation (Pannocchia and Rawlings style). The prediction model is the
    nominal discrete 10-state model of `NominalModel` (7 physical states + 3 command
    filter states), augmented with a constant disturbance d:

        s+ = A s + B u + Bd d + d_res,        d+ = d

    The disturbance enters only the 7 physical states (the command-filter states are
    computed from the commands and are known exactly). Two disturbance models:
      "thrust": d (3) is an offset on the *produced* thrust of rotors 1 to 3;
                Bd = [B7d; 0], B7d the ZOH discretisation of the 7-state thrust input matrix.
      "state" : d (7) is an offset on each physical state per step; Bd = [I7; 0].
    The measured output is the whole 10-state vector. d_res is the optional one-step
    residual-Koopman correction (zero for the plain offset-free MPC).

    With fewer disturbance states than unknown mismatch rows ("thrust": 3 against 7), the
    steady-state Kalman innovation need not vanish (it may lie in the null space of the
    disturbance block of the gain), and the closed loop can settle with a tracking error
    although the estimator is at rest. With "state" the innovation of the 7 physical outputs
    is forced to zero in steady state, which gives zero offset in (n_x, n_y, z).

    Each step: (1) Kalman correction of the augmented state, giving d_hat; (2) target
    (s_s, u_s) with s_s = A s_s + B u_s + D, D = d_res + Bd d_hat, tracked outputs
    (n_x, n_y, z) at their set-points, input box as the only hard constraint (a small QP
    when the exact target violates the box); (3) MPC on the deviations of the *filtered state
    estimate* from the target, with the same Q, R, horizon, DARE terminal cost and input box
    as `FailureMPC`. Regulating the estimate rather than the raw measurement is what makes the
    scheme offset-free when the plant is not exactly in the model class: at a closed-loop
    steady state the estimator equations then force a zero innovation (L has full column
    rank), so the measured tracked outputs equal their targets (Pannocchia and Rawlings 2003).

FailureLQRIntegral
    Classical reference: the failure LQR with an integrator on the altitude error.
"""
import time
from dataclasses import dataclass, field

import cvxpy as cp
import numpy as np
from scipy.linalg import solve_continuous_are, solve_discrete_are
from scipy.signal import cont2discrete

from .control import failure_weights
from .dynamics import IDX_Q, E3, quat_to_rot
from .equilibrium import RelaxedHover
from .koopman import TS, NominalModel, ResidualEDMD
from .models import add_motor_lag, failed_linear
from .params import QuadParams

TRACKED = [3, 4, 5]          # n_x, n_y, z in the 10-state vector


@dataclass(frozen=True)
class NoiseSpec:
    """Kalman filter covariances, fixed a priori (see experiments/e8_offset_free.py)."""
    q_phys: float = 1e-4     # process noise variance on the 7 physical states
    q_filt: float = 1e-8     # on the 3 command-filter states
    q_dist: float = 1e-3     # "thrust" model: variance of each of the 3 disturbance states (random walk)
    q_dist_state: float = 1e-6   # "state" model: variance of each of the 7 disturbance states
    r_meas: float = 1e-6     # measurement noise variance, all 10 outputs
    d_clip: float = 1.0      # "thrust" model: N, bound on |d_hat| (anti-windup safeguard)
    d_clip_state: float = 0.5    # "state" model: bound on |d_hat| per step, in state units


def thrust_offset_matrix(p: QuadParams, eq: RelaxedHover, ts: float = TS):
    """Bd (10 x 3): ZOH discretisation of an offset on the produced thrusts of rotors 1 to 3."""
    lin7 = failed_linear(p, eq)
    lin10 = add_motor_lag(lin7, p.sigma_mot)
    B7 = np.vstack((lin7.B, np.zeros((3, 3))))
    n = lin10.A.shape[0]
    _, Bd, *_ = cont2discrete((lin10.A, B7, np.eye(n), np.zeros((n, 3))), ts)
    return Bd


def augmented_model(A, B, Bd):
    """(A_aug, B_aug, C_aug) of the model [s; d] with y = s."""
    n, m = B.shape
    nd = Bd.shape[1]
    Aa = np.block([[A, Bd], [np.zeros((nd, n)), np.eye(nd)]])
    Ba = np.vstack((B, np.zeros((nd, m))))
    Ca = np.hstack((np.eye(n), np.zeros((n, nd))))
    return Aa, Ba, Ca


def detectability_rank(A, Bd, tol=1e-9):
    """Rank (relative tolerance tol) and smallest singular value of [[I - A, -Bd], [C, 0]] (C = I)."""
    n, nd = A.shape[0], Bd.shape[1]
    M = np.block([[np.eye(n) - A, -Bd], [np.eye(n), np.zeros((n, nd))]])
    sv = np.linalg.svd(M, compute_uv=False)
    return int(np.sum(sv > tol * sv[0])), float(sv[-1])


class OffsetFreeMPC:
    def __init__(self, p: QuadParams, eq: RelaxedHover, horizon: int = 20,
                 residual: ResidualEDMD | None = None, z_ref: float = 0.0, ts: float = TS,
                 noise: NoiseSpec = NoiseSpec(), disturbance: str = "thrust", weights: dict | None = None):
        assert disturbance in ("thrust", "state")
        self.disturbance = disturbance
        self.p, self.eq, self.N, self.ts = p, eq, horizon, ts
        self.residual, self.z_ref, self.noise = residual, z_ref, noise
        self.nom = NominalModel.build(p, eq, ts)
        self.A, self.B = self.nom.Ad, self.nom.Bd
        if disturbance == "thrust":
            self.Bd = thrust_offset_matrix(p, eq, ts)
            q_d, self.d_clip = noise.q_dist, noise.d_clip
        else:
            self.Bd = np.vstack((np.eye(7), np.zeros((3, 7))))
            q_d, self.d_clip = noise.q_dist_state, noise.d_clip_state
        n, m = self.B.shape
        self.nd = self.Bd.shape[1]
        self.n, self.m = n, m
        Q, R = failure_weights(**(weights or {}))
        PN = solve_discrete_are(self.A, self.B, Q, R)

        # --- Kalman filter on the augmented model (current-estimator form)
        Aa, Ba, Ca = augmented_model(self.A, self.B, self.Bd)
        self.Aa, self.Ba, self.Ca = Aa, Ba, Ca
        Qw = np.diag([noise.q_phys] * 7 + [noise.q_filt] * 3 + [q_d] * self.nd)
        Rv = noise.r_meas * np.eye(n)
        Pp = solve_discrete_are(Aa.T, Ca.T, Qw, Rv)            # prior covariance
        self.L = Pp @ Ca.T @ np.linalg.inv(Ca @ Pp @ Ca.T + Rv)

        # --- target calculation: unconstrained solution is linear in D
        self.H = np.zeros((3, n))
        for i, j in enumerate(TRACKED):
            self.H[i, j] = 1.0
        M = np.block([[np.eye(n) - self.A, -self.B], [self.H, np.zeros((3, m))]])
        self.Minv = np.linalg.inv(M)
        self.u_lo = p.f_min - eq.f[:3]
        self.u_hi = p.f_max - eq.f[:3]
        self.Dt = cp.Parameter(n)
        self.ss = cp.Variable(n)
        self.us = cp.Variable(m)
        self.tprob = cp.Problem(
            cp.Minimize(cp.sum_squares(self.H @ self.ss) + 1e-9 * (cp.sum_squares(self.ss) + cp.sum_squares(self.us))),
            [(np.eye(n) - self.A) @ self.ss - self.B @ self.us == self.Dt,
             self.us >= self.u_lo, self.us <= self.u_hi])

        # --- MPC on the deviations from the target
        self.e0 = cp.Parameter(n)
        self.w = cp.Parameter(n)               # target defect (zero when the target is exact)
        self.v_lo = cp.Parameter(m)
        self.v_hi = cp.Parameter(m)
        X = cp.Variable((n, self.N + 1))
        V = cp.Variable((m, self.N))
        cons = [X[:, 0] == self.e0]
        cost = 0
        for j in range(self.N):
            cons += [X[:, j + 1] == self.A @ X[:, j] + self.B @ V[:, j] + self.w,
                     V[:, j] >= self.v_lo, V[:, j] <= self.v_hi]
            cost += cp.quad_form(X[:, j], Q) + cp.quad_form(V[:, j], R)
        cost += cp.quad_form(X[:, self.N], PN)
        self.prob = cp.Problem(cp.Minimize(cost), cons)
        self.V = V

        self.solve_times, self.qp_times = [], []
        self.d_hat_log, self.target_exact, self.clip_active, self.bad_status = [], [], [], 0
        self.target_u_log = []        # u_s of every step (diagnostics only)
        self.reset(self.eq.f[:3])

    # ------------------------------------------------------------------ state
    def reset(self, f_now):
        self.fe = np.clip(np.asarray(f_now[:3], float), 0.0, self.p.f_max) - self.eq.f[:3]
        self.u_prev = self.fe.copy()
        self.xhat = None                       # initialised from the first measurement
        self.D_res_prev = np.zeros(self.n)

    def measure(self, x):
        n = quat_to_rot(x[IDX_Q]).T @ E3
        w = x[10:13]
        s = np.array([w[0], w[1], w[2], n[0], n[1], x[2] - self.z_ref, x[5]])
        return s - np.concatenate((self.eq.w, self.eq.n[:2], [0.0, 0.0]))

    # ------------------------------------------------------------------ pieces
    def estimate(self, y):
        """Kalman correction; returns d_hat."""
        if self.xhat is None:
            self.xhat = np.concatenate((y, np.zeros(self.nd)))
        else:
            xp = self.Aa @ self.xhat + self.Ba @ self.u_prev
            xp[:self.n] += self.D_res_prev
            self.xhat = xp + self.L @ (y - self.Ca @ xp)
        self.xhat[self.n:] = np.clip(self.xhat[self.n:], -self.d_clip, self.d_clip)
        return self.xhat[self.n:].copy()

    def target(self, D):
        """(s_s, u_s, exact). exact: the unconstrained target met the input box."""
        sol = self.Minv @ np.concatenate((D, np.zeros(3)))
        ss, us = sol[:self.n], sol[self.n:]
        if np.all(us >= self.u_lo - 1e-9) and np.all(us <= self.u_hi + 1e-9):
            return ss, us, True
        self.Dt.value = D
        try:
            self.tprob.solve(solver=cp.OSQP, eps_abs=1e-8, eps_rel=1e-8, max_iter=20000)
        except cp.SolverError:
            pass
        if self.tprob.status in ("optimal", "optimal_inaccurate") and self.ss.value is not None:
            return self.ss.value.copy(), np.clip(self.us.value, self.u_lo, self.u_hi), False
        return np.zeros(self.n), np.zeros(self.m), False      # fallback: nominal trim, D in the defect

    def act(self, x7):
        """One control step from the measured 7-state deviation x7. Returns u (deviation, 3)."""
        y = np.concatenate((x7, self.fe))
        d_hat = self.estimate(y)
        D_res = np.zeros(self.n)
        if self.residual is not None:
            D_res[:7] = self.residual.residual(x7, self.fe, self.u_prev)
        D = D_res + self.Bd @ d_hat
        ss, us, exact = self.target(D)
        self.e0.value = self.xhat[:self.n] - ss
        self.w.value = D + self.A @ ss + self.B @ us - ss
        self.v_lo.value = self.u_lo - us
        self.v_hi.value = self.u_hi - us
        t0 = time.perf_counter()
        self.prob.solve(solver=cp.OSQP, warm_start=True, eps_abs=1e-5, eps_rel=1e-5, max_iter=4000)
        self.solve_times.append(time.perf_counter() - t0)
        st = self.prob.solver_stats.solve_time
        self.qp_times.append(float(st) if st is not None else float("nan"))
        if self.prob.status != "optimal":
            self.bad_status += 1
        u = us + self.V.value[:, 0] if self.V.value is not None else self.u_prev
        u = np.clip(u, self.u_lo, self.u_hi)
        a = 1 - np.exp(-self.ts / self.p.sigma_mot)
        self.fe = self.fe + a * (u - self.fe)
        self.u_prev = u
        self.D_res_prev = D_res
        self.d_hat_log.append(d_hat)
        self.target_exact.append(exact)
        self.target_u_log.append(us.copy())
        self.clip_active.append(bool(np.any(np.abs(self.xhat[self.n:]) >= self.d_clip - 1e-12)))
        return u

    def __call__(self, t, x):
        u = self.act(self.measure(x))
        f = self.eq.f[:3] + u
        return np.array([f[0], f[1], f[2], 0.0])


@dataclass
class FailureLQRIntegral:
    """Failure LQR plus an integrator on the altitude error (classical reference).

    State e = [e7 (z relative to z_ref), f_est - f_eq, xi], xi' = z - z_ref. The 10-state
    weights are those of `failure_weights`; the integrator weight w_int is fixed a priori.
    Anti-windup: the integrator is not advanced at a sample whose previous command was
    clipped. The motor filter and the interface follow `FailureLQR`.
    """
    p: QuadParams
    eq: RelaxedHover
    z_ref: float = 0.0
    w_int: float = 1.0
    K: np.ndarray = field(init=False)

    def __post_init__(self):
        lin = add_motor_lag(failed_linear(self.p, self.eq), self.p.sigma_mot)
        n = lin.A.shape[0]
        A = np.zeros((n + 1, n + 1))
        A[:n, :n] = lin.A
        A[n, 5] = 1.0
        B = np.vstack((lin.B, np.zeros((1, 3))))
        Q10, R = failure_weights()
        Q = np.zeros((n + 1, n + 1))
        Q[:n, :n] = Q10
        Q[n, n] = self.w_int
        P = solve_continuous_are(A, B, Q, R)
        self.K = np.linalg.solve(R, B.T @ P)
        self.A_aug, self.B_aug = A, B
        self.base_trim = lin.x_trim[:7]
        self.reset(self.eq.f[:3])

    def reset(self, f_now):
        self.f_est = np.clip(np.asarray(f_now[:3], float), 0.0, self.p.f_max)
        self.xi = 0.0
        self.t_last = None
        self._clipped = False

    def __call__(self, t, x):
        n = quat_to_rot(x[IDX_Q]).T @ E3
        w = x[10:13]
        s7 = np.array([w[0], w[1], w[2], n[0], n[1], x[2], x[5]])
        e7 = s7 - self.base_trim
        e7[5] -= self.z_ref
        dt = 0.0 if self.t_last is None else t - self.t_last
        if not self._clipped:
            self.xi += dt * e7[5]
        e = np.concatenate((e7, self.f_est - self.eq.f[:3], [self.xi]))
        u_raw = self.eq.f[:3] - self.K @ e
        u3 = np.clip(u_raw, self.p.f_min, self.p.f_max)
        self._clipped = bool(np.any(u3 != u_raw))
        a = 1.0 - np.exp(-dt / self.p.sigma_mot)
        self.f_est = self.f_est + a * (u3 - self.f_est)
        self.t_last = t
        return np.array([u3[0], u3[1], u3[2], 0.0])
