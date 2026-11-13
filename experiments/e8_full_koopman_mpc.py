"""E8b: MPC on the full-state Koopman model (proposal controller 2) against the other two proposal controllers.

Controllers (all designed on the nominal Mueller & D'Andrea parameters, horizon 20 x 5 ms, same Q, R,
input box):
  MPC, analytical             FailureMPC (proposal controller 1)
  MPC, full-state Koopman     LiftedKoopmanMPC (proposal controller 2): FullEDMDc, 55 lifted states + altitude
  MPC, residual Koopman       FailureMPC + residual EDMDc (proposal controller 3)
  LQR                         reference
The offset-free variants are in E8a (results/tables/e8_offset_free.md).

Fixed before running (do not tune afterwards)
  - Training: generate(truth_family("A"), P, eq, 40, 4.0, seed=11) as in E6/E7; FullEDMDc ridge 1e-6,
    ResidualEDMD as in E7.
  - Lifted MPC: lifted state re-computed from the measurement at every step; altitude state integrated
    with the rectangle rule from v_z; weights of FailureMPC mapped to the xi ordering plus 1e-6 I on the
    lifted state; terminal cost from the DARE of the lifted pair without the constant coordinate (the
    constant coordinate makes the full Riccati solution very ill-conditioned, so it is excluded);
    checks: Riccati residual, symmetry and PSD tolerance 1e-8, spectral radius of the closed loop < 1.
    If a check fails there is no terminal cost (documented fallback) and a horizon-40 variant is
    reported as sensitivity. OSQP: 4000 iterations, tolerances 1e-5; on a failed solve the previous
    input is kept and the event is counted.
  - Divergence rule: the run stops if |w| > 100 rad/s or |z| > 100 m (any run), or, in Part 1 only,
    if |n_xy - n_bar_xy| > 0.5; a stopped run is recorded with its stop time and counted as not captured.
  - Per run: maximum standardised |xi| seen by the dictionary (to diagnose out-of-distribution lifting),
    number of non-optimal QPs, wall time per step.
  - Part 1 and Part 2 protocols of E8a (E7): six plants, start 1 m below the set-point, 8 s, steady error =
    mean altitude over the last 2 s; capture after delay tau = 0, 10, 20, 30, 40, 60 ms on family A and the
    nominal plant, spin-up 2.95 N, judged with rotorfail/metrics.py against each controller's own steady
    state (12 s run from the trim).
  - Also reported: the lifted model's eigenvalues outside the unit circle, the Riccati checks, the same
    checks for the Riccati equation with the constant coordinate included (model check only; this is why
    the constant coordinate is excluded from the terminal cost), and the command the lifted MPC issues at
    the exact trim (a bias of the learned model).

Outputs: results/tables/e8_full_koopman_mpc.md, results/figures/e8_full_koopman.png
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
from rotorfail.koopman import TS, FullEDMDc, NominalModel, ResidualEDMD, generate, initial_state  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.mpc import FailureMPC, LiftedKoopmanMPC  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.params import truth_family  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

CTRLS = ["LQR", "MPC, analytical", "MPC, full-state Koopman", "MPC, residual Koopman"]
TAUS = [0.0, 0.01, 0.02, 0.03, 0.04, 0.06]
PLANTS2 = ["A (full)", "nominal"]
EQ = relaxed_hover(P)


def make_ctrl(name, bundle):
    res, full = bundle
    if name == "LQR":
        return FailureLQR(P, EQ)
    if name == "MPC, analytical":
        return FailureMPC(P, EQ)
    if name == "MPC, residual Koopman":
        return FailureMPC(P, EQ, residual=res)
    return LiftedKoopmanMPC(P, EQ, full)


def stop_fn(part1):
    def f(t, x):
        from rotorfail.dynamics import E3, quat_to_rot
        w = np.linalg.norm(x[10:13])
        if not np.isfinite(w) or w > 100.0 or abs(x[2]) > 100.0:
            return True
        if part1:
            n = quat_to_rot(x[IDX_Q]).T @ E3
            return bool(np.linalg.norm(n[:2] - EQ.n[:2]) > 0.5)
        return False
    return f


def stats(c):
    out = dict(wall_ms=float("nan"), max_std=float("nan"), bad=0)
    if hasattr(c, "solve_times") and c.solve_times:
        out["wall_ms"] = float(np.median(c.solve_times) * 1e3)
    if isinstance(c, LiftedKoopmanMPC):
        out["max_std"] = float(c.max_std)
        out["bad"] = int(c.n_bad)
    return out


def run_regulation(args):
    name, plant_name, bundle = args
    PT = plants()[plant_name]
    x0 = initial_state(EQ, np.random.default_rng(0))
    x0[2] = -1.0
    c = make_ctrl(name, bundle)
    c.reset(x0[13:16])
    log = simulate(x0, c, PT, 8.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5, stop_fn=stop_fn(True))
    late = log.t >= 6.0
    return dict(ctrl=name, plant=plant_name, completed=bool(log.completed), t_end=float(log.t[-1]),
                z_ss=float(np.mean(log.z[late])) if log.completed else float("nan"),
                z_rms=float(np.sqrt(np.mean(log.z ** 2))), t=log.t, z=log.z, **stats(c))


def plant2(name):
    return truth_family("A") if name == "A (full)" else P


def closed_loop_reference(args):
    name, plant_name, bundle = args
    x = make_state(w=EQ.w, f=np.concatenate((EQ.f[:3], [0.0])))
    x[IDX_Q] = quat_from_n(EQ.n)
    c = make_ctrl(name, bundle)
    c.reset(EQ.f[:3])
    log = simulate(x, c, plant2(plant_name), 12.0, dt=1e-3, ctrl_period=TS, alive_fn=ALIVE3, log_every=5,
                   stop_fn=stop_fn(False))
    last = log.t >= 11.0
    if not log.completed:       # diverged on the way to its own steady state: fall back to the nominal hover
        return (name, plant_name), SimpleNamespace(n=EQ.n, w=EQ.w, ok=False)
    return (name, plant_name), SimpleNamespace(n=log.n[last].mean(axis=0), w=log.w[last].mean(axis=0), ok=True)


def run_delay(args):
    name, plant_name, tau, bundle, ref = args
    c = make_ctrl(name, bundle)
    cap = SpinUpThenLQR(P, c, f_spin=F_SPIN)
    sup = DelaySupervisor(HealthyLQR(P), cap, t_fail=0.0, tau=tau)
    log = simulate(make_state(), sup, plant2(plant_name), 10.0, dt=1e-3, ctrl_period=TS, log_every=5,
                   stop_fn=stop_fn(False))
    o = evaluate(log, ref)
    return dict(ctrl=name, plant=plant_name, tau=tau, alt_loss=o.alt_loss, min_nz=o.min_nz, captured=o.captured,
                safe=o.safe, completed=bool(log.completed), t_end=float(log.t[-1]), ref_ok=bool(getattr(ref, "ok", True)),
                **stats(c))


def main():
    t_start = time.perf_counter()
    apply_style()
    train = generate(truth_family("A"), P, EQ, 40, 4.0, seed=11)
    res = ResidualEDMD.fit(train, NominalModel.build(P, EQ), P)
    full = FullEDMDc.fit(train)
    bundle = (res, full)

    ev = np.linalg.eigvals(full.A)
    probe = LiftedKoopmanMPC(P, EQ, full)
    d = probe.dare
    d_inc = LiftedKoopmanMPC._terminal(probe.Aa, probe.Ba, probe.Ql, probe.R, "dare", 1e-8, exclude_constant=False)
    probe.reset(EQ.f[:3])
    u_trim = probe.act(np.zeros(7))
    L = ["# E8b: MPC on the full-state Koopman model (proposal controller 2)", "",
         "Controllers: analytical MPC, MPC on the full-state Koopman model (`LiftedKoopmanMPC`), residual Koopman "
         "MPC, and the LQR as reference. Pre-registered settings are in the docstring of "
         "`experiments/e8_full_koopman_mpc.py`.", "",
         "## Model and terminal-cost checks", "",
         f"- Lifted states: {full.A.shape[0]} (+1 altitude state in the MPC); eigenvalues outside the unit circle: "
         f"{int(np.sum(np.abs(ev) > 1))} of {len(ev)}, largest modulus {np.max(np.abs(ev)):.4f}.",
         f"- Terminal cost: `{d['kind']}`. Riccati residual (relative) {d['residual']:.1e}, asymmetry {d['sym']:.1e}, "
         f"smallest/largest eigenvalue {d['min_eig']:.1e}, spectral radius of the lifted closed loop {d['rho']:.4f}, "
         f"condition number {d['cond']:.1e}; all checks passed: {d['ok']}.",
         f"- Same Riccati equation with the constant coordinate included (not used): relative residual "
         f"{d_inc['residual']:.1e}, smallest/largest eigenvalue {d_inc['min_eig']:.1e}, spectral radius "
         f"{d_inc['rho']:.10f}, condition number {d_inc['cond']:.1e}.",
         f"- Command issued at the exact trim (should be zero; a bias of the learned model): "
         f"({u_trim[0]:+.3f}, {u_trim[1]:+.3f}, {u_trim[2]:+.3f}) N from the relaxed-hover thrusts.", ""]

    names = list(plants())
    with ProcessPoolExecutor(max_workers=8) as ex:
        reg = list(ex.map(run_regulation, [(c, pl, bundle) for pl in names for c in CTRLS]))
    get = lambda c, pl: next(r for r in reg if r["ctrl"] == c and r["plant"] == pl)  # noqa: E731

    L += ["## Part 1: steady altitude bias by mismatch effect", "",
          "Protocol of E7/E8a. A run that diverged is shown with its stop time.", "",
          "| Plant | " + " | ".join(CTRLS) + " |", "|---|" + "---|" * len(CTRLS)]
    for pl in names:
        cells = []
        for c in CTRLS:
            r = get(c, pl)
            cells.append(f"{r['z_ss']:+.3f} m" if r["completed"] else f"diverged at {r['t_end']:.2f} s")
        L.append(f"| {pl} | " + " | ".join(cells) + " |")
    L += ["", "| Plant | Controller | RMS z (m) | max standardised xi | non-optimal QPs | median wall time per step (ms) |",
          "|---|---|---|---|---|---|"]
    for pl in names:
        r = get("MPC, full-state Koopman", pl)
        L.append(f"| {pl} | MPC, full-state Koopman | {r['z_rms']:.3f} | {r['max_std']:.1f} | {r['bad']} | {r['wall_ms']:.1f} |")
    L.append("")

    keys = [(c, pl) for c in CTRLS for pl in PLANTS2]
    with ProcessPoolExecutor(max_workers=8) as ex:
        refs = dict(ex.map(closed_loop_reference, [(c, pl, bundle) for c, pl in keys]))
        dl = list(ex.map(run_delay, [(c, pl, t, bundle, refs[(c, pl)]) for pl in PLANTS2 for c in CTRLS for t in TAUS]))

    L += ["## Part 2: capture after a detection delay (exact hover start)", "",
          f"Hover, rotor 4 fails, healthy LQR for τ, spin-up on rotors 1 and 3 at {F_SPIN} N, then the capture "
          "controller. Criterion: `rotorfail/metrics.py`; capture is judged against each controller's own "
          "closed-loop steady state on that plant. Cells: altitude loss (m) / minimum n_z / SAFE; "
          "'stopped' = the run hit the divergence rule at the given time.", ""]
    for pl in PLANTS2:
        L += [f"### Plant: {pl}", "", "| τ (ms) | " + " | ".join(CTRLS) + " |", "|---|" + "---|" * len(CTRLS)]
        for t in TAUS:
            cells = []
            for c in CTRLS:
                r = next(r for r in dl if r["ctrl"] == c and r["plant"] == pl and r["tau"] == t)
                s = f"{r['alt_loss']:.2f} / {r['min_nz']:.2f} / {'yes' if r['safe'] else 'no'}"
                if not r["completed"]:
                    s += f" (stopped {r['t_end']:.2f} s)"
                cells.append(s)
            L.append(f"| {t * 1e3:.0f} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["### Full-state Koopman MPC during capture", "",
          "| Plant | τ (ms) | max standardised xi | non-optimal QPs | median wall time per step (ms) |", "|---|---|---|---|---|"]
    for pl in PLANTS2:
        for t in TAUS:
            r = next(r for r in dl if r["ctrl"] == "MPC, full-state Koopman" and r["plant"] == pl and r["tau"] == t)
            L.append(f"| {pl} | {t * 1e3:.0f} | {r['max_std']:.1f} | {r['bad']} | {r['wall_ms']:.1f} |")
    L += ["", f"Total run time: {time.perf_counter() - t_start:.0f} s on 8 processes.", ""]
    (ROOT / "results/tables/e8_full_koopman_mpc.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    for a, pl in zip(ax, ("A (full)", "B (full, held out)")):
        for c, col in zip(CTRLS, SERIES):
            r = get(c, pl)
            a.plot(r["t"], r["z"], color=col, label=c, lw=3.0 if c == "LQR" else 1.8)
        a.axhline(0, color=REF, lw=0.8)
        a.set_title(f"Truth family {pl[0]}" + (" (models trained here)" if pl.startswith("A") else " (held out)"))
        a.set_xlabel("time (s)")
    ax[0].set_ylabel("altitude (m), set-point 0")
    ax[0].legend(loc="lower right", fontsize=8)
    fig.suptitle("E8b · Altitude regulation with the three proposal controllers", fontsize=12)
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e8_full_koopman.png")


if __name__ == "__main__":
    main()
