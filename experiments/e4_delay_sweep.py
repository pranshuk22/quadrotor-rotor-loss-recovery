"""E4: empirical effect of fault-detection delay tau (preview of the main contribution).

Scenario: hover at z = 0; rotor 4 fails at t = 0; the healthy LQR keeps running
(its rotor-4 command is lost) until t = tau; then the failure-mode strategy takes over.

Failure-mode strategies compared
  A  "LQR at r̄"      : relaxed-hover LQR switched on directly
  B  "Spin-up + LQR"  : Mueller & D'Andrea flight strategy (rotors 1, 3 only until
                        |w| > 10 rad/s, then the LQR)

Outputs
  results/tables/e4_delay_sweep.md, results/tables/e4_delay_sweep.csv
  results/figures/e4_delay_sweep.png, e4_time_histories.png, e4_undetected_phase.png
"""
import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.dynamics import make_state  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.metrics import ALT_LOSS_MAX, evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import MUTED, REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

T_RUN = 10.0
DT = 1e-3
TAUS = np.round(np.arange(0.0, 0.301, 0.01), 3)
ALPHAS = [0.3, 1.0, 3.0]
DETECTOR_BAND = (0.030, 0.130)   # reported detector delays (literature/notes)
STRATS = {"A": "LQR at r̄ (direct)", "B": "Spin-up + LQR (M&D)"}


def build(strategy, tau, alpha=1.0):
    eq = relaxed_hover(P)
    fail = FailureLQR(P, eq)
    if strategy == "B":
        fail = SpinUpThenLQR(P, fail)
    return eq, DelaySupervisor(HealthyLQR(P, alpha=alpha), fail, t_fail=0.0, tau=tau)


def x0_hover(seed=None):
    if seed is None:
        return make_state()
    rng = np.random.default_rng(seed)
    return make_state(v=rng.normal(0, 0.3, 3), euler=rng.normal(0, np.deg2rad(3), 3),
                      w=rng.normal(0, 0.3, 3))


def run(args):
    strategy, tau, alpha, seed = args
    eq, sup = build(strategy, tau, alpha)
    log = simulate(x0_hover(seed), sup, P, T_RUN, dt=DT, ctrl_period=DT, log_every=5)
    o = evaluate(log, eq)
    return dict(strategy=strategy, tau=tau, alpha=alpha, seed=-1 if seed is None else seed, **o.as_dict())


