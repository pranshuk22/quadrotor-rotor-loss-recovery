"""Physics validation of the simulator against analytic solutions and conservation laws.

Every test compares the simulator (`rotorfail.dynamics`) with a result derived by hand,
not with another run of the same code.

Run:  .venv/bin/python -m pytest -q tests/test_physics.py
"""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import expm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rotorfail.dynamics import (IDX_F, IDX_Q, IDX_W, body_rate_derivative, deriv,  # noqa: E402
                                euler_to_quat, make_state, quat_to_rot, reduced_attitude, rk4_step,
                                saturate)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import G  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.validation import GeneralMulticopter  # noqa: E402

ALL = np.ones(4, bool)


def run(x, f_cmd, p, T, dt, alive=ALL, lag=False):
    for _ in range(int(round(T / dt))):
        x = rk4_step(x, f_cmd, dt, p, alive, motor_lag=lag)
    return x


def skew(a):
    return np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])


# ------------------------------------------------------------------ translation
def test_free_fall():
    """No thrust: z(t) = z0 + vz0 t - g t^2 / 2, horizontal motion uniform."""
    x = make_state(d=(1.0, -2.0, 10.0), v=(0.5, 0.2, 1.0), euler=(0.3, -0.2, 1.0), w=(0.0, 0.0, 0.0))
    x = run(x, np.zeros(4), P, 1.0, 1e-3, alive=np.zeros(4, bool))
    T = 1.0
    assert np.allclose(x[0:3], [1.0 + 0.5 * T, -2.0 + 0.2 * T, 10.0 + 1.0 * T - 0.5 * G * T ** 2], atol=1e-9)
    assert np.allclose(x[3:6], [0.5, 0.2, 1.0 - G * T], atol=1e-9)


def test_thrust_direction_and_magnitude():
    """Tilted body, no torque: d_ddot = R e3 f_Sigma / m - g e3 (checked against R built by hand)."""
    phi, theta = 0.3, -0.2
    f = np.full(4, 1.5)                        # equal thrusts: zero roll/pitch torque
    x = make_state(euler=(phi, theta, 0.0))
    xd = deriv(x, f, P, ALL, motor_lag=False)
    Rx = np.array([[1, 0, 0], [0, np.cos(phi), -np.sin(phi)], [0, np.sin(phi), np.cos(phi)]])
    Ry = np.array([[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], [-np.sin(theta), 0, np.cos(theta)]])
    expected = (Ry @ Rx)[:, 2] * 6.0 / P.m - np.array([0, 0, G])   # yaw = 0: R = Ry Rx
    assert np.allclose(xd[3:6], expected, atol=1e-12)


def test_hover_thrust_balances_weight():
    x = make_state()
    xd = deriv(x, np.full(4, P.weight / 4), P, ALL, motor_lag=False)
    assert np.allclose(xd, 0, atol=1e-12)


# ------------------------------------------------------------------ rotation
def test_torque_free_axisymmetric_precession():
    """f = 0, gamma = 0, I_xx = I_yy: r is constant and (p, q) rotate at
    lambda = (Izz_T - Ixx_T) r / Ixx_B  (Euler's equations, closed form)."""
    p = replace(P, gamma=0.0)
    w0 = np.array([1.2, -0.7, 8.0])
    x = make_state(w=w0, f=np.zeros(4))
    T = 2.0
    x = run(x, np.zeros(4), p, T, 1e-4, alive=np.zeros(4, bool))
    lam = (p.Izz_T - p.Ixx_T) * w0[2] / p.Ixx_B
    p_exact = w0[0] * np.cos(lam * T) - w0[1] * np.sin(lam * T)
    q_exact = w0[1] * np.cos(lam * T) + w0[0] * np.sin(lam * T)
    assert np.allclose(x[IDX_W], [p_exact, q_exact, w0[2]], atol=1e-8)


def test_angular_momentum_and_energy_conserved():
    """Torque-free rigid body (no propeller inertia, no drag, no thrust): the inertial angular
    momentum R I w and the kinetic energy w' I w / 2 are invariants."""
    p = replace(P, gamma=0.0, Izz_P=0.0, Ixx_T=3.2e-3, Izz_T=5.5e-3)
    I = p.I_T
    x = make_state(euler=(0.4, -0.3, 1.1), w=(2.0, -3.0, 6.0), f=np.zeros(4))

    def invariants(x):
        R = quat_to_rot(x[IDX_Q])
        w = x[IDX_W]
        return R @ I @ w, 0.5 * w @ I @ w

    H0, E0 = invariants(x)
    x = run(x, np.zeros(4), p, 3.0, 2e-4, alive=np.zeros(4, bool))
    H1, E1 = invariants(x)
    assert np.allclose(H1, H0, rtol=1e-8, atol=1e-12)
    assert E1 == pytest.approx(E0, rel=1e-8)


def test_reduced_attitude_kinematics():
    """Constant w (spherical inertia, torque-free): n(t) = expm(-[w]x t) n(0), i.e. n_dot = -w x n."""
    p = replace(P, gamma=0.0, Izz_P=0.0, Ixx_T=4e-3, Izz_T=4e-3)
    w = np.array([3.0, -2.0, 5.0])
    x = make_state(euler=(0.2, 0.1, -0.5), w=w, f=np.zeros(4))
    n0 = reduced_attitude(x)
    T = 1.3
    x = run(x, np.zeros(4), p, T, 1e-4, alive=np.zeros(4, bool))
    assert np.allclose(x[IDX_W], w, atol=1e-12)
    assert np.allclose(reduced_attitude(x), expm(-skew(w) * T) @ n0, atol=1e-9)


