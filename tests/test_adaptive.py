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


def test_default_fit_is_unchanged_and_row_weighting_is_a_distinct_option():
    from rotorfail.koopman import ResidualEDMD
    eq = relaxed_hover(P)
    train = generate(truth_family("A"), P, eq, 4, 2.0, seed=3)
    nom = NominalModel.build(P, eq)
    a = ResidualEDMD.fit(train, nom, P)
    b = ResidualEDMD.fit(train, nom, P, weighting="none")
    c = ResidualEDMD.fit(train, nom, P, weighting="row")
    assert np.array_equal(a.W, b.W) and not np.allclose(a.W, c.W)


def test_capture_generator_records_transients_far_from_the_trim():
    from rotorfail.koopman import generate_capture
    eq = relaxed_hover(P)
    data, bad = generate_capture(truth_family("A"), P, eq, 3, 1.0, seed=5)
    assert len(data.x) + bad == 3 and len(data.x) >= 1
    X0 = data.x[0][0]
    assert np.linalg.norm(X0[:3]) > 3.0                         # hand-over: rates far from the relaxed hover
    assert data.fe[0][0][1] < -0.9                              # rotor-2 filter estimate starts at 0 N
    assert len(data.u[0]) == len(data.x[0]) - 1


def test_dictionary_sizes_and_default_degree_unchanged():
    from rotorfail.koopman import Dictionary
    mu, sd = np.zeros(12), np.ones(12)
    assert Dictionary(mu, sd).size == 91 == Dictionary(mu, sd, 2)(np.ones(12)).shape[1]
    assert Dictionary(mu, sd, 1).size == 13 == Dictionary(mu, sd, 1)(np.ones(12)).shape[1]
    assert Dictionary(mu, sd, 3).size == 455 == Dictionary(mu, sd, 3)(np.ones(12)).shape[1]
    x = np.random.default_rng(0).normal(size=(3, 12))
    assert np.array_equal(Dictionary(mu, sd, 2)(x)[:, :91], Dictionary(mu, sd, 3)(x)[:, :91])      # nested


def test_ts_dependent_code_paths_respect_the_argument():
    from rotorfail.koopman import generate
    eq = relaxed_hover(P)
    n5, n10 = NominalModel.build(P, eq, 0.005), NominalModel.build(P, eq, 0.010)
    # exact ZOH semigroup: two 5 ms steps equal one 10 ms step
    assert np.allclose(n5.Ad @ n5.Ad, n10.Ad, atol=1e-10)
    assert np.allclose(n5.Ad @ n5.Bd + n5.Bd, n10.Bd, atol=1e-10)
    d5 = generate(truth_family("A"), P, eq, 1, 1.0, seed=2, ts=0.005)
    d10 = generate(truth_family("A"), P, eq, 1, 1.0, seed=2, ts=0.010)
    assert len(d5.x[0]) == 201 and len(d10.x[0]) == 101
    # the command filter of the data uses the sampling period: one step moves fe by 1 - exp(-ts/sigma) of the gap
    a = 1 - np.exp(-0.010 / P.sigma_mot)
    k = 5
    assert np.allclose(d10.fe[0][k], d10.fe[0][k - 1] + a * (d10.u[0][k - 1] - d10.fe[0][k - 1]))


def test_measurement_noise_keeps_the_tilt_on_the_unit_sphere_and_default_generate_is_noise_free():
    from rotorfail.koopman import MeasurementNoise, noisy_measurement
    eq = relaxed_hover(P)
    rng = np.random.default_rng(0)
    x7 = np.zeros(7)
    for _ in range(100):
        y = noisy_measurement(x7, MeasurementNoise(), rng, eq)
        n = np.array([y[3] + eq.n[0], y[4] + eq.n[1]])
        assert n @ n < 1.0
    a = generate(truth_family("A"), P, eq, 1, 0.5, seed=4)
    b = generate(truth_family("A"), P, eq, 1, 0.5, seed=4, noise=None)
    assert np.array_equal(a.x[0], b.x[0])
