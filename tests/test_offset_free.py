"""Checks for the offset-free controllers (K6).

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest
from scipy.signal import cont2discrete

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.models import failed_linear  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.offset_free import (FailureLQRIntegral, OffsetFreeMPC, detectability_rank,  # noqa: E402
                                   thrust_offset_matrix)
from rotorfail.params import DEFAULT as P  # noqa: E402

EQ = relaxed_hover(P)


@pytest.fixture(scope="module")
def mpc():
    return OffsetFreeMPC(P, EQ, horizon=20)


def test_thrust_offset_matrix_is_zoh_of_the_seven_state_input_matrix(mpc):
    lin = failed_linear(P, EQ)
    _, B7d, *_ = cont2discrete((lin.A, lin.B, np.eye(7), np.zeros((7, 3))), 0.005)
    # the 7-state ZOH of the thrust input matrix must equal the physical block of Bd
    assert np.allclose(mpc.Bd[:7], B7d, atol=1e-9)
    assert np.all(mpc.Bd[7:] == 0.0)


def test_detectability_and_target_matrix_have_full_rank(mpc):
    rank, smin = detectability_rank(mpc.A, mpc.Bd)
    assert rank == 13 and smin > 1e-3
    M = np.linalg.inv(mpc.Minv)
    assert M.shape == (13, 13) and np.linalg.matrix_rank(M) == 13


def _linear_loop(ctrl, d_true, steps):
    """Linear plant s+ = A s + B u + Bd d_true under the controller; returns the state history."""
    A, B, Bd = ctrl.A, ctrl.B, ctrl.Bd
    s = np.zeros(10)
    hist = []
    for _ in range(steps):
        u = ctrl.act(s[:7])
        s = A @ s + B @ u + Bd @ d_true
        hist.append(s.copy())
    return np.array(hist)


def test_offset_free_removes_a_constant_thrust_offset_on_the_linear_model():
    c = OffsetFreeMPC(P, EQ, horizon=20)
    d_true = np.array([0.08, -0.05, 0.06])
    h = _linear_loop(c, d_true, 1000)                    # 5 s
    assert abs(h[-1, 5]) < 1e-3                          # altitude error
    assert np.abs(h[-1, 3:5]).max() < 1e-3               # tilt error
    assert np.allclose(c.d_hat_log[-1], d_true, atol=1e-3)
    assert bool(np.all(c.target_exact))


def test_plain_mpc_keeps_an_offset_under_the_same_disturbance():
    """Sanity check of the test itself: without integral action the offset remains."""
    f = FailureMPC(P, EQ, horizon=20)
    f.reset(EQ.f[:3])
    A, B, Bd = f.nom.Ad, f.nom.Bd, thrust_offset_matrix(P, EQ)
    s = np.zeros(10)
    for _ in range(1000):
        s_meas = np.concatenate((s[:7], f.fe))
        f.x0.value = s_meas
        f.d.value = np.zeros(10)
        f.prob.solve(solver="OSQP", warm_start=True, eps_abs=1e-5, eps_rel=1e-5, max_iter=4000)
        u = f.U.value[:, 0]
        a = 1 - np.exp(-f.ts / P.sigma_mot)
        f.fe = f.fe + a * (u - f.fe)
        s = A @ s + B @ u + Bd @ np.array([0.08, -0.05, 0.06])
    assert abs(s[5]) > 1e-2 or np.abs(s[3:5]).max() > 1e-3


def test_first_move_equals_failure_mpc_when_disturbance_estimate_is_zero():
    x = make_state(w=EQ.w + np.array([0.2, -0.1, 0.3]), f=np.concatenate((EQ.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(EQ.n + np.array([0.01, -0.01, 0.0]))
    a, b = OffsetFreeMPC(P, EQ, horizon=10), FailureMPC(P, EQ, horizon=10)
    a.reset(x[13:16])
    b.reset(x[13:16])
    ua, ub = a(0.0, x), b(0.0, x)
    assert a.prob.status == "optimal"
    assert np.allclose(ua, ub, atol=1e-4)


def test_target_satisfies_steady_state_equations_and_reports_inexact_when_box_binds(mpc):
    D = mpc.Bd @ np.array([0.1, 0.05, -0.1])
    ss, us, exact = mpc.target(D)
    assert exact
    assert np.allclose(ss, mpc.A @ ss + mpc.B @ us + D, atol=1e-9)
    assert np.allclose(mpc.H @ ss, 0.0, atol=1e-9)
    # a disturbance that would need rotor 2 below its idle thrust: target is closest feasible
    D_big = mpc.Bd @ np.array([0.0, 3.0, 0.0])
    ss, us, exact = mpc.target(D_big)
    assert not exact
    assert np.all(us >= mpc.u_lo - 1e-9) and np.all(us <= mpc.u_hi + 1e-9)
    assert np.allclose(ss, mpc.A @ ss + mpc.B @ us + D_big, atol=1e-6)


def test_qp_status_optimal_on_random_near_trim_states():
    rng = np.random.default_rng(5)
    c = OffsetFreeMPC(P, EQ, horizon=10)
    for _ in range(40):
        x7 = np.concatenate((rng.normal(0, 0.3, 3), rng.normal(0, 0.02, 2), rng.normal(0, 0.1, 2)))
        c.act(x7)
    assert c.bad_status == 0


def test_integral_lqr_removes_the_offset_on_the_linear_model():
    c = FailureLQRIntegral(P, EQ)
    # discrete linear plant with a thrust offset; the sampled LQR acts on the 10-state model
    from rotorfail.koopman import NominalModel
    nom = NominalModel.build(P, EQ)
    Bd = thrust_offset_matrix(P, EQ)
    d_true = np.array([0.08, -0.05, 0.06])
    s = np.zeros(10)
    c.reset(EQ.f[:3])
    for k in range(4000):                                # 20 s
        e7 = s[:7]
        x = make_state(d=(0, 0, e7[5]), v=(0, 0, e7[6]), w=EQ.w + e7[:3], f=np.concatenate((EQ.f[:3] + s[7:], [0.0])))
        x[IDX_Q] = quat_from_n(np.array([EQ.n[0] + e7[3], EQ.n[1] + e7[4],
                                         np.sqrt(1 - (EQ.n[0] + e7[3]) ** 2 - (EQ.n[1] + e7[4]) ** 2)]))
        u = c(k * 0.005, x)[:3] - EQ.f[:3]
        s = nom.Ad @ s + nom.Bd @ u + Bd @ d_true
    assert abs(s[5]) < 5e-3
