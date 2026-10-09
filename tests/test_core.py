"""Core checks: equilibria, linearization, controllers, certificate sanity.

Run:  .venv/bin/python -m pytest -q
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rotorfail.certify import invariant_ellipsoid  # noqa: E402
from rotorfail.control import FailureLQR, HealthyLQR  # noqa: E402
from rotorfail.dynamics import (IDX_Q, deriv, make_state, quat_from_n, quat_to_rot,  # noqa: E402
                                reduced_attitude)
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.models import failed_f, failed_linear, healthy_f, healthy_linear  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

ALIVE3 = np.array([True, True, True, False])


@pytest.fixture(scope="module")
def eq():
    return relaxed_hover(P, 0.5)


def test_relaxed_hover_matches_paper(eq):
    # Mueller & D'Andrea ICRA 2014: f1 = 2.05, f2 = 1.02, r = 18.89, n_z = 0.958
    assert eq.f[0] == pytest.approx(2.05, rel=0.01)
    assert eq.f[1] == pytest.approx(1.02, rel=0.01)
    assert eq.w[2] == pytest.approx(18.89, rel=0.01)
    assert eq.n[2] == pytest.approx(0.958, rel=0.01)
    assert eq.f_sum * eq.n[2] == pytest.approx(P.weight, rel=1e-9)
    assert np.allclose(np.cross(eq.w, eq.n), 0, atol=1e-9)   # n parallel to w


def test_relaxed_hover_is_fixed_point_of_reduced_model(eq):
    s0 = np.array([*eq.w, eq.n[0], eq.n[1], 0.0, 0.0])
    assert np.allclose(failed_f(s0, eq.f[:3], P), 0, atol=1e-9)


def test_relaxed_hover_in_full_simulation(eq):
    """Open loop at the exact trim: rates and reduced attitude stay constant for a short time."""
    x = make_state(w=eq.w, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n)
    assert np.allclose(reduced_attitude(x), eq.n, atol=1e-12)
    from rotorfail.dynamics import rk4_step
    for _ in range(200):
        x = rk4_step(x, np.concatenate((eq.f[:3], [0.0])), 5e-4, P, ALIVE3, motor_lag=False)
    assert np.allclose(x[10:13], eq.w, atol=1e-6)
    assert np.allclose(reduced_attitude(x), eq.n, atol=1e-6)


def test_quat_from_n_roundtrip():
    rng = np.random.default_rng(0)
    for _ in range(20):
        n = rng.normal(size=3)
        n /= np.linalg.norm(n)
        R = quat_to_rot(quat_from_n(n))
        assert np.allclose(R.T @ np.array([0, 0, 1.0]), n, atol=1e-12)


def test_linearizations_match_finite_differences(eq):
    rng = np.random.default_rng(1)
    for model, fun in ((healthy_linear(P), lambda x, u: healthy_f(x, u, P)),
                       (failed_linear(P, eq), lambda x, u: failed_f(x, u, P))):
        dx = 1e-5 * rng.normal(size=len(model.x_trim))
        du = 1e-5 * rng.normal(size=len(model.u_trim))
        exact = fun(model.x_trim + dx, model.u_trim + du) - fun(model.x_trim, model.u_trim)
        lin = model.A @ dx + model.B @ du
        assert np.allclose(exact, lin, atol=1e-8)


def test_lqr_closed_loops_are_stable(eq):
    h = HealthyLQR(P)
    f = FailureLQR(P, eq)
    assert np.max(np.linalg.eigvals(h.model.A - h.model.B @ h.K).real) < 0
    assert np.max(np.linalg.eigvals(f.model.A - f.model.B @ f.K).real) < 0


def test_failure_lqr_recovers_small_perturbation(eq):
    f = FailureLQR(P, eq)
    x = make_state(d=(0, 0, -0.5), w=eq.w + np.array([0.5, -0.5, 1.0]),
                   f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n + np.array([0.05, 0.0, 0.0]))
    log = simulate(x, f, P, 5.0, dt=1e-3, alive_fn=lambda t: ALIVE3)
    assert np.linalg.norm(log.n[-1] - eq.n) < 1e-3
    assert abs(log.z[-1]) < 1e-2


def test_certificate_is_an_invariant_set_of_the_linear_saturated_loop(eq):
    """Points on the certified ellipsoid boundary: V decreases along x' = Ax + B sat(-Kx),
    with the plant's asymmetric thrust limits."""
    f = FailureLQR(P, eq)
    A, B, K = f.model.A, f.model.B, f.K
    ubar = np.minimum(eq.f[:3] - P.f_min, P.f_max - eq.f[:3])
    r = invariant_ellipsoid(A, B, K, ubar, decay=0.1, box=[np.inf] * 7 + list(ubar))
    Pm = r["P"]
    rng = np.random.default_rng(2)
    L = np.linalg.cholesky(np.linalg.inv(Pm))
    for _ in range(500):
        v = rng.normal(size=10)
        x = L @ (v / np.linalg.norm(v))           # on the boundary x^T P x = 1
        # the plant's real, asymmetric limits around the trim (not the LMI's symmetric ones)
        u = np.clip(-K @ x, P.f_min - eq.f[:3], P.f_max - eq.f[:3])
        assert 2 * x @ Pm @ (A @ x + B @ u) < 0


def test_controller_called_once_per_period():
    calls = []

    def ctrl(t, x):
        calls.append(t)
        return np.full(4, P.weight / 4)

    simulate(make_state(), ctrl, P, 0.01, dt=1e-3, ctrl_period=5e-3)
    assert calls == [0.0, 0.005, 0.01]


def test_supervisor_switch_uses_filtered_commands_not_true_thrust(eq):
    """At detection the failure controller is initialised from the nominal filter of the
    commands sent, which the flight computer knows, not from the plant's thrust state."""
    from rotorfail.control import DelaySupervisor, HealthyLQR, FailureLQR
    from rotorfail.params import truth_family
    fail = FailureLQR(P, eq)
    sup = DelaySupervisor(HealthyLQR(P), fail, t_fail=0.0, tau=0.05)
    log = simulate(make_state(), sup, truth_family("A"), 0.06, dt=1e-3, ctrl_period=1e-3, log_every=1)
    true_f = log.x[-1, 13:16]
    assert not np.allclose(fail.f_est, true_f, atol=1e-3)   # different motor lag in the plant
    assert np.all(np.isfinite(fail.f_est))
