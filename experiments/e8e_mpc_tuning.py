"""E8e (K10): MPC horizon and tuning study for capture.

Question. How do horizon and weights affect capture after a detection delay, and are the E7/E8 conclusions an
artefact of the single setting (horizon 20, published weights)?

Fixed before running (do not tune afterwards)
  - Horizons {10, 20, 40, 80} steps of 5 ms. Weight sets: "published" (failure_weights defaults) and "heavy attitude"
    (w_att = 60 instead of 20, everything else unchanged).
  - Controllers: MPC analytical, MPC with the offline residual (E6/E7 model, trained on family A), offset-free MPC
    (state disturbance model, the E8a baseline).
  - Plants: nominal and family A. Protocol: E7 Part 2 (exact hover start, healthy LQR for tau, spin-up 2.95 N, MPC
    capture; judged against each configuration's own steady state), tau in {0, 10, 20, 30, 40, 60} ms.
  - Reported per configuration: SAFE (yes/no), altitude loss, median CVXPY wall time per step, median QP time. Horizon 80
    exceeds the 5 ms period by far and is reported as an analysis result, not a real-time controller.
  - No "best" setting is selected or claimed: the whole grid is reported (the capture protocol has no random seeds, so a
    selection could not be evaluated on separate seeds).
  - Long-horizon check: for horizons 40 and 80 the first move of the DARE-terminal MPC is compared with the plain
    finite-horizon problem (terminal='none') at 20 states drawn from the capture hand-over distribution
    (seed 8100): maximum absolute difference of the first command.

Outputs: results/tables/e8e_mpc_tuning.md, results/figures/e8e_horizon.png
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

from rq1_common import closed_loop_reference, run_delay  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import NominalModel, ResidualEDMD, generate  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import SERIES, apply_style, save  # noqa: E402

HORIZONS = (10, 20, 40, 80)
WEIGHTS = {"published": {}, "heavy attitude": dict(w_att=60.0)}
TAUS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]


def main():
    apply_style()
    eq = relaxed_hover(P)
    res = ResidualEDMD.fit(generate(truth_family("A"), P, eq, 40, 4.0, seed=11), NominalModel.build(P, eq), P)
    plants = {"nominal": P, "A (full)": truth_family("A")}
    specs = {}
    for h in HORIZONS:
        for wn, w in WEIGHTS.items():
            specs[("MPC analytical", h, wn)] = ("mpc", dict(horizon=h, weights=w))
            specs[("MPC residual", h, wn)] = ("mpc", dict(horizon=h, weights=w, residual=res))
            specs[("Offset-free", h, wn)] = ("of", dict(horizon=h, weights=w, disturbance="state"))
    with ProcessPoolExecutor(max_workers=8) as ex:
        refs = {(k, pl): ex.submit(closed_loop_reference, (s, plants[pl])) for k, s in specs.items() for pl in plants}
        refs = {k: f.result() for k, f in refs.items()}
        futs = {(k, pl, t): ex.submit(run_delay, (specs[k], plants[pl], t, refs[(k, pl)], None))
                for k in specs for pl in plants for t in TAUS}
        dl = {k: f.result() for k, f in futs.items()}
    L = ["# E8e: MPC horizon and tuning study for capture", "",
         "Capture after a detection delay (E7 Part 2 protocol, exact hover start, spin-up 2.95 N). Cells: SAFE count over the six delays "
         "tau = 0, 10, ..., 60 ms (the first failing tau in brackets, '-' if none), median altitude loss over the delays (m), "
         "median CVXPY wall time per step (ms). Settings fixed in the docstring of `experiments/e8e_mpc_tuning.py`. "
         "Horizon 80 exceeds the 5 ms period by far and is an analysis result, not a real-time controller.", ""]
    for pl in plants:
        L += [f"## Plant: {pl}", "", "| Controller | weights | " + " | ".join(f"H = {h}" for h in HORIZONS) + " |", "|---|---|" + "---|" * len(HORIZONS)]
        for ctrl in ("MPC analytical", "MPC residual", "Offset-free"):
            for wn in WEIGHTS:
                cells = []
                for h in HORIZONS:
                    rr = [dl[((ctrl, h, wn), pl, t)] for t in TAUS]
                    safe = sum(r["safe"] for r in rr)
                    fail = next((f"{t * 1e3:.0f} ms" for t, r in zip(TAUS, rr) if not r["safe"]), "-")
                    cells.append(f"{safe}/{len(rr)} ({fail}); {np.median([r['alt_loss'] for r in rr]):.2f} m; {np.nanmedian([r['wall_ms'] for r in rr]):.1f} ms")
                L.append(f"| {ctrl} | {wn} | " + " | ".join(cells) + " |")
        L.append("")
    # long-horizon check
    rng = np.random.default_rng(8100)
    states = []
    for _ in range(20):
        nxy = eq.n[:2] + np.array([rng.uniform(-0.3, 0.1), rng.uniform(-0.9, -0.3)])
        n = np.array([nxy[0], nxy[1], np.sqrt(max(1 - nxy @ nxy, 0.05))])
        x = make_state(w=eq.w + np.array([0.0, rng.uniform(-7, -5), rng.uniform(-10, -8)]), f=np.array([2.95, 0.0, 2.95, 0.0]),
                       d=(0, 0, rng.uniform(-0.2, 0.4)), v=(0, 0, rng.uniform(0, 1)))
        x[IDX_Q] = quat_from_n(n)
        states.append(x)
    L += ["## Long-horizon check: DARE terminal cost versus plain finite horizon (first command, 20 hand-over-like states)", "",
          "| Horizon | max abs difference of the first command (N) | median (N) |", "|---|---|---|"]
    for h in (20, 40, 80):
        a, b = FailureMPC(P, eq, horizon=h), FailureMPC(P, eq, horizon=h, terminal="none")
        d = []
        for x in states:
            a.reset(x[13:16]), b.reset(x[13:16])
            d.append(np.max(np.abs(a(0.0, x) - b(0.0, x))))
        L.append(f"| {h} | {np.max(d):.3f} | {np.median(d):.3f} |")
    L.append("")
    (ROOT / "results/tables/e8e_mpc_tuning.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    for ax, pl in zip(axs, plants):
        for k, ctrl in enumerate(("MPC analytical", "MPC residual", "Offset-free")):
            for wn, ls in zip(WEIGHTS, ("-", "--")):
                ax.plot(HORIZONS, [sum(dl[((ctrl, h, wn), pl, t)]["safe"] for t in TAUS) for h in HORIZONS], ls=ls, marker="o",
                        color=SERIES[k], label=f"{ctrl}, {wn}")
        ax.set_xscale("log")
        ax.set_xlabel("horizon (steps of 5 ms)")
        ax.set_ylabel("SAFE delays of 6")
        ax.set_title(f"E8e · {pl}")
    axs[0].legend(fontsize=6.5)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8e_horizon.png")


if __name__ == "__main__":
    main()
