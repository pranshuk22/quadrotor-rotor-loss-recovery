"""E10c (D8): certificate for the residual Koopman MPC loop.

Question. Can the residual-Koopman MPC loop (nominal MPC + clipped learned residual, horizon 20) be certified, and under which bound
on the plant mismatch? The proposal (section 6, "Link to RQ1") says this needs a bound on the true plant mismatch and an argument
for the MPC constraints; both are delivered as far as they go.

Fixed before running (do not tune afterwards)
  - Controller: FailureMPC, horizon 20, published weights, DARE terminal cost, residual EDMDc trained on family A (E6/E7 data), residual
    clipped at d_max (99.5 % percentile of the training residuals, 7 values): |d_hat| <= d_max holds by construction.
  - Unconstrained law and region: `rotorfail.mpc_cert` (closed form checked against the QP at 4 random states in the tests): u_j = M_j s + N_j d,
    face data robust to all |d| <= d_max; input bounds f_min and f_max.
  - Ellipsoid: largest log-volume ellipsoid in the region with contraction A_cl Q A_cl' <= (0.995 - 0.001) Q (verified at 0.995), scaled
    coordinates (1, 1, 1, 0.1, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5), and the command-filter states bounded by the physical thrust range
    min(f_bar - f_min... i.e. min(hi, -lo)) (the filter state is a convex combination of commands that lie in the bounds). Cross-check:
    Clarabel versus SCS on the volume objective.
  - Mismatch margin: robust invariance of {s'Ps <= 1}, P = Q^-1, under s+ = A_cl s + B G d_hat + d_true holds if
    sqrt(lam) + Delta_dhat + delta * sum_i ||P^(1/2) e_i|| <= 1 (triangle inequality in the P-norm; lam = 0.995; d_hat bounded by d_max,
    d_true by delta per physical state). Reported: Delta_dhat at d_max, the largest uniform delta*, and the required enlargement of the
    ellipsoid for the empirical mismatch.
  - Empirical mismatch: 1000 truth plants from `random_family` (seeds 9700 for the 500 boundary starts, 9701 for the 500 interior starts), start
    states on the boundary (V = 0.999999) or in the interior of the ellipsoid (10-state s = (x7, f_est), true motor thrusts set to the
    filter estimates), the actual residual MPC for 3 s on that plant. Per step the mismatch m_k = x7_{k+1} - nominal one-step prediction is
    recorded while V(s_k) <= 1; the empirical bound delta_emp is the maximum per component (and the 99.9 % percentile). This is an EMPIRICAL
    bound, not a proof.
  - Falsification of the certificate claim ('the loop stays in the ellipsoid'): the number of the 1000 runs in which V exceeds 1.001 at some
    step, and the maximum V. Because the certificate is conditional on the mismatch bound, a failure when delta_emp > delta* is the expected
    outcome and is reported as such.
  - Use in D6: the centre scaling alpha_c of the hand-over centres (published chain, w_sw = 10, f_spin = 2.95, tau in the E4 grid, exact hover)
    against this ellipsoid, i.e. the capture set for the residual MPC.

Outputs: results/tables/e10c_mpc_certificate.md, results/figures/e10c_mpc_certificate.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import TS, NominalModel, ResidualEDMD, generate  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.mpc_cert import (design_ellipsoid, mismatch_margin, unconstrained_law, unconstrained_region,  # noqa: E402
                                verify_design)
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import random_family, truth_family  # noqa: E402
from rotorfail.plotting import SERIES, apply_style, save  # noqa: E402
from rotorfail.reach import ChainSpec, chain_jacobian, centre_scaling  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

LAM = 0.995
SCALE = np.array([1.0, 1.0, 1.0, 0.1, 0.1, 0.5, 0.5, 0.5, 0.5, 0.5])
ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731
TAUS = [round(t, 3) for t in list(np.arange(0.0, 0.0601, 0.005)) + [0.08, 0.10, 0.13]]
EQ = relaxed_hover(P)
NOM = NominalModel.build(P, EQ)


class Recording(FailureMPC):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.rec = []

    def __call__(self, t, x):
        x7, fe = self.measure(x), self.fe.copy()
        out = super().__call__(t, x)
        self.rec.append((x7, fe, self.u_prev.copy()))
        return out


def setup():
    train = generate(truth_family("A"), P, EQ, 40, 4.0, seed=11)
    res = ResidualEDMD.fit(train, NOM, P)
    law = unconstrained_law(NOM, horizon=20)
    lo, hi = P.f_min - EQ.f[:3], P.f_max - EQ.f[:3]
    H, b = unconstrained_region(law, 20, lo, hi, res.d_max)
    box = {7 + i: float(min(hi[i], -lo[i])) for i in range(3)}
    return res, law, lo, hi, H, b, box


def sim_job(args):
    s0, plant_seed, Pm, res = args
    rng = np.random.default_rng(plant_seed)
    PT = random_family(rng)
    fe = s0[7:]
    x7 = s0[:7]
    n = np.array([EQ.n[0] + x7[3], EQ.n[1] + x7[4], 0.0])
    n[2] = np.sqrt(max(1 - n[0] ** 2 - n[1] ** 2, 1e-12))
    x = make_state(d=(0, 0, x7[5]), v=(0, 0, x7[6]), w=EQ.w + x7[:3], f=np.concatenate((EQ.f[:3] + fe, [0.0])))
    x[IDX_Q] = quat_from_n(n)
    c = Recording(P, EQ, horizon=20, residual=res)
    c.reset(x[13:16])
    log = simulate(x, c, PT, 3.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    R = c.rec
    V, mm = [], []
    for k in range(len(R) - 1):
        s = np.concatenate((R[k][0], R[k][1]))
        v = float(s @ Pm @ s)
        V.append(v)
        x1n, _ = NOM.step(R[k][0], R[k][1], R[k][2])
        if v <= 1.0:
            mm.append(R[k + 1][0] - x1n)
    return dict(vmax=float(np.max(V)), mismatch=np.array(mm), ok=bool(log.completed and np.min(log.n[:, 2]) > 0))


def main():
    apply_style()
    res, law, lo, hi, H, b, box = setup()
    des = design_ellipsoid(law, H, b, lam=LAM, scale=SCALE, box=box)
    ver = verify_design(des, law, H, b, lam=LAM)
    des2 = design_ellipsoid(law, H, b, lam=LAM, scale=SCALE, box=box, solver="SCS")
    Q = des["Q"]
    P_ = np.linalg.inv(Q)
    sa = np.sqrt(np.diag(Q))
    dstar, Dhat, w = mismatch_margin(law, Q, res.d_max, lam=LAM)
    L = ["# E10c: Certificate for the residual Koopman MPC loop", "",
         "The unconstrained finite-horizon MPC with DARE terminal cost is a linear law u = -K s + G d in the 10-state measurement s = (x7, f_est) and the "
         "(clipped) residual d (`rotorfail/mpc_cert.py`; checked against the QP). Settings fixed in the docstring of `experiments/e10c_mpc_certificate.py`.", "",
         f"Closed-loop spectral radius of A - B K: {np.max(np.abs(np.linalg.eigvals(law['Acl']))):.4f}. Learned-term bound d_max (99.5 % percentile, 7 states): "
         + ", ".join(f"{v:.4f}" for v in res.d_max) + ".", "",
         "## Unconstrained region and inscribed ellipsoid", "",
         f"Solver status {des['status']}; semi-axes (sqrt Q_ii): " + ", ".join(f"{n} {v:.3f}" for n, v in zip(["p", "q", "r", "n_x", "n_y", "z", "v_z", "f1", "f2", "f3"], sa)) + ".", "",
         f"Verification (scaled, numpy): worst eigenvalue of A_cl Q A_cl' - {LAM} Q = {ver['worst_contraction']:.2e}; smallest face margin b^2 - h'Qh = {ver['min_face_margin']:.1e}; "
         f"min eig Q = {ver['min_eig_Q']:.2e}. Cross-check: log det Q Clarabel {np.linalg.slogdet(des['Qs'])[1]:.5f} versus SCS "
         f"{np.linalg.slogdet(des2['Qs'])[1] if des2 else float('nan'):.5f}.", "",
         "## Mismatch margin (triangle inequality in the P-norm)", "",
         f"Contraction margin 1 - sqrt(lam) = {1 - np.sqrt(LAM):.4f}. Learned-term contribution Delta_dhat at d_max = {Dhat:.4f}. "
         f"Largest uniform one-step mismatch delta* the ellipsoid tolerates: {dstar:.2e} per physical state "
         f"(0 means the learned term alone already exceeds the margin).", ""]
    # empirical mismatch and falsification
    rng = np.random.default_rng(9700)
    Lc = np.linalg.cholesky(Q)
    starts = []
    for seed_set, n, boundary in ((9700, 500, True), (9701, 500, False)):
        r = np.random.default_rng(seed_set)
        for i in range(n):
            u = r.normal(size=10)
            u /= np.linalg.norm(u)
            rad = 0.999999 if boundary else r.uniform() ** (1 / 10)
            starts.append((Lc @ (u * rad), seed_set * 10000 + i, boundary))
    # keep only physical starts (|n_xy| < 1 and non-negative thrust estimates)
    ok = []
    for s0, ps, bd in starts:
        n_xy = EQ.n[:2] + s0[3:5]
        if n_xy @ n_xy < 0.98 and np.all(EQ.f[:3] + s0[7:] >= 0):
            ok.append((s0, ps, bd))
    with ProcessPoolExecutor(max_workers=8) as ex:
        out = list(ex.map(sim_job, [(s0, ps, P_, res) for s0, ps, bd in ok], chunksize=4))
    mm = np.vstack([o["mismatch"] for o in out if len(o["mismatch"])])
    emp_max, emp_p = np.max(np.abs(mm), axis=0), np.percentile(np.abs(mm), 99.9, axis=0)
    left = sum(o["vmax"] > 1 + 1e-3 for o in out)
    left_b = sum(o["vmax"] > 1 + 1e-3 for (s0, ps, bd), o in zip(ok, out) if bd)
    n_b = sum(bd for _, _, bd in ok)
    delta_total = Dhat + float(np.sum(w * emp_max))
    L += ["## Empirical mismatch and falsification", "",
          f"{len(ok)} runs from physical starts ({n_b} on the boundary, {len(ok) - n_b} interior; {len(starts) - len(ok)} sampled points were not physical and skipped), "
          "each on its own plant of `random_family`, 3 s with the actual residual MPC. Mismatch per step while the state is inside the ellipsoid "
          f"({len(mm)} steps):", "",
          "| State | p | q | r | n_x | n_y | z | v_z |", "|---|---|---|---|---|---|---|---|",
          "| max abs mismatch (empirical bound delta_emp) | " + " | ".join(f"{v:.2e}" for v in emp_max) + " |",
          "| 99.9th percentile | " + " | ".join(f"{v:.2e}" for v in emp_p) + " |", "",
          f"Largest tolerated uniform mismatch delta* = {dstar:.2e}; empirical maximum over components {np.max(emp_max):.2e}. With delta_emp the left side of the "
          f"invariance condition is sqrt(lam) + Delta_dhat + sum w_i delta_i = {np.sqrt(LAM) + delta_total:.3f} against 1: "
          f"{'satisfied' if np.sqrt(LAM) + delta_total <= 1 else 'NOT satisfied, so no certificate; the ellipsoid would have to be about %.0f times larger' % (delta_total / (1 - np.sqrt(LAM)))}.", "",
          f"Runs in which V(s) exceeded 1.001 at some step: {left} of {len(out)} ({left_b} of {n_b} boundary starts). Maximum V over all runs: {max(o['vmax'] for o in out):.2f}. "
          f"Runs that ended inverted or not completed: {sum(not o['ok'] for o in out)}.", ""]
    # hand-over centre scaling (D6 step 5)
    L += ["## Use as capture set in D6: centre of the hand-over set (published chain, exact hover)", "",
          "| tau (ms) | alpha_c (centre scaling onto the boundary; < 1 means outside) |", "|---|---|"]
    for tau in TAUS:
        c, J, info = chain_jacobian(ChainSpec(P, tau=tau, w_sw=10.0, f_spin=2.95))
        L.append(f"| {tau * 1e3:.0f} | {'-' if c is None else f'{centre_scaling(P_, c):.4f}'} |")
    L.append("")
    (ROOT / "results/tables/e10c_mpc_certificate.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.bar(range(7), emp_max, color=SERIES[0], label="empirical max |mismatch|")
    ax.axhline(dstar, color=SERIES[1], label="tolerated delta*")
    ax.set_yscale("log")
    ax.set_xticks(range(7))
    ax.set_xticklabels(["p", "q", "r", "n_x", "n_y", "z", "v_z"])
    ax.set_ylabel("one-step mismatch per state")
    ax.set_title("E10c · empirical plant mismatch vs the tolerated bound")
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e10c_mpc_certificate.png")


if __name__ == "__main__":
    main()
