"""Reachable sets of the failure chain and ellipsoid containment (task D6).

Chain (plan section 4):  X0  --[undetected phase: healthy LQR, rotor 4 at 0 N]-->  --[open-loop spin-up
until |w| > w_sw]-->  hand-over set S(tau)  --[capture controller]-->  relaxed hover.

Everything here is a deviation from the relaxed hover in the 10 capture coordinates
(p, q, r, n_x, n_y, z, v_z, f1, f2, f3), the ordering of `rotorfail.lpv`.

Pieces
  * `run_chain`            : the nonlinear chain with the same controllers, sampling and switching rules as E4
                             (DelaySupervisor, SpinUpThenLQR), stopped at the hand-over; returns the hand-over
                             state at the first controller sample and the state interpolated to the exact
                             crossing of |w| = w_sw (a smooth function of the start).
  * `chain_jacobian`       : central-difference Jacobian of the interpolated hand-over deviation with respect to
                             the 9 pre-failure variables (v, Euler angles, w), i.e. the variational method of
                             the plan along the nonlinear nominal trajectory.
  * `UndetectedLTI`        : the proposal's method for the undetected phase: affine LTI model at the hover,
                             exact ellipsoid propagation (centre via the augmented matrix exponential).
  * `command_ranges`       : support-function range of each rotor command over the propagated set.
  * `max_beta`, `max_beta_exact`, `centre_scaling`: ellipsoid containment by the S-procedure LMI (Boyd et al.
                             1994, 3.7) and an independent trust-region evaluation.
"""
from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq
from scipy.stats import chi2

from .control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR
from .dynamics import E3, IDX_Q, make_state, quat_to_rot, rk4_step
from .equilibrium import relaxed_hover
from .models import healthy_linear
from .params import QuadParams

SIGMA_V, SIGMA_EUL, SIGMA_W = 0.3, np.deg2rad(3.0), 0.3
X0_SIGMA = np.array([SIGMA_V] * 3 + [SIGMA_EUL] * 3 + [SIGMA_W] * 3)
X0_NAMES = ["v_x", "v_y", "v_z", "phi", "theta", "psi", "p", "q", "r"]
CHI2_99 = float(chi2.ppf(0.99, 9))
X0_RADIUS = float(np.sqrt(CHI2_99))          # 99 % ellipsoid in units of sigma


def x0_state(u, p=None):
    """Full 17-state initial state for pre-failure deviations u (9 entries, physical units)."""
    return make_state(v=u[0:3], euler=u[3:6], w=u[6:9], p=p)


def capture_dev(x, eq):
    """10 capture coordinates of a full simulator state."""
    n = quat_to_rot(x[IDX_Q]).T @ E3
    return np.concatenate((x[10:13] - eq.w, n[:2] - eq.n[:2], [x[2], x[5]], x[13:16] - eq.f[:3]))


@dataclass
class ChainSpec:
    p: QuadParams
    tau: float = 0.0
    w_sw: float = 10.0
    f_spin: float = 2.95
    alpha: float = 1.0                 # healthy-LQR aggressiveness
    dt: float = 1e-3
    ctrl_period: float = 1e-3
    t_max: float = 3.0


class _Probe(SpinUpThenLQR):
    ho = None

    def __call__(self, t, x):
        was = self.spinning_up
        u = super().__call__(t, x)
        if was and not self.spinning_up:
            self.ho = (t, x.copy())
        return u


def run_chain(spec: ChainSpec, u):
    """Simulate X0 start u through the undetected phase and the spin-up until the hand-over.

    Returns dict(handed, t_h, sample, dev (state at the first controller sample after the crossing),
    dev_interp (state interpolated to |w| = w_sw between simulation steps), x_h).
    """
    p, eq = spec.p, relaxed_hover(spec.p)
    probe = _Probe(p, FailureLQR(p, eq), w_switch=spec.w_sw, f_spin=spec.f_spin)
    sup = DelaySupervisor(HealthyLQR(p, alpha=spec.alpha), probe, t_fail=0.0, tau=spec.tau)
    x = x0_state(u, p)
    ctrl_every = max(1, int(round(spec.ctrl_period / spec.dt)))
    alive = np.array([True, True, True, False])
    cmd = np.zeros(4)
    prev = x.copy()
    n_steps = int(round(spec.t_max / spec.dt))
    for k in range(n_steps + 1):
        t = k * spec.dt
        if k % ctrl_every == 0:
            cmd = sup(t, x)
            if probe.ho is not None:
                break
        prev = x.copy()
        x = rk4_step(x, cmd, spec.dt, p, alive, True)
    if probe.ho is None:
        return dict(handed=False)
    t_h, x_h = probe.ho
    # smooth reference: interpolate the last simulation step before the controller sample at which the
    # rate norm crosses w_sw (the crossing happens within the last ctrl_every steps)
    # walk back to the step interval containing the crossing
    w_prev, w_now = np.linalg.norm(prev[10:13]), np.linalg.norm(x_h[10:13])
    if w_now > w_prev and w_prev <= spec.w_sw <= w_now and w_now - w_prev > 1e-12:
        s = (spec.w_sw - w_prev) / (w_now - w_prev)
        x_i = (1 - s) * prev + s * x_h
        x_i[IDX_Q] /= np.linalg.norm(x_i[IDX_Q])
    else:
        x_i = x_h
    return dict(handed=True, t_h=float(t_h), sample=int(round(t_h / spec.dt)), x_h=x_h,
                dev=capture_dev(x_h, eq), dev_interp=capture_dev(x_i, eq))