def read_csv(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["strategy"] = r["strategy"]
        for k in ("tau", "alpha", "alt_loss", "min_nz", "t_capture", "max_rate"):
            r[k] = float(r[k])
        r["seed"] = int(r["seed"])
        for k in ("captured", "safe"):
            r[k] = r[k] == "True"
    return rows


def tau_star(rows):
    """Largest tau such that every tau' <= tau on the grid is SAFE."""
    best = None
    for r in sorted(rows, key=lambda r: r["tau"]):
        if not r["safe"]:
            break
        best = r["tau"]
    return best


def main():
    apply_style()
    out_t, out_f = ROOT / "results/tables", ROOT / "results/figures"
    jobs = [(s, t, 1.0, None) for s in STRATS for t in TAUS]
    jobs += [("B", t, a, None) for a in ALPHAS if a != 1.0 for t in TAUS]
    mc_taus = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08]
    jobs += [("B", t, 1.0, s) for t in mc_taus for s in range(20)]
    csv_path = out_t / "e4_delay_sweep.csv"
    if "--plot-only" not in sys.argv:
        with ProcessPoolExecutor(max_workers=8) as ex:
            res = list(ex.map(run, jobs, chunksize=2))
        with open(csv_path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
            w.writeheader()
            w.writerows(res)
    res = read_csv(csv_path)

    nominal = [r for r in res if r["seed"] == -1]

    def sel(s, a=1.0):
        return sorted([r for r in nominal if r["strategy"] == s and r["alpha"] == a], key=lambda r: r["tau"])

    L = ["# E4: Empirical detection-delay tolerance (nonlinear simulation)", "",
         "Hover at z = 0, rotor 4 fails at t = 0, healthy LQR runs until t = τ, then the failure strategy. "
         f"Run length {T_RUN:.0f} s. Success criterion fixed in advance (`rotorfail/metrics.py`): attitude "
         f"captured (|n − n̄| < 0.05 and |ω − ω̄| < 2 rad/s over the last 1 s), altitude loss < {ALT_LOSS_MAX:.0f} m, "
         "never inverted (n_z > 0).", "",
         "## Nominal start (exact hover), healthy-LQR aggressiveness α = 1", "",
         "| τ (ms) | A: captured | A: alt. loss (m) | A: min n_z | B: captured | B: alt. loss (m) | B: min n_z |",
         "|---|---|---|---|---|---|---|"]
    A, B = sel("A"), sel("B")
    for ra, rb in zip(A, B):
        L.append(f"| {ra['tau']*1e3:.0f} | {'yes' if ra['captured'] else 'no'} | {ra['alt_loss']:.2f} | "
                 f"{ra['min_nz']:.2f} | {'yes' if rb['captured'] else 'no'} | {rb['alt_loss']:.2f} | {rb['min_nz']:.2f} |")
    L += ["", "## Empirical delay tolerance τ*_emp (largest τ with every smaller grid τ SAFE)", "",
          "| Strategy | α (healthy aggressiveness) | τ*_emp |", "|---|---|---|"]
    for s in STRATS:
        for a in ([1.0] if s == "A" else ALPHAS):
            ts = tau_star(sel(s, a))
            L.append(f"| {STRATS[s]} | {a} | {'not safe even at τ = 0' if ts is None else f'{ts*1e3:.0f} ms'} |")
    L += ["", "## Monte Carlo (strategy B, α = 1): 20 random pre-failure states per τ", "",
          "Pre-failure state: velocity σ = 0.3 m/s, Euler angles σ = 3°, body rates σ = 0.3 rad/s.", "",
          "| τ (ms) | SAFE | captured | median alt. loss (m) |", "|---|---|---|---|"]
    mc = [r for r in res if r["seed"] >= 0]
    for t in mc_taus:
        rr = [r for r in mc if r["tau"] == t]
        L.append(f"| {t*1e3:.0f} | {sum(r['safe'] for r in rr)}/{len(rr)} | {sum(r['captured'] for r in rr)}/{len(rr)} "
                 f"| {np.median([r['alt_loss'] for r in rr]):.2f} |")
    L.append("")
    (out_t / "e4_delay_sweep.md").write_text("\n".join(L))
    print("\n".join(L))

    # ---- figure: sweep
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
    for a in ax:
        a.axvspan(DETECTOR_BAND[0] * 1e3, DETECTOR_BAND[1] * 1e3, color="#f0efec", zorder=0)
    for s, c in zip(STRATS, SERIES):
        rr = sel(s)
        t = np.array([r["tau"] for r in rr]) * 1e3
        ax[0].plot(t, [r["alt_loss"] for r in rr], color=c, marker="o", ms=3.5, label=STRATS[s])
        ax[1].plot(t, [r["min_nz"] for r in rr], color=c, marker="o", ms=3.5, label=STRATS[s])
    ax[0].set_yscale("log")
    ax[0].axhline(ALT_LOSS_MAX, color=REF, lw=0.8)
    ax[0].text(302, ALT_LOSS_MAX * 1.1, "2 m limit", color=REF, fontsize=8, ha="right")
    ax[0].set_title("Altitude loss after the failure")
    ax[0].set_ylabel("m (log scale)")
    ax[1].axhline(0, color=REF, lw=0.8)
    ax[1].text(302, 0.04, "inverted below", color=REF, fontsize=8, ha="right")
    ax[1].set_title("Worst tilt: min n_z (1 = level, < 0 = upside down)")
    for a in ax:
        a.set_xlabel("detection delay τ (ms)")
        a.text(80, 0.97, "reported\ndetector delays", color=MUTED, fontsize=8, ha="center", va="top",
               transform=blended_transform_factory(a.transData, a.transAxes))
    ax[0].legend(loc="lower right")
    fig.suptitle("E4 · Recovery vs. fault-detection delay (nonlinear sim, hover start)", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e4_delay_sweep.png")

    # ---- figure: time histories for strategy B
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    for tau, c in zip([0.0, 0.04, 0.10], SERIES):
        eq, sup = build("B", tau)
        log = simulate(x0_hover(), sup, P, 6.0, dt=DT, ctrl_period=DT, log_every=2)
        lab = f"τ = {tau*1e3:.0f} ms"
        ax[0].plot(log.t, log.n[:, 2], color=c, label=lab)
        ax[1].plot(log.t, log.w[:, 2], color=c, label=lab)
        ax[2].plot(log.t, log.z, color=c, label=lab)
    ax[0].axhline(0, color=REF, lw=0.8)
    ax[0].set_title("n_z (tilt of the thrust axis)")
    ax[1].axhline(eq.w[2], color=REF, lw=0.8)
    ax[1].set_title("Yaw rate r (line: r̄)")
    ax[1].set_ylabel("rad/s")
    ax[2].set_title("Altitude")
    ax[2].set_ylabel("m")
    ax[2].set_ylim(max(ax[2].get_ylim()[0], -40), 3)
    ax[0].legend(loc="lower right")
    for a in ax:
        a.set_xlabel("time after failure (s)")
    fig.suptitle("E4 · Mueller & D'Andrea strategy with detection delay τ", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e4_time_histories.png")

    # ---- figure: undetected phase (healthy LQR flying a 3-rotor vehicle)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    alive = lambda t: np.array([True, True, True, False])  # noqa: E731
    for a_, c in zip(ALPHAS, SERIES):
        h = HealthyLQR(P, alpha=a_)
        log = simulate(make_state(), h, P, 0.3, dt=5e-4, ctrl_period=1e-3, alive_fn=alive, log_every=2)
        tilt = np.degrees(np.arccos(np.clip(log.n[:, 2], -1, 1)))
        ax[0].plot(log.t * 1e3, tilt, color=c, label=f"healthy LQR, α = {a_}")
        ax[1].plot(log.t * 1e3, log.x[:, 14], color=c, label=f"α = {a_}")
    t = np.linspace(0, 0.3, 100)
    pdot_min = P.l * P.f_min / P.Ixx_B
    ax[0].plot(t * 1e3, np.degrees(0.5 * pdot_min * t ** 2), color=REF, lw=1.0,
               label="lower bound ½·(l f_min / I_xx)·t²")
    ax[0].set_title("Tilt during the undetected phase")
    ax[0].set_ylabel("deg")
    ax[0].legend(loc="upper left")
    ax[1].axhline(P.f_min, color=REF, lw=0.8)
    ax[1].text(5, P.f_min + 0.05, "idle thrust f_min", color=REF, fontsize=8)
    ax[1].set_title("Thrust of rotor 2 (opposite the failed rotor)")
    ax[1].set_ylabel("N")
    for a in ax:
        a.set_xlabel("time after failure (ms)")
    fig.suptitle("E4 · Why the delay matters: the healthy controller cannot cancel the roll torque", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e4_undetected_phase.png")


if __name__ == "__main__":
    main()
