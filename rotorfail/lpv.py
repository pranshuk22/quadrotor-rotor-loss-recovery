"""Quasi-LPV model of the failed vehicle with the yaw rate r and the vertical tilt component n_z as
scheduling parameters (task D3).

States (the 10-state ordering of the failure LQR, `add_motor_lag(failed_linear(...))`):
    e = [dp, dq, dr, dn_x, dn_y, dz, dv_z, df1, df2, df3]      deviations from the relaxed hover
Input: deviation of the commanded thrusts of rotors 1 to 3 from the trim, du; motors: df' = (du - df)/sigma.

Exact structure (I_xx = I_yy, rotor 4 lost, h = I_T w + I_zz,P w_sum e3):
    I_xx,B p' = l f2 - (I_zz,T - I_xx,T) q r - I_zz,P w_sum q
    I_xx,B q' = l (f3 - f1) + (I_zz,T - I_xx,T) p r + I_zz,P w_sum p
    I_zz,B r' = kappa_tau (f1 - f2 + f3) - gamma r                (no coupling: yaw is decoupled)
    n_x' = -(q n_z - r n_y),   n_y' = -(r n_x - p n_z),   n_z = sqrt(1 - n_x^2 - n_y^2)
    z' = v_z,   v_z' = (f1 + f2 + f3) n_z / m - g

Every product a b satisfies a b - abar bbar = a (b - bbar) + bbar (a - abar) exactly. With a = r (and
a = n_z) this gives  e' = A(rho) e + B du + R(e)  with A affine in rho = (r, n_z) (both are states):
    A(rho) = A0 + (r) Ar + (n_z) An,
and the remainder R(e) contains only (i) the dependence of w_sum on sqrt(f) and (ii) the dependence
of n_z on (n_x, n_y), each linearised at the trim:
    dw_sum ~ sum_i c_i df_i,  c_i = s_i / (2 sqrt(kappa_f fbar_i))          (s_i: propeller sign)
    dn_z   ~ -(nbar_x dn_x + nbar_y dn_y) / nbar_z
Remainder, with a = I_zz,P / I_xx,B and rem_nz = dn_z - dn_z(lin):
    R_p = -a [ w_sum q - wbar qbar - wbar dq - qbar sum c_i df_i ]
    R_q = +a [ w_sum p - wbar pbar - wbar dp - pbar sum c_i df_i ]
    R_nx = -qbar rem_nz,  R_ny = +pbar rem_nz  (pbar = 0 at the relaxed hover),  R_vz = (sum fbar) rem_nz / m.
The model is for the NOMINAL plant (thrust_loss = 0). With thrust loss the yaw decoupling is lost and
|w|^2 terms appear; this is not included.

Scheduling ranges (fixed from the hand-over diagnostic E9a, before any certificate is computed)
  E9a hand-over deviations of the published strategy, tau <= 60 ms, both spin-up thrusts, exact and
  Monte Carlo starts: r - rbar in [-10.62, -8.81] rad/s (all tau up to 130 ms: [-10.91, -8.81]).
  R_RANGE : r in [rbar - 11, rbar + 11] = [7.81, 29.81] rad/s. The half-width 11 contains the whole
            E9a range with a margin; the range is symmetric because an ellipsoid centred at the trim has
            symmetric extent in r (the self-consistency constraint of D4).
  NZ_RANGE: n_z in [0.2, 1.0]. E9a hand-over n_z at tau = 0 (exact and Monte Carlo) is at least 0.65, and
            0.25 at the exact-hover tau = 30 ms; 0.2 leaves a margin of 0.05 at that case. States with
            n_z below 0.2 are not covered (and the vehicle is inverted at hand-over for tau >= 45 ms).
  The frozen-parameter stability of the failure LQR on this box is checked in `tests/test_lpv.py` and in
  the table of E9b.
"""
from dataclasses import dataclass

import numpy as np

from .dynamics import body_rate_derivative
from .equilibrium import RelaxedHover
from .models import add_motor_lag, failed_f, failed_linear
from .params import G, QuadParams

STATES = ["p", "q", "r", "n_x", "n_y", "z", "v_z", "f1", "f2", "f3"]
R_HALF = 11.0
NZ_RANGE = (0.2, 1.0)


