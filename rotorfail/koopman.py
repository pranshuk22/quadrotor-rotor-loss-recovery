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
    """[1, xi, all degree-2 monomials of xi], on standardized xi."""
    mu: np.ndarray
    sd: np.ndarray

    def __call__(self, xi):
        xi = np.atleast_2d(xi)
        y = (xi - self.mu) / self.sd
        n = y.shape[1]
        iu = np.triu_indices(n)
        quad = (y[:, :, None] * y[:, None, :])[:, iu[0], iu[1]]
        return np.hstack((np.ones((y.shape[0], 1)), y, quad))

    @property
    def size(self):
        n = len(self.mu)
        return 1 + n + n * (n + 1) // 2


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

    def __call__(self, t, x):
        if t >= self.t_next:
            self.exc = self.rng.uniform(-self.amp, self.amp, 3)
            self.t_next = t + self.hold
        u = self.lqr(t, x)
        u[:3] = np.clip(u[:3] + self.exc, self.p.f_min, self.p.f_max)
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


def generate(p_truth, p_nom, eq, n_episodes, T, seed, amp=0.35, ts=TS):
    """Closed-loop excited episodes on the truth plant, sampled at ts.

    p_truth: a QuadParams, or a callable rng -> QuadParams (new draw per episode).
    """
    rng = np.random.default_rng(seed)
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
        xs.append(X)
        fes.append(fe)
        us.append(U[:-1])
    return Dataset(xs, fes, us)


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

    def rollout(self, x0, fe0, U):
        xi0 = np.concatenate((x0[XI_IDX], fe0))
        z = self.dic(xi0)[0]
        out = [x0.copy()]
        zpos = x0[5]
        for u in U:
            z = self.A @ z + self.B @ u
            xi = self.C @ z + self.dic.mu
            vz = xi[5]
            zpos = zpos + TS * vz
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
    def fit(cls, data: Dataset, nom: NominalModel, p_nom, lam=1e-3, clip_pct=99.5):
        F, E = [], []
        for X, fe, U in zip(data.x, data.fe, data.u):
            for k in range(len(U)):
                x1n, _ = nom.step(X[k], fe[k], U[k])
                E.append(X[k + 1] - x1n)
                F.append(np.concatenate((X[k, XI_IDX], fe[k], U[k])))
        F, E = np.array(F), np.array(E)
        dic = Dictionary(F.mean(0), F.std(0) + 1e-9)
        W = ridge(dic(F), E, lam)
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
