"""E4: empirical effect of fault-detection delay tau on recovery.

Scenario: hover at z = 0; rotor 4 fails at t = 0; the healthy LQR keeps running
(its rotor-4 command is lost) until t = tau; then the failure-mode strategy takes over.

Strategies
  A    relaxed-hover LQR switched on directly
  B    spin-up on rotors 1 and 3 at thrust f_spin each (rotor 2 stopped), then the LQR
       once |w| > 10 rad/s (Mueller & D'Andrea 2014, Sec. V-D, Fig. 4)
       f_spin = 2.95 N  read from the flight data in Fig. 4 (main case)
       f_spin = 2.45 N  m g / 2 (sensitivity case)

Fixed before running (do not tune afterwards)
  - success criterion: rotorfail/metrics.py (SAFE = captured, altitude loss < 2 m, never inverted)
  - Monte Carlo: 40 random pre-failure states per delay, delays 0, 5, ..., 60 ms
  - P(SAFE) with 95 % Wilson intervals; tau_50 and tau_90 = delays at which the observed
    P(SAFE) first falls below 0.5 and 0.9 (linear interpolation between grid points)

Outputs
  results/tables/e4_delay_sweep.md, results/tables/e4_delay_sweep.csv
  results/figures/e4_p_safe.png, e4_delay_sweep.png, e4_time_histories.png, e4_undetected_phase.png
"""
import os

# One BLAS/OpenMP thread per process: the experiments parallelize over runs instead.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

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
F_FLIGHT = 2.95
F_HALF = round(P.weight / 2, 3)
TAUS = np.round(np.arange(0.0, 0.301, 0.01), 3)          # nominal sweep (figures)
MC_TAUS = np.round(np.arange(0.0, 0.0601, 0.005), 3)       # Monte Carlo grid
MC_SEEDS = 40
ALPHAS = [0.3, 1.0, 3.0]
DETECTOR_BAND = (0.030, 0.130)   # Strack van Schijndel et al. (2021)
CASES = {"A": "LQR directly", "B_flight": f"Spin-up {F_FLIGHT:.2f} N (flight) + LQR", "B_half": f"Spin-up {F_HALF:.2f} N (m g/2) + LQR"}


def build(case, tau, alpha=1.0):
    eq = relaxed_hover(P)
    fail = FailureLQR(P, eq)
    if case == "B_flight":
        fail = SpinUpThenLQR(P, fail, f_spin=F_FLIGHT)
    elif case == "B_half":
        fail = SpinUpThenLQR(P, fail, f_spin=F_HALF)
    return eq, DelaySupervisor(HealthyLQR(P, alpha=alpha), fail, t_fail=0.0, tau=tau)


def x0_hover(seed=None):
    if seed is None:
        return make_state()
    rng = np.random.default_rng(seed)
    return make_state(v=rng.normal(0, 0.3, 3), euler=rng.normal(0, np.deg2rad(3), 3),
                      w=rng.normal(0, 0.3, 3))


def run(args):
    case, tau, alpha, seed = args
    eq, sup = build(case, tau, alpha)
    log = simulate(x0_hover(seed), sup, P, T_RUN, dt=DT, ctrl_period=DT, log_every=5)
    o = evaluate(log, eq)
    return dict(case=case, tau=tau, alpha=alpha, seed=-1 if seed is None else seed,
                z_max=float(np.max(log.z)), **o.as_dict())


def read_csv(path):
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in ("tau", "alpha", "alt_loss", "min_nz", "t_capture", "max_rate", "z_max"):
            r[k] = float(r[k])
        r["seed"] = int(r["seed"])
        for k in ("captured", "safe"):
            r[k] = r[k] == "True"
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def crossing(taus, p, level):
    """First delay at which p falls below `level` (linear interpolation); nan if never."""
    for i in range(len(taus)):
        if p[i] < level:
            if i == 0:
                return 0.0
            t0, t1, p0, p1 = taus[i - 1], taus[i], p[i - 1], p[i]
            return t0 + (p0 - level) / (p0 - p1) * (t1 - t0)
    return float("nan")


