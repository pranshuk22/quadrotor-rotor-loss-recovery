"""E9b: r-robust, saturation-aware capture certificate for the existing failure LQR (task D4).

Question. Is there a certified invariant ellipsoid of the closed loop (published failure LQR, nominal
plant) that is valid over a range of yaw rates r and vertical tilt components n_z, and does it contain
the hand-over state of the published strategy (E9a)? How does the certified extent depend on the size
of the scheduling box?

Model. The 10-state quasi-LPV closed loop of `rotorfail/lpv.py`, e' = A(rho) e + B sat(-K e) + R(e),
K = the gain of `FailureLQR` (designed at the relaxed hover), rho = (r, n_z), saturation levels
ubar = min(fbar - f_min, f_max - fbar) = (1.76, 0.82, 1.76) N (as E5). z and v_z are INCLUDED: the plan
assumed they do not feed back into the attitude, but K has z and v_z columns of size 1.0 to 1.5 (see
the completion-plan deviation list), so the closed loop is not block-triangular.

Fixed before running (do not tune afterwards)
  - Scheduling-box family, one scalar nu in {1.0, 0.8, 0.6, 0.4, 0.25, 0.15}:
      r in [rbar - 11 nu, rbar + 11 nu];  n_z in [1 - 0.8 nu, 1]  (nu = 1: [7.81, 29.81] and [0.2, 1]);
      box half-widths H(nu) = nu * (4, 8, 11, 0.5, 1.0, 3, 4, 1.76, 1.02, 1.76) for
      (p, q, r, n_x, n_y, z, v_z, f1, f2, f3). The ellipsoid is confined to this box (Q_ii <= H_i^2).
      The motor half-widths are the physical thrust range min(fbar_i, f_max - fbar_i) (rotor 2 stopped is
      0 N, deviation -1.02), not the saturation level ubar used in E5 (documented deviation).
  - Scaled coordinates: x~ = x / H(nu); inputs scaled by ubar.
  - Common quadratic Lyapunov function (a parameter-dependent matrix is not attempted; the problem is
    already restrictive on a common Q), all 4 vertices of the (r, n_z) box x all 8 saturation patterns,
    decay rate 0.1 1/s, contraction margin eps = 1e-5.
  - Self-consistency: r projection inside the box (Q_rr <= (11 nu)^2); (n_x, n_y) projection shifted by
    nbar_xy inside the disc of radius sqrt(1 - n_z,lo^2) (support-function polygon with 64 sides, a
    sufficient condition; the corner-box form of the plan cannot be met by any ellipsoid centred at the
    hover that contains the hand-over, see the analytic ceiling below).
  - Remainder R(e): the numerical bound (dense sampling plus a local optimiser, restricted to
    n_z >= n_z,lo, 'remainder_sup') is NOT put into the SDP (probe: that makes the certified r semi-axis
    0.04 to 0.24 rad/s). Instead the remainder-free LPV problem is solved, and the S-procedure block
    [[L + mu I, gamma Q], [gamma Q, -mu I]] is checked a posteriori with the decay relaxed to 0.05, on
    the ellipsoid kappa Q for a decreasing kappa in {1, 0.9, ..., 0.1, 0.07, 0.05, 0.03, 0.02, 0.01}
    (gamma recomputed on the box of the shrunk ellipsoid; mu on a log grid). The final certificate is the
    largest kappa that passes. Scaling (Q, Y) by kappa < 1 keeps all Hu-Lin conditions.
  - METHOD CHANGE after run 1 (kept in results/tables/e9b_run1_euclidean_check.md): the Euclidean-sector
    check above failed for every box and kappa (the sector bound in the Euclidean norm is badly matched to
    thin ellipsoids). It is replaced by the P-norm bound: with the Hu-Lin conditions at decay 0.1,
    V' <= -0.2 V + 2 e'P R(e) <= -2 (0.1 - g_P) V on E_kappa, where
    g_P = max over the boundary of E_kappa of sqrt(R' P_kappa R) (e'P_kappa e = 1 on the boundary).
    A kappa passes when g_P <= 0.05 (guaranteed decay >= 0.05 1/s). g_P is estimated by 4000 boundary
    samples plus a local optimiser from the 5 worst; this is a numerical estimate, not a proof.
    Second change: if the Clarabel solution fails the numerical verification (worst dynamics eigenvalue
    >= -1e-6, linear-region minimum < -1e-8), the problem is re-solved with SCS and that solution is
    verified; if it also fails, that nu has no certificate.
  - Objectives: (b) log det Q; (a) maximise beta such that beta * d is in E, d = the exact-hover
    hand-over deviation at tau = 0, f_spin = 2.95 N (row of results/tables/e9a_handover.csv).
  - Analytic ceiling: any ellipsoid centred at the hover that contains beta d also contains -beta d, so
    the disc condition gives beta <= beta_disc(nu) with |nbar_xy - beta d_xy| <= sqrt(1 - n_z,lo^2);
    the box gives beta <= min_i H_i / |d_i|. Both are reported.
  - Verification (section 1.4 of the plan) on the final certificate: worst eigenvalue over every
    vertex x pattern block and over a 15 x 15 grid of (r, n_z) (225 points) x patterns, with and without
    the remainder block; linear-region and Q > 0 minima; solver status; second-solver cross-check
    (Clarabel vs SCS, objective (a), nu = 0.6, before shrinking).
  - Falsification in the nonlinear nominal plant with FailureLQR, 8 s runs, controller period 1 ms:
    for the log det certificates at nu = 1.0 and nu = 0.6 (after shrinking), 500 boundary samples
    (V = 0.999999) and 500 interior samples (volume-uniform), seeds 9000 (boundary), 9001 (interior).
    A failure: not captured (metrics.py), or V leaves 1 + 1e-3 along the run, or n_z <= 0.
  - Hand-over scaling: for the hand-over states of E9a (both f_spin, tau grid, exact and Monte Carlo)
    the scaling alpha of the largest-volume certificate is reported with the count inside.

Outputs
  results/tables/e9b_robust_certificate.md, results/figures/e9b_robust_certificate.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import csv
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

from e5_first_certificate import state_from_dev  # noqa: E402
from rotorfail.certify import (invariant_ellipsoid, robust_invariant_ellipsoid, slice_ellipse,  # noqa: E402
                               verify_robust, _lmi_blocks)
from rotorfail.control import FailureLQR  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.lpv import QuasiLPV, remainder_sup  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import MUTED, REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

NUS = (1.0, 0.8, 0.6, 0.4, 0.25, 0.15)
H0 = np.array([4, 8, 11, 0.5, 1.0, 3, 4, 1.76, 1.02, 1.76], float)
DECAY = 0.1
DECAY_REM = 0.05
KAPPAS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.07, 0.05, 0.03, 0.02, 0.01)
MUS = np.logspace(-6, 3, 61)
NAMES = ["p", "q", "r", "n_x", "n_y", "z", "v_z", "f1", "f2", "f3"]
N_BOUNDARY = N_INTERIOR = 500
T_RUN = 8.0
ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731

EQ = relaxed_hover(P)
LPV = QuasiLPV(P, EQ)
K = FailureLQR(P, EQ).K
FB = EQ.f[:3]
UBAR = np.minimum(FB - P.f_min, P.f_max - FB)


def box(nu):
    H = nu * H0
    rh = 11.0 * nu
    nzlo = 1.0 - 0.8 * nu
    return H, rh, nzlo


def handover_dev():
    with open(ROOT / "results/tables/e9a_handover.csv") as fh:
        for r in csv.DictReader(fh):
            if r["f_spin"] == "2.95" and float(r["tau"]) == 0.0 and r["seed"] == "-1":
                return np.array([float(r[f"d_{n}"]) for n in NAMES])
    raise RuntimeError("hand-over row not found")


def vertices(nu):
    H, rh, nzlo = box(nu)
    return LPV.vertices((EQ.w[2] - rh, EQ.w[2] + rh), (nzlo, 1.0))


def solve(nu, objective, solver="CLARABEL"):
    H, rh, nzlo = box(nu)
    d = handover_dev() if objective == "a" else None
    return robust_invariant_ellipsoid(vertices(nu), LPV.B, K, UBAR, H, direction=d, decay=DECAY,
                                      disc=((3, 4), np.array([0.0, EQ.n[1]]), np.sqrt(1 - nzlo ** 2)),
                                      solver=solver)


def gamma_p(res, nu, kappa, n=4000, seed=0):
    """g_P = max over the boundary of kappa*E of sqrt(R' P R), P = (kappa Q)^-1 (numerical estimate)."""
    from scipy.optimize import minimize
    Qk = kappa * res["Q"]
    L = np.linalg.cholesky(Qk)
    Pk = np.linalg.inv(Qk)
    rng = np.random.default_rng(seed)
    U = rng.normal(size=(n, 10))
    U /= np.linalg.norm(U, axis=1, keepdims=True)

    def g(u):
        e = L @ (u / np.linalg.norm(u))
        r = LPV.remainder(e)
        return float(np.sqrt(r @ Pk @ r))

    vals = np.array([g(u) for u in U])
    best = float(vals.max())
    for k in np.argsort(-vals)[:5]:
        res_o = minimize(lambda u: -g(u), U[k], method="Nelder-Mead", options=dict(maxiter=400, xatol=1e-6, fatol=1e-12))
        best = max(best, -float(res_o.fun))
    return best


def shrink(res, nu):
    """Largest kappa with g_P <= 0.05 (None if none)."""
    for kappa in KAPPAS:
        gp = gamma_p(res, nu, kappa)
        if gp <= 0.05:
            return kappa, gp
    return None, None


def worst_over_grid(res, nu, kappa, mu, gamma, decay):
    H, rh, nzlo = box(nu)
    rg = np.linspace(EQ.w[2] - rh, EQ.w[2] + rh, 15)
    ng = np.linspace(nzlo, 1.0, 15)
    scaled = dict(res)
    scaled["Qs"], scaled["Y"], scaled["mu"] = kappa * res["Qs"], kappa * res["Y"], mu
    return verify_robust(scaled, LPV.A, LPV.B, K, UBAR, H, rg, ng, decay=decay, gamma=gamma, A_list=vertices(nu))


def disc_ceiling(nu, d):
    H, rh, nzlo = box(nu)
    R = np.sqrt(1 - nzlo ** 2)
    c = np.array([0.0, EQ.n[1]])
    lo, hi = 0.0, 50.0
    for _ in range(100):
        b = 0.5 * (lo + hi)
        ok = np.linalg.norm(c + b * d[3:5]) <= R and np.linalg.norm(c - b * d[3:5]) <= R
        lo, hi = (b, hi) if ok else (lo, b)
    return lo, float(np.min(H / np.maximum(np.abs(d), 1e-12)))


def job(args):
    nu, obj = args
    res = solve(nu, obj)
    ver = worst_over_grid(res, nu, 1.0, 0.0, 0.0, DECAY) if res["Q"] is not None else None
    fell_back = False
    if ver is None or ver["worst_dynamics"] >= -1e-6 or ver["worst_linear_region"] < -1e-8:
        res2 = solve(nu, obj, solver="SCS")
        if res2["Q"] is not None:
            ver2 = worst_over_grid(res2, nu, 1.0, 0.0, 0.0, DECAY)
            if ver is None or ver2["worst_dynamics"] < ver["worst_dynamics"]:
                res, ver, fell_back = res2, ver2, True
    out = dict(nu=nu, obj=obj, status=res["status"], Q=res["Q"], Qs=res["Qs"], Y=res["Y"], beta=res["beta"],
               value=res["value"], verify=ver, fell_back=fell_back, kappa=None, gp=None)
    ok = ver is not None and ver["worst_dynamics"] < -1e-6 and ver["worst_linear_region"] >= -1e-8
    out["ok"] = bool(ok)
    if ok:
        out["kappa"], out["gp"] = shrink(res, nu)
    return out


def sample_points(Q, n_b, n_i, seed_b, seed_i):
    L = np.linalg.cholesky(Q)
    rb, ri = np.random.default_rng(seed_b), np.random.default_rng(seed_i)
    u = rb.normal(size=(n_b, 10))
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    bnd = (u @ L.T) * 0.999999
    v = ri.normal(size=(n_i, 10))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    inn = (v * (ri.uniform(size=(n_i, 1)) ** (1 / 10))) @ L.T
    return bnd, inn


def run_dev(args):
    dev, Pm = args
    x0 = state_from_dev(EQ, dev)
    if x0 is None:
        return None
    f = FailureLQR(P, EQ)
    f.reset(x0[13:16])
    log = simulate(x0, f, P, T_RUN, dt=1e-3, ctrl_period=1e-3, alive_fn=ALIVE3, log_every=5)
    o = evaluate(log, EQ)
    e = np.column_stack((log.w - EQ.w, log.n[:, :2] - EQ.n[:2], log.x[:, 2], log.x[:, 5], log.x[:, 13:16] - EQ.f[:3]))
    vmax = float(np.max(np.einsum("ij,jk,ik->i", e, Pm, e)))
    return dict(captured=bool(o.captured), vmax=vmax, min_nz=float(o.min_nz))


def falsify(Q, Pm, seeds):
    bnd, inn = sample_points(Q, N_BOUNDARY, N_INTERIOR, *seeds)
    out = {}
    with ProcessPoolExecutor(max_workers=8) as ex:
        for key, pts in (("boundary", bnd), ("interior", inn)):
            res = list(ex.map(run_dev, [(p, Pm) for p in pts], chunksize=8))
            res = [r for r in res if r is not None]
            out[key] = dict(n=len(res), not_captured=sum(not r["captured"] for r in res),
                            left=sum(r["vmax"] > 1 + 1e-3 for r in res), inverted=sum(r["min_nz"] <= 0 for r in res),
                            vmax=max(r["vmax"] for r in res))
    return out


def main():
    apply_style()
    out_t, out_f = ROOT / "results/tables", ROOT / "results/figures"
    d = handover_dev()
    # E5 reference (LTI certificate, decay 0.1)
    f = FailureLQR(P, EQ)
    box5 = [np.inf] * 7 + list(UBAR)
    e5 = invariant_ellipsoid(f.model.A, f.model.B, f.K, UBAR, decay=DECAY, box=box5)
    jobs = [(nu, o) for nu in NUS for o in ("b", "a")]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(job, jobs))
    R = {(r["nu"], r["obj"]): r for r in res}

    L = ["# E9b: r-robust saturation-aware certificate for the published failure LQR (LPV model, nominal plant)", "",
         "Closed loop e' = A(rho) e + B sat(-K e) + R(e) on the 10-state quasi-LPV model, rho = (r, n_z). "
         "Hu-Lin conditions at the 4 vertices x 8 saturation patterns with a common quadratic Lyapunov "
         "function, decay 0.1, scaled coordinates. The remainder R is handled a posteriori (shrinking factor "
         "kappa). Choices fixed in the docstring of `experiments/e9b_robust_certificate.py`. "
         "Certified here means: for the quasi-LPV model, remainder bounded numerically on the box, "
         "re-verified with numpy; the nonlinear check is the falsification section.", "",
         f"Hand-over direction d (exact hover, tau = 0, f_spin = 2.95 N): " + ", ".join(
             f"{n} {v:+.3f}" for n, v in zip(NAMES, d)) + ".", "",
         "## Certificate versus the size of the scheduling box (nu)", "",
         "| nu | r range (rad/s) | n_z range | objective | solver status | kappa (remainder shrink) | final semi-axes p, q, r | n_x, n_y | z, v_z | "
         "beta to d (final) | beta ceiling: disc / box |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for nu in NUS:
        H, rh, nzlo = box(nu)
        cd, cb = disc_ceiling(nu, d)
        for o in ("b", "a"):
            r = R[(nu, o)]
            if r["Q"] is None or not r["ok"]:
                L.append(f"| {nu} | [{EQ.w[2] - rh:.2f}, {EQ.w[2] + rh:.2f}] | [{nzlo:.2f}, 1] | "
                         f"{'log det' if o == 'b' else 'toward d'} | {r['status']} | not verified | - | - | - | - | {cd:.3f} / {cb:.3f} |")
                continue
            kap = r["kappa"]
            if kap is None:
                L.append(f"| {nu} | [{EQ.w[2] - rh:.2f}, {EQ.w[2] + rh:.2f}] | [{nzlo:.2f}, 1] | "
                         f"{'log det' if o == 'b' else 'toward d'} | {r['status']} | none passes | - | - | - | - | {cd:.3f} / {cb:.3f} |")
                continue
            Qf = kap * r["Q"]
            sa = np.sqrt(np.diag(Qf))
            bet = float(1.0 / np.sqrt(d @ np.linalg.solve(Qf, d)))
            L.append(f"| {nu} | [{EQ.w[2] - rh:.2f}, {EQ.w[2] + rh:.2f}] | [{nzlo:.2f}, 1] | "
                     f"{'log det' if o == 'b' else 'toward d'} | {r['status']} | {kap} | "
                     f"{sa[0]:.2f}, {sa[1]:.2f}, {sa[2]:.2f} | {sa[3]:.3f}, {sa[4]:.3f} | {sa[5]:.2f}, {sa[6]:.2f} | "
                     f"{bet:.4f} | {cd:.3f} / {cb:.3f} |")
    sa5 = np.sqrt(np.diag(e5["Q"]))
    bet5 = float(1.0 / np.sqrt(d @ np.linalg.solve(e5["Q"], d)))
    L += ["", f"E5 (LTI at the relaxed hover, same decay): semi-axes p, q, r = {sa5[0]:.2f}, {sa5[1]:.2f}, {sa5[2]:.2f}; "
          f"n_x, n_y = {sa5[3]:.3f}, {sa5[4]:.3f}; z, v_z = {sa5[5]:.2f}, {sa5[6]:.2f}; beta to d = {bet5:.4f}. "
          "The E5 ellipsoid used the saturation level (not the physical range) as motor-state box and no box on z, v_z.", ""]

    # verification
    L += ["## Verification (section 1.4 of the plan), scaled units", "",
          "Worst (largest) eigenvalue of any dynamics block over the 4 vertices x 8 saturation patterns and the "
          "15 x 15 grid x 8 patterns (must be below -1e-6), the smallest eigenvalue of the linear-region blocks "
          "(PSD, accepted down to -1e-8) and of Q, and the remainder measure g_P of the final kappa "
          "(guaranteed decay 2 (0.1 - g_P) when g_P < 0.1).", "",
          "| nu | objective | solver used | worst eig of dynamics blocks | linear-region min eig | min eig Q | passes | g_P at final kappa |",
          "|---|---|---|---|---|---|---|---|"]
    for nu in NUS:
        for o in ("b", "a"):
            r = R[(nu, o)]
            if r["verify"] is None:
                L.append(f"| {nu} | {'log det' if o == 'b' else 'toward d'} | - | no solution | | | no | |")
                continue
            v = r["verify"]
            L.append(f"| {nu} | {'log det' if o == 'b' else 'toward d'} | {'SCS (fallback)' if r['fell_back'] else 'Clarabel'} | "
                     f"{v['worst_dynamics']:.2e} | {v['worst_linear_region']:.1e} | {v['min_eig_Q']:.1e} | "
                     f"{'yes' if r['ok'] else 'NO'} | {'-' if r['gp'] is None else f'{r['gp']:.4f}'} |")
    L.append("")

    # cross-check
    nu_c = 0.6
    r_c = solve(nu_c, "a", solver="SCS")
    rb = R[(nu_c, "a")]
    if r_c["beta"] and rb["beta"]:
        L += ["## Second-solver cross-check (objective: extent toward d, nu = 0.6, before shrinking)", "",
              f"Clarabel: beta = {rb['beta']:.6f} ({rb['status']}); SCS: beta = {r_c['beta']:.6f} ({r_c['status']}); "
              f"relative difference {abs(rb['beta'] - r_c['beta']) / rb['beta']:.2e}.", ""]
    else:
        L += ["## Second-solver cross-check", "", f"SCS status {r_c['status']}, Clarabel status {rb['status']}: "
              "no comparable objective.", ""]

    # falsification
    L += ["## Falsification in the nonlinear nominal plant (log det certificate after shrinking)", "",
          "Samples on the boundary (V = 0.999999) and in the interior; initial state in capture coordinates; "
          "FailureLQR, 8 s. A failure is: not captured, V above 1.001 at some time, or n_z <= 0.", "",
          "| nu | kappa | set | samples | not captured | left the set (V > 1.001) | inverted | max V |", "|---|---|---|---|---|---|---|---|"]
    fals = {}
    for nu in (1.0, 0.6):
        r = R[(nu, "b")]
        if r["Q"] is None or not r["ok"] or r["kappa"] is None:
            L.append(f"| {nu} | - | no certificate | | | | | |")
            continue
        Qf = r["kappa"] * r["Q"]
        fr = falsify(Qf, np.linalg.inv(Qf), (9000, 9001))
        fals[nu] = fr
        for key in ("boundary", "interior"):
            x = fr[key]
            L.append(f"| {nu} | {r['kappa']} | {key} | {x['n']} | {x['not_captured']} | {x['left']} | {x['inverted']} | {x['vmax']:.3f} |")
    L.append("")

    # hand-over scaling with the largest volume certificate
    best = None
    for nu in NUS:
        r = R[(nu, "b")]
        if r["Q"] is not None and r["ok"] and r["kappa"] is not None:
            vol = np.linalg.slogdet(r["kappa"] * r["Q"])[1]
            if best is None or vol > best[0]:
                best = (vol, nu, r["kappa"] * r["Q"])
    rows = list(csv.DictReader(open(out_t / "e9a_handover.csv")))
    hh = [np.array([float(r[f"d_{n}"]) for n in NAMES]) for r in rows if r["handed"] == "True"]
    if best:
        _, nu_b, Qb = best
        al = np.array([1.0 / np.sqrt(h @ np.linalg.solve(Qb, h)) for h in hh])
        L += ["## Hand-over states of E9a against the largest-volume robust certificate", "",
              f"Largest log-volume certificate: nu = {nu_b}. Hand-over states: {len(hh)}; inside (alpha >= 1): "
              f"{int(np.sum(al >= 1))}; largest alpha {al.max():.4f}; median alpha {np.median(al):.4f}. "
              f"E5 for comparison: largest alpha 0.353.", ""]
    (out_t / "e9b_robust_certificate.md").write_text("\n".join(L))
    print("\n".join(L))

    # figure: slices
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    pts = [np.array([float(r[f"d_{n}"]) for n in NAMES]) for r in rows if r["handed"] == "True" and r["tau"] == "0.0"]
    sel = [(0.15, SERIES[1]), (0.4, SERIES[2]), (1.0, SERIES[3])]
    for ax, (i, j, xl, yl) in zip(axs, [(2, 4, "Δr = r − r̄ (rad/s)", "Δn_y"), (3, 4, "Δn_x", "Δn_y")]):
        E = slice_ellipse(e5["P"], i, j)
        ax.plot(E[0], E[1], color=SERIES[0], lw=2, label="E5 (LTI)")
        for nu, col in sel:
            r = R[(nu, "b")]
            if r["Q"] is not None and r["ok"] and r["kappa"] is not None:
                Pm = np.linalg.inv(r["kappa"] * r["Q"])
                E = slice_ellipse(Pm, i, j)
                ax.plot(E[0], E[1], color=col, lw=1.6, label=f"robust, ν = {nu}")
        ax.scatter([p[i] for p in pts], [p[j] for p in pts], s=10, color=MUTED, alpha=0.6, label="hand-over, τ = 0 (E9a)")
        ax.scatter([d[i]], [d[j]], s=60, marker="*", color=REF, label="exact hover, 2.95 N")
        ax.axhline(0, color=REF, lw=0.6)
        ax.axvline(0, color=REF, lw=0.6)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
    axs[0].set_title("E9b · robust certificate, slice (Δr, Δn_y)")
    axs[1].set_title("E9b · robust certificate, slice (Δn_x, Δn_y)")
    axs[0].legend(fontsize=7.5, loc="lower left")
    fig.tight_layout()
    save(fig, out_f / "e9b_robust_certificate.png")


if __name__ == "__main__":
    main()
