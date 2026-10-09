"""E7: closed-loop comparison of LQR, analytical MPC and residual-Koopman MPC on mismatched plants.

Controllers (all designed on the nominal Mueller & D'Andrea parameters):
  LQR                     relaxed-hover LQR (baseline)
  MPC, analytical         linear MPC on the nominal model
  MPC, residual Koopman   same MPC + residual EDMDc correction as a measured disturbance
                          (residual trained on truth family A, as in E6)

Part 1  steady altitude bias near the relaxed hover, broken down by mismatch effect:
        full families A and B, each without its thrust loss, and the nominal plant with
        only that family's thrust loss. The steady state does not depend on the start,
        so one start (1 m below the set-point) is used per plant.
Part 2  capture after a detection delay on family A: hover, rotor 4 fails, healthy LQR
        for tau, spin-up at 2.95 N (flight value), then the capture controller. Judged with
        the pre-fixed criterion (rotorfail/metrics.py). On a mismatched plant a controller
        designed on the nominal model settles at its own closed-loop steady state, so capture
        is measured against that state (a 12 s run of the same controller from the trim).

Outputs: results/tables/e7_mpc_closed_loop.md, results/figures/e7_altitude.png
"""
import os

# One BLAS/OpenMP thread per process: the experiments parallelize over runs instead.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
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
F_SPIN = 2.95


def plants():
    A, B = truth_family("A"), truth_family("B")
    return {
        "A (full)": A,
        "A without thrust loss": replace(A, thrust_loss=0.0),
        "nominal + A's thrust loss only": replace(P, thrust_loss=A.thrust_loss),
        "B (full, held out)": B,
        "B without thrust loss": replace(B, thrust_loss=0.0),
        "nominal + B's thrust loss only": replace(P, thrust_loss=B.thrust_loss),
    }


def make_ctrl(name, eq, res):
    if name == "LQR":
        return FailureLQR(P, eq)
    if name == "MPC, analytical":
        return FailureMPC(P, eq)
    return FailureMPC(P, eq, residual=res)


