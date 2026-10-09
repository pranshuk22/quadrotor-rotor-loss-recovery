"""E7 (RQ1, first version): closed-loop comparison on the mismatched truth plant.

Controllers (all designed on the nominal M&D parameters):
  LQR                     relaxed-hover LQR (baseline)
  MPC, analytical         linear MPC on the nominal model (PDF controller 1)
  MPC, residual Koopman   same MPC + residual EDMDc correction as a measured disturbance (PDF controller 3)
(PDF controller 2, MPC on the full-state Koopman model, is scheduled for E8.)

Part 1  regulation near the relaxed hover, truth families A (training) and B (held out)
Part 2  link to RQ2: hover -> rotor 4 fails -> detection delay tau -> M&D spin-up -> capture controller

Outputs: results/tables/e7_mpc_closed_loop.md, results/figures/e7_altitude.png
"""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import make_state  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import TS, NominalModel, ResidualEDMD, generate, initial_state  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

CTRLS = ["LQR", "MPC, analytical", "MPC, residual Koopman"]
ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731


def make_ctrl(name, eq, res):
    if name == "LQR":
        return FailureLQR(P, eq)
    if name == "MPC, analytical":
        return FailureMPC(P, eq)
    return FailureMPC(P, eq, residual=res)


def run_regulation(args):
    name, fam, seed, res = args
    eq = relaxed_hover(P)
    PT = truth_family(fam)
    x0 = initial_state(eq, np.random.default_rng(seed))
    x0[2] = -1.0                                   # 1 m below the set-point
    c = make_ctrl(name, eq, res)
    c.reset(x0[13:16])
    log = simulate(x0, c, PT, 8.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    late = log.t >= 6.0
    ok = np.all(np.isfinite(log.x[-1])) and np.min(log.n[:, 2]) > 0
    st = float(np.median(c.solve_times) * 1e3) if hasattr(c, "solve_times") else 0.0
    return dict(ctrl=name, fam=fam, seed=seed, z_ss=float(np.mean(log.z[late])),
                z_rms=float(np.sqrt(np.mean(log.z ** 2))), stable=bool(ok), solve_ms=st,
                t=log.t if seed == 0 else None, z=log.z if seed == 0 else None)


def run_delay(args):
    name, tau, res = args
    eq = relaxed_hover(P)
    PT = truth_family("A")
    cap = SpinUpThenLQR(P, make_ctrl(name, eq, res))
    sup = DelaySupervisor(HealthyLQR(P), cap, t_fail=0.0, tau=tau)
    log = simulate(make_state(), sup, PT, 10.0, dt=1e-3, ctrl_period=TS, log_every=5)
    o = evaluate(log, eq)
    # truth equilibrium differs from the nominal one, so judge capture by attitude settling
    late = log.t >= 8.0
    settled = bool(np.all(np.isfinite(log.x[-1])) and np.ptp(log.n[late, 2]) < 0.05 and np.min(log.n[late, 2]) > 0.8)
    return dict(ctrl=name, tau=tau, alt_loss=o.alt_loss, min_nz=o.min_nz, settled=settled)


def main():
    apply_style()
    eq = relaxed_hover(P)
    train = generate(truth_family("A"), P, eq, 40, 4.0, seed=11)   # same data as E6
    res = ResidualEDMD.fit(train, NominalModel.build(P, eq), P)

    jobs = [(c, fam, s, res) for c in CTRLS for fam in ("A", "B") for s in range(8)]
    with ProcessPoolExecutor(max_workers=8) as ex:
        reg = list(ex.map(run_regulation, jobs))
    L = ["# E7 (RQ1, first version): closed-loop MPC comparison on the mismatched truth plant", "",
         "All controllers are designed on the nominal parameters; the plant is truth family A "
         "(the family the residual was trained on) or B (held out). MPC: horizon 20 × 5 ms, DARE terminal "
         "cost, thrust limits, OSQP. The residual is evaluated outside the QP and held constant over the "
         "horizon (measured disturbance), so the QP stays convex.", "",
         "## Part 1: regulation (8 random starts near the relaxed hover, 1 m below the set-point, 8 s)", "",
         "| Controller | Truth | Steady altitude error (m), mean ± sd | Altitude RMS (m) | Upright & finite | QP time (ms, median) |",
         "|---|---|---|---|---|---|"]
    for fam in ("A", "B"):
        for c in CTRLS:
            rr = [r for r in reg if r["ctrl"] == c and r["fam"] == fam]
            zs = np.array([r["z_ss"] for r in rr])
            L.append(f"| {c} | {fam} | {zs.mean():+.3f} ± {zs.std():.3f} | "
                     f"{np.mean([r['z_rms'] for r in rr]):.3f} | {sum(r['stable'] for r in rr)}/{len(rr)} | "
                     f"{np.median([r['solve_ms'] for r in rr]):.2f} |")
    L.append("")

    taus = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]
    with ProcessPoolExecutor(max_workers=8) as ex:
        dl = list(ex.map(run_delay, [(c, t, res) for c in CTRLS for t in taus]))
    L += ["## Part 2: capture controller after a detection delay (truth family A, hover start)", "",
          "Hover → rotor 4 fails → healthy LQR for τ → M&D two-rotor spin-up → capture controller. "
          "'Settled' = n_z steady (spread < 0.05) and > 0.8 over the last 2 s.", "",
          "| τ (ms) | " + " | ".join(f"{c}: alt. loss (m) / min n_z / settled" for c in CTRLS) + " |",
          "|---|" + "---|" * len(CTRLS)]
    for t in taus:
        cells = []
        for c in CTRLS:
            r = next(r for r in dl if r["ctrl"] == c and r["tau"] == t)
            cells.append(f"{r['alt_loss']:.2f} / {r['min_nz']:.2f} / {'yes' if r['settled'] else 'no'}")
        L.append(f"| {t*1e3:.0f} | " + " | ".join(cells) + " |")
    L.append("")
    (ROOT / "results/tables/e7_mpc_closed_loop.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for a, fam in zip(ax, ("A", "B")):
        for c, col in zip(CTRLS, SERIES):
            r = next(r for r in reg if r["ctrl"] == c and r["fam"] == fam and r["seed"] == 0)
            lab = "LQR (overlaps analytical MPC)" if c == "LQR" else c
            a.plot(r["t"], r["z"], color=col, label=lab, lw=3.0 if c == "LQR" else 1.8)
        a.axhline(0, color=REF, lw=0.8)
        a.set_title(f"Truth family {fam}" + (" (residual trained here)" if fam == "A" else " (held out)"))
        a.set_xlabel("time (s)")
    ax[0].set_ylabel("altitude (m), set-point 0")
    ax[0].legend(loc="lower right")
    fig.suptitle("E7 · Altitude regulation of the failed quadrotor under model mismatch", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e7_altitude.png")


if __name__ == "__main__":
    main()