def test_yaw_spin_up_is_first_order():
    """Rotors 1 and 3 only, equal thrust: p = q = 0 stay zero and
    Izz_B r_dot = kappa_tau (f1 + f3) - gamma r  =>  r(t) = r_ss (1 - exp(-gamma t / Izz_B))."""
    f = np.array([2.0, 0.0, 2.0, 0.0])
    x = make_state(f=f)
    T = 1.5
    x = run(x, f, P, T, 1e-3)
    r_ss = P.kappa_tau * 4.0 / P.gamma
    r_exact = r_ss * (1 - np.exp(-P.gamma * T / P.Izz_B))
    assert np.allclose(x[IDX_W][:2], 0, atol=1e-12)
    assert x[IDX_W][2] == pytest.approx(r_exact, rel=1e-9)


def test_rk4_is_fourth_order():
    """Halving dt reduces the error of the precession solution by about 2^4 = 16."""
    p = replace(P, gamma=0.0)
    w0 = np.array([1.2, -0.7, 8.0])
    T = 1.0
    lam = (p.Izz_T - p.Ixx_T) * w0[2] / p.Ixx_B
    exact = np.array([w0[0] * np.cos(lam * T) - w0[1] * np.sin(lam * T),
                      w0[1] * np.cos(lam * T) + w0[0] * np.sin(lam * T)])
    errs = []
    for dt in (0.02, 0.01):
        x = run(make_state(w=w0, f=np.zeros(4)), np.zeros(4), p, T, dt, alive=np.zeros(4, bool))
        errs.append(np.linalg.norm(x[IDX_W][:2] - exact))
    assert 12 < errs[0] / errs[1] < 20


# ------------------------------------------------------------------ actuators
def test_motor_lag_step_response():
    """f_dot = (f_cmd - f) / sigma  =>  f(t) = f_cmd + (f0 - f_cmd) exp(-t / sigma)."""
    f0, fc, T = 1.0, 3.0, 0.03
    x = make_state(f=np.full(4, f0))
    x = run(x, np.full(4, fc), P, T, 1e-4, lag=True)
    assert np.allclose(x[IDX_F], fc + (f0 - fc) * np.exp(-T / P.sigma_mot), atol=1e-10)


def test_saturation_and_failure_rules():
    alive = np.array([True, True, True, False])
    out = saturate(np.array([-1.0, 0.05, 9.0, 2.0]), P, alive)
    assert np.allclose(out, [0.0, P.f_min, P.f_max, 0.0])   # <= 0 stops the motor; failed rotor gives 0


# ------------------------------------------------------------------ paper equations
def test_matches_transcription_of_icra_eqs_12_to_14():
    """Independent transcription of Mueller & D'Andrea (2014) eqs. (12)-(14), written with
    signed propeller speeds w_i (f_i = kappa_f w_i^2), versus the simulator."""
    rng = np.random.default_rng(0)
    for _ in range(50):
        w = rng.normal(0, 10, 3)
        f = rng.uniform(0, 3.8, 4)
        om = P.prop_speeds(f)
        osum = om.sum()
        IxB, IxT, IzT, IzP = P.Ixx_B, P.Ixx_T, P.Izz_T, P.Izz_P
        pd = (P.kappa_f * (om[1] ** 2 - om[3] ** 2) * P.l - (IzT - IxT) * w[1] * w[2] - IzP * w[1] * osum) / IxB
        qd = (P.kappa_f * (om[2] ** 2 - om[0] ** 2) * P.l + (IzT - IxT) * w[0] * w[2] + IzP * w[0] * osum) / IxB
        rd = (-P.gamma * w[2] + P.kappa_tau * P.kappa_f * (om[0] ** 2 - om[1] ** 2 + om[2] ** 2 - om[3] ** 2)) / P.Izz_B
        assert np.allclose(body_rate_derivative(w, f, P), [pd, qd, rd], rtol=1e-10, atol=1e-10)


def test_general_ijrr_model_reduces_to_simulator():
    """The independent IJRR-model implementation, with its extra effects switched off
    (thrust from speed relative to the body, linear yaw drag, I_P w_dot neglected),
    must equal the simulator for any state and input."""
    g = GeneralMulticopter(I_B=(P.Ixx_B, P.Ixx_B, P.Izz_B), I_Pzz=P.Izz_P, kf=P.kappa_f,
                           ktau=P.kappa_tau * P.kappa_f, air_relative=False, drag="linear_yaw",
                           gamma=P.gamma, l=P.l, prop_inertia_accel=False)
    rng = np.random.default_rng(1)
    for _ in range(50):
        w = rng.normal(0, 10, 3)
        f = rng.uniform(0, 3.8, 4)
        Omega = P.prop_speeds(f)
        assert np.allclose(g.angular_acceleration(w, Omega), body_rate_derivative(w, f, P), rtol=1e-10, atol=1e-10)


def test_relaxed_hover_centre_of_mass_acceleration():
    """At the relaxed hover the vertical acceleration is zero and the horizontal acceleration
    has magnitude g * tan(tilt) = g sqrt(1 - n_z^2) / n_z (eq. 18-20 of the ICRA paper)."""
    from rotorfail.dynamics import quat_from_n
    eq = relaxed_hover(P)
    x = make_state(w=eq.w, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n)
    xd = deriv(x, np.concatenate((eq.f[:3], [0.0])), P, np.array([1, 1, 1, 0], bool), motor_lag=False)
    nz = eq.n[2]
    assert xd[5] == pytest.approx(0.0, abs=1e-12)
    assert np.linalg.norm(xd[3:5]) == pytest.approx(G * np.sqrt(1 - nz ** 2) / nz, rel=1e-10)
