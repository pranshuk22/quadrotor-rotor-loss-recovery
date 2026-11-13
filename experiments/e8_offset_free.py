"""E8a: offset-free baselines against the residual Koopman MPC (task K6).

Question: is the residual Koopman MPC's reduction of the steady altitude bias better than what
classical integral action achieves? Controllers, all designed on the nominal Mueller & D'Andrea
parameters:
  LQR                         relaxed-hover LQR
  MPC, analytical             linear MPC on the nominal model (FailureMPC)
  MPC, residual Koopman       FailureMPC + residual EDMDc as a measured disturbance (as in E7)
  MPC, offset-free            OffsetFreeMPC, thrust-offset disturbance model (3 states), no residual
  MPC, offset-free (state d)  OffsetFreeMPC, disturbance on the 7 physical states, no residual
  MPC, residual + offset-free OffsetFreeMPC (thrust model) with the residual in the prediction
  MPC, residual + o.-f. (state d)  same with the 7-state disturbance model
  LQR + integrator            failure LQR with an integrator on the altitude error

Fixed before running (do not tune afterwards)
  - Same Q, R, horizon 20, DARE terminal cost, input box and 5 ms sample period for every MPC.
  - Residual: ResidualEDMD fitted on generate(truth_family("A"), P, eq, 40, 4.0, seed=11), as in E6/E7.
  - Disturbance model 1 ("thrust", the design specified in the work plan): constant offset d (3) on
    the produced thrust of rotors 1 to 3, entering the 7 physical states through the ZOH-discretised
    thrust input matrix (not the command-filter states). Output: all 10 states. Tracked outputs
    (n_x, n_y, z) at (n_bar_x, n_bar_y, z_ref).
  - Disturbance model 2 ("state", added after a pre-run check, see history/CHANGELOG.md): constant
    offset d (7) on each physical state per step, Bd = [I7; 0]. Added because with 3 disturbance
    states the steady-state innovation need not vanish and the closed loop can settle with an
    error: in a single pre-run check on family A the thrust model left z = -0.239 m. No setting
    was tuned; the check only exposed the structural reason.
  - Kalman filter (current-estimator form), covariances fixed a priori: process variance 1e-4 on
    the 7 physical states, 1e-8 on the 3 filter states; disturbance random-walk variance 1e-3 per
    state ("thrust") or 1e-6 per state ("state"); measurement variance 1e-6. |d_hat| is clipped at
    1.0 N ("thrust") or 0.5 per step ("state") as an anti-windup safeguard; the estimator uses the
    command actually sent. The estimator starts from the measurement with d_hat = 0 at the (last)
    reset, i.e. at the switch. The MPC regulates the filtered state estimate.
  - Target: exact steady state if it satisfies the input box, otherwise the closest feasible one
    (small QP); the fraction of inexact targets is reported.
  - LQR + integrator: integrator weight 1.0 (on top of the failure_weights of the LQR); the
    integrator is not advanced at a sample whose previous command was clipped.
  - Part 1 protocol of E7 (six plants, start 1 m below the set-point, 8 s, one start), steady error
    = mean altitude over the last 2 s. Added metrics: settling time to |z| < 5 cm (last time the
    altitude is outside the band, nan if it ends outside), RMS z, steady attitude error
    |mean(n) - n_bar| over the last 2 s, maximum |w - w_bar| over the run, solver statistics.
  - Part 2 protocol of E7 (hover, rotor 4 fails, healthy LQR for tau, spin-up at 2.95 N, capture
    controller), tau = 0, 10, 20, 30, 40, 60 ms, on family A and on the nominal plant, exact hover
    start. Capture is judged against each controller's own closed-loop steady state on that plant
    (12 s run from the trim), as in E7. Criterion: rotorfail/metrics.py, unchanged.
  - If the estimator proves unstable with the values above, fix it once, record it in
    history/CHANGELOG.md and re-run everything.

Outputs: results/tables/e8_offset_free.md, results/figures/e8_altitude.png
"""
import os

