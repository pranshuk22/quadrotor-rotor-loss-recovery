"""RQ1: Koopman/EDMDc models of the failed quadrotor (rotor 4 lost) around the relaxed hover.

Sampling period TS. Measured state (deviations from the relaxed hover):
    x = [p, q, r, n_x, n_y, z, v_z]                     (7)
Commanded thrusts u = [f1, f2, f3] (deviations). The produced thrust is not measured;
f_est is the nominal first-order filter of the commands (known to the controller).

Models
  nominal  : ZOH discretization of the Mueller & D'Andrea LTI model + nominal motor lag
             (10 states: x and f_est), designed on the nominal parameters.
  full     : full-state EDMDc (Korda & Mezic 2018): lifted z = psi(xi), z+ = A z + B u,
             xi = [p, q, r, n_x, n_y, v_z, f_est] (z excluded: it only integrates v_z).
  residual : nominal prediction + learned one-step residual
             e_{k+1} = x_{k+1} - x_nom_{k+1} = W [psi(xi_k); u_k]  (EDMD regression on the
             same dictionary), clipped to |e| <= d_max (empirical percentile).
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import cont2discrete

from .control import FailureLQR
from .dynamics import IDX_F, IDX_Q, E3, make_state, quat_from_n, quat_to_rot
from .equilibrium import RelaxedHover
from .models import add_motor_lag, failed_linear
from .params import QuadParams
from .sim import simulate

TS = 0.005
MEAS = ["p", "q", "r", "n_x", "n_y", "z", "v_z"]
XI_IDX = [0, 1, 2, 3, 4, 6]          # entries of x used by the dictionaries (no z)


# ------------------------------------------------------------------ nominal
@dataclass
class NominalModel:
    Ad: np.ndarray       # 10 x 10
    Bd: np.ndarray       # 10 x 3
    x_trim: np.ndarray   # 7
    u_trim: np.ndarray   # 3
    sigma: float

    @classmethod
    def build(cls, p: QuadParams, eq: RelaxedHover, ts: float = TS):
        lin = add_motor_lag(failed_linear(p, eq), p.sigma_mot)
        n, m = lin.B.shape
        Ad, Bd, *_ = cont2discrete((lin.A, lin.B, np.eye(n), np.zeros((n, m))), ts)
        return cls(Ad, Bd, lin.x_trim[:7], lin.u_trim, p.sigma_mot)

    def step(self, x7, fe, u):
        """One step in deviation coordinates. x7: (7,), fe, u: (3,). Returns (x7+, fe+)."""
        s = np.concatenate((x7, fe))
        s1 = self.Ad @ s + self.Bd @ u
        return s1[:7], s1[7:]


# ------------------------------------------------------------------ dictionary
@dataclass
class Dictionary:
    """[1, xi, monomials up to `degree` (default 2: all degree-2 monomials)], on standardized xi."""
    mu: np.ndarray
    sd: np.ndarray
    degree: int = 2

    def __call__(self, xi):
        xi = np.atleast_2d(xi)
        y = (xi - self.mu) / self.sd
        n = y.shape[1]
        blocks = [np.ones((y.shape[0], 1)), y]
        if self.degree >= 2:
            iu = np.triu_indices(n)
            blocks.append((y[:, :, None] * y[:, None, :])[:, iu[0], iu[1]])
        if self.degree >= 3:
            import itertools
            idx = np.array(list(itertools.combinations_with_replacement(range(n), 3)))
            blocks.append(y[:, idx[:, 0]] * y[:, idx[:, 1]] * y[:, idx[:, 2]])
        return np.hstack(blocks)

    @property
    def size(self):
        n = len(self.mu)
        out = 1 + n
        if self.degree >= 2:
            out += n * (n + 1) // 2
        if self.degree >= 3:
            out += n * (n + 1) * (n + 2) // 6
        return out


def ridge(X, Y, lam):
    """argmin_W |Y - X W|^2 + lam |W|^2 (rows are samples)."""
    G = X.T @ X + lam * np.eye(X.shape[1])
    return np.linalg.solve(G, X.T @ Y)


# ------------------------------------------------------------------ data
@dataclass
class Dataset:
    x: list    # per episode: (T+1, 7) measured deviations
    fe: list   # per episode: (T+1, 3) filtered-command deviations
    u: list    # per episode: (T, 3) command deviations


def _measure(xfull, eq):
    n = quat_to_rot(xfull[IDX_Q]).T @ E3
    w = xfull[10:13]
    s = np.array([w[0], w[1], w[2], n[0], n[1], xfull[2], xfull[5]])
    return s - np.concatenate((eq.w, eq.n[:2], [0.0, 0.0]))


class ExcitedLQR:
    """Failure LQR (nominal design) + piecewise-constant random excitation on the commands."""

    def __init__(self, p_nom, eq, rng, amp=0.35, hold=0.05):
        self.lqr = FailureLQR(p_nom, eq)
        self.p = p_nom
        self.rng = rng
        self.amp, self.hold = amp, hold
        self.t_next, self.exc = -1.0, np.zeros(3)

    def reset(self, f_now):
        """Forward to the inner failure LQR (needed when used as the capture controller of the spin-up chain)."""
        self.lqr.reset(f_now)

    def __call__(self, t, x):
        if t >= self.t_next:
            self.exc = self.rng.uniform(-self.amp, self.amp, 3)
            self.t_next = t + self.hold
        u = self.lqr(t, x)
        u[:3] = np.clip(u[:3] + self.exc, self.p.f_min, self.p.f_max)
        self.lqr.correct_last_command(u[:3])   # the filter must see the command actually sent
        return u


def initial_state(eq, rng, scale=1.0):
    dw = rng.uniform(-2, 2, 3) * scale
    dn = rng.uniform(-0.15, 0.15, 2) * scale
    nxy = eq.n[:2] + dn
    n = np.array([nxy[0], nxy[1], np.sqrt(1 - nxy @ nxy)])
    x = make_state(d=(0, 0, rng.uniform(-0.5, 0.5) * scale), v=(0, 0, rng.uniform(-0.5, 0.5) * scale),
                   w=eq.w + dw, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(n)
    return x


@dataclass(frozen=True)
class MeasurementNoise:
    """Gaussian sensor noise (task K9): rates (rad/s), tilt (rad, applied as a small rotation so |n| = 1 is kept),
    altitude (m), vertical speed (m/s)."""
    rate: float = 0.05
    tilt: float = 0.005
    z: float = 0.02
    vz: float = 0.05


def noisy_measurement(x7, spec: MeasurementNoise, rng, eq):
    """Noisy copy of a measured 7-state deviation x7 = [p, q, r, n_x, n_y, z, v_z] (n kept on the unit sphere)."""
    out = np.array(x7, float)
    out[:3] += rng.normal(0, spec.rate, 3)
    n = np.array([out[3] + eq.n[0], out[4] + eq.n[1], np.sqrt(max(1.0 - (out[3] + eq.n[0]) ** 2 - (out[4] + eq.n[1]) ** 2, 1e-12))])
    a = rng.normal(0, spec.tilt, 3)                       # small rotation vector
    n = n + np.cross(a, n)
    n /= np.linalg.norm(n)
    out[3:5] = n[:2] - eq.n[:2]
    out[5] += rng.normal(0, spec.z)
    out[6] += rng.normal(0, spec.vz)
    return out


def generate(p_truth, p_nom, eq, n_episodes, T, seed, amp=0.35, ts=TS, noise: MeasurementNoise | None = None,
             noise_seed: int = 0):
    """Closed-loop excited episodes on the truth plant, sampled at ts.

    p_truth: a QuadParams, or a callable rng -> QuadParams (new draw per episode).
    """
    rng = np.random.default_rng(seed)
    nrng = np.random.default_rng(noise_seed)
    alive = lambda t: np.array([True, True, True, False])  # noqa: E731
    xs, fes, us = [], [], []
    for _ in range(n_episodes):
        pt = p_truth(rng) if callable(p_truth) else p_truth
        ctrl = ExcitedLQR(p_nom, eq, rng, amp=amp)
        x0 = initial_state(eq, rng)
        dt = 1e-3
        every = int(round(ts / dt))
        log = simulate(x0, ctrl, pt, T, dt=dt, ctrl_period=ts, alive_fn=alive, log_every=every)
        X = np.array([_measure(xf, eq) for xf in log.x])
        U = log.u[:, :3] - eq.f[:3]
        # nominal command filter (what the controller knows), starting from the trim
        fe = np.zeros((len(U), 3))
        a = ts / p_nom.sigma_mot
        for k in range(1, len(U)):
            fe[k] = fe[k - 1] + (1 - np.exp(-a)) * (U[k - 1] - fe[k - 1])
        if not np.all(np.isfinite(X)) or np.max(np.abs(X[:, 3:5])) > 0.6:
            continue  # discard diverged episodes
        if noise is not None:
            X = np.array([noisy_measurement(x, noise, nrng, eq) for x in X])
        xs.append(X)
        fes.append(fe)
        us.append(U[:-1])
    return Dataset(xs, fes, us)


def generate_capture(p_truth, p_nom, eq, n_episodes, T, seed, tau_max=0.02, amp=0.35, ts=TS, f_spin=2.95):
    """Capture transients (task K8): E4-style failures on the truth plant with a random detection delay
    tau ~ U[0, tau_max] and a random pre-failure state (E4 distribution); the spin-up at f_spin hands over at
    |w| > 10 rad/s to the excited failure LQR; the episode records T seconds from the hand-over on.

    The command filter of the controller starts at the spin-up thrusts (f_spin, 0, f_spin). Diverged episodes
    (|n_xy| deviation above 0.6 or non-finite) are discarded; returns (Dataset, n_discarded).
    """
    from .control import DelaySupervisor, HealthyLQR, SpinUpThenLQR
    rng = np.random.default_rng(seed)
    xs, fes, us, bad = [], [], [], 0
    for _ in range(n_episodes):
        pt = p_truth(rng) if callable(p_truth) else p_truth
        tau = float(rng.uniform(0.0, tau_max))
        x0 = make_state(v=rng.normal(0, 0.3, 3), euler=rng.normal(0, np.deg2rad(3), 3), w=rng.normal(0, 0.3, 3))
        exc = ExcitedLQR(p_nom, eq, rng, amp=amp)
        sup = DelaySupervisor(HealthyLQR(p_nom), SpinUpThenLQR(p_nom, exc, f_spin=f_spin), t_fail=0.0, tau=tau)
        log = simulate(x0, sup, pt, 3.0 + T, dt=1e-3, ctrl_period=1e-3, log_every=1)
        # hand-over: first time the controller is the failure LQR (rate norm above the switch, after tau)
        wn = np.linalg.norm(log.w, axis=1)
        idx = np.where((log.t >= tau) & (wn > 10.0))[0]
        if len(idx) == 0:
            bad += 1
            continue
        k0 = int(idx[0])
        step = int(round(ts / 1e-3))
        sel = np.arange(k0, min(len(log.t), k0 + int(round(T / 1e-3)) + 1), step)
        X = np.array([_measure(log.x[k], eq) for k in sel])
        U = log.u[sel][:, :3] - eq.f[:3]
        if len(sel) < 10 or not np.all(np.isfinite(X)) or np.max(np.abs(X[:, 3:5])) > 0.9:
            bad += 1
            continue
        fe = np.zeros((len(U), 3))
        fe[0] = np.array([f_spin, 0.0, f_spin]) - eq.f[:3]
        a = ts / p_nom.sigma_mot
        for k in range(1, len(U)):
            fe[k] = fe[k - 1] + (1 - np.exp(-a)) * (U[k - 1] - fe[k - 1])
        xs.append(X)
        fes.append(fe)
        us.append(U[:-1])
    return Dataset(xs, fes, us), bad


# ------------------------------------------------------------------ models
@dataclass
class FullEDMDc:
    dic: Dictionary
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray     # lifted -> xi (first n_xi lifted coordinates after the constant)

    @classmethod
    def fit(cls, data: Dataset, lam=1e-6):
        XI0, XI1, U0 = [], [], []
        for X, fe, U in zip(data.x, data.fe, data.u):
            xi = np.hstack((X[:, XI_IDX], fe))
            XI0.append(xi[:-1])
            XI1.append(xi[1:])
            U0.append(U)
        XI0, XI1, U0 = map(np.vstack, (XI0, XI1, U0))
        dic = Dictionary(XI0.mean(0), XI0.std(0) + 1e-9)
        Z0, Z1 = dic(XI0), dic(XI1)
        AB = ridge(np.hstack((Z0, U0)), Z1, lam)        # Z1 ≈ Z0 A^T + U0 B^T
        nz = Z0.shape[1]
        A, B = AB[:nz].T, AB[nz:].T
        n_xi = XI0.shape[1]
        C = np.zeros((n_xi, nz))
        C[:, 1:1 + n_xi] = np.diag(dic.sd)
        return cls(dic, A, B, C)

    def eigs(self):
        return np.linalg.eigvals(self.A)

    def rollout(self, x0, fe0, U, ts=TS):
        xi0 = np.concatenate((x0[XI_IDX], fe0))
        z = self.dic(xi0)[0]
        out = [x0.copy()]
        zpos = x0[5]
        vz_prev = x0[6]
        for u in U:
            z = self.A @ z + self.B @ u
            xi = self.C @ z + self.dic.mu
            vz = xi[5]
            zpos = zpos + ts * 0.5 * (vz_prev + vz)   # trapezoidal integration of v_z
            vz_prev = vz
            out.append(np.array([xi[0], xi[1], xi[2], xi[3], xi[4], zpos, vz]))
        return np.array(out)


@dataclass
class ResidualEDMD:
    nom: NominalModel
    dic: Dictionary
    W: np.ndarray
    d_max: np.ndarray
    p_nom: QuadParams

    @classmethod
    def fit(cls, data: Dataset, nom: NominalModel, p_nom, lam=1e-3, clip_pct=99.5, weighting="none", degree=2):
        """weighting "none" (default, the published E6/E7 fit) or "row": each regression row and its target are divided by
        the norm of the dictionary row (weighted least squares; pre-registered variant of K8)."""
        F, E = [], []
        for X, fe, U in zip(data.x, data.fe, data.u):
            for k in range(len(U)):
                x1n, _ = nom.step(X[k], fe[k], U[k])
                E.append(X[k + 1] - x1n)
                F.append(np.concatenate((X[k, XI_IDX], fe[k], U[k])))
        F, E = np.array(F), np.array(E)
        dic = Dictionary(F.mean(0), F.std(0) + 1e-9, degree)
        Psi = dic(F)
        if weighting == "row":
            nrm = np.linalg.norm(Psi, axis=1, keepdims=True)
            W = ridge(Psi / nrm, E / nrm, lam)
        else:
            W = ridge(Psi, E, lam)
        d_max = np.percentile(np.abs(E), clip_pct, axis=0)
        return cls(nom, dic, W, d_max, p_nom)

    def residual(self, x7, fe, u):
        d = (self.dic(np.concatenate((x7[XI_IDX], fe, u))) @ self.W)[0]
        return np.clip(d, -self.d_max, self.d_max)

    def rollout(self, x0, fe0, U):
        x, fe = x0.copy(), fe0.copy()
        out = [x.copy()]
        for u in U:
            d = self.residual(x, fe, u)
            x, fe = self.nom.step(x, fe, u)
            x = x + d
            out.append(x.copy())
        return np.array(out)


def nominal_rollout(nom: NominalModel, x0, fe0, U):
    x, fe = x0.copy(), fe0.copy()
    out = [x.copy()]
    for u in U:
        x, fe = nom.step(x, fe, u)
        out.append(x.copy())
    return np.array(out)


def multistep_errors(model_rollouts: dict, data: Dataset, horizons_steps, scale, starts_every=20):
    """Normalized RMSE (per state, divided by `scale`, averaged over states) vs horizon."""
    H = max(horizons_steps)
    errs = {k: [] for k in model_rollouts}
    for X, fe, U in zip(data.x, data.fe, data.u):
        for k0 in range(0, len(U) - H, starts_every):
            for name, roll in model_rollouts.items():
                pred = roll(X[k0], fe[k0], U[k0:k0 + H])
                e = (pred - X[k0:k0 + H + 1]) / scale
                errs[name].append(e[horizons_steps])
    out = {}
    for name, E in errs.items():
        E = np.array(E)                        # (n_starts, n_h, 7)
        with np.errstate(over="ignore", invalid="ignore"):
            out[name] = np.sqrt(np.nanmean(np.minimum(E ** 2, 1e12), axis=(0, 2)))
    return out


# ------------------------------------------------------------------ online adaptation (task K7)
class RLS:
    """Recursive least squares with exponential forgetting and ONE covariance shared by all outputs.

    W (n_feat x n_out) minimises sum_k lam^(N-k) |e_k - W' phi_k|^2. P is bounded: when trace(P) exceeds
    `trace_max_factor` times its initial trace it is rescaled (covariance wind-up guard, fixed a priori).
    """

    def __init__(self, W0, p0=1.0, lam=0.995, trace_max_factor=10.0):
        self.W = np.array(W0, float).copy()
        n = self.W.shape[0]
        self.P = p0 * np.eye(n)
        self.lam = lam
        self.tr0 = float(np.trace(self.P))
        self.tmax = trace_max_factor * self.tr0
        self.n_updates = 0
        self.n_rescaled = 0
        self.min_eig_violations = 0
        self.trace_log = []

    def update(self, phi, e):
        phi = np.asarray(phi, float).ravel()
        Pphi = self.P @ phi
        k = Pphi / (self.lam + phi @ Pphi)
        self.W = self.W + np.outer(k, e - phi @ self.W)
        self.P = (self.P - np.outer(k, Pphi)) / self.lam
        self.P = 0.5 * (self.P + self.P.T)
        tr = float(np.trace(self.P))
        if tr > self.tmax:
            self.P *= self.tmax / tr
            self.n_rescaled += 1
        self.n_updates += 1
        if self.n_updates % 50 == 0:
            if np.linalg.eigvalsh(self.P)[0] <= 0.0:
                self.min_eig_violations += 1
        self.trace_log.append(float(np.trace(self.P)))


class AdaptiveResidual:
    """Online-adapted residual EDMDc (K7): same 91-function dictionary and standardisation as the offline
    `ResidualEDMD`, weights adapted by RLS (one shared covariance).

    Causality: at call k the model receives (x_k, fe_k, u_{k-1}) as `residual(x7, fe, u)` does in `FailureMPC`.
    The pair (features at k-1, e_k = x_k - nominal prediction from k-1) is used to update W; only then the residual
    for step k is evaluated. x_k is never used to predict x_k. `u` of the current call is the command that was
    applied after the previous call, i.e. the regressor input u_{k-1}.
    """

    def __init__(self, base: ResidualEDMD, p0=1.0, lam=0.995, clip_scale=1.0, trace_max_factor=10.0):
        self.base = base
        self.nom, self.dic, self.d_max = base.nom, base.dic, base.d_max * clip_scale
        self.rls = RLS(base.W, p0=p0, lam=lam, trace_max_factor=trace_max_factor)
        self.prev = None
        self.n_clipped = 0
        self.n_calls = 0

    def reset(self):
        self.prev = None

    @property
    def W(self):
        return self.rls.W

    def residual(self, x7, fe, u):
        if self.prev is not None:
            x_prev, fe_prev = self.prev
            x1n, _ = self.nom.step(x_prev, fe_prev, u)
            e = x7 - x1n
            phi = self.dic(np.concatenate((x_prev[XI_IDX], fe_prev, u)))[0]
            self.rls.update(phi, e)
        self.prev = (np.array(x7, float), np.array(fe, float))
        d = (self.dic(np.concatenate((x7[XI_IDX], fe, u))) @ self.rls.W)[0]
        dc = np.clip(d, -self.d_max, self.d_max)
        self.n_calls += 1
        self.n_clipped += int(np.any(dc != d))
        return dc

    def rollout(self, x0, fe0, U):
        """Multi-step prediction with the CURRENT weights (frozen during the rollout)."""
        x, fe = x0.copy(), fe0.copy()
        out = [x.copy()]
        for u in U:
            d = np.clip((self.dic(np.concatenate((x[XI_IDX], fe, u))) @ self.rls.W)[0], -self.d_max, self.d_max)
            x, fe = self.nom.step(x, fe, u)
            x = x + d
            out.append(x.copy())
        return np.array(out)
