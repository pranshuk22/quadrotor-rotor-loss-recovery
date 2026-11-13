"""E9e: confirmation of the earlier hand-over (redesigned capture, threshold only).

Why. E9c compared hand-over thresholds on the 40 seeds 1000 to 1039 and found that the PUBLISHED failure LQR with a lower switch
threshold (6 rad/s instead of 10) was SAFE for every delay up to 80 ms there. Because the threshold was picked by looking at those
seeds, the claim is re-tested here on new seeds and on other plants before it is reported. This is an empirical, not a certified,
result ("observed in simulation"); the published strategy (w_sw = 10) is always run alongside, unchanged.

Fixed before running (do not tune afterwards)
  - Chain: healthy LQR for tau, spin-up (rotors 1 and 3 at f_spin, rotor 2 stopped), then FailureLQR when |w| > w_sw; controller period 1 ms,
    10 s runs, the criterion of `rotorfail/metrics.py` (judged against the plant's own closed-loop steady state on mismatched plants).
  - Part 1 (nominal plant, 2.95 N): w_sw in {5, 6, 7, 10}; starts: new seeds 3000 to 3039 of the E4 Gaussian generator plus the exact hover;
    tau in {0, 5, ..., 60, 80, 100, 130} ms. P(SAFE) with Wilson intervals, tau_90 and tau_50 as in E4, median altitude loss.
  - Part 2 (robustness, w_sw in {6, 10}): truth family A, truth family B, and the nominal plant at f_spin = 2.45 N; seeds 3000 to 3039 plus the
    exact hover; tau in {0, 10, 20, 30, 40, 60, 100, 130} ms.
  - Nothing is chosen on these seeds: the thresholds are the pre-fixed grid, and the report states the result for all of them.

Outputs: results/tables/e9e_early_handover.md, results/figures/e9e_early_handover.png
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from e4_delay_sweep import crossing, wilson, x0_hover  # noqa: E402
from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

SEEDS = list(range(3000, 3040))
TAUS1 = [round(t, 3) for t in list(np.arange(0.0, 0.0601, 0.005)) + [0.08, 0.10, 0.13]]
TAUS2 = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06, 0.10, 0.13]
ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731
PLANTS = {"nominal": P, "family A": truth_family("A"), "family B": truth_family("B")}


def reference(plant):
    eq = relaxed_hover(P)
    x = make_state(w=eq.w, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n)
    c = FailureLQR(P, eq)
    c.reset(eq.f[:3])
    log = simulate(x, c, PLANTS[plant], 12.0, dt=1e-3, ctrl_period=1e-3, alive_fn=ALIVE3, log_every=5)
    last = log.t >= 11.0
    return SimpleNamespace(n=log.n[last].mean(axis=0), w=log.w[last].mean(axis=0))


def run(args):
    plant, f_spin, w_sw, tau, seed, ref = args
    eq = relaxed_hover(P)
    sup = DelaySupervisor(HealthyLQR(P), SpinUpThenLQR(P, FailureLQR(P, eq), w_switch=float(w_sw), f_spin=f_spin), t_fail=0.0, tau=tau)
    log = simulate(x0_hover(seed), sup, PLANTS[plant], 10.0, dt=1e-3, ctrl_period=1e-3, log_every=5)
    o = evaluate(log, ref if ref is not None else eq)
    return dict(safe=bool(o.safe), alt_loss=float(o.alt_loss))


def block(res, idx, taus, n):
    pr, al, lo, hi = [], [], [], []
    for t in taus:
        rr = res[idx:idx + n]
        idx += n
        mc = rr[1:]
        k = sum(r["safe"] for r in mc)
        pr.append(k / len(mc))
        a, b = wilson(k, len(mc))
        lo.append(a)
        hi.append(b)
        al.append(float(np.median([r["alt_loss"] for r in mc])))
    return idx, np.array(pr), al, lo, hi, [res[idx - n * (len(taus) - i)]["safe"] for i in range(len(taus))]


def main():
    apply_style()
    refs = {pl: reference(pl) for pl in PLANTS if pl != "nominal"}
    jobs, layout = [], []
    for w in (5, 6, 7, 10):
        layout.append(("p1", w))
        jobs += [("nominal", 2.95, w, t, s, None) for t in TAUS1 for s in [None] + SEEDS]
    for pl, f in (("family A", 2.95), ("family B", 2.95), ("nominal", 2.45)):
        for w in (6, 10):
            layout.append(("p2", (pl, f, w)))
            jobs += [(pl, f, w, t, s, refs.get(pl) if pl != "nominal" else None) for t in TAUS2 for s in [None] + SEEDS]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run, jobs, chunksize=8))
    L = ["# E9e: Confirmation of the earlier hand-over on new seeds", "",
         "Published failure LQR with the hand-over threshold w_sw changed (the published value is 10 rad/s). New seeds 3000 to 3039 (the E4 generator) plus the exact hover. "
         "This is observed in simulation, not certified. Settings fixed in the docstring of `experiments/e9e_early_handover.py`.", "",
         "## Part 1: nominal plant, 2.95 N", "", "| w_sw (rad/s) | tau_90 | tau_50 | " + " | ".join(f"{t * 1e3:.0f} ms" for t in TAUS1) + " |",
         "|---|---|---|" + "---|" * len(TAUS1)]
    idx = 0
    n = 1 + len(SEEDS)
    stats1, ex1 = {}, {}
    for kind, w in [x for x in layout if x[0] == "p1"]:
        idx, p, al, lo, hi, exact = block(res, idx, TAUS1, n)
        t90, t50 = crossing(np.array(TAUS1[:13]), p[:13], 0.9), crossing(np.array(TAUS1[:13]), p[:13], 0.5)
        ms = lambda v: ">60 ms" if np.isnan(v) else f"{v * 1e3:.0f} ms"  # noqa: E731
        stats1[w] = (p, lo, hi, al)
        ex1[w] = exact
        L.append(f"| {w} | {ms(t90)} | {ms(t50)} | " + " | ".join(f"{v:.2f}" for v in p) + " |")
    L += ["", "95 % Wilson intervals of P(SAFE) at selected delays:", "", "| w_sw | " + " | ".join(f"{t * 1e3:.0f} ms" for t in (0.02, 0.06, 0.10, 0.13)) + " |", "|---|---|---|---|---|"]
    for w, (p, lo, hi, al) in stats1.items():
        cells = []
        for t in (0.02, 0.06, 0.10, 0.13):
            i = TAUS1.index(t)
            cells.append(f"{p[i]:.2f} [{lo[i]:.2f}, {hi[i]:.2f}]")
        L.append(f"| {w} | " + " | ".join(cells) + " |")
    L += ["", "Median altitude loss (m) at selected delays:", "", "| w_sw | " + " | ".join(f"{t * 1e3:.0f} ms" for t in (0.0, 0.02, 0.06, 0.13)) + " |", "|---|---|---|---|---|"]
    for w, (p, lo, hi, al) in stats1.items():
        L.append(f"| {w} | " + " | ".join(f"{al[TAUS1.index(t)]:.2f}" for t in (0.0, 0.02, 0.06, 0.13)) + " |")
    L += ["", "Exact hover start, SAFE by tau (1 = SAFE):", "", "| w_sw | " + " | ".join(f"{t * 1e3:.0f}" for t in TAUS1) + " |", "|---|" + "---|" * len(TAUS1)]
    for w, e in ex1.items():
        L.append(f"| {w} | " + " | ".join("1" if x else "0" for x in e) + " |")
    L += ["", "## Part 2: robustness (published threshold 10 against 6)", "", "| plant / spin-up | w_sw | " + " | ".join(f"{t * 1e3:.0f} ms" for t in TAUS2) + " | median alt. loss at 60 ms (m) |", "|---|---|" + "---|" * len(TAUS2) + "---|"]
    stats2 = {}
    for kind, key in [x for x in layout if x[0] == "p2"]:
        idx, p, al, lo, hi, exact = block(res, idx, TAUS2, n)
        pl, f, w = key
        stats2[key] = p
        L.append(f"| {pl}, {f} N | {w} | " + " | ".join(f"{v:.2f}" for v in p) + f" | {al[TAUS2.index(0.06)]:.2f} |")
    L.append("")
    (ROOT / "results/tables/e9e_early_handover.md").write_text("\n".join(L))
    print("\n".join(L))
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for k, w in enumerate(stats1):
        ax.plot([t * 1e3 for t in TAUS1], stats1[w][0], marker="o", ms=3, color=SERIES[k], label=f"w_sw = {w} rad/s")
    ax.set_xlabel("detection delay τ (ms)")
    ax.set_ylabel("P(SAFE), 40 new starts")
    ax.set_title("E9e · hand-over threshold, published failure LQR")
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e9e_early_handover.png")


if __name__ == "__main__":
    main()
