"""Trim points: healthy hover and the relaxed hover with rotor 4 failed.

Relaxed hover (Mueller & D'Andrea 2014, Sec. III-A): rotor 4 lost, f1 = f3,
f2 = rho * f1. The body rate w_bar is constant in the body frame, the reduced
attitude n_bar = w_bar / |w_bar| is parallel to it, and f_Sigma * n_z = m g.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq, fsolve

from .dynamics import body_rate_derivative
from .params import G, QuadParams

FAILED_ROTOR = 3  # zero-based index: rotor 4


@dataclass
class RelaxedHover:
    rho: float
    f: np.ndarray          # (4,) trim thrusts, f[3] = 0
    w: np.ndarray          # (3,) body rates (p, q, r)
    n: np.ndarray          # (3,) reduced attitude (inertial up in body axes)
    prop_speeds: np.ndarray

    @property
    def f_sum(self) -> float:
        return float(np.sum(self.f))

    @property
    def orbit_radius(self) -> float:
        """Radius of the horizontal circle the centre of mass follows, eq. (20)."""
        wn = np.linalg.norm(self.w)
        nz = self.n[2]
        return float(np.sqrt(1 - nz ** 2) / nz * G / wn ** 2)


def _rates_for_thrust(f: np.ndarray, p: QuadParams, w0: np.ndarray) -> np.ndarray:
    """Constant body rates for constant thrusts f with f1 = f3, f4 = 0.

    Closed form of eqs. (12)-(14) with the rate derivatives set to zero:
      p = 0,  r = kappa_tau (f1 - f2 + f3) / gamma,
      q = l f2 / ((Izz_T - Ixx_T) r + Izz_P w_Sigma).
    Falls back to a numerical solve for other thrust patterns.
    """
    if np.isclose(f[0], f[2]) and f[3] == 0.0 and p.thrust_loss == 0.0:
        r = p.kappa_tau * (f[0] - f[1] + f[2]) / p.gamma
        w_sigma = np.sum(p.prop_speeds(f))
        q = p.l * f[1] / ((p.Izz_T - p.Ixx_T) * r + p.Izz_P * w_sigma)
        return np.array([0.0, q, r])
    sol, info, ier, msg = fsolve(lambda w: body_rate_derivative(w, f, p), w0,
                                 full_output=True, xtol=1e-13)
    if ier != 1:
        raise RuntimeError(f"body-rate equilibrium not found: {msg}")
    return sol


def relaxed_hover(p: QuadParams, rho: float = 0.5, w_guess=None) -> RelaxedHover:
    """Solve the 8 equilibrium equations by a 1-D root find on f1."""

    def thrusts(f1):
        return np.array([f1, rho * f1, f1, 0.0])

    w_guess = np.array([0.0, 5.0, 19.0]) if w_guess is None else np.asarray(w_guess, float)

    def residual(f1):
        f = thrusts(f1)
        w = _rates_for_thrust(f, p, w_guess)
        n = w / np.linalg.norm(w) * np.sign(w[2])
        return np.sum(f) * p.thrust_efficiency(w) * n[2] - p.weight

    f_lo = p.weight / (2 + rho)  # lower bound: n_z = 1
    f1 = brentq(residual, f_lo * (1 + 1e-9), 6 * f_lo, xtol=1e-14)
    f = thrusts(f1)
    w = _rates_for_thrust(f, p, w_guess)
    n = w / np.linalg.norm(w) * np.sign(w[2])
    return RelaxedHover(rho=rho, f=f, w=w, n=n, prop_speeds=p.prop_speeds(f))


def healthy_hover_thrust(p: QuadParams) -> np.ndarray:
    return np.full(4, p.weight / 4.0)


@dataclass
class HoverSolution:
    f: np.ndarray            # (4,) thrusts
    w: np.ndarray            # (3,) body rates
    n: np.ndarray            # (3,) reduced attitude
    prop_speeds: np.ndarray  # (4,) signed propeller speeds


def two_rotor_hover(p: QuadParams) -> HoverSolution:
    """Rotors 2 and 4 lost, f1 = f3 (Mueller & D'Andrea 2014, eqs. 22-25)."""
    f1 = p.weight / 2.0
    f = np.array([f1, 0.0, f1, 0.0])
    w = _rates_for_thrust(f, p, np.array([0.0, 0.0, 30.0]))
    return HoverSolution(f, w, np.array([0.0, 0.0, 1.0]), p.prop_speeds(f))


def single_rotor_hover(p: QuadParams, w_guess=(10.0, 0.0, 30.0)) -> HoverSolution:
    """Only rotor 1 left (Mueller & D'Andrea 2014, Sec. III-C): solve f1 and w jointly."""

    def rates(f1, guess):
        f = np.array([f1, 0.0, 0.0, 0.0])
        sol, info, ier, msg = fsolve(lambda w: body_rate_derivative(w, f, p), guess,
                                     full_output=True, xtol=1e-13)
        if ier != 1:
            raise RuntimeError(msg)
        return sol

    guess = np.asarray(w_guess, float)

    def residual(f1):
        w = rates(f1, guess)
        n = w / np.linalg.norm(w) * np.sign(w[2])
        return f1 * n[2] - p.weight

    f1 = brentq(residual, p.weight * (1 + 1e-6), 3 * p.weight, xtol=1e-13)
    w = rates(f1, guess)
    n = w / np.linalg.norm(w) * np.sign(w[2])
    f = np.array([f1, 0.0, 0.0, 0.0])
    return HoverSolution(f, w, n, p.prop_speeds(f))


def fig3_minima(p: QuadParams, lo: float = 0.3, hi: float = 1.0) -> dict:
    """Minimizers over rho of |w| and of f1 (Mueller & D'Andrea 2014, Fig. 3 text)."""
    from scipy.optimize import minimize_scalar
    opt = dict(bounds=(lo, hi), method="bounded", options={"xatol": 1e-6})
    rw = minimize_scalar(lambda r: np.linalg.norm(relaxed_hover(p, r).w), **opt)
    rf = minimize_scalar(lambda r: relaxed_hover(p, r).f[0], **opt)
    return {"w_min": float(rw.fun), "rho_w": float(rw.x), "f1_min": float(rf.fun), "rho_f": float(rf.x)}
