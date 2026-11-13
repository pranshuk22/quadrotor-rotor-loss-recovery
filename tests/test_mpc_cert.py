"""Checks for the residual-MPC certificate (D8).

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import NominalModel  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.mpc_cert import (design_ellipsoid, horizon_gains, mismatch_margin, unconstrained_law,  # noqa: E402
                                unconstrained_region, verify_design)
from rotorfail.params import DEFAULT as P  # noqa: E402

EQ = relaxed_hover(P)
NOM = NominalModel.build(P, EQ)
LAW = unconstrained_law(NOM)


def _mpc_first_move(s, d, horizon=20):
    mpc = FailureMPC(P, EQ, horizon=horizon)
    mpc.x0.value = s
    mpc.d.value = np.concatenate((d, np.zeros(3)))
    mpc.prob.solve(solver="CLARABEL")
    return mpc.U.value[:, 0]


def test_unconstrained_mpc_equals_lqr_plus_affine_term_in_d():
    """Closed form (K, G) against the QP solution with inactive constraints (two independent routes)."""
    rng = np.random.default_rng(0)
    for _ in range(4):
        s = np.concatenate((rng.normal(0, 0.05, 3), rng.normal(0, 0.005, 2), rng.normal(0, 0.02, 2), rng.normal(0, 0.05, 3)))
        d = np.concatenate((rng.normal(0, 0.002, 3), rng.normal(0, 0.0005, 2), rng.normal(0, 0.001, 2)))
        u_qp = _mpc_first_move(s, d)
        u_law = -LAW["K"] @ s + LAW["G"] @ np.concatenate((d, np.zeros(3)))
        assert np.allclose(u_qp, u_law, atol=1e-5)


def test_horizon_gains_reproduce_the_predicted_input_sequence():
    s = np.concatenate((np.full(3, 0.05), np.full(2, 0.004), [0.01, 0.01], np.full(3, 0.02)))
    d = np.concatenate((np.full(7, 1e-3), np.zeros(3)))
    Ms, Ns = horizon_gains(LAW, 20)
    x = s.copy()
    for j in range(20):
        u = -LAW["K"] @ x + LAW["Gj"][j] @ d
        assert np.allclose(u, Ms[j] @ s + Ns[j] @ d, atol=1e-10)
        x = LAW["A"] @ x + LAW["B"] @ u + d


def test_region_ellipsoid_is_inside_the_region_and_contractive():
    lo, hi = P.f_min - EQ.f[:3], P.f_max - EQ.f[:3]
    H, b = unconstrained_region(LAW, 20, lo, hi, np.full(7, 1e-3))
    sc = np.array([1.0, 1.0, 1.0, 0.1, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5])
    box = {7 + i: min(hi[i], -lo[i]) for i in range(3)}
    des = design_ellipsoid(LAW, H, b, lam=0.995, scale=sc, box=box)
    assert des is not None and des["status"] in ("optimal", "optimal_inaccurate")
    v = verify_design(des, LAW, H, b)
    assert v["worst_contraction"] < 1e-7 and v["min_face_margin"] > -1e-7 and v["min_eig_Q"] > 0
    # every sampled point of the ellipsoid keeps all predicted inputs inside the bounds
    rng = np.random.default_rng(1)
    L = np.linalg.cholesky(des["Q"])
    Ms, Ns = horizon_gains(LAW, 20)
    for _ in range(300):
        u = rng.normal(size=10)
        s = L @ (u / np.linalg.norm(u))
        d = np.concatenate((rng.uniform(-1e-3, 1e-3, 7), np.zeros(3)))
        for M, Nn in zip(Ms, Ns):
            uu = M @ s + Nn @ d
            assert np.all(uu >= lo - 1e-7) and np.all(uu <= hi + 1e-7)


def test_mismatch_margin_is_monotone_in_the_learned_term():
    lo, hi = P.f_min - EQ.f[:3], P.f_max - EQ.f[:3]
    H, b = unconstrained_region(LAW, 20, lo, hi, np.full(7, 1e-4))
    sc = np.array([1.0, 1.0, 1.0, 0.1, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5])
    box = {7 + i: min(hi[i], -lo[i]) for i in range(3)}
    des = design_ellipsoid(LAW, H, b, lam=0.995, scale=sc, box=box)
    m0, D0, _ = mismatch_margin(LAW, des["Q"], np.zeros(7))
    m1, D1, _ = mismatch_margin(LAW, des["Q"], np.full(7, 1e-3))
    assert D0 == 0.0 and D1 > 0 and m1 <= m0