# One BLAS/OpenMP thread per process: the experiments parallelize over runs instead.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import time
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

from e7_mpc_closed_loop import ALIVE3, F_SPIN, plants  # noqa: E402
from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.koopman import TS, NominalModel, ResidualEDMD, generate, initial_state  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.mpc import FailureMPC  # noqa: E402
from rotorfail.offset_free import FailureLQRIntegral, OffsetFreeMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

CTRLS = ["LQR", "MPC, analytical", "MPC, residual Koopman", "MPC, offset-free",
         "MPC, offset-free (state d)", "MPC, residual + offset-free", "MPC, residual + o.-f. (state d)",
         "LQR + integrator"]
OFREE = CTRLS[3:7]
TAUS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]
PLANTS2 = ["A (full)", "nominal"]


def make_ctrl(name, eq, res):
    if name == "LQR":
        return FailureLQR(P, eq)
    if name == "MPC, analytical":
        return FailureMPC(P, eq)
    if name == "MPC, residual Koopman":
        return FailureMPC(P, eq, residual=res)
    if name == "MPC, offset-free":
        return OffsetFreeMPC(P, eq)
    if name == "MPC, offset-free (state d)":
        return OffsetFreeMPC(P, eq, disturbance="state")
    if name == "MPC, residual + offset-free":
        return OffsetFreeMPC(P, eq, residual=res)
    if name == "MPC, residual + o.-f. (state d)":
        return OffsetFreeMPC(P, eq, residual=res, disturbance="state")
    return FailureLQRIntegral(P, eq)


def stats(c):
    """Solver and estimator statistics of a controller after a run."""
    out = dict(wall_ms=float("nan"), qp_ms=float("nan"), inexact=float("nan"), clip=float("nan"),
               bad=0, dmax=float("nan"))
    if hasattr(c, "solve_times") and c.solve_times:
        out["wall_ms"] = float(np.median(c.solve_times) * 1e3)
        out["qp_ms"] = float(np.nanmedian(c.qp_times) * 1e3)
    if isinstance(c, OffsetFreeMPC) and c.target_exact:
        out["inexact"] = float(1.0 - np.mean(c.target_exact))
        out["clip"] = float(np.mean(c.clip_active))
        out["bad"] = int(c.bad_status)
        out["dmax"] = float(np.max(np.abs(c.d_hat_log)))
    return out


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
    out_of_band = np.where(np.abs(log.z) >= 0.05)[0]
    if len(out_of_band) == 0:
        t_settle = 0.0
    elif out_of_band[-1] == len(log.t) - 1:
        t_settle = float("nan")
    else:
        t_settle = float(log.t[out_of_band[-1] + 1])
    return dict(ctrl=name, plant=plant_name, z_ss=float(np.mean(log.z[late])),
                z_rms=float(np.sqrt(np.mean(log.z ** 2))), t_settle=t_settle,
                n_err=float(np.linalg.norm(log.n[late].mean(axis=0) - eq.n)),
                w_max=float(np.max(np.linalg.norm(log.w - eq.w, axis=1))),
                upright=bool(log.completed and np.min(log.n[:, 2]) > 0),
                t=log.t, z=log.z, **stats(c))


def plant2(name):
    return truth_family("A") if name == "A (full)" else P


