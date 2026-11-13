"""Checks for the r-robust saturation-aware certificate (D4).

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.certify import robust_invariant_ellipsoid, verify_robust  # noqa: E402


def _scalar(a_list, k=3.0, b=1.0, ubar=1.0, gamma=0.0, eps=1e-7):
    A_list = [np.array([[a]]) for a in a_list]
    return robust_invariant_ellipsoid(A_list, np.array([[b]]), np.array([[k]]), np.array([ubar]),
                                      np.array([10.0]), decay=0.0, eps=eps, gamma=gamma)


def test_scalar_unstable_plant_recovers_the_exact_region_of_attraction():
    """x' = a x + b sat(-k x), |u| <= ubar: the region of attraction is |x| < b ubar / a exactly.
    The Hu-Lin ellipsoid reaches it (up to the contraction margin)."""
    res = _scalar([1.0])
    assert res["status"] in ("optimal", "optimal_inaccurate")
    assert abs(np.sqrt(res["Q"][0, 0]) - 1.0) < 0.01


def test_vertex_set_is_limited_by_its_worst_vertex():
    res = _scalar([0.5, 1.25])
    assert abs(np.sqrt(res["Q"][0, 0]) - 1.0 / 1.25) < 0.01


def test_two_state_extent_matches_the_scalar_bound_along_the_unstable_direction():
    """x1' = x1 + sat(-3 x1), x2' = -x2 (decoupled): extent along e1 is the scalar bound, along e2 the box."""
    A = [np.array([[1.0, 0.0], [0.0, -1.0]])]
    B = np.array([[1.0], [0.0]])
    K = np.array([[3.0, 0.0]])
    res = robust_invariant_ellipsoid(A, B, K, np.array([1.0]), np.array([10.0, 10.0]), direction=[1.0, 0.0],
                                     decay=0.0, eps=1e-7)
    assert abs(res["beta"] - 1.0) < 0.01
    res2 = robust_invariant_ellipsoid(A, B, K, np.array([1.0]), np.array([10.0, 10.0]), direction=[0.0, 1.0],
                                      decay=0.0, eps=1e-7)
    assert res2["beta"] > 9.9


def test_disc_constraint_keeps_the_shifted_ellipsoid_inside_the_disc():
    A = [-np.eye(2)]
    B = np.array([[1.0], [0.0]])
    K = np.zeros((1, 2))
    c, R = np.array([0.0, 0.3]), 0.9
    res = robust_invariant_ellipsoid(A, B, K, np.array([1.0]), np.array([5.0, 5.0]), decay=0.0, eps=1e-7,
                                     disc=((0, 1), c, R))
    Q = res["Q"]
    L = np.linalg.cholesky(Q)
    rng = np.random.default_rng(0)
    u = rng.normal(size=(2000, 2))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    pts = u @ L.T + c
    assert np.max(np.linalg.norm(pts, axis=1)) <= R * (1 + 1e-6)
    # at least as large as the circle of radius R - |c| (a feasible ellipsoid)
    assert np.linalg.det(Q) >= (R - np.linalg.norm(c)) ** 4 * (1 - 1e-3)


def test_numerical_verification_reports_negative_blocks_and_positive_linear_region():
    res = _scalar([0.5, 1.0], eps=1e-5)
    v = verify_robust(res, lambda r, nz: np.array([[0.5 + 0.5 * r]]), np.array([[1.0]]), np.array([[3.0]]),
                      np.array([1.0]), np.array([10.0]), np.linspace(0, 1, 11), [0.0], decay=0.0,
                      A_list=[np.array([[0.5]]), np.array([[1.0]])])
    assert v["worst_dynamics"] < -1e-6 and v["worst_linear_region"] > -1e-8 and v["min_eig_Q"] > 0


def test_remainder_term_shrinks_the_certified_set():
    base = _scalar([1.0])
    rem = _scalar([1.0], gamma=0.3)
    assert rem["status"] in ("optimal", "optimal_inaccurate")
    assert rem["Q"][0, 0] < base["Q"][0, 0]
