"""Validation against published numbers from the papers we discuss.

Sources (PDFs in literature/papers/):
  [ICRA14] Mueller & D'Andrea, ICRA 2014: Sec. V-A parameters, eqs. (21)-(28), (37)-(39), (50)-(64), Fig. 3
  [IJRR16] Mueller & D'Andrea, IJRR 2016: Sec. 5.1 parameters, Sec. 5.2 hover solutions (31)-(50)
  [TRO20]  Sun, Wang, Chu & de Visser, T-RO 2020 (Bebop 2): Table III, eq. (60)

Tolerances reflect the precision of the published numbers. Where a published value is not
reproduced, the test documents the gap and its explanation (see results/tables/validation_report.md).

Run:  .venv/bin/python -m pytest -q tests/test_paper_validation.py
"""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rotorfail.analysis import ctrb, scaled_rank  # noqa: E402
from rotorfail.equilibrium import relaxed_hover, single_rotor_hover, two_rotor_hover  # noqa: E402
from rotorfail.models import failed_linear  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import G, QuadParams  # noqa: E402
from rotorfail.validation import IJRR_CASES, GeneralMulticopter, ijrr_speeds  # noqa: E402


# ------------------------------------------------------------------ ICRA 2014
def test_icra_one_rotor_loss_equilibrium():
    """[ICRA14] eqs. (50)-(53), rho = 0.5: f = (2.05, 1.02, 2.05), r = 18.89, n_z = 0.958."""
    eq = relaxed_hover(P, 0.5)
    assert eq.f[0] == pytest.approx(2.05, abs=0.011)
    assert eq.f[1] == pytest.approx(1.02, abs=0.006)
    assert eq.w[2] == pytest.approx(18.89, rel=0.006)
    assert eq.n[2] == pytest.approx(0.958, abs=0.005)
    # Known gap: q = 5.37 vs published 5.69 (-6%). The paper's own numbers leave a residual in its
    # eq. (12); the other two published equilibria below are reproduced exactly with the same model.
    assert eq.w[1] == pytest.approx(5.69, rel=0.07)


def test_icra_eq21_yaw_rate():
    """[ICRA14] eq. (21): r = kappa_tau kappa_f (w1^2 - w2^2 + w3^2 - w4^2) / gamma."""
    eq = relaxed_hover(P, 0.5)
    om = eq.prop_speeds
    assert eq.w[2] == pytest.approx(P.kappa_tau * P.kappa_f * (om[0]**2 - om[1]**2 + om[2]**2 - om[3]**2) / P.gamma,
                                    rel=1e-12)


def test_icra_two_rotor_loss_equilibrium():
    """[ICRA14] eqs. (57)-(59): f1 = f3 = 2.45 N, w1 = w3 = -619 rad/s, w_B = (0, 0, 30.1)."""
    s = two_rotor_hover(P)
    assert s.f[0] == pytest.approx(2.45, abs=0.005)
    assert s.prop_speeds[0] == pytest.approx(-619, abs=0.5)
    assert np.allclose(s.w, [0, 0, 30.1], atol=0.05)


def test_icra_single_rotor_equilibrium():
    """[ICRA14] eqs. (62)-(64): f1 = 5.37 N, w1 = -915 rad/s, w_B = (14.7, 0, 33.0), n = (0.41, 0, 0.91)."""
    s = single_rotor_hover(P)
    assert s.f[0] == pytest.approx(5.37, abs=0.005)
    assert s.prop_speeds[0] == pytest.approx(-915, abs=0.5)
    assert np.allclose(s.w, [14.7, 0.0, 33.0], atol=0.05)
    assert np.allclose(s.n, [0.41, 0.0, 0.91], atol=0.005)


def test_icra_fig3_minima():
    """[ICRA14] Sec. V-D / Fig. 3: min |w| = 19.0 rad/s at rho = 0.655; min f1 = 2.04 N at rho = 0.563."""
    rhos = np.linspace(0.3, 1.0, 141)
    sols = [relaxed_hover(P, r) for r in rhos]
    wn = np.array([np.linalg.norm(s.w) for s in sols])
    f1 = np.array([s.f[0] for s in sols])
    assert wn.min() == pytest.approx(19.0, rel=0.03)          # ours 18.6 (q-dependent, see above)
    assert rhos[wn.argmin()] == pytest.approx(0.655, abs=0.04)
    assert f1.min() == pytest.approx(2.04, abs=0.015)
    assert rhos[f1.argmin()] == pytest.approx(0.563, abs=0.03)


def test_icra_coupling_constant_abar():
    """[ICRA14] eq. (28): a_bar = (Ixx_T - Izz_T)/Ixx_B r - Izz_P/Ixx_B (w1+w2+w3+w4),
    which is the (p, q) entry of the linearized attitude matrix, eq. (27)."""
    eq = relaxed_hover(P, 0.5)
    A = failed_linear(P, eq).A
    abar = (P.Ixx_T - P.Izz_T) / P.Ixx_B * eq.w[2] - P.Izz_P / P.Ixx_B * eq.prop_speeds.sum()
    assert A[0, 1] == pytest.approx(abar, rel=1e-6)
    assert A[1, 0] == pytest.approx(-abar, rel=1e-6)