def closed_loop_reference(args):
    name, plant_name, res = args
    eq = relaxed_hover(P)
    x = make_state(w=eq.w, f=np.concatenate((eq.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(eq.n)
    c = make_ctrl(name, eq, res)
    c.reset(eq.f[:3])
    log = simulate(x, c, plant2(plant_name), 12.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5)
    last = log.t >= 11.0
    return (name, plant_name), SimpleNamespace(n=log.n[last].mean(axis=0), w=log.w[last].mean(axis=0))


def run_delay(args):
    name, plant_name, tau, res, ref = args
    eq = relaxed_hover(P)
    c = make_ctrl(name, eq, res)
    cap = SpinUpThenLQR(P, c, f_spin=F_SPIN)
    sup = DelaySupervisor(HealthyLQR(P), cap, t_fail=0.0, tau=tau)
    log = simulate(make_state(), sup, plant2(plant_name), 10.0, dt=1e-3, ctrl_period=TS, log_every=5)
    o = evaluate(log, ref)
    return dict(ctrl=name, plant=plant_name, tau=tau, alt_loss=o.alt_loss, min_nz=o.min_nz,
                captured=o.captured, safe=o.safe, **stats(c))


def main():
    t_start = time.perf_counter()
    apply_style()
    eq = relaxed_hover(P)
    train = generate(truth_family("A"), P, eq, 40, 4.0, seed=11)   # same data as E6, E7
    res = ResidualEDMD.fit(train, NominalModel.build(P, eq), P)

    names = list(plants())
    with ProcessPoolExecutor(max_workers=8) as ex:
        reg = list(ex.map(run_regulation, [(c, pl, res) for pl in names for c in CTRLS]))
    get = lambda c, pl: next(r for r in reg if r["ctrl"] == c and r["plant"] == pl)  # noqa: E731

    L = ["# E8a: Offset-free baselines against the residual Koopman MPC", "",
         "All controllers are designed on the nominal parameters. Every MPC uses horizon 20 × 5 ms, the same "
         "weights, DARE terminal cost and thrust limits. The offset-free MPC adds a constant thrust-offset "
         "disturbance model, a steady-state Kalman filter and a target calculation (`rotorfail/offset_free.py`); "
         "the pre-registered settings are in the docstring of `experiments/e8_offset_free.py`. 'LQR + integrator' "
         "is the failure LQR with an integrator on the altitude error.", "",
         "## Part 1: steady altitude bias by mismatch effect", "",
         "Protocol of E7: one start per plant (1 m below the set-point, 8 s); steady error = mean altitude over "
         "the last 2 s.", "",
         "| Plant | " + " | ".join(CTRLS) + " |", "|---|" + "---|" * len(CTRLS)]
    for pl in names:
        L.append(f"| {pl} | " + " | ".join(f"{get(c, pl)['z_ss']:+.3f} m" for c in CTRLS) + " |")

    L += ["", "### Further metrics", "",
          "| Plant | Controller | RMS z (m) | settling to ±5 cm (s) | steady attitude error | max rate error (rad/s) | upright |",
          "|---|---|---|---|---|---|---|"]
    for pl in names:
        for c in CTRLS:
            r = get(c, pl)
            ts_ = "not settled" if np.isnan(r["t_settle"]) else f"{r['t_settle']:.2f}"
            L.append(f"| {pl} | {c} | {r['z_rms']:.3f} | {ts_} | {r['n_err']:.4f} | {r['w_max']:.2f} | "
                     f"{'yes' if r['upright'] else 'no'} |")

    L += ["", "### Solver and estimator statistics (Part 1)", "",
          "| Controller | median wall time per step (ms) | median time inside OSQP (ms) | inexact targets | "
          "d_hat at its bound | non-optimal QPs | largest abs. d_hat |", "|---|---|---|---|---|---|---|"]
    for c in CTRLS[1:7]:
        rs = [r for r in reg if r["ctrl"] == c]
        f = lambda k: np.nanmedian([r[k] for r in rs]) if not np.all(np.isnan([r[k] for r in rs])) else float("nan")  # noqa: E731
        L.append(f"| {c} | {f('wall_ms'):.1f} | {f('qp_ms'):.2f} | "
                 f"{'n/a' if np.isnan(f('inexact')) else format(np.nanmax([r['inexact'] for r in rs]), '.3f') + ' (max)'} | "
                 f"{'n/a' if np.isnan(f('clip')) else format(np.nanmax([r['clip'] for r in rs]), '.3f') + ' (max)'} | "
                 f"{sum(r['bad'] for r in rs)} | "
                 f"{'n/a' if np.isnan(f('dmax')) else format(np.nanmax([r['dmax'] for r in rs]), '.3f')} |")
    L += ["", "d_hat is in N for the thrust model and in state units per step for the state model, so the "
          "two are not comparable.", ""]

    keys = [(c, pl) for c in CTRLS for pl in PLANTS2]
    with ProcessPoolExecutor(max_workers=8) as ex:
        refs = dict(ex.map(closed_loop_reference, [(c, pl, res) for c, pl in keys]))
        dl = list(ex.map(run_delay, [(c, pl, t, res, refs[(c, pl)]) for pl in PLANTS2 for c in CTRLS for t in TAUS]))

    L += ["## Part 2: capture after a detection delay (exact hover start)", "",
          f"Hover, rotor 4 fails, healthy LQR for τ, spin-up on rotors 1 and 3 at {F_SPIN} N, then the capture "
          "controller. Criterion: `rotorfail/metrics.py`. Capture is measured against each controller's own "
          "closed-loop steady state on that plant (12 s run from the trim).", ""]
    for pl in PLANTS2:
        L += [f"### Plant: {pl}", "",
              "| τ (ms) | " + " | ".join(CTRLS) + " |", "|---|" + "---|" * len(CTRLS)]
        for t in TAUS:
            cells = []
            for c in CTRLS:
                r = next(r for r in dl if r["ctrl"] == c and r["plant"] == pl and r["tau"] == t)
                cells.append(f"{r['alt_loss']:.2f} / {r['min_nz']:.2f} / {'yes' if r['safe'] else 'no'}")
            L.append(f"| {t * 1e3:.0f} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["Cells: altitude loss (m) / minimum n_z / SAFE.", "",
          "E8a ran without the divergence rule that E8b uses (stop at |w| > 100 rad/s or |z| > 100 m), so a run that has inverted keeps falling and its height loss is not meaningful beyond about 100 m (for example, the analytical MPC on family A at 60 ms shows 339.10 m here and a stopped run at 100.07 m in E8b). Read such entries as 'diverged'.", "",
          "### Estimator behaviour during capture (offset-free controllers)", "",
          "| Plant | Controller | τ (ms) | largest abs. d_hat | share of inexact targets | share of d_hat at its bound | non-optimal QPs |",
          "|---|---|---|---|---|---|---|"]
    for pl in PLANTS2:
        for c in OFREE:
            for t in TAUS:
                r = next(r for r in dl if r["ctrl"] == c and r["plant"] == pl and r["tau"] == t)
                L.append(f"| {pl} | {c} | {t * 1e3:.0f} | {r['dmax']:.3f} | {r['inexact']:.3f} | {r['clip']:.3f} | {r['bad']} |")
    L += ["", f"Total run time: {time.perf_counter() - t_start:.0f} s on 8 processes.", ""]
    (ROOT / "results/tables/e8_offset_free.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    styles = ["-", "--", "-", "-", "--", "-", "--", ":"]
    for a, pl in zip(ax, ("A (full)", "B (full, held out)")):
        for c, col, ls in zip(CTRLS, SERIES, styles):
            r = get(c, pl)
            a.plot(r["t"], r["z"], color=col, ls=ls, label=c, lw=3.0 if c == "LQR" else 1.8)
        a.axhline(0, color=REF, lw=0.8)
        a.set_title(f"Truth family {pl[0]}" + (" (residual trained here)" if pl.startswith("A") else " (held out)"))
        a.set_xlabel("time (s)")
    ax[0].set_ylabel("altitude (m), set-point 0")
    ax[0].legend(loc="lower right", fontsize=7.5)
    fig.suptitle("E8a · Altitude regulation of the failed quadrotor under model mismatch", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8_altitude.png")


if __name__ == "__main__":
    main()