@dataclass
class QuasiLPV:
    p: QuadParams
    eq: RelaxedHover

    def __post_init__(self):
        p, eq = self.p, self.eq
        self.sigma = p.sigma_mot
        self.xbar = np.array([eq.w[0], eq.w[1], eq.w[2], eq.n[0], eq.n[1], 0.0, 0.0, *eq.f[:3]])
        self.nz_bar = float(eq.n[2])
        self.r_bar = float(eq.w[2])
        self.fbar = eq.f[:3].copy()
        self.signs = np.array(p.prop_sign[:3])
        self.c = self.signs / (2.0 * np.sqrt(p.kappa_f * self.fbar))        # d w_sum / d f_i at the trim
        self.wsum_bar = float(np.sum(self.signs * np.sqrt(self.fbar / p.kappa_f)))
        Ixx, Izz = p.Ixx_B, p.Izz_B
        self.kxz = (p.Izz_T - p.Ixx_T) / Ixx
        self.a = p.Izz_P / Ixx
        self._build_affine()
        self.B = np.zeros((10, 3))
        self.B[7:, :] = np.eye(3) / self.sigma

    # ----------------------------------------------------------- affine matrices
    def _A(self, r, nz):
        p, eq = self.p, self.eq
        Ixx, Izz = p.Ixx_B, p.Izz_B
        pb, qb = eq.w[0], eq.w[1]
        nxb, nyb = eq.n[0], eq.n[1]
        nzb = self.nz_bar
        kxz, a, c = self.kxz, self.a, self.c
        wb = self.wsum_bar
        A = np.zeros((10, 10))
        # p' : [l f2 - (Izz_T-Ixx_T) q r - Izz_P w_sum q] / Ixx
        A[0, 1] = -kxz * r - a * wb
        A[0, 2] = -kxz * qb
        A[0, 7:10] = -a * qb * c
        A[0, 8] += p.l / Ixx
        # q' : [l (f3 - f1) + (Izz_T-Ixx_T) p r + Izz_P w_sum p] / Ixx
        A[1, 0] = kxz * r + a * wb
        A[1, 2] = kxz * pb
        A[1, 7:10] = a * pb * c
        A[1, 7] += -p.l / Ixx
        A[1, 9] += p.l / Ixx
        # r' : decoupled
        A[2, 2] = -p.gamma / Izz
        A[2, 7:10] = p.kappa_tau / Izz * np.array([1.0, -1.0, 1.0])
        # n_x' = -(q n_z - r n_y) ; n_y' = -(r n_x - p n_z), dn_z lin = -(nxb dn_x + nyb dn_y)/nzb
        gz = np.array([-nxb / nzb, -nyb / nzb])                 # d n_z / d(n_x, n_y)
        A[3, 1] = -nz
        A[3, 2] = nyb
        A[3, 4] = r - qb * gz[1]
        A[3, 3] = -qb * gz[0]
        A[4, 0] = nz
        A[4, 3] = -r + pb * gz[0]
        A[4, 4] = pb * gz[1]
        A[4, 2] += -nxb
        # z' = v_z ; v_z' = (sum f) n_z / m - g
        A[5, 6] = 1.0
        A[6, 3] = self.fbar.sum() / p.m * gz[0]
        A[6, 4] = self.fbar.sum() / p.m * gz[1]
        A[6, 7:10] = nz / p.m
        # motors: df' = (du - df)/sigma
        A[7:, 7:] = -np.eye(3) / self.sigma
        return A

    def _build_affine(self):
        r0, n0 = 0.0, 0.0
        self.A0 = self._A(r0, n0)
        self.Ar = self._A(1.0, n0) - self.A0
        self.An = self._A(r0, 1.0) - self.A0

    def A(self, r, nz):
        """A(rho) with rho = (r, n_z) (absolute values of the scheduling states)."""
        return self.A0 + r * self.Ar + nz * self.An

    def rho(self, e):
        """Scheduling parameters from a deviation e."""
        nx, ny = self.xbar[3] + e[3], self.xbar[4] + e[4]
        return self.xbar[2] + e[2], float(np.sqrt(max(1.0 - nx * nx - ny * ny, 0.0)))

    def vertices(self, r_range=None, nz_range=NZ_RANGE):
        r_range = r_range or (self.r_bar - R_HALF, self.r_bar + R_HALF)
        return [self.A(r, nz) for r in r_range for nz in nz_range]

    # ----------------------------------------------------------- nonlinear reference and remainder
    def f_nonlinear(self, e, du):
        """Exact nonlinear deviation dynamics e' = f(xbar + e, ubar + du) - f(xbar, ubar)."""
        x = self.xbar + e
        s = x[:7].copy()
        f = x[7:]
        out = failed_f(s, f, self.p) - failed_f(self.xbar[:7], self.fbar, self.p)
        mot = (du - e[7:]) / self.sigma
        return np.concatenate((out, mot))

    def remainder(self, e):
        """R(e) = f_nonlinear(e, du) - A(rho(e)) e - B du  (independent of du), from the closed form."""
        p = self.p
        pb, qb = self.eq.w[0], self.eq.w[1]
        nx, ny = self.xbar[3] + e[3], self.xbar[4] + e[4]
        nz = float(np.sqrt(max(1.0 - nx * nx - ny * ny, 1e-12)))
        f = self.fbar + e[7:]
        wsum = float(np.sum(p.prop_speeds(np.concatenate((f, [0.0])))))
        dw_lin = float(self.c @ e[7:])
        a, wb = self.a, self.wsum_bar
        q, pp = qb + e[1], pb + e[0]
        R = np.zeros(10)
        R[0] = -a * (wsum * q - wb * qb - wb * e[1] - qb * dw_lin)
        R[1] = a * (wsum * pp - wb * pb - wb * e[0] - pb * dw_lin)
        dnz = nz - self.nz_bar
        dnz_lin = -(self.xbar[3] * e[3] + self.xbar[4] * e[4]) / self.nz_bar
        rem = dnz - dnz_lin
        R[3] = -qb * rem
        R[4] = pb * rem
        R[6] = self.fbar.sum() / p.m * rem
        return R

    def remainder_numeric(self, e):
        """R(e) from the difference of the exact model and the affine part (for tests)."""
        r, nz = self.rho(e)
        return self.f_nonlinear(e, np.zeros(3)) - self.A(r, nz) @ e