def test_icra_two_rotor_controllability_condition():
    """[ICRA14] eqs. (37)-(39): with two opposing rotors the attitude is controllable unless
    a_bar = 0, i.e. (Ixx_T - Izz_T) r = 2 Izz_P w1, in which case the roll rate p is uncontrollable."""
    s = two_rotor_hover(P)
    lin = failed_linear(P, s)
    B = lin.B[:, [0, 2]]                              # inputs f1, f3 only
    assert scaled_rank(ctrb(lin.A, B)) == 7
    izz = P.Ixx_T - 2 * P.Izz_P * s.prop_speeds[0] / s.w[2]   # makes eq. (39) hold
    p39 = replace(P, Izz_T=izz)
    s39 = two_rotor_hover(p39)
    lin39 = failed_linear(p39, s39)
    assert lin39.A[0, 1] == pytest.approx(0.0, abs=1e-6)
    assert scaled_rank(ctrb(lin39.A, lin39.B[:, [0, 2]])) == 6
    # the lost direction is the roll rate p: it is in the uncontrollable subspace
    C = ctrb(lin39.A, lin39.B[:, [0, 2]])
    assert np.linalg.norm(C[0, :]) < 1e-9


# ------------------------------------------------------------------ IJRR 2016
@pytest.mark.parametrize("case", list(IJRR_CASES))
def test_ijrr_hover_solutions_published_parameters(case):
    """[IJRR16] (31)-(50) with the published parameters, solved by the independent general model:
    body rates within 5 % of the published ones and vertical force balance within 4 %."""
    M = GeneralMulticopter()
    c = IJRR_CASES[case]
    Om = ijrr_speeds(c["Omega"])
    w = M.hover_rates(Om, guess=np.array(c["w"]) + np.array([1.0, -1.0, 3.0]))
    ref = np.array(c["w"])
    assert np.linalg.norm(w - ref) <= 0.05 * max(np.linalg.norm(ref), 1.0)
    assert M.vertical_force_ratio(Om, w) == pytest.approx(1.0, abs=0.04)


@pytest.mark.parametrize("case", list(IJRR_CASES))
def test_ijrr_hover_solutions_within_rounding(case):
    """Same, with I_xx = 2.75e-3 (inside the rounding of the published 2.7e-3): all five cases
    within 1 % in body rate and 1 % in vertical force balance."""
    M = replace(GeneralMulticopter(), I_B=(2.75e-3, 2.75e-3, 5.2e-3))
    c = IJRR_CASES[case]
    Om = ijrr_speeds(c["Omega"])
    w = M.hover_rates(Om, guess=np.array(c["w"]) + np.array([1.0, -1.0, 3.0]))
    ref = np.array(c["w"])
    assert np.linalg.norm(w - ref) <= 0.01 * max(np.linalg.norm(ref), 1.0)
    assert M.vertical_force_ratio(Om, w) == pytest.approx(1.0, abs=0.01)


def test_ijrr_air_relative_thrust_explains_two_rotor_speed():
    """[IJRR16] (39)-(40): Omega = 643 rad/s and r = 24.5 rad/s. With thrust from the speed relative
    to the air, kappa_f (643 - 24.5)^2 = m g / 2; with body-relative thrust it would be 8 % too high."""
    kf, m = 6.41e-6, 0.50
    assert kf * (643 - 24.5) ** 2 == pytest.approx(m * G / 2, rel=0.003)
    assert kf * 643 ** 2 / (m * G / 2) == pytest.approx(1.08, abs=0.01)


# ------------------------------------------------------------------ Sun et al. T-RO 2020 (Bebop 2)
def bebop2():
    """[TRO20] Table III. Only the quantities that enter the two-rotor equilibrium matter here;
    the X-frame geometry does not (opposite rotors with equal thrust give zero roll/pitch torque)."""
    return QuadParams(m=0.410, l=0.145, Ixx_T=1.45e-3, Izz_T=2.52e-3, Izz_P=8.0e-6,
                      kappa_f=1.90e-6, kappa_tau=0.01, gamma=1.50e-3, f_min=0.0, f_max=10.0)


def test_tro20_two_rotor_equilibrium_eq60():
    """[TRO20] eq. (60): r = m g sigma / gamma, w = sqrt(m g / (2 kappa)). Published: 26.4 rad/s,
    1015 rad/s. Evaluating eq. (60) with Table III gives 26.8 and 1029 (the paper's numbers are ~1.5 %
    lower than its own formula); our solver must equal the formula and be within 2 % of the text."""
    p = bebop2()
    s = two_rotor_hover(p)
    r60 = p.m * G * p.kappa_tau / p.gamma
    w60 = np.sqrt(p.m * G / (2 * p.kappa_f))
    assert s.w[2] == pytest.approx(r60, rel=1e-9)
    assert abs(s.prop_speeds[0]) == pytest.approx(w60, rel=1e-9)
    assert s.w[2] == pytest.approx(26.4, rel=0.02)
    assert abs(s.prop_speeds[0]) == pytest.approx(1015, rel=0.02)
