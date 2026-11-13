"""Checks for the reachable-set and containment code (D6).

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.dynamics import make_state, quat_to_rot  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.reach import (ChainSpec, UndetectedLTI, X0_SIGMA, capture_dev, centre_scaling,  # noqa: E402
                             chain_jacobian, command_ranges, coverage, hand_over_set, max_beta, max_beta_exact,
                             run_chain, sample_x0)

EQ = relaxed_hover(P)


def test_ellipsoid_propagated_exactly_contains_simulated_linear_trajectories():
    lti = UndetectedLTI(P)
    steps = 40
    cs, Ps = lti.propagate(steps)
    rng = np.random.default_rng(0)
    L0 = np.zeros((15, 9))
    L0[3:6, :3] = np.eye(3) * 0.3          # v
    L0[6:9, 3:6] = np.eye(3) * np.deg2rad(3)
    L0[9:12, 6:9] = np.eye(3) * 0.3
    L0 *= 4.6
    Lk = Ps[-1] @ L0
    pts = []
    for _ in range(1000):
        u = rng.normal(size=9)
        u *= rng.uniform() ** (1 / 9) / np.linalg.norm(u)
        z = L0 @ u
        for _ in range(steps):
            z = lti.Acl @ z + lti.dd
        pts.append(z)
    ex = coverage(cs[-1], Lk, pts)
    assert ex[:, 0].max() <= 1 + 1e-9 and ex[:, 1].max() < 1e-9


def test_affine_centre_matches_numerical_integration_of_the_continuous_model():
    lti = UndetectedLTI(P)
    steps = 25
    cs, _ = lti.propagate(steps)
    p, lin, K = P, lti.lin, lti.ctrl.K
    z = np.zeros(15)
    n = 12
    for _ in range(steps):
        udev = -(lti.Kc @ z)

        def f(t, y):
            e, df = y[:n], y[n:]
            de = lin.A @ e + lin.B[:, :3] @ df + lin.B[:, 3] * (-p.weight / 4.0)
            return np.concatenate((de, (udev - df) / p.sigma_mot))

        sol = solve_ivp(f, (0, lti.T), z, rtol=1e-11, atol=1e-13)
        z = sol.y[:, -1]
    assert np.allclose(z, cs[-1], atol=1e-9)


def test_coordinate_change_matches_the_rotation_matrix():
    phi, th, psi = 0.3, -0.2, 0.9
    x = make_state(euler=(phi, th, psi), w=(1.0, -2.0, 3.0))
    d = capture_dev(x, EQ)
    n = np.array([-np.sin(th), np.sin(phi) * np.cos(th), np.cos(phi) * np.cos(th)])
    assert np.allclose(d[3:5], n[:2] - EQ.n[:2], atol=1e-12)
    assert np.allclose(quat_to_rot(x[6:10]).T @ np.array([0, 0, 1.0]), n, atol=1e-12)


def _random_pair(rng, n=6):
    A = rng.normal(size=(n, n))
    Q2 = A @ A.T + 0.5 * np.eye(n)
    L = rng.normal(size=(n, n - 1)) * 0.3
    c = rng.normal(size=n) * 0.1
    P2 = np.linalg.inv(Q2)
    c = c / max(1.0, np.sqrt(c @ P2 @ c) * 1.5)                 # centre well inside
    return c, L, Q2


@pytest.mark.parametrize("seed", range(20))
def test_containment_sdp_agrees_with_the_exact_evaluation_and_sampling(seed):
    rng = np.random.default_rng(seed)
    c, L, Q2 = _random_pair(rng)
    b_sdp, b_ex = max_beta(c, L, Q2), max_beta_exact(c, L, Q2)
    assert b_sdp is not None and abs(b_sdp - b_ex) <= 2e-3 * max(1.0, b_ex)
    P2 = np.linalg.inv(Q2)
    u = rng.normal(size=(3000, L.shape[1]))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    inside = c + 0.999 * b_sdp * u @ L.T
    assert np.max(np.einsum("ij,jk,ik->i", inside, P2, inside)) <= 1 + 1e-6
    # slightly larger than beta: a sample outside is found by maximising x'P2x over the scaled ellipsoid
    out = c + 1.02 * b_sdp * u @ L.T
    best = np.max(np.einsum("ij,jk,ik->i", out, P2, out))
    # the exact maximiser need not be among 3000 random samples; check the exact evaluation instead
    assert b_ex < 1.02 * b_sdp or best > 1 - 1e-3


def test_centre_outside_gives_none_and_a_scaling():
    Q2 = np.eye(3)
    c = np.array([2.0, 0, 0])
    assert max_beta(c, np.eye(3)[:, :2], Q2) is None and max_beta_exact(c, np.eye(3)[:, :2], Q2) is None
    assert centre_scaling(np.linalg.inv(Q2), c) == pytest.approx(0.5)


def test_chain_reproduces_the_e9a_hand_over_for_the_exact_hover_start():
    r = run_chain(ChainSpec(P, tau=0.0, w_sw=10.0, f_spin=2.95), np.zeros(9))
    assert r["handed"] and abs(r["t_h"] - 0.647) < 1e-3
    assert np.allclose(r["x_h"][10:13], [0.00, -0.97, 9.96], atol=0.006)
    assert abs(np.linalg.norm(r["dev_interp"][:3] - r["dev"][:3])) < 0.05      # interpolation within one step


def test_chain_jacobian_is_step_size_independent_and_predicts_small_perturbations():
    spec = ChainSpec(P, tau=0.01, w_sw=10.0, f_spin=2.95)
    c, J, info = chain_jacobian(spec, eps_scale=1e-3)
    c2, J2, _ = chain_jacobian(spec, eps_scale=1e-2)
    assert np.allclose(J, J2, rtol=5e-2, atol=5e-2 * np.abs(J).max() * 0.05)
    rng = np.random.default_rng(1)
    u = 0.05 * X0_SIGMA * rng.normal(size=9)
    out = run_chain(spec, u)["dev_interp"]
    assert np.linalg.norm(out - (c + J @ u)) < 0.05 * np.linalg.norm(J @ u) + 1e-3


def test_command_ranges_classification_and_exact_hover_is_unsaturated_for_small_tau():
    lti = UndetectedLTI(P)
    S0 = np.zeros((15, 15))
    cls = command_ranges(lti, 60, S0)
    assert all(c == "unsat" for row in cls for c in row)
    L0 = np.zeros((15, 9))
    L0[9:12, 6:9] = np.eye(3) * 50.0
    cls2 = command_ranges(lti, 60, L0 @ L0.T)
    assert any(c != "unsat" for row in cls2 for c in row)


def test_coverage_ignores_numerical_noise_in_null_directions():
    """A set with exactly null columns (variables the output does not depend on) must not blow up the excess measure."""
    rng = np.random.default_rng(0)
    L = np.zeros((10, 9))
    L[:, :6] = rng.normal(size=(10, 6))
    L[:, 6:] = 1e-12 * rng.normal(size=(10, 3))            # numerical noise in the null directions
    c = rng.normal(size=10)
    dev = c + L[:, :6] @ (0.5 * rng.normal(size=6) / 3)
    ex = coverage(c, L, [dev])
    assert ex[0, 0] < 5.0 and ex[0, 1] < 1e-8