def closed_loop_vertices(lpv: QuasiLPV, K, r_range=None, nz_range=NZ_RANGE):
    """Closed-loop matrices A_i - B K at the vertices of the scheduling box."""
    return [A - lpv.B @ K for A in lpv.vertices(r_range, nz_range)]


def frozen_check(lpv: QuasiLPV, K, r_grid, nz_grid):
    """Largest real part of the closed-loop eigenvalues of A(r, n_z) - B K over a grid."""
    worst = -np.inf
    for r in r_grid:
        for nz in nz_grid:
            worst = max(worst, float(np.max(np.linalg.eigvals(lpv.A(r, nz) - lpv.B @ K).real)))
    return worst


def check_against_linearisation(lpv: QuasiLPV):
    """Max abs difference between A(rbar, nz_bar) and the numerical Jacobian of the 10-state model."""
    m = add_motor_lag(failed_linear(lpv.p, lpv.eq), lpv.p.sigma_mot)
    return float(np.max(np.abs(lpv.A(lpv.r_bar, lpv.nz_bar) - m.A)))


def remainder_sup(lpv: QuasiLPV, half, scale=None, n=20000, seed=0, local=15, nz_min=0.0):
    """Numerical bound on the remainder over the box |e_i| <= half_i, restricted to n_z >= nz_min.

    Returns (sup |R_i| per component, sup |R_i| / ||S^-1 e|| per component) where S = diag(scale)
    (default: half). Dense random sampling plus a bounded local optimiser started from the worst
    samples; this is a numerical estimate, not a proof.
    """
    from scipy.optimize import minimize
    half = np.asarray(half, float)
    S = half if scale is None else np.asarray(scale, float)
    rng = np.random.default_rng(seed)
    E = rng.uniform(-1, 1, (n, 10)) * half
    E = np.vstack((E, np.sign(rng.uniform(-1, 1, (n // 2, 10))) * half))          # vertices of the box
    lim = min(0.999, 1.0 - nz_min ** 2)
    ok = (lpv.xbar[3] + E[:, 3]) ** 2 + (lpv.xbar[4] + E[:, 4]) ** 2 < lim
    E = E[ok]
    Rs = np.array([lpv.remainder(e) for e in E])
    ratio = np.abs(Rs) / np.maximum(np.linalg.norm(E / S, axis=1), 1e-12)[:, None]
    sup_abs, sup_gain = np.abs(Rs).max(axis=0), ratio.max(axis=0)
    for i in range(10):
        if sup_abs[i] == 0.0 and sup_gain[i] == 0.0:
            continue
        for key, arr in (("abs", np.abs(Rs[:, i])), ("gain", ratio[:, i])):
            for k in np.argsort(-arr)[:local]:
                def obj(x, i=i, key=key):
                    v = abs(lpv.remainder(x)[i])
                    return -(v if key == "abs" else v / max(np.linalg.norm(x / S), 1e-12))
                res = minimize(obj, E[k], bounds=list(zip(-half, half)), method="L-BFGS-B")
                x = res.x
                if (lpv.xbar[3] + x[3]) ** 2 + (lpv.xbar[4] + x[4]) ** 2 >= lim:
                    continue
                if key == "abs":
                    sup_abs[i] = max(sup_abs[i], -res.fun)
                else:
                    sup_gain[i] = max(sup_gain[i], -res.fun)
    return sup_abs, sup_gain
