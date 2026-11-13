"""E10b (D7): trade study of the certificate gap and the empirical delay budget.

Question. How do the hand-over centre (its scaling alpha_c against the certified set), the certified delay budget and the empirical
delay budget move together when one design or vehicle parameter is changed at a time?

Fixed before running (do not tune afterwards)
  - Baseline: nominal parameters, healthy LQR alpha = 1, controller period 1 ms, f_spin = 2.95 N, f_min = 0.2 N, motor time constant 15 ms, w_sw = 10
    rad/s, capture controller = the published failure LQR.
  - One parameter at a time: f_spin in {2.45, 2.95, 3.3}; f_min in {0.1, 0.2, 0.4}; healthy alpha in {0.3, 1, 3}; motor time constant in {10, 15, 25}
    ms; controller period in {1, 2, 5} ms; capture controller in {published LQR, redesigned gain}; w_sw in {10, 12, 14, 16, 18}.
  - For every setting everything is rebuilt from the changed QuadParams (dataclasses.replace): relaxed hover, failure LQR, quasi-LPV model, saturation
    levels, certificate, hand-over states. Never reuse nominal objects.
  - Certificate ("LPV tier" of E9c, remainder-free): robust_invariant_ellipsoid (LQR) or synthesize_gain (redesigned, gain bound 8) on the box built from the
    exact-hover hand-over of the setting at tau = 0 (E9c rule: r half-width 1.15 |d_r|, n_z in [0.5, 1], H as in E9c), decay 0.1, scaled coordinates,
    Clarabel with SCS fallback. A certificate counts only if the numerical verification passes (worst dynamics eigenvalue < -1e-6,
    linear-region minimum >= -1e-8, gain bound for the redesign).
  - Hand-over centre c(tau) from the nominal run of the chain for tau in {0, 5, ..., 60} ms; for the exact hover start the delay budget is
    tau* = first tau at which c(tau) is outside the certificate (alpha_c < 1) and 'does not exist' when this happens at tau = 0.
    alpha_c(0) is reported.
  - Empirical: E4 Monte Carlo with new seeds 2000 to 2039 plus the exact hover, tau in {0, 10, ..., 60} ms, 10 s runs, same plant parameters as
    the setting; P(SAFE), tau_90 and tau_50 as in E4. Controller period 1 ms except in the period study.
  - Altitude: reported as the median altitude loss over the Monte Carlo runs (observed).

Outputs: results/tables/e10b_trade_study.md, results/figures/e10b_trade_study.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from e4_delay_sweep import crossing, x0_hover  # noqa: E402
from rotorfail.certify import robust_invariant_ellipsoid, synthesize_gain, verify_design, verify_robust  # noqa: E402
from rotorfail.control import (CertifiedCaptureController, DelaySupervisor, FailureLQR, HealthyLQR,  # noqa: E402
                               SpinUpThenLQR)
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.lpv import QuasiLPV  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P0  # noqa: E402
from rotorfail.plotting import SERIES, apply_style, save  # noqa: E402
from rotorfail.reach import ChainSpec, run_chain  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

NZ_LO = 0.5
TAUS_C = [round(t, 3) for t in np.arange(0.0, 0.0601, 0.005)]
TAUS_E = [round(t, 3) for t in np.arange(0.0, 0.0601, 0.010)]
SEEDS = list(range(2000, 2040))
BASE = dict(f_spin=2.95, f_min=0.2, alpha=1.0, sigma=0.015, period=1e-3, ctrl="LQR", w_sw=10)


def settings():
    out = [("baseline", dict(BASE))]
    for k, vals in (("f_spin", (2.45, 3.3)), ("f_min", (0.1, 0.4)), ("alpha", (0.3, 3.0)), ("sigma", (0.010, 0.025)),
                    ("period", (2e-3, 5e-3)), ("ctrl", ("redesigned",)), ("w_sw", (12, 14, 16, 18))):
        for v in vals:
            s = dict(BASE)
            s[k] = v
            out.append((f"{k} = {v}", s))
    return out


def params(s):
    return replace(P0, f_min=s["f_min"], sigma_mot=s["sigma"])


def hand_over_dev(s, tau):
    spec = ChainSpec(params(s), tau=tau, w_sw=float(s["w_sw"]), f_spin=s["f_spin"], alpha=s["alpha"], ctrl_period=s["period"])
    r = run_chain(spec, np.zeros(9))
    return r["dev_interp"] if r["handed"] else None


def certificate(s):
    p = params(s)
    eq = relaxed_hover(p)
    lpv = QuasiLPV(p, eq)
    K = FailureLQR(p, eq).K
    fb = eq.f[:3]
    ubar = np.minimum(fb - p.f_min, p.f_max - fb)
    d = hand_over_dev(s, 0.0)
    hr = 1.15 * abs(d[2])
    H = np.array([max(1.3 * abs(d[0]), 2.0), max(1.3 * abs(d[1]), 3.0), hr, max(1.3 * abs(d[3]), 0.15), max(1.3 * abs(d[4]), 0.2),
                  max(1.3 * abs(d[5]), 0.5), max(1.3 * abs(d[6]), 1.0), min(1.76, fb[0]), min(1.1, 1.1), min(1.76, fb[2])])
    H[7:] = np.minimum(H[7:], p.f_max - fb)
    disc = ((3, 4), np.array([0.0, eq.n[1]]), np.sqrt(1 - NZ_LO ** 2))
    Al = lpv.vertices((eq.w[2] - hr, eq.w[2] + hr), (NZ_LO, 1.0))
    rg, ng = np.linspace(eq.w[2] - hr, eq.w[2] + hr, 15), np.linspace(NZ_LO, 1, 15)
    for solver in ("CLARABEL", "SCS"):
        if s["ctrl"] == "LQR":
            res = robust_invariant_ellipsoid(Al, lpv.B, K, ubar, H, direction=d, decay=0.1, disc=disc, solver=solver)
            ok = False
            if res["Q"] is not None:
                v = verify_robust(res, lpv.A, lpv.B, K, ubar, H, rg, ng, decay=0.1, A_list=Al)
                ok = v["worst_dynamics"] < -1e-6 and v["worst_linear_region"] >= -1e-8
            Kc = K
        else:
            res = synthesize_gain(Al, lpv.B, ubar, H, direction=d, gain_bound=8.0, decay=0.1, disc=disc, solver=solver)
            ok = False
            if res["Q"] is not None:
                v = verify_design(res, Al, lpv.B, ubar, H, decay=0.1, gain_bound=8.0)
                ok = v["worst_dynamics"] < -1e-6 and v["worst_linear_region"] >= -1e-8 and v["worst_gain_bound"] >= -1e-8
            Kc = -res["F"] if res["F"] is not None else None
        if ok:
            break
    return dict(ok=bool(ok), status=res["status"], Q=res["Q"] if ok else None, K=Kc if ok else None, beta=res["beta"] if ok else None, d=d)


def job(item):
    name, s = item
    cert = certificate(s)
    ac = []
    for tau in TAUS_C:
        c = hand_over_dev(s, tau)
        if c is None or not cert["ok"]:
            ac.append(np.nan)
        else:
            ac.append(float(1.0 / np.sqrt(c @ np.linalg.solve(cert["Q"], c))))
    return name, dict(cert=cert, alpha_c=ac)


def mc(args):
    s, tau, seed, K = args
    p = params(s)
    eq = relaxed_hover(p)
    ctrl = CertifiedCaptureController(p, eq, gain=K) if (s["ctrl"] == "redesigned" and K is not None) else FailureLQR(p, eq)
    sup = DelaySupervisor(HealthyLQR(p, alpha=s["alpha"]), SpinUpThenLQR(p, ctrl, w_switch=float(s["w_sw"]), f_spin=s["f_spin"]), t_fail=0.0, tau=tau)
    log = simulate(x0_hover(seed), sup, p, 10.0, dt=1e-3, ctrl_period=s["period"], log_every=5)
    o = evaluate(log, eq)
    return dict(safe=bool(o.safe), alt_loss=float(o.alt_loss))


def main():
    apply_style()
    ST = settings()
    with ProcessPoolExecutor(max_workers=8) as ex:
        cert = dict(ex.map(job, ST))
    jobs = [(s, t, sd, cert[n]["cert"]["K"]) for n, s in ST for t in TAUS_E for sd in [None] + SEEDS]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(mc, jobs, chunksize=8))
    L = ["# E10b: Trade study, one parameter at a time", "",
         "alpha_c(0): scaling of the exact-hover hand-over centre at tau = 0 onto the boundary of the remainder-free LPV certificate of the setting "
         "(< 1: outside; the certified delay budget does not exist). tau_90 and tau_50 are empirical (new seeds 2000 to 2039, nominal plant of the setting). "
         "Settings fixed in the docstring of `experiments/e10b_trade_study.py`.", "",
         "| Setting | certificate verified | alpha_c(0) | certified tau* (exact hover, LPV tier) | tau_90 | tau_50 | median alt. loss at 10 ms (m) |", "|---|---|---|---|---|---|---|"]
    idx = 0
    emp = {}
    for n, s in ST:
        pr, al = [], []
        for t in TAUS_E:
            rr = res[idx:idx + 1 + len(SEEDS)]
            idx += 1 + len(SEEDS)
            mcs = rr[1:]
            pr.append(sum(r["safe"] for r in mcs) / len(mcs))
            al.append(float(np.median([r["alt_loss"] for r in mcs])))
        p = np.array(pr)
        emp[n] = (p, crossing(np.array(TAUS_E), p, 0.9), crossing(np.array(TAUS_E), p, 0.5), al)
    fm = lambda v: ">60 ms" if np.isnan(v) else f"{v * 1e3:.0f} ms"  # noqa: E731
    for n, s in ST:
        c = cert[n]
        ac = c["alpha_c"]
        if not c["cert"]["ok"]:
            L.append(f"| {n} | no ({c['cert']['status']}) | - | - | {fm(emp[n][1])} | {fm(emp[n][2])} | {emp[n][3][1]:.2f} |")
            continue
        ts = next((t for t, a in zip(TAUS_C, ac) if np.isfinite(a) and a < 1.0), None)
        L.append(f"| {n} | yes | {ac[0]:.4f} | {'does not exist' if ts == 0.0 else ('> 60 ms' if ts is None else f'{ts * 1e3:.0f} ms')} | {fm(emp[n][1])} | {fm(emp[n][2])} | {emp[n][3][1]:.2f} |")
    L.append("")
    (ROOT / "results/tables/e10b_trade_study.md").write_text("\n".join(L))
    print("\n".join(L))
    fig, ax = plt.subplots(figsize=(9, 4))
    names = [n for n, _ in ST]
    ax.bar(range(len(names)), [0 if np.isnan(emp[n][1]) else emp[n][1] * 1e3 for n in names], color=SERIES[0], label="empirical tau_90 (ms)")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("tau_90 (ms)")
    ax.set_title("E10b · empirical delay budget by setting")
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e10b_trade_study.png")


if __name__ == "__main__":
    main()