def run_regulation(args):
    name, plant_name, res = args
    eq = relaxed_hover(P)
    PT = plants()[plant_name]
    x0 = initial_state(eq, np.random.default_rng(0))
    x0[2] = -1.0                                   # 1 m below the set-point
    c = make_ctrl(name, eq, res)
    c.reset(x0[13:16])
    log = simulate(x0, c, PT, 8.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    late = log.t >= 6.0
    ok = log.completed and np.min(log.n[:, 2]) > 0
    wall = float(np.median(c.solve_times) * 1e3) if hasattr(c, "solve_times") else float("nan")
    qp = float(np.nanmedian(c.qp_times) * 1e3) if hasattr(c, "qp_times") else float("nan")
    return dict(ctrl=name, plant=plant_name, z_ss=float(np.mean(log.z[late])),
                z_rms=float(np.sqrt(np.mean(log.z ** 2))), upright=bool(ok), wall_ms=wall, qp_ms=qp,
                t=log.t, z=log.z)


def closed_loop_reference(name, res, PT):
    """Steady (n, w) of the controller on plant PT: 12 s from the nominal trim, mean of the last 1 s."""
    eq = relaxed_hover(P)
    x = make_state(w=eq.w, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n)
    c = make_ctrl(name, eq, res)
    c.reset(eq.f[:3])
    log = simulate(x, c, PT, 12.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    last = log.t >= 11.0
    return SimpleNamespace(n=log.n[last].mean(axis=0), w=log.w[last].mean(axis=0))


def run_delay(args):
    name, tau, res = args
    eq_nom = relaxed_hover(P)
    PT = truth_family("A")
    ref = closed_loop_reference(name, res, PT)
    cap = SpinUpThenLQR(P, make_ctrl(name, eq_nom, res), f_spin=F_SPIN)
    sup = DelaySupervisor(HealthyLQR(P), cap, t_fail=0.0, tau=tau)
    log = simulate(make_state(), sup, PT, 10.0, dt=1e-3, ctrl_period=TS, log_every=5)
    o = evaluate(log, ref)
    return dict(ctrl=name, tau=tau, alt_loss=o.alt_loss, min_nz=o.min_nz, captured=o.captured, safe=o.safe)


def main():
    apply_style()
    eq = relaxed_hover(P)
    train = generate(truth_family("A"), P, eq, 40, 4.0, seed=11)   # same data as E6
    res = ResidualEDMD.fit(train, NominalModel.build(P, eq), P)

    names = list(plants())
    with ProcessPoolExecutor(max_workers=8) as ex:
        reg = list(ex.map(run_regulation, [(c, pl, res) for pl in names for c in CTRLS]))
    get = lambda c, pl: next(r for r in reg if r["ctrl"] == c and r["plant"] == pl)  # noqa: E731

    L = ["# E7: Closed-loop comparison on mismatched plants", "",
         "All controllers are designed on the nominal parameters. MPC: horizon 20 × 5 ms, DARE terminal cost, "
         "thrust limits, OSQP through CVXPY. The residual (trained on family A, as in E6) is evaluated outside "
         "the QP and held constant over the horizon (measured disturbance), so the QP stays convex.", "",
         "## Part 1: steady altitude bias by mismatch effect", "",
         "One start per plant (1 m below the set-point, 8 s); the steady error is the mean altitude over the "
         "last 2 s. The steady state does not depend on the start.", "",
         "| Plant | LQR | MPC, analytical | MPC, residual Koopman | Residual MPC vs LQR |", "|---|---|---|---|---|"]
    for pl in names:
        zl, za, zr = (get(c, pl)["z_ss"] for c in CTRLS)
        change = f"{(abs(zr) - abs(zl)) / abs(zl) * 100:+.0f}% in magnitude" if abs(zl) > 1e-3 else "n/a"
        L.append(f"| {pl} | {zl:+.3f} m | {za:+.3f} m | {zr:+.3f} m | {change} |")
    walls = [r["wall_ms"] for r in reg if r["ctrl"] != "LQR"]
    qps = [r["qp_ms"] for r in reg if r["ctrl"] != "LQR"]
    L += ["", f"Median time per MPC step: {np.median(walls):.1f} ms wall clock through CVXPY, "
          f"{np.nanmedian(qps):.2f} ms inside OSQP. The sample period is {TS * 1e3:.0f} ms, so the CVXPY wrapper "
          "leaves no real-time margin; the solver itself does.", ""]

    taus = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]
    with ProcessPoolExecutor(max_workers=8) as ex:
        dl = list(ex.map(run_delay, [(c, t, res) for c in CTRLS for t in taus]))
    L += ["## Part 2: capture after a detection delay (family A, exact hover start)", "",
          f"Hover, rotor 4 fails, healthy LQR for τ, spin-up on rotors 1 and 3 at {F_SPIN} N, then the capture "
          "controller. Criterion: `rotorfail/metrics.py` (captured, altitude loss < 2 m, never inverted). Capture "
          "is measured against each controller's own closed-loop steady state on family A, because a controller "
          "designed on the nominal model does not settle at the plant's open-loop relaxed hover.", "",
          "| τ (ms) | " + " | ".join(f"{c}: alt. loss (m) / min n_z / SAFE" for c in CTRLS) + " |",
          "|---|" + "---|" * len(CTRLS)]
    for t in taus:
        cells = []
        for c in CTRLS:
            r = next(r for r in dl if r["ctrl"] == c and r["tau"] == t)
            cells.append(f"{r['alt_loss']:.2f} / {r['min_nz']:.2f} / {'yes' if r['safe'] else 'no'}")
        L.append(f"| {t * 1e3:.0f} | " + " | ".join(cells) + " |")
    L.append("")
    (ROOT / "results/tables/e7_mpc_closed_loop.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for a, pl in zip(ax, ("A (full)", "B (full, held out)")):
        for c, col in zip(CTRLS, SERIES):
            r = get(c, pl)
            lab = "LQR (overlaps analytical MPC)" if c == "LQR" else c
            a.plot(r["t"], r["z"], color=col, label=lab, lw=3.0 if c == "LQR" else 1.8)
        a.axhline(0, color=REF, lw=0.8)
        a.set_title(f"Truth family {pl[0]}" + (" (residual trained here)" if pl.startswith("A") else " (held out)"))
        a.set_xlabel("time (s)")
    ax[0].set_ylabel("altitude (m), set-point 0")
    ax[0].legend(loc="lower right")
    fig.suptitle("E7 · Altitude regulation of the failed quadrotor under model mismatch", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e7_altitude.png")


if __name__ == "__main__":
    main()