def main():
    apply_style()
    out_t, out_f = ROOT / "results/tables", ROOT / "results/figures"
    jobs = [(c, t, 1.0, None) for c in CASES for t in TAUS]
    jobs += [("B_flight", t, a, None) for a in ALPHAS if a != 1.0 for t in TAUS]
    jobs += [(c, t, 1.0, s) for c in ("B_flight", "B_half") for t in MC_TAUS for s in range(MC_SEEDS)]
    csv_path = out_t / "e4_delay_sweep.csv"
    if "--plot-only" not in sys.argv:
        with ProcessPoolExecutor(max_workers=8) as ex:
            res = list(ex.map(run, jobs, chunksize=4))
        with open(csv_path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
            w.writeheader()
            w.writerows(res)
    res = read_csv(csv_path)
    nominal = [r for r in res if r["seed"] == -1]
    mc = [r for r in res if r["seed"] >= 0]

    def sel(c, a=1.0):
        return sorted([r for r in nominal if r["case"] == c and r["alpha"] == a], key=lambda r: r["tau"])

    stats = {}
    for c in ("B_flight", "B_half"):
        rows = []
        for t in MC_TAUS:
            rr = [r for r in mc if r["case"] == c and r["tau"] == t]
            k = sum(r["safe"] for r in rr)
            kc = sum(r["captured"] for r in rr)
            lo, hi = wilson(k, len(rr))
            rows.append(dict(tau=t, n=len(rr), safe=k, captured=kc, p=k / len(rr), lo=lo, hi=hi,
                             med_loss=float(np.median([r["alt_loss"] for r in rr]))))
        p = np.array([r["p"] for r in rows])
        pc = np.array([r["captured"] / r["n"] for r in rows])
        stats[c] = dict(rows=rows, tau50=crossing(MC_TAUS, p, 0.5), tau90=crossing(MC_TAUS, p, 0.9),
                        tau50_cap=crossing(MC_TAUS, pc, 0.5))

    ms = lambda v: "> 60 ms" if np.isnan(v) else f"{v * 1e3:.0f} ms"  # noqa: E731
    L = ["# E4: Recovery versus fault-detection delay (nonlinear simulation, nominal plant)", "",
         f"Hover at z = 0; rotor 4 fails at t = 0; healthy LQR until t = τ; then the failure strategy. "
         f"Runs of {T_RUN:.0f} s. Success criterion fixed in advance (`rotorfail/metrics.py`): attitude captured "
         f"(|n − n̄| < 0.05 and |ω − ω̄| < 2 rad/s over the last 1 s of a completed run), altitude loss < "
         f"{ALT_LOSS_MAX:.0f} m, never inverted (n_z > 0).", "",
         f"Spin-up thrust: **{F_FLIGHT} N** per rotor is read from the flight data in Mueller & D'Andrea "
         f"(2014) Fig. 4; **{F_HALF:.2f} N** (m g / 2) is a sensitivity case.", "",
         f"## Monte Carlo: {MC_SEEDS} random pre-failure states per delay", "",
         "Pre-failure state: velocity σ = 0.3 m/s, Euler angles σ = 3°, body rates σ = 0.3 rad/s. "
         "P(SAFE) with 95% Wilson interval.", "",
         "| τ (ms) | " + " | ".join(f"{CASES[c]}: P(SAFE) [95% CI] / captured / median alt. loss (m)" for c in stats) + " |",
         "|---|" + "---|" * len(stats)]
    for i, t in enumerate(MC_TAUS):
        cells = []
        for c in stats:
            r = stats[c]["rows"][i]
            cells.append(f"{r['p']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}] / {r['captured']}/{r['n']} / {r['med_loss']:.2f}")
        L.append(f"| {t * 1e3:.0f} | " + " | ".join(cells) + " |")
    L += ["", "| Spin-up thrust | τ₉₀ (P(SAFE) falls below 0.9) | τ₅₀ (P(SAFE) falls below 0.5) | τ₅₀ for capture only |",
          "|---|---|---|---|"]
    for c in stats:
        st = stats[c]
        L.append(f"| {CASES[c]} | {ms(st['tau90'])} | {ms(st['tau50'])} | {ms(st['tau50_cap'])} |")
    L += ["", "## Nominal start (exact hover), healthy-LQR aggressiveness α = 1", "",
          "| τ (ms) | " + " | ".join(f"{CASES[c]}: alt. loss (m) / min n_z / SAFE" for c in CASES) + " |",
          "|---|" + "---|" * len(CASES)]
    for i, t in enumerate(TAUS):
        cells = []
        for c in CASES:
            r = sel(c)[i]
            cells.append(f"{r['alt_loss']:.2f} / {r['min_nz']:.2f} / {'yes' if r['safe'] else 'no'}")
        L.append(f"| {t * 1e3:.0f} | " + " | ".join(cells) + " |")
    L += ["", "## Healthy-LQR aggressiveness (spin-up at the flight thrust, nominal start)", "",
          "| α | Largest grid τ with every smaller τ SAFE |", "|---|---|"]
    for a in ALPHAS:
        best = None
        for r in sel("B_flight", a):
            if not r["safe"]:
                break
            best = r["tau"]
        L.append(f"| {a} | {'none' if best is None else f'{best * 1e3:.0f} ms'} |")
    rb = sel("B_flight")[0]
    L += ["", f"At τ = 0 with the flight thrust the vehicle first climbs {rb['z_max']:.2f} m and loses "
          f"{rb['alt_loss']:.2f} m below its starting height (transient), qualitatively like Fig. 4 of the paper, "
          "where it climbs about 0.9 m. The steady height offset seen in flight comes from thrust loss while "
          "spinning, which the nominal model does not contain.", ""]
    (out_t / "e4_delay_sweep.md").write_text("\n".join(L))
    print("\n".join(L[:40]))

    # ---- figure: P(SAFE | tau)
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    ax.axvspan(DETECTOR_BAND[0] * 1e3, 60, color="#f0efec", zorder=0)
    ax.text(45, 0.97, "fast detectors\n(30–130 ms)", color=MUTED, fontsize=8, ha="center", va="top",
            transform=blended_transform_factory(ax.transData, ax.transAxes))
    for c, col in zip(stats, SERIES):
        rows = stats[c]["rows"]
        t = np.array([r["tau"] for r in rows]) * 1e3
        ax.fill_between(t, [r["lo"] for r in rows], [r["hi"] for r in rows], color=col, alpha=0.15, lw=0)
        ax.plot(t, [r["p"] for r in rows], color=col, marker="o", ms=3.5, label=CASES[c])
    ax.set_xlabel("detection delay τ (ms)")
    ax.set_ylabel("P(SAFE), 40 starts per delay")
    ax.set_ylim(-0.03, 1.03)
    ax.set_title("E4 · Probability of a safe recovery versus detection delay (95% Wilson bands)")
    ax.legend(loc="lower left")
    fig.tight_layout()
    save(fig, out_f / "e4_p_safe.png")

    # ---- figure: nominal sweep
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    for a in ax:
        a.axvspan(DETECTOR_BAND[0] * 1e3, DETECTOR_BAND[1] * 1e3, color="#f0efec", zorder=0)
        a.text(80, 0.97, "fast\ndetectors", color=MUTED, fontsize=8, ha="center", va="top",
               transform=blended_transform_factory(a.transData, a.transAxes))
    for c, col in zip(CASES, SERIES):
        rr = sel(c)
        t = np.array([r["tau"] for r in rr]) * 1e3
        ax[0].plot(t, [max(r["alt_loss"], 1e-2) for r in rr], color=col, marker="o", ms=3, label=CASES[c])
        ax[1].plot(t, [r["min_nz"] for r in rr], color=col, marker="o", ms=3, label=CASES[c])
    ax[0].set_yscale("log")
    ax[0].axhline(ALT_LOSS_MAX, color=REF, lw=0.8)
    ax[0].text(302, ALT_LOSS_MAX * 1.12, "2 m limit", color=REF, fontsize=8, ha="right")
    ax[0].set_title("Altitude loss after the failure")
    ax[0].set_ylabel("m (log scale)")
    ax[1].axhline(0, color=REF, lw=0.8)
    ax[1].text(302, 0.04, "inverted below", color=REF, fontsize=8, ha="right")
    ax[1].set_title("Worst tilt: min n_z (1 = level, < 0 = upside down)")
    for a in ax:
        a.set_xlabel("detection delay τ (ms)")
    ax[0].legend(loc="lower right", fontsize=8)
    fig.suptitle("E4 · Recovery versus detection delay, exact hover start", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e4_delay_sweep.png")

    # ---- figure: time histories at the flight thrust
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    eq = None
    for tau, col in zip([0.0, 0.02, 0.05], SERIES):
        eq, sup = build("B_flight", tau)
        log = simulate(x0_hover(), sup, P, 6.0, dt=DT, ctrl_period=DT, log_every=2)
        lab = f"τ = {tau * 1e3:.0f} ms"
        ax[0].plot(log.t, log.n[:, 2], color=col, label=lab)
        ax[1].plot(log.t, log.w[:, 2], color=col, label=lab)
        ax[2].plot(log.t, log.z, color=col, label=lab)
    ax[0].axhline(0, color=REF, lw=0.8)
    ax[0].set_title("n_z (tilt of the thrust axis)")
    ax[1].axhline(eq.w[2], color=REF, lw=0.8)
    ax[1].set_title("Yaw rate r (line: r̄)")
    ax[1].set_ylabel("rad/s")
    ax[2].set_title("Altitude")
    ax[2].set_ylabel("m")
    ax[2].set_ylim(max(ax[2].get_ylim()[0], -40), max(ax[2].get_ylim()[1], 1))
    ax[0].legend(loc="lower right")
    for a in ax:
        a.set_xlabel("time after failure (s)")
    fig.suptitle(f"E4 · Spin-up ({F_FLIGHT} N) + LQR with detection delay τ", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e4_time_histories.png")

    # ---- figure: undetected phase (healthy LQR flying a 3-rotor vehicle)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    alive = lambda t: np.array([True, True, True, False])  # noqa: E731
    for a_, col in zip(ALPHAS, SERIES):
        h = HealthyLQR(P, alpha=a_)
        log = simulate(make_state(), h, P, 0.3, dt=5e-4, ctrl_period=1e-3, alive_fn=alive, log_every=2)
        tilt = np.degrees(np.arccos(np.clip(log.n[:, 2], -1, 1)))
        ax[0].plot(log.t * 1e3, tilt, color=col, label=f"healthy LQR, α = {a_}")
        ax[1].plot(log.t * 1e3, log.x[:, 14], color=col, label=f"α = {a_}")
    t = np.linspace(0, 0.3, 100)
    pdot_min = P.l * P.f_min / P.Ixx_B
    ax[0].plot(t * 1e3, np.degrees(0.5 * pdot_min * t ** 2), color=REF, lw=1.0,
               label="lower bound ½·(l f_min / I_xx)·t²")
    ax[0].set_title("Tilt during the undetected phase")
    ax[0].set_ylabel("deg")
    ax[0].legend(loc="upper left")
    ax[1].axhline(P.f_min, color=REF, lw=0.8)
    ax[1].text(150, P.f_min + 0.05, "idle thrust f_min", color=REF, fontsize=8)
    ax[1].set_title("Thrust of rotor 2 (opposite the failed rotor)")
    ax[1].set_ylabel("N")
    for a in ax:
        a.set_xlabel("time after failure (ms)")
    fig.suptitle("E4 · The healthy controller cannot cancel the roll torque", fontsize=12)
    fig.tight_layout()
    save(fig, out_f / "e4_undetected_phase.png")


if __name__ == "__main__":
    main()
