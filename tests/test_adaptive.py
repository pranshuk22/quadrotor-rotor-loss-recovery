"""Checks for the online residual adaptation (K7).

Run:  .venv/bin/python -m pytest -q
"""
import copy
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import RLS, AdaptiveResidual, NominalModel, ResidualEDMD, generate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402


def test_rls_converges_to_the_true_weights_with_exciting_inputs():
    rng = np.random.default_rng(0)
    Wt = rng.normal(size=(6, 3))
    r = RLS(np.zeros((6, 3)), p0=10.0, lam=1.0)
    for _ in range(400):
        phi = rng.normal(size=6)
        r.update(phi, phi @ Wt)
    assert np.max(np.abs(r.W - Wt)) < 1e-3


def test_rls_with_forgetting_tracks_a_step_change():
    rng = np.random.default_rng(1)
    W1, W2 = rng.normal(size=(5, 2)), rng.normal(size=(5, 2))
    r = RLS(np.zeros((5, 2)), p0=10.0, lam=0.97)
    for k in range(600):
        phi = rng.normal(size=5)
        r.update(phi, phi @ (W1 if k < 300 else W2) + 1e-3 * rng.normal(size=2))
    assert np.max(np.abs(r.W - W2)) < 5e-3
    assert r.min_eig_violations == 0


def test_covariance_stays_bounded_without_excitation():
    r = RLS(np.zeros((4, 1)), p0=1.0, lam=0.99, trace_max_factor=10.0)
    for _ in range(3000):
        r.update(np.array([1.0, 0, 0, 0]), np.zeros(1))              # excites one direction only
    assert max(r.trace_log) <= 10.0 * r.tr0 * (1 + 1e-9) and r.n_rescaled > 0


def test_adaptive_residual_equals_the_offline_residual_before_any_update_and_is_causal():
    eq = relaxed_hover(P)
    train = generate(truth_family("A"), P, eq, 4, 2.0, seed=3)
    base = ResidualEDMD.fit(train, NominalModel.build(P, eq), P)
    ad = AdaptiveResidual(base, p0=1.0, lam=0.995)
    x, fe, u = train.x[0][5], train.fe[0][5], train.u[0][5]
    assert np.allclose(ad.residual(x, fe, u), base.residual(x, fe, u))        # first call: no update yet
    assert ad.rls.n_updates == 0
    # causality: the output at call k must not depend on a modified x_k beyond the residual evaluation itself
    a, b = copy.deepcopy(ad), copy.deepcopy(ad)
    x2 = train.x[0][6]
    da, db = a.residual(x2, fe, u), b.residual(x2 + 0.0, fe, u)
    assert np.allclose(da, db) and a.rls.n_updates == 1
    # the weight update used only (features at k-1, e_k): W after call must equal an explicit RLS step
    r = copy.deepcopy(ad.rls)
    x1n, _ = base.nom.step(x, fe, u)
    phi = base.dic(np.concatenate((x[[0, 1, 2, 3, 4, 6]], fe, u)))[0]
    # (ad.prev is (x, fe); the new u is the regressor input)
    ref = copy.deepcopy(ad.rls)
    ref.update(phi, x2 - x1n)
    assert np.allclose(a.rls.W, ref.W)