def chain_jacobian(spec: ChainSpec, eps_scale=1e-3):
    """(centre, J, info): interpolated hand-over deviation at u = 0 and its 10 x 9 Jacobian with respect to u
    (physical units of u). J[:, i] is the central difference in coordinate i with step eps_scale * sigma_i."""
    nom = run_chain(spec, np.zeros(9))
    if not nom["handed"]:
        return None, None, dict(handed=False)
    J = np.zeros((10, 9))
    for i in range(9):
        h = eps_scale * X0_SIGMA[i]
        e = np.zeros(9)
        e[i] = h
        a, b = run_chain(spec, e), run_chain(spec, -e)
        if not (a["handed"] and b["handed"]):
            return None, None, dict(handed=False)
        J[:, i] = (a["dev_interp"] - b["dev_interp"]) / (2 * h)
    return nom["dev_interp"], J, dict(handed=True, t_h=nom["t_h"], dev_sample=nom["dev"])


def hand_over_set(c, J, gamma):
    """S = {c + L w : |w| <= 1}, L = J diag(sigma) * gamma * X0_RADIUS (10 x 9)."""
    return c, J @ np.diag(X0_SIGMA) * gamma * X0_RADIUS


def sample_x0(gamma, n, seed):
    """n starts uniform in the gamma-scaled 99 % ellipsoid of X0 (physical units)."""
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(n, 9))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    r = (rng.uniform(size=(n, 1)) ** (1 / 9)) * gamma * X0_RADIUS
    return d * r * X0_SIGMA


def coverage(c, L, devs, rcond=1e-6):
    """Normalised excess of each deviation with respect to the set c + L ball: min t with dev in c + t L ball
    (via the pseudo-inverse with a relative rank tolerance `rcond`: the map has exactly zero columns for the pre-failure
    variables the capture coordinates do not depend on, horizontal velocity and yaw angle) and the residual orthogonal to
    range(L) (the set is rank deficient)."""
    Lp = np.linalg.pinv(L, rcond=rcond)
    out = []
    for d in devs:
        r = d - c
        w = Lp @ r
        out.append((float(np.linalg.norm(w)), float(np.linalg.norm(r - L @ w))))
    return np.array(out)


# ---------------------------------------------------------------- containment
def centre_scaling(P2, c):
    """alpha such that alpha * c is on the boundary of {x : x' P2 x <= 1} (>= 1 means c inside)."""
    v = float(c @ P2 @ c)
    return np.inf if v == 0 else 1.0 / np.sqrt(v)


def max_beta(c, L, Q2, solver="CLARABEL"):
    """Largest beta with c + beta L ball inside {x : x' Q2^-1 x <= 1}, by the S-procedure LMI
    [[1 - lam, 0, c'], [0, lam I, beta L'], [c, beta L, Q2]] >= 0 (maximise beta). None if the centre is outside."""
    import cvxpy as cp
    n, m = L.shape
    P2 = np.linalg.inv(Q2)
    if float(c @ P2 @ c) > 1.0:
        return None
    lam, beta = cp.Variable(), cp.Variable()
    M = cp.bmat([[cp.reshape(1 - lam, (1, 1), order="C"), np.zeros((1, m)), c.reshape(1, n)],
                 [np.zeros((m, 1)), lam * np.eye(m), beta * L.T],
                 [c.reshape(n, 1), beta * L, Q2]])
    prob = cp.Problem(cp.Maximize(beta), [0.5 * (M + M.T) >> 0, lam >= 0, beta >= 0])
    try:
        prob.solve(solver=solver)
    except cp.error.SolverError:
        prob.solve(solver="SCS", eps=1e-9, max_iters=100000)
    return None if beta.value is None else float(beta.value)


