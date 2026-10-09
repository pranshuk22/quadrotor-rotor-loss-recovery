"""Checks for the RQ1 pipeline: data, nominal model, EDMDc fits, MPC.

Run:  .venv/bin/python -m pytest -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import (FullEDMDc, NominalModel, ResidualEDMD, generate,  # noqa: E402
                               nominal_rollout)
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402


@pytest.fixture(scope="module")
def setup():
    eq = relaxed_hover(P)
    data = generate(truth_family("A"), P, eq, 4, 2.0, seed=0)
    return eq, data, NominalModel.build(P, eq)


def test_nominal_model_is_exact_on_nominal_plant():
    """On the nominal plant with small inputs, the discrete nominal model predicts one step well."""
    eq = relaxed_hover(P)
    data = generate(P, P, eq, 1, 1.0, seed=3, amp=0.05)
    nom = NominalModel.build(P, eq)
    X, fe, U = data.x[0], data.fe[0], data.u[0]
    err = [np.abs(nom.step(X[k], fe[k], U[k])[0] - X[k + 1]).max() for k in range(len(U))]
    assert np.median(err) < 2e-3


def test_residual_reduces_one_step_error(setup):
    eq, data, nom = setup
    res = ResidualEDMD.fit(data, nom, P)
    X, fe, U = data.x[0], data.fe[0], data.u[0]
    e_nom = np.mean([np.sum((nom.step(X[k], fe[k], U[k])[0] - X[k + 1]) ** 2) for k in range(len(U))])
    e_res = np.mean([np.sum((nom.step(X[k], fe[k], U[k])[0] + res.residual(X[k], fe[k], U[k]) - X[k + 1]) ** 2)
                     for k in range(len(U))])
    assert e_res < 0.2 * e_nom


def test_full_edmdc_rollout_shapes_and_first_step(setup):
    eq, data, nom = setup
    full = FullEDMDc.fit(data)
    X, fe, U = data.x[0], data.fe[0], data.u[0]
    pred = full.rollout(X[0], fe[0], U[:10])
    assert pred.shape == (11, 7)
    assert np.abs(pred[1] - X[1]).max() < 0.05
    assert nominal_rollout(nom, X[0], fe[0], U[:10]).shape == (11, 7)


def test_mpc_returns_feasible_thrusts(setup):
    eq, data, nom = setup
    mpc = FailureMPC(P, eq, horizon=10)
    from rotorfail.koopman import initial_state
    x = initial_state(eq, np.random.default_rng(0))
    mpc.reset(x[13:16])
    u = mpc(0.0, x)
    assert u[3] == 0.0
    assert np.all(u[:3] >= P.f_min - 1e-9) and np.all(u[:3] <= P.f_max + 1e-9)
