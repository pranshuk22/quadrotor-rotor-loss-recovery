"""Checks for the Koopman and MPC pipeline: data, nominal model, EDMDc fits, MPC.

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
    """Fitted on the training episodes, evaluated on a held-out episode of the same plant."""
    eq, data, nom = setup
    res = ResidualEDMD.fit(data, nom, P)
    test = generate(truth_family("A"), P, eq, 1, 2.0, seed=99)
    X, fe, U = test.x[0], test.fe[0], test.u[0]
    e_nom = np.mean([np.sum((nom.step(X[k], fe[k], U[k])[0] - X[k + 1]) ** 2) for k in range(len(U))])
    e_res = np.mean([np.sum((nom.step(X[k], fe[k], U[k])[0] + res.residual(X[k], fe[k], U[k]) - X[k + 1]) ** 2)
                     for k in range(len(U))])
    assert e_res < 0.5 * e_nom


def test_full_edmdc_rollout_shapes_and_first_step(setup):
    eq, data, nom = setup
    full = FullEDMDc.fit(data)
    X, fe, U = data.x[0], data.fe[0], data.u[0]
    pred = full.rollout(X[0], fe[0], U[:10])
    assert pred.shape == (11, 7)
    assert np.abs(pred[1] - X[1]).max() < 0.05
    assert nominal_rollout(nom, X[0], fe[0], U[:10]).shape == (11, 7)


def test_mpc_solves_and_matches_lqr_near_trim(setup):
    """Near the trim the constraints are inactive, so the first MPC move (with the DARE
    terminal cost) should be close to the discrete LQR move."""
    from scipy.linalg import solve_discrete_are
    from rotorfail.control import failure_weights
    from rotorfail.dynamics import IDX_Q, make_state, quat_from_n
    eq, data, nom = setup
    mpc = FailureMPC(P, eq, horizon=10)
    x = make_state(w=eq.w + np.array([0.2, -0.1, 0.3]), f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n + np.array([0.01, -0.01, 0.0]))
    mpc.reset(x[13:16])
    u = mpc(0.0, x)
    assert mpc.prob.status == "optimal"
    Q, R = failure_weights()
    Pd = solve_discrete_are(mpc.nom.Ad, mpc.nom.Bd, Q, R)
    Kd = np.linalg.solve(R + mpc.nom.Bd.T @ Pd @ mpc.nom.Bd, mpc.nom.Bd.T @ Pd @ mpc.nom.Ad)
    s0 = np.concatenate((mpc.measure(x), x[13:16] - eq.f[:3]))
    u_lqr = eq.f[:3] - Kd @ s0
    assert np.allclose(u[:3], u_lqr, atol=1e-3)
    assert u[3] == 0.0


# ------------------------------------------------------------------ K5: MPC on the lifted model
class _EmbeddedNominal:
    """The exact nominal linear model written in lifted form (dictionary = identity on xi, quadratic rows 0)."""

    def __init__(self, nom):
        from rotorfail.koopman import Dictionary
        idx = [0, 1, 2, 3, 4, 6, 7, 8, 9]
        n = 9
        self.dic = Dictionary(np.zeros(n), np.ones(n))
        nz = self.dic.size
        self.A = np.zeros((nz, nz))
        self.A[0, 0] = 1.0
        self.A[1:1 + n, 1:1 + n] = nom.Ad[np.ix_(idx, idx)]
        self.B = np.zeros((nz, 3))
        self.B[1:1 + n] = nom.Bd[idx]
        self.C = np.zeros((n, nz))
        self.C[:, 1:1 + n] = np.eye(n)


def test_lifted_mpc_matches_failure_mpc_on_the_embedded_nominal_model():
    """With the exact nominal model embedded in lifted form, the first move equals FailureMPC's up to
    the altitude integration rule (rectangle in the lifted model, ZOH in FailureMPC) and the 1e-6 I
    weight on the lifted state. Measured difference on this state: 1.3e-7 N (the same with z = 0),
    so the tolerance is about three times that."""
    from rotorfail.dynamics import IDX_Q, make_state, quat_from_n
    from rotorfail.mpc import LiftedKoopmanMPC
    eq = relaxed_hover(P)
    ref = FailureMPC(P, eq, horizon=10)
    lm = LiftedKoopmanMPC(P, eq, _EmbeddedNominal(ref.nom), horizon=10)
    assert lm.dare["kind"] == "dare"
    x = make_state(w=eq.w + np.array([0.2, -0.1, 0.3]), d=(0, 0, 0.05), f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n + np.array([0.01, -0.01, 0.0]))
    ref.reset(x[13:16])
    lm.reset(x[13:16])
    u_ref, u_lm = ref(0.0, x), lm(0.0, x)
    assert lm.prob.status == "optimal"
    assert np.allclose(u_ref, u_lm, atol=4e-7)


def test_lifted_mpc_qp_is_optimal_on_random_near_trim_states(setup):
    from rotorfail.mpc import LiftedKoopmanMPC
    eq, data, nom = setup
    full = FullEDMDc.fit(data)
    lm = LiftedKoopmanMPC(P, eq, full, horizon=10)
    rng = np.random.default_rng(1)
    for _ in range(100):
        x7 = np.concatenate((rng.normal(0, 0.3, 3), rng.normal(0, 0.03, 2), rng.normal(0, 0.1, 2)))
        u = lm.act(x7)
        assert np.all(np.isfinite(u))
    assert lm.n_bad == 0


def test_mpc_weight_and_terminal_options_default_to_the_published_behaviour():
    import numpy as np
    from rotorfail.dynamics import make_state
    from rotorfail.equilibrium import relaxed_hover
    from rotorfail.mpc import FailureMPC
    from rotorfail.offset_free import OffsetFreeMPC
    from rotorfail.params import DEFAULT as P
    eq = relaxed_hover(P)
    x = make_state(w=eq.w + np.array([0.5, -0.4, 1.0]), f=np.concatenate((eq.f[:3], [0.0])))
    a, b = FailureMPC(P, eq, horizon=10), FailureMPC(P, eq, horizon=10, weights={}, terminal="dare")
    a.reset(x[13:16]), b.reset(x[13:16])
    assert np.allclose(a(0.0, x), b(0.0, x), atol=1e-9)
    heavy = FailureMPC(P, eq, horizon=10, weights=dict(w_att=60.0))
    heavy.reset(x[13:16])
    ua, uh = a(0.0, x), heavy(0.0, x)
    assert np.all(np.isfinite(uh)) and not np.allclose(ua, uh, atol=1e-6)    # heavier attitude weight changes the move
    none = FailureMPC(P, eq, horizon=10, terminal="none")
    none.reset(x[13:16])
    assert np.all(np.isfinite(none(0.0, x)))
    o1, o2 = OffsetFreeMPC(P, eq, horizon=10), OffsetFreeMPC(P, eq, horizon=10, weights={})
    o1.reset(x[13:16]), o2.reset(x[13:16])
    assert np.allclose(o1(0.0, x), o2(0.0, x), atol=1e-9)