def max_beta_exact(c, L, Q2):
    """Independent evaluation by the trust-region problem: max over |u| <= 1 of |P^(1/2)(c + beta L u)|^2,
    solved exactly by an eigen-decomposition and a one-dimensional root search; bisection on beta."""
    P2 = np.linalg.inv(Q2)
    if float(c @ P2 @ c) > 1.0:
        return None

    def worst(beta):
        A = beta * beta * (L.T @ P2 @ L)
        b = beta * (L.T @ P2 @ c)
        w, V = np.linalg.eigh(A)
        bt = V.T @ b
        # maximise u' A u + 2 b' u over |u| <= 1:  stationary u = (mu I - A)^-1 b with mu >= w_max
        def g(mu):
            return np.sum((bt / (mu - w)) ** 2) - 1.0
        wmax = w[-1]
        if np.all(np.abs(bt[w > wmax - 1e-12]) < 1e-14):
            # hard case: take the boundary value along the top eigenvector
            u = V[:, -1]
            return max(float(c @ P2 @ c + 2 * b @ u + u @ A @ u), float(c @ P2 @ c + 2 * b @ (-u) + u @ A @ u))
        lo = wmax + 1e-12 + 1e-12 * abs(wmax)
        hi = wmax + np.linalg.norm(bt) + 1.0
        if g(lo) < 0:
            mu = lo
        else:
            mu = brentq(g, lo, hi, xtol=1e-14, rtol=1e-14)
        u = V @ (bt / (mu - w))
        u = u / max(1.0, np.linalg.norm(u))
        return float(c @ P2 @ c + 2 * b @ u + u @ A @ u)

    lo, hi = 0.0, 1.0
    while worst(hi) <= 1.0 and hi < 1e6:
        lo, hi = hi, hi * 2
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if worst(mid) <= 1.0 else (lo, mid)
    return lo


# ---------------------------------------------------------------- undetected phase: affine LTI (proposal)
class UndetectedLTI:
    """Affine LTI model of the undetected phase from the healthy hover.

    State z = [e12 (healthy Euler model deviation), df1, df2, df3] (motor-lag thrust deviations of the three
    working rotors); rotor 4 produces 0 N, i.e. a constant thrust deviation of -m g / 4 enters the 12-state
    model: affine term. The healthy LQR (static gain on e12, commands clipped in the nonlinear plant, not here) is
    sampled at the controller period and held (ZOH); the model is discretised exactly at that period.
    """

    def __init__(self, p: QuadParams, alpha=1.0, ctrl_period=1e-3):
        self.p, self.T = p, ctrl_period
        self.lin = healthy_linear(p)
        self.ctrl = HealthyLQR(p, alpha=alpha)
        A, B = self.lin.A, self.lin.B
        K = self.ctrl.K
        sig = p.sigma_mot
        n = 12
        # continuous: e' = A e + B[:, :3] df + B[:, 3] (-mg/4) ; df' = (du - df)/sig, du = -K[:3] e (held)
        Ac = np.zeros((15, 15))
        Ac[:n, :n] = A
        Ac[:n, n:] = B[:, :3]
        Ac[n:, n:] = -np.eye(3) / sig
        Bc = np.zeros((15, 3))
        Bc[n:, :] = np.eye(3) / sig
        dc = np.zeros(15)
        dc[:n] = B[:, 3] * (-p.weight / 4.0)
        M = np.zeros((15 + 3 + 1, 15 + 3 + 1))
        M[:15, :15] = Ac
        M[:15, 15:18] = Bc
        M[:15, 18] = dc
        E = expm(M * ctrl_period)
        self.Phi, self.Gam, self.dd = E[:15, :15], E[:15, 15:18], E[:15, 18]
        self.Kc = np.hstack((K[:3, :], np.zeros((3, 3))))                # u_dev = -Kc z
        self.Acl = self.Phi - self.Gam @ self.Kc

    def propagate(self, steps, z0=None, S0=None):
        """After `steps` controller samples: centre c_k, transition matrix Phi_k (z_k = Phi_k z_0 + c_k)."""
        z = np.zeros(15) if z0 is None else z0
        Pk = np.eye(15)
        cs, Ps = [z.copy()], [Pk.copy()]
        for _ in range(steps):
            z = self.Acl @ z + self.dd
            Pk = self.Acl @ Pk
            cs.append(z.copy())
            Ps.append(Pk.copy())
        return cs, Ps


def command_ranges(lti: UndetectedLTI, steps, S0):
    """Support-function range of the unclipped rotor commands over the propagated ellipsoid (shape S0 = L0 L0',
    on the 15-dim state): u_i = u_trim_i - k_i' z, range = centre -+ sqrt(k_i' S_k k_i). Classify each rotor and time
    as 'unsat', 'sat' (always outside [f_min, f_max]) or 'ambiguous'."""
    cs, Ps = lti.propagate(steps)
    p = lti.p
    u_trim = lti.lin.u_trim[:3]
    out = []
    for c, Pk in zip(cs, Ps):
        Sk = Pk @ S0 @ Pk.T
        row = []
        for i in range(3):
            k = lti.Kc[i]
            mid = u_trim[i] - k @ c
            half = float(np.sqrt(max(k @ Sk @ k, 0.0)))
            lo, hi = mid - half, mid + half
            if lo >= p.f_min and hi <= p.f_max:
                row.append("unsat")
            elif hi < p.f_min or lo > p.f_max:
                row.append("sat")
            else:
                row.append("ambiguous")
        out.append(row)
    return out
