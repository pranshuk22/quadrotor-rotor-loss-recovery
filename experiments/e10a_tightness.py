"""E10a (D9): tightness of the certified delay budget against the empirical one.

Question. Where a certified tau* exists, how close is it to the empirical tau_90 and tau_50 for starts inside the same X0 (H7: within 2 to 3
times)? Is every certified delay sound (every Monte Carlo run from X0 with tau <= tau* captured)? Where no tau* exists (the expected case after
E9a to E9d), H7 is not testable and the empirical delay and the certificate gap are reported instead.

Fixed before running (do not tune afterwards)
  - Starts: 40 starts uniform in gamma X0 (the 99 % ellipsoid of the E4 pre-failure distribution scaled by gamma), gamma in {0.25, 0.5, 1.0}, seeds 6000
    (gamma 0.25), 6001 (0.5), 6002 (1.0), plus the exact hover. Number of the 40 Gaussian E4 starts (seeds 0 to 39 of e4_delay_sweep) outside the
    99 % ellipsoid is reported (they are excluded from soundness).
  - Chains: the published chain (FailureLQR, w_sw = 10, f_spin 2.95 N) and, if E9d produced a certificate for it, the redesigned chains of E9c at their
    threshold w_sw; nominal plant; tau in {0, 5, ..., 60} ms; 10 s runs, controller period 1 ms; the criterion of `rotorfail/metrics.py`.
  - Empirical: P(SAFE) with Wilson intervals, tau_90 and tau_50 as in E4 (first grid delay with P(SAFE) below the level, linear interpolation).
  - Certified: tau* and beta from results/tables/e9d_certified_delay.csv (rigorous tier and LPV tier); "does not exist" when the centre is outside or
    beta(0) < 1.
  - Soundness: for every tau <= tau* every start of the gamma X0 set must be CAPTURED (and SAFE). Any counterexample is reported with its seed.
  - Ratio empirical / certified (H7) only where tau* exists and is positive; otherwise 'not testable'.

Outputs: results/tables/e10a_tightness.md
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

from e4_delay_sweep import crossing, wilson  # noqa: E402
from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.reach import X0_RADIUS, X0_SIGMA, sample_x0, x0_state  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

TAUS = [round(t, 3) for t in np.arange(0.0, 0.0601, 0.005)]
GAMMAS = (0.25, 0.5, 1.0)
SEEDS = {0.25: 6000, 0.5: 6001, 1.0: 6002}
N = 40


def run(args):
    w_sw, tau, u = args
    eq = relaxed_hover(P)
    sup = DelaySupervisor(HealthyLQR(P), SpinUpThenLQR(P, FailureLQR(P, eq), w_switch=w_sw, f_spin=2.95), t_fail=0.0, tau=tau)
    x0 = x0_state(np.asarray(u), P)
    log = simulate(x0, sup, P, 10.0, dt=1e-3, ctrl_period=1e-3, log_every=5)
    o = evaluate(log, eq)
    return dict(safe=bool(o.safe), captured=bool(o.captured))


def main():
    eq = relaxed_hover(P)
    rng_g = [np.random.default_rng(s) for s in range(40)]
    # E4 Gaussian starts: Mahalanobis radius in X0 coordinates
    out_of = 0
    for s in range(40):
        r = np.random.default_rng(s)
        v = r.normal(0, 0.3, 3)
        eul = r.normal(0, np.deg2rad(3), 3)
        w = r.normal(0, 0.3, 3)
        z = np.concatenate((v, eul, w)) / X0_SIGMA
        out_of += float(np.linalg.norm(z)) > X0_RADIUS
    L = ["# E10a: tightness of the certified delay budget", "",
         f"The E4 Monte Carlo draws Gaussian starts; {out_of} of its 40 starts lie outside the 99 % ellipsoid X0 (they are excluded from soundness; "
         "the starts below are drawn uniformly inside gamma X0). Settings fixed in the docstring of `experiments/e10a_tightness.py`.", ""]
    # certified results
    rows = []
    try:
        with open(ROOT / "results/tables/e9d_certified_delay.csv") as fh:
            rows = list(csv.DictReader(fh))
    except FileNotFoundError:
        pass
    jobs = [(10, t, np.zeros(9)) for t in TAUS]
    for g in GAMMAS:
        us = sample_x0(g, N, SEEDS[g])
        jobs += [(10, t, u) for t in TAUS for u in us]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run, jobs, chunksize=4))
    idx = 0
    exact = res[:len(TAUS)]
    idx = len(TAUS)
    stats = {}
    for g in GAMMAS:
        pr, cap = [], []
        for t in TAUS:
            rr = res[idx:idx + N]
            idx += N
            pr.append(sum(r["safe"] for r in rr) / N)
            cap.append(sum(r["captured"] for r in rr) / N)
        p = np.array(pr)
        stats[g] = (p, np.array(cap), crossing(np.array(TAUS), p, 0.9), crossing(np.array(TAUS), p, 0.5))
    ms = lambda v: ">60 ms" if np.isnan(v) else f"{v * 1e3:.0f} ms"  # noqa: E731
    L += ["## Empirical delay budget from starts inside gamma X0 (published chain, w_sw = 10, 2.95 N, nominal plant)", "",
          "| gamma | tau_90 | tau_50 | " + " | ".join(f"{t * 1e3:.0f}" for t in TAUS) + " |", "|---|---|---|" + "---|" * len(TAUS)]
    for g in GAMMAS:
        p, c, t90, t50 = stats[g]
        L.append(f"| {g} | {ms(t90)} | {ms(t50)} | " + " | ".join(f"{v:.2f}" for v in p) + " |")
    L.append("| exact hover (SAFE) | - | - | " + " | ".join("1" if r["safe"] else "0" for r in exact) + " |")
    L.append("")
    # certified, published chain
    L += ["## Certified delay budget for the same chain (from E9d, f_spin 2.95 N, w_sw 10)", "",
          "| gamma | controller | tier | state at tau = 0 | tau* | tau_90 / tau* | tau_50 / tau* |", "|---|---|---|---|---|---|---|"]
    any_cert = False
    for g in (0.0,) + GAMMAS:
        for ctrl in ("LQR",):
            for tier in ("rigorous", "LPV"):
                rr = sorted([r for r in rows if r["f"] == "2.95" and r["w"] == "10" and float(r["gamma"]) == g and r["ctrl"] == ctrl and r["tier"] == tier],
                            key=lambda r: float(r["tau"]))
                if not rr:
                    L.append(f"| {g} | {ctrl} | {tier} | no certificate for this chain | does not exist | not testable | not testable |")
                    continue
                first = rr[0]
                state = f"centre outside, alpha_c = {float(first['alpha_c']):.4f}" if first["status"] == "out" else f"beta(0) = {first['beta']}"
                ts = next((float(r["tau"]) for r in rr if r["status"] != "in" or (r["beta"] not in ("", "nan") and float(r["beta"]) < 1.0)), None)
                if ts is None or ts == 0.0:
                    L.append(f"| {g} | {ctrl} | {tier} | {state} | does not exist | not testable | not testable |")
                else:
                    any_cert = True
                    st = stats.get(g)
                    L.append(f"| {g} | {ctrl} | {tier} | {state} | {ts * 1e3:.0f} ms | " + (f"{stats[g][2] / ts:.1f}" if st and not np.isnan(stats[g][2]) else "-") + " | "
                             + (f"{stats[g][3] / ts:.1f}" if st and not np.isnan(stats[g][3]) else "-") + " |")
    L += ["", "H7 (certified tau* within 2 to 3 times the empirical value): " + ("see the ratios above." if any_cert else "NOT TESTABLE, no certified tau* exists for the published chain."), ""]
    # soundness
    L += ["## Soundness check", ""]
    if not any_cert:
        L.append("No certified tau* > 0 exists, so the condition 'every run with tau <= tau* is captured' is vacuous. (The certificates themselves were falsified "
                 "in E9b and E9c: see those tables.)")
    else:
        L.append("Every run of the gamma X0 sets with tau <= tau*:")
        for g in GAMMAS:
            p, c, _, _ = stats[g]
            L.append(f"- gamma {g}: captured fraction by tau: " + ", ".join(f"{t * 1e3:.0f} ms {v:.2f}" for t, v in zip(TAUS, c)))
    L.append("")
    (ROOT / "results/tables/e10a_tightness.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
