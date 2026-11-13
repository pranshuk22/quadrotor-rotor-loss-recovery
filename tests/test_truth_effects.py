"""K11: optional IJRR effects (air-relative thrust, quadratic drag) in the truth plant.

With the effects off (the defaults) the dynamics must be BIT-IDENTICAL to the published model, so every existing result
stays valid; the reference implementations below are verbatim copies of the pre-K11 code.

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.dynamics import (E3, IDX_F, IDX_Q, IDX_V, IDX_W, body_rate_derivative, deriv, make_state,  # noqa: E402
                                quat_mult, quat_to_rot, saturate)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import G, truth_family  # noqa: E402
from rotorfail.validation import IJRR_CASES, GeneralMulticopter, ijrr_speeds  # noqa: E402


def _ref_body_rate_derivative(w, f, p):
    w_sigma = np.sum(p.prop_speeds(f))
    h = p.I_T @ w + p.Izz_P * w_sigma * E3
    f1, f2, f3, f4 = f * p.thrust_efficiency(w)
    tau = np.array([p.l * (f2 - f4), p.l * (f3 - f1), p.kappa_tau * (f1 - f2 + f3 - f4) - p.gamma * w[2]])
    return np.linalg.solve(p.I_B, tau - np.cross(w, h))


def _ref_deriv(x, f_cmd, p, alive, motor_lag=True):
    q, w = x[IDX_Q], x[IDX_W]
    f_sat = saturate(f_cmd, p, alive)
    if motor_lag:
        f = np.where(alive, x[IDX_F], 0.0)
        f_dot = np.where(alive, (f_sat - f) / p.sigma_mot, 0.0)
    else:
        f = f_sat
        f_dot = np.zeros(4)
    R = quat_to_rot(q)
    acc = R @ E3 * np.sum(f) * p.thrust_efficiency(w) / p.m - G * E3
    q_dot = 0.5 * quat_mult(q, np.concatenate(([0.0], w)))
    w_dot = _ref_body_rate_derivative(w, f, p)
    return np.concatenate((x[IDX_V], acc, q_dot, w_dot, f_dot))


def test_defaults_are_bit_identical_to_the_pre_k11_dynamics():
    rng = np.random.default_rng(0)
    for p in (P, truth_family("A"), truth_family("B")):
        for _ in range(300):
            w = rng.normal(0, 10, 3)
            f = np.append(rng.uniform(0.0, 3.8, 3), 0.0)
            assert np.array_equal(body_rate_derivative(w, f, p), _ref_body_rate_derivative(w, f, p))
            x = make_state(v=rng.normal(size=3), euler=rng.normal(0, 0.5, 3), w=w, f=rng.uniform(0.2, 3.8, 4))
            cmd = rng.uniform(-0.5, 4.0, 4)
            alive = np.array([True, True, True, False])
            assert np.array_equal(deriv(x, cmd, p, alive), _ref_deriv(x, cmd, p, alive))


def _ijrr_params():
    """QuadParams matching GeneralMulticopter: I_T = I_B + 4 I_P, kappa_tau = ktau / kf, quadratic drag, air-relative."""
    g = GeneralMulticopter()
    return replace(P, Ixx_T=g.I_B[0] + 4 * 0.0, Izz_T=g.I_B[2] + 4 * g.I_Pzz, Ixx_P=0.0, kappa_tau=g.ktau / g.kf,
                   gamma=0.0, air_relative=True, quad_drag=g.Kd)


def test_effects_on_match_the_independent_implementation():
    g = GeneralMulticopter(prop_inertia_accel=False)
    p = _ijrr_params()
    rng = np.random.default_rng(1)
    for _ in range(200):
        Om = ijrr_speeds(rng.uniform(300, 700, 4))
        w = rng.normal(0, 8, 3)
        f = g.kf * np.abs(Om) ** 2                       # commanded thrust corresponds to the speed relative to the body
        assert np.allclose(body_rate_derivative(w, f, p), g.angular_acceleration(w, Om), rtol=1e-9, atol=1e-9)


def test_hover_rates_of_the_ijrr_cases_match_within_one_percent():
    g = GeneralMulticopter()
    p = _ijrr_params()
    from scipy.optimize import fsolve
    for name, c in IJRR_CASES.items():
        if name == "no failure":
            continue
        Om = ijrr_speeds(c["Omega"])
        f = g.kf * np.abs(Om) ** 2
        w_ref = g.hover_rates(Om, guess=c["w"])
        w_ours = fsolve(lambda w: body_rate_derivative(w, f, p), np.asarray(c["w"], float), xtol=1e-12)
        # the independent model lets a stopped rotor produce kf r |r| (a few mN); ours masks it, hence the 1 % norm bound
        assert np.linalg.norm(w_ours - w_ref) <= 1e-2 * np.linalg.norm(w_ref), name


def test_quadratic_drag_dissipates_rotational_energy_in_free_flight():
    p = replace(P, quad_drag=(0.7e-4, 0.7e-4, 1.4e-4), gamma=0.0)
    w = np.array([6.0, -4.0, 15.0])
    f = np.zeros(4)
    dt, E = 1e-3, []
    for _ in range(3000):
        E.append(0.5 * w @ p.I_T @ w)
        w = w + dt * body_rate_derivative(w, f, p)
    assert E[-1] < E[0] and np.all(np.diff(E) <= 1e-12)


def test_family_names_with_plus_add_the_effects_and_leave_a_and_b_unchanged():
    a, ap = truth_family("A"), truth_family("A+")
    assert not a.air_relative and a.quad_drag is None
    assert ap.air_relative and ap.quad_drag is not None and ap.thrust_loss == a.thrust_loss
    assert truth_family("B+").air_relative
