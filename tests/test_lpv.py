"""Checks for the quasi-LPV model (D3).

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.control import FailureLQR  # noqa: E402
from rotorfail.dynamics import body_rate_derivative  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.lpv import (NZ_RANGE, R_HALF, QuasiLPV, check_against_linearisation, frozen_check,  # noqa: E402
                           remainder_sup)
from rotorfail.params import DEFAULT as P  # noqa: E402

EQ = relaxed_hover(P)


@pytest.fixture(scope="module")
def lpv():
    return QuasiLPV(P, EQ)


def _rand_state(rng, w_scale=8.0, n_scale=0.4, f_scale=0.8):
    w = rng.normal(0, w_scale, 3)
    w[2] += EQ.w[2]
    nxy = EQ.n[:2] + rng.normal(0, n_scale, 2)
    f = np.clip(rng.normal(EQ.f[:3], f_scale), 0.0, 3.8)
    return w, nxy, f


def test_yaw_rate_is_decoupled_on_the_nominal_plant():
    rng = np.random.default_rng(1)
    worst = 0.0
    for _ in range(200):
        w = rng.normal(0, 10, 3)
        f = np.append(rng.uniform(0.2, 3.5, 3), 0.0)
        r_dot = (P.kappa_tau * (f[0] - f[1] + f[2] - f[3]) - P.gamma * w[2]) / P.Izz_B
        worst = max(worst, abs(body_rate_derivative(w, f, P)[2] - r_dot))
    assert worst < 1e-10


def test_exact_rotational_equations_match_the_simulator():
    """The component form in the module docstring equals body_rate_derivative (random states)."""
    rng = np.random.default_rng(2)
    for _ in range(200):
        w = rng.normal(0, 10, 3)
        f = np.append(rng.uniform(0.2, 3.5, 3), 0.0)
        ws = float(np.sum(P.prop_speeds(f)))
        p, q, r = w
        pd = (P.l * (f[1] - f[3]) - (P.Izz_T - P.Ixx_T) * q * r - P.Izz_P * ws * q) / P.Ixx_B
        qd = (P.l * (f[2] - f[0]) + (P.Izz_T - P.Ixx_T) * p * r + P.Izz_P * ws * p) / P.Ixx_B
        assert np.allclose(body_rate_derivative(w, f, P)[:2], [pd, qd], atol=1e-10)


def test_affine_in_the_scheduling_parameters(lpv):
    r, nz = 13.0, 0.7
    assert np.allclose(lpv.A(r, nz), lpv.A0 + r * lpv.Ar + nz * lpv.An)
    # the two non-constant parts are the only parameter dependence
    assert np.allclose(lpv.A(2 * r, nz) - lpv.A(r, nz), r * lpv.Ar)


def test_matches_the_numerical_jacobian_at_the_trim(lpv):
    assert check_against_linearisation(lpv) < 5e-4


def test_decomposition_is_exact_with_the_closed_form_remainder(lpv):
    """f(xbar + e) - f(xbar) = A(rho(e)) e + B du + R(e) to 1e-10, with R from the closed form."""
    rng = np.random.default_rng(3)
    for _ in range(300):
        w, nxy, f = _rand_state(rng)
        if nxy @ nxy > 0.95:                                # outside the unit disc n_z is undefined
            continue
        e = np.concatenate((w - EQ.w, nxy - EQ.n[:2], [rng.normal(0, 1), rng.normal(0, 2)], f - EQ.f[:3]))
        du = rng.normal(0, 0.5, 3)
        r, nz = lpv.rho(e)
        lhs = lpv.f_nonlinear(e, du)
        rhs = lpv.A(r, nz) @ e + lpv.B @ du + lpv.remainder(e)
        assert np.allclose(lhs, rhs, atol=1e-10, rtol=1e-12)


def test_remainder_is_second_order_near_the_trim(lpv):
    rng = np.random.default_rng(4)
    d = rng.normal(0, 1, 10)
    d[5:7] = 0
    r1 = np.linalg.norm(lpv.remainder(1e-2 * d))
    r2 = np.linalg.norm(lpv.remainder(1e-3 * d))
    assert r1 < 1e-2 and 50 < r1 / r2 < 200                 # quadratic scaling


def test_remainder_bound_helper_returns_finite_values_and_dominates_samples(lpv):
    half = np.array([3, 3, 10, 0.3, 0.3, 1, 2, 1, 1, 1], float)
    sa, sg = remainder_sup(lpv, half, n=2000, local=2)
    assert np.all(np.isfinite(sa)) and np.all(np.isfinite(sg))
    e = np.array([1, -2, 5, 0.2, -0.2, 0, 0, 0.5, -0.5, 0.5], float)
    assert np.all(np.abs(lpv.remainder(e)) <= sa + 1e-12)


def test_failure_lqr_is_stable_at_frozen_parameters_over_the_scheduling_box(lpv):
    K = FailureLQR(P, EQ).K
    rg = np.linspace(EQ.w[2] - R_HALF, EQ.w[2] + R_HALF, 15)
    ng = np.linspace(NZ_RANGE[0], NZ_RANGE[1], 9)
    assert frozen_check(lpv, K, rg, ng) < 0
