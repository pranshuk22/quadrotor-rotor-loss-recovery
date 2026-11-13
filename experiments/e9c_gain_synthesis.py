"""E9c: capture-gain synthesis and later hand-over (task D5): "redesigned capture".

Question. The published strategy hands over at |w| > 10 rad/s to the failure LQR. E9a shows that hand-over
state is far from the relaxed hover and E9b shows that no hover-centred ellipsoid can contain it. Can the
certificate framework design (i) a capture gain K and (ii) a hand-over threshold w_sw such that the hand-over
state of the (open-loop) spin-up is certified, and what does it cost? Everything here is a labelled addition
("redesigned capture"); the published strategy (FailureLQR, w_sw = 10 rad/s) is always run alongside, unchanged.

Fixed before running (do not tune afterwards)
  - Spin-up thrust 2.95 N (flight data), nominal plant, exact hover start, tau = 0, for the design. The
    spin-up is open loop, so the hand-over state d(w_sw) does not depend on the capture gain.
  - Hand-over threshold grid w_sw in {10 (published), the later thresholds 12, 14, 16, 18 of plan task D6 step 7,
    and the earlier thresholds 8, 6, 4, 3} rad/s (a later threshold brings r closer to rbar but lets the tilt grow;
    an earlier one does the opposite; both directions are tested).
  - Scheduling box for each w_sw from d = d(w_sw): r in [rbar - h_r, rbar + h_r], h_r = 1.15 |d_r|;
    n_z in [0.5, 1]; half-widths H = (max(1.3|d_p|, 2), max(1.3|d_q|, 3), h_r, max(1.3|d_nx|, 0.15),
    max(1.3|d_ny|, 0.2), max(1.3|d_z|, 0.5), max(1.3|d_vz|, 1.0), 1.76, 1.1, 1.76).
    The f2 half-width 1.1 exceeds the physical 1.02 so that the stopped rotor (deviation -1.02) can be
    contained with slack; points of the ellipsoid with a negative thrust are not physical and are skipped
    (and counted) in the falsification.
  - Disc (self-consistency) condition as in E9b with n_z,lo = 0.5 (radius 0.866). Common quadratic
    Lyapunov function, 4 vertices x 8 saturation patterns, decay 0.1, eps 1e-5, scaled coordinates.
  - Gain-size bound ||F~ x~|| <= g on the ellipsoid, g in {2, 4, 8, 16} (scaled input units, a priori).
  - Objective: maximise beta such that beta d is in the ellipsoid (d the hand-over deviation). Comparison:
    the same box and objective with the published LQR gain (fixed-gain certificate, as E9b).
  - Remainder: the same P-norm check as E9b (kappa grid down to 1e-4, g_P <= 0.05, 4000 boundary samples plus local
    optimiser); beta_final = beta_LPV * sqrt(kappa).
  - Rejection rule for fast gains: reject a design whose closed-loop eigenvalues (A(rho) - B K at the vertices
    and at the trim) exceed 100 rad/s in magnitude (1.5 x the motor bandwidth; the plan's "a third of the
    motor bandwidth" cannot be met by the 10-state model whose motor-lag pole alone is at 67 rad/s;
    the LQR itself has 69 rad/s). Sampled-data stability of the frozen LPV loop on a 9 x 9 grid of (r, n_z) at
    1 ms and 5 ms is reported, and a design that fails it is rejected.
  - Verification as in E9b (worst design-block eigenvalue < -1e-6, linear-region min >= -1e-8, gain-bound block
    min >= -1e-8, Q > 0; SCS fallback; cross-check Clarabel vs SCS on one design (w_sw = 4, g = 8)).
  - Selection: for each w_sw the verified, non-rejected design with the largest beta_final (the gain used in the
    empirical chains); the design with the largest beta_final overall is falsified in the nonlinear plant:
    500 boundary and 500 interior samples (seeds 9100, 9101), controller CertifiedCaptureController,
    8 s runs; a failure is not captured, V above 1.001, or n_z <= 0.
  - Empirical protocol (new seeds, separate from the design): E4 Monte Carlo (x0_hover, seeds 1000 to 1039 plus
    the exact hover), tau in {0, 5, ..., 60, 80, 100, 130} ms, 10 s runs, controller period 1 ms, chains:
      published:       FailureLQR, w_sw = 10
      LQR, w_sw       FailureLQR with another threshold (all thresholds except 10)
      redesigned K, w_sw   selected K_w with threshold w_sw (all thresholds, including 10)
    P(SAFE) with Wilson intervals, tau_90 and tau_50 as in E4.
  - Regulation at the trim (design seeds 5000 to 5019, small deviations: dw ~ N(0, 1^2) rad/s, dn ~ N(0, 0.05^2),
    dz ~ N(0, 0.2^2) m, dv_z ~ N(0, 0.2^2) m/s, f at trim; FailureLQR vs the globally best K; 8 s runs):
    capture rate, median capture time, max |z|.

Outputs
  results/tables/e9c_gain_synthesis.md, results/figures/e9c_gain_synthesis.png
  results/certificates/e9c_designs.npz  (per design: Q, K, kappa, box H, hand-over deviation d, scheduling half-width;
                                         read by the delay-budget experiment E9d)
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from e4_delay_sweep import crossing, wilson, x0_hover  # noqa: E402
from e5_first_certificate import state_from_dev  # noqa: E402
from e9b_robust_certificate import gamma_p, sample_points  # noqa: E402
from rotorfail.certify import (robust_invariant_ellipsoid, slice_ellipse, synthesize_gain,  # noqa: E402
                               verify_design, verify_robust)
from rotorfail.control import (CertifiedCaptureController, DelaySupervisor, FailureLQR, HealthyLQR,  # noqa: E402
                               SpinUpThenLQR)
from rotorfail.dynamics import E3, make_state, quat_to_rot  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.lpv import QuasiLPV  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import MUTED, REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

F_SPIN = 2.95
W_SWS = (18, 16, 14, 12, 10, 8, 6, 4, 3)
GAINS = (2, 4, 8, 16)
NZ_LO = 0.5
DECAY = 0.1
KAPPAS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.07, 0.05, 0.03, 0.02, 0.01,
          0.007, 0.005, 0.003, 0.002, 0.001, 5e-4, 3e-4, 2e-4, 1e-4)
POLE_MAX = 100.0
TAUS = [round(t, 3) for t in list(np.arange(0.0, 0.0601, 0.005)) + [0.08, 0.10, 0.13]]
EVAL_SEEDS = list(range(1000, 1040))
REG_SEEDS = list(range(5000, 5020))
NAMES = ["p", "q", "r", "n_x", "n_y", "z", "v_z", "f1", "f2", "f3"]
ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731

EQ = relaxed_hover(P)
LPV = QuasiLPV(P, EQ)
K_LQR = FailureLQR(P, EQ).K
FB = EQ.f[:3]
UBAR = np.minimum(FB - P.f_min, P.f_max - FB)


class Probe(SpinUpThenLQR):
    ho = None

    def __call__(self, t, x):
        was = self.spinning_up
        u = super().__call__(t, x)
        if was and not self.spinning_up:
            self.ho = (t, x.copy())
        return u


def handover(w_sw, f_spin=F_SPIN):
    pr = Probe(P, FailureLQR(P, EQ), w_switch=w_sw, f_spin=f_spin)
    sup = DelaySupervisor(HealthyLQR(P), pr, t_fail=0.0, tau=0.0)
    simulate(make_state(), sup, P, 4.0, dt=1e-3, ctrl_period=1e-3, log_every=500, stop_fn=lambda t, x: pr.ho is not None)
    t, x = pr.ho
    n = quat_to_rot(x[6:10]).T @ E3
    return t, np.concatenate((x[10:13] - EQ.w, n[:2] - EQ.n[:2], [x[2], x[5]], x[13:16] - EQ.f[:3]))


def box(w_sw):
    t, d = handover(w_sw)
    hr = 1.15 * abs(d[2])
    H = np.array([max(1.3 * abs(d[0]), 2.0), max(1.3 * abs(d[1]), 3.0), hr, max(1.3 * abs(d[3]), 0.15),
                  max(1.3 * abs(d[4]), 0.2), max(1.3 * abs(d[5]), 0.5), max(1.3 * abs(d[6]), 1.0), 1.76, 1.1, 1.76])
    return d, H, hr


def vertices(hr):
    return LPV.vertices((EQ.w[2] - hr, EQ.w[2] + hr), (NZ_LO, 1.0))


def ceilings(d, H):
    R = np.sqrt(1 - NZ_LO ** 2)
    c = np.array([0.0, EQ.n[1]])
    lo, hi = 0.0, 50.0
    for _ in range(100):
        b = 0.5 * (lo + hi)
        ok = np.linalg.norm(c + b * d[3:5]) <= R and np.linalg.norm(c - b * d[3:5]) <= R
        lo, hi = (b, hi) if ok else (lo, b)
    return lo, float(np.min(H / np.maximum(np.abs(d), 1e-12)))


def sampled_radius(K, hr, T):
    worst = 0.0
    for r in np.linspace(EQ.w[2] - hr, EQ.w[2] + hr, 9):
        for nz in np.linspace(NZ_LO, 1.0, 9):
            A = LPV.A(r, nz)
            M = np.zeros((13, 13))
            M[:10, :10] = A
            M[:10, 10:] = LPV.B
            E = expm(M * T)
            worst = max(worst, float(np.max(np.abs(np.linalg.eigvals(E[:10, :10] - E[:10, 10:] @ K)))))
    return worst


def max_pole(K, hr):
    return max(float(np.max(np.abs(np.linalg.eigvals(A - LPV.B @ K)))) for A in vertices(hr) + [LPV.A(EQ.w[2], EQ.n[2])])


def design(w_sw, gain, solver="CLARABEL"):
    """gain = None: fixed LQR; otherwise the gain bound g. Returns the full result dict."""
    d, H, hr = box(w_sw)
    disc = ((3, 4), np.array([0.0, EQ.n[1]]), np.sqrt(1 - NZ_LO ** 2))
    Al = vertices(hr)
    if gain is None:
        res = robust_invariant_ellipsoid(Al, LPV.B, K_LQR, UBAR, H, direction=d, decay=DECAY, disc=disc, solver=solver)
        K = K_LQR
        ver = verify_robust(res, LPV.A, LPV.B, K, UBAR, H, np.linspace(EQ.w[2] - hr, EQ.w[2] + hr, 15),
                            np.linspace(NZ_LO, 1, 15), decay=DECAY, A_list=Al) if res["Q"] is not None else None
        ok = ver is not None and ver["worst_dynamics"] < -1e-6 and ver["worst_linear_region"] >= -1e-8
    else:
        res = synthesize_gain(Al, LPV.B, UBAR, H, direction=d, gain_bound=gain, decay=DECAY, disc=disc, solver=solver)
        K = None if res["F"] is None else -res["F"]
        ver = verify_design(res, Al, LPV.B, UBAR, H, decay=DECAY, gain_bound=gain) if res["Q"] is not None else None
        ok = (ver is not None and ver["worst_dynamics"] < -1e-6 and ver["worst_linear_region"] >= -1e-8
              and ver["worst_gain_bound"] >= -1e-8)
    return dict(w_sw=w_sw, gain=gain, d=d, H=H, hr=hr, res=res, K=K, ver=ver, ok=bool(ok), solver=solver)


def job(args):
    w_sw, gain = args
    r = design(w_sw, gain)
    if not r["ok"] and r["res"]["Q"] is not None:           # SCS fallback
        r2 = design(w_sw, gain, solver="SCS")
        if r2["ok"]:
            r = r2
            r["fell_back"] = True
    r.setdefault("fell_back", False)
    r["kappa"], r["gp"], r["beta_final"], r["pole"], r["rho1"], r["rho5"] = None, None, None, None, None, None
    if r["res"]["Q"] is not None:
        r["beta_lpv"] = r["res"]["beta"]
    if r["ok"]:
        for kap in KAPPAS:
            gp = gamma_p(r["res"], 0, kap)
            if gp <= 0.05:
                r["kappa"], r["gp"] = kap, gp
                r["beta_final"] = r["res"]["beta"] * np.sqrt(kap)
                break
        r["pole"] = max_pole(r["K"], r["hr"])
        r["rho1"] = sampled_radius(r["K"], r["hr"], 1e-3)
        r["rho5"] = sampled_radius(r["K"], r["hr"], 5e-3)
    r["res"] = {k: v for k, v in r["res"].items()}
    return r


def accepted(r):
    return (r["ok"] and r["kappa"] is not None and r["pole"] <= POLE_MAX and r["rho1"] < 1 and r["rho5"] < 1)


# ------------------------------------------------------------------ evaluation runs
def run_chain(args):
    chain, tau, seed = args
    ctrl = CertifiedCaptureController(P, EQ, gain=chain["K"]) if chain["K"] is not None else FailureLQR(P, EQ)
    sup = DelaySupervisor(HealthyLQR(P), SpinUpThenLQR(P, ctrl, w_switch=chain["w_sw"], f_spin=F_SPIN), t_fail=0.0, tau=tau)
    log = simulate(x0_hover(seed), sup, P, 10.0, dt=1e-3, ctrl_period=1e-3, log_every=5)
    o = evaluate(log, EQ)
    return dict(chain=chain["name"], tau=tau, seed=-1 if seed is None else seed, safe=bool(o.safe),
                captured=bool(o.captured), alt_loss=float(o.alt_loss))


def run_dev(args):
    dev, Pm, K = args
    x0 = state_from_dev(EQ, dev)
    if x0 is None or np.any(x0[13:16] < 0):
        return None
    f = CertifiedCaptureController(P, EQ, gain=K)
    f.reset(x0[13:16])
    log = simulate(x0, f, P, 8.0, dt=1e-3, ctrl_period=1e-3, alive_fn=ALIVE3, log_every=5)
    o = evaluate(log, EQ)
    e = np.column_stack((log.w - EQ.w, log.n[:, :2] - EQ.n[:2], log.x[:, 2], log.x[:, 5], log.x[:, 13:16] - EQ.f[:3]))
    return dict(captured=bool(o.captured), vmax=float(np.max(np.einsum("ij,jk,ik->i", e, Pm, e))), min_nz=float(o.min_nz))


def run_reg(args):
    seed, K = args
    rng = np.random.default_rng(seed)
    dev = np.concatenate((rng.normal(0, 1.0, 3), rng.normal(0, 0.05, 2), [rng.normal(0, 0.2), rng.normal(0, 0.2)], np.zeros(3)))
    x0 = state_from_dev(EQ, dev)
    f = FailureLQR(P, EQ) if K is None else CertifiedCaptureController(P, EQ, gain=K)
    f.reset(x0[13:16])
    log = simulate(x0, f, P, 8.0, dt=1e-3, ctrl_period=1e-3, alive_fn=ALIVE3, log_every=5)
    o = evaluate(log, EQ)
    return dict(captured=bool(o.captured), t_cap=float(o.t_capture), zmax=float(np.max(np.abs(log.z))))


def main():
    apply_style()
    out_t, out_f = ROOT / "results/tables", ROOT / "results/figures"
    jobs = [(w, g) for w in W_SWS for g in (None,) + GAINS]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(job, jobs))
    R = {(r["w_sw"], r["gain"]): r for r in res}
    (ROOT / "results/certificates").mkdir(parents=True, exist_ok=True)
    pack = {}
    for (w, g), r in R.items():
        if r["res"]["Q"] is None:
            continue
        key = f"w{w}_g{'lqr' if g is None else g}"
        pack[key + "_Q"] = r["res"]["Q"]
        pack[key + "_K"] = r["K"] if r["K"] is not None else np.zeros((3, 10))
        pack[key + "_kappa"] = np.array([np.nan if r["kappa"] is None else r["kappa"]])
        pack[key + "_ok"] = np.array([float(accepted(r))])
        pack[key + "_H"] = r["H"]
        pack[key + "_d"] = r["d"]
        pack[key + "_hr"] = np.array([r["hr"]])
    np.savez(ROOT / "results/certificates/e9c_designs.npz", **pack)
    L = ["# E9c: capture-gain synthesis and later hand-over (redesigned capture)", "",
         "The published strategy (FailureLQR, hand-over at |w| > 10 rad/s) is the reference in every table; the "
         "synthesised gains and the later thresholds are labelled **redesigned capture**. Choices fixed in the docstring of "
         "`experiments/e9c_gain_synthesis.py`. 'Certified' is used only for the LPV-model certificates that pass the numerical "
         "verification (quasi-LPV model, remainder estimated numerically, nonlinear falsification below).", "",
         "## Hand-over state versus the threshold w_sw (exact hover, tau = 0, 2.95 N)", "",
         "| w_sw (rad/s) | t_h (s) | Delta p, q, r (rad/s) | Delta n_x, n_y | Delta z, v_z | Delta f1, f2, f3 (N) | abs(Dn) | beta ceiling: disc / box |",
         "|---|---|---|---|---|---|---|---|"]
    for w in W_SWS:
        d, H, hr = box(w)
        t, _ = handover(w)
        cd, cb = ceilings(d, H)
        L.append(f"| {w} | {t:.3f} | {d[0]:+.2f}, {d[1]:+.2f}, {d[2]:+.2f} | {d[3]:+.3f}, {d[4]:+.3f} | {d[5]:+.2f}, {d[6]:+.2f} | "
                 f"{d[7]:+.2f}, {d[8]:+.2f}, {d[9]:+.2f} | {np.linalg.norm(d[3:5]):.2f} | {cd:.3f} / {cb:.3f} |")
    L += ["", "## Certified extent toward the hand-over state (beta >= 1 means contained)", "",
          "beta_LPV: remainder-free LPV certificate; kappa, g_P: remainder shrink (g_P <= 0.05); beta_final = beta_LPV sqrt(kappa). "
          "'pole' is the largest closed-loop eigenvalue magnitude (rad/s); rho(1 ms), rho(5 ms) the worst spectral radius of the sampled "
          "frozen-parameter loop. Status 'infeasible' marks the infeasibility boundary.", "",
          "| w_sw | gain | solver status | verified | beta_LPV | kappa | g_P | beta_final | pole | rho(1 ms) | rho(5 ms) | accepted |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in W_SWS:
        for g in (None,) + GAINS:
            r = R[(w, g)]
            nm = "published LQR gain" if g is None else f"synthesised, g = {g}"
            if r["res"]["Q"] is None:
                L.append(f"| {w} | {nm} | {r['res']['status']} | - | - | - | - | - | - | - | - | no |")
                continue
            f = lambda v, fmt: "-" if v is None else format(v, fmt)  # noqa: E731
            L.append(f"| {w} | {nm} | {r['res']['status']}{' (SCS)' if r['fell_back'] else ''} | {'yes' if r['ok'] else 'NO'} | "
                     f"{f(r['res']['beta'], '.4f')} | {f(r['kappa'], '')} | {f(r['gp'], '.4f')} | {f(r['beta_final'], '.4f')} | "
                     f"{f(r['pole'], '.1f')} | {f(r['rho1'], '.4f')} | {f(r['rho5'], '.4f')} | {'yes' if accepted(r) else 'no'} |")
    # verification
    L += ["", "## Verification (section 1.4), scaled units", "",
          "| w_sw | gain | worst eig of dynamics blocks | linear-region min eig | gain-bound min eig | min eig Q |", "|---|---|---|---|---|---|"]
    for w in W_SWS:
        for g in (None,) + GAINS:
            r = R[(w, g)]
            if r["ver"] is None:
                continue
            v = r["ver"]
            L.append(f"| {w} | {'LQR' if g is None else g} | {v['worst_dynamics']:.2e} | {v['worst_linear_region']:.1e} | "
                     f"{('-' if 'worst_gain_bound' not in v else format(v['worst_gain_bound'], '.1e'))} | {v['min_eig_Q']:.1e} |")
    # cross-check
    rc = design(4, 8, solver="SCS")
    rb = R[(4, 8)]
    if rc["res"]["beta"] and rb["res"]["beta"]:
        L += ["", "## Second-solver cross-check (w_sw = 4, g = 8, beta_LPV)", "",
              f"Clarabel {rb['res']['beta']:.6f} ({rb['res']['status']}); SCS {rc['res']['beta']:.6f} ({rc['res']['status']}); "
              f"relative difference {abs(rb['res']['beta'] - rc['res']['beta']) / rb['res']['beta']:.2e}."]
    else:
        L += ["", "## Second-solver cross-check (w_sw = 4, g = 8)", "", f"statuses: Clarabel {rb['res']['status']}, SCS {rc['res']['status']}."]

    # selection
    sel = {}
    for w in W_SWS:
        cand = [R[(w, g)] for g in GAINS if accepted(R[(w, g)])]
        if cand:
            sel[w] = max(cand, key=lambda r: r["beta_final"])
    best = max(sel.values(), key=lambda r: r["beta_final"]) if sel else None
    L += ["", "## Selected designs", "",
          "| w_sw | selected gain bound | beta_final | published-gain beta_final (same box) |", "|---|---|---|---|"]
    for w in W_SWS:
        rl = R[(w, None)]
        bl = "-" if rl["beta_final"] is None else f"{rl['beta_final']:.4f}"
        if w in sel:
            L.append(f"| {w} | {sel[w]['gain']} | {sel[w]['beta_final']:.4f} | {bl} |")
        else:
            L.append(f"| {w} | none accepted | - | {bl} |")
    L.append("")

    # falsification
    if best is not None:
        Qf = best["kappa"] * best["res"]["Q"]
        Pm = np.linalg.inv(Qf)
        bnd, inn = sample_points(Qf, 1200, 1200, 9100, 9101)
        L += [f"## Falsification of the best design (w_sw = {best['w_sw']}, g = {best['gain']}, kappa = {best['kappa']})", "",
              "Nonlinear nominal plant, CertifiedCaptureController, 8 s. Samples with a negative initial thrust are not physical and are skipped. "
              "Failure: not captured, V above 1.001, or n_z <= 0.", "",
              "| set | samples run | skipped (negative thrust) | not captured | left the set | inverted | max V |", "|---|---|---|---|---|---|---|"]
        with ProcessPoolExecutor(max_workers=8) as ex:
            for key, pts in (("boundary", bnd), ("interior", inn)):
                out = list(ex.map(run_dev, [(p, Pm, best["K"]) for p in pts], chunksize=8))
                ok = [o for o in out if o is not None][:500]
                L.append(f"| {key} | {len(ok)} | {sum(o is None for o in out)} | {sum(not o['captured'] for o in ok)} | "
                         f"{sum(o['vmax'] > 1 + 1e-3 for o in ok)} | {sum(o['min_nz'] <= 0 for o in ok)} | {max(o['vmax'] for o in ok):.3f} |")
        L.append("")
    # empirical chains
    chains = [dict(name="published (LQR, w_sw 10)", K=None, w_sw=10)]
    for w in W_SWS:
        if w != 10:
            chains.append(dict(name=f"LQR, w_sw {w}", K=None, w_sw=w))
    for w in W_SWS:
        if w in sel:
            chains.append(dict(name=f"redesigned K, w_sw {w}", K=sel[w]["K"], w_sw=w))
    jobs = [(c, t, s) for c in chains for t in TAUS for s in [None] + EVAL_SEEDS]
    with ProcessPoolExecutor(max_workers=8) as ex:
        ev = list(ex.map(run_chain, jobs, chunksize=4))
    L += ["## Empirical protocol (E4 Monte Carlo, new seeds 1000 to 1039, nominal plant)", "",
          "P(SAFE) over the 40 starts; exact-hover start in the last block. tau_90 and tau_50 as in E4 (linear interpolation on the "
          "grid 0 to 60 ms).", "",
          "| chain | tau_90 | tau_50 | " + " | ".join(f"{t * 1e3:.0f} ms" for t in TAUS) + " |", "|---|---|---|" + "---|" * len(TAUS)]
    grid = np.array([t for t in TAUS if t <= 0.0601])
    stats = {}
    for c in chains:
        pr = []
        for t in TAUS:
            rr = [e for e in ev if e["chain"] == c["name"] and e["tau"] == t and e["seed"] >= 0]
            pr.append(sum(e["safe"] for e in rr) / len(rr))
        p = np.array(pr)
        t90, t50 = crossing(grid, p[:len(grid)], 0.9), crossing(grid, p[:len(grid)], 0.5)
        stats[c["name"]] = (p, t90, t50)
        ms = lambda v: ">60 ms" if np.isnan(v) else f"{v * 1e3:.0f} ms"  # noqa: E731
        L.append(f"| {c['name']} | {ms(t90)} | {ms(t50)} | " + " | ".join(f"{v:.2f}" for v in p) + " |")
    L += ["", "Exact hover start, SAFE by tau (1 = SAFE):", "",
          "| chain | " + " | ".join(f"{t * 1e3:.0f}" for t in TAUS) + " |", "|---|" + "---|" * len(TAUS)]
    for c in chains:
        row = []
        for t in TAUS:
            e = [x for x in ev if x["chain"] == c["name"] and x["tau"] == t and x["seed"] == -1][0]
            row.append("1" if e["safe"] else "0")
        L.append(f"| {c['name']} | " + " | ".join(row) + " |")
    L.append("")

    # regulation
    if best is not None:
        L += ["## Regulation at the trim (design seeds 5000 to 5019, small deviations)", "",
              "| controller | captured | median capture time (s) | max abs z (m), median |", "|---|---|---|---|"]
        for name, K in (("published LQR", None), (f"redesigned K (w_sw {best['w_sw']}, g {best['gain']})", best["K"])):
            with ProcessPoolExecutor(max_workers=8) as ex:
                rg = list(ex.map(run_reg, [(s, K) for s in REG_SEEDS]))
            tc = [r["t_cap"] for r in rg if r["captured"]]
            L.append(f"| {name} | {sum(r['captured'] for r in rg)}/{len(rg)} | {np.median(tc) if tc else float('nan'):.2f} | "
                     f"{np.median([r['zmax'] for r in rg]):.3f} |")
        L.append("")
    (out_t / "e9c_gain_synthesis.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    for k, c in enumerate(chains):
        p, _, _ = stats[c["name"]]
        axs[0].plot([t * 1e3 for t in TAUS], p, marker="o", ms=3, color=SERIES[k % 8], ls="-" if c["K"] is None else "--", label=c["name"])
    axs[0].set_xlabel("detection delay τ (ms)")
    axs[0].set_ylabel("P(SAFE), 40 new starts")
    axs[0].set_title("E9c · empirical recovery, published vs redesigned capture")
    axs[0].legend(fontsize=6.5, ncol=2)
    if best is not None:
        Pm = np.linalg.inv(best["kappa"] * best["res"]["Q"])
        E = slice_ellipse(Pm, 2, 4)
        axs[1].plot(E[0], E[1], color=SERIES[0], lw=2, label=f"certificate, w_sw {best['w_sw']}")
        for w in W_SWS:
            d, _, _ = box(w)
            axs[1].scatter([d[2]], [d[4]], marker="*", s=70, color=SERIES[(w * 3) % 8], label=f"hand-over, w_sw {w}")
        axs[1].axhline(0, color=REF, lw=0.6)
        axs[1].axvline(0, color=REF, lw=0.6)
        axs[1].set_xlabel("Δr = r − r̄ (rad/s)")
        axs[1].set_ylabel("Δn_y")
        axs[1].set_title("E9c · best redesigned certificate, slice (Δr, Δn_y)")
        axs[1].legend(fontsize=7)
    fig.tight_layout()
    save(fig, out_f / "e9c_gain_synthesis.png")


if __name__ == "__main__":
    main()
