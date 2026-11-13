"""E9a: where is the hand-over state of the published strategy, and is it inside the E5 certificate?

Question. In the strategy of Mueller and D'Andrea (2014) the vehicle spins up on rotors 1 and 3 with
no feedback and the failure LQR takes over when |w| > 10 rad/s. Where is the state at that hand-over
(in capture coordinates), how does it depend on the detection delay tau and on the pre-failure state,
and does the existing saturation-aware LTI certificate (E5, decay 0.1) contain it? The answer fixes
the target of the delay-budget certificates (E9b to E9d).

Fixed before running (do not tune afterwards)
  - Plant: nominal (`DEFAULT`). Chain: healthy LQR for tau, then SpinUpThenLQR (w_switch = 10 rad/s)
    with the failure LQR (default weights). Controller period 1 ms, simulation step 1 ms, 10 s runs
    (the E4 protocol; `DelaySupervisor` and `SpinUpThenLQR` are used unchanged).
  - Spin-up thrust f_spin in {2.95 N (flight data), 2.45 N (m g / 2)}.
  - tau in {0, 5, ..., 60, 80, 100, 130} ms.
  - Starts: the exact hover (seed None), and the 40 Monte Carlo starts of E4 (seeds 0 to 39, the same
    generator `x0_hover` imported from `e4_delay_sweep`).
  - Hand-over state: the true simulator state at the first controller sample at which SpinUpThenLQR
    stops spinning up. Capture coordinates: the 10-state deviation from the relaxed hover
    (p, q, r, n_x, n_y, z, v_z and the true thrusts of rotors 1 to 3). The LQR's reset motor estimate is
    (f_spin, 0, f_spin); the difference to the true thrusts is recorded.
  - Certificate: E5 setup (`FailureLQR` default, ubar = min(f_bar - f_min, f_max - f_bar), motor-state
    box = ubar, decay 0.1, maximal log det), recomputed here with `invariant_ellipsoid`. For each
    hand-over state x the value x'Px on all 10 states and the scaling alpha = 1/sqrt(x'Px) such that
    alpha*x is on the boundary (alpha >= 1 means inside). Altitude is bounded separately in the
    delay-budget chain, so the same two numbers are also computed on the 8 attitude/motor states (p, q, r, n_x,
    n_y, three thrusts) with the projection of the ellipsoid (the Q sub-block).
  - Outcome: the fixed criterion of `rotorfail/metrics.py` (SAFE).
  - Acceptance: the six exact-hover rows of section 3.2 of the completion plan are reproduced to two
    decimals (hand-over time, w, n, |n - n_bar|, SAFE). The check is printed in the table.
  - Decision rule (stated before the run): if alpha < 1 (outside the E5 ellipsoid) for the exact-hover
    hand-over at tau = 0 and f_spin = 2.95 N, the published hand-over state is not certifiable with the
    E5 certificate; this is reported and the work stops after X1 for review before D4 and D5.
  - Trajectories: |n - n_bar| and r - r_bar at every controller sample from the failure time until the
    hand-over, for the exact-hover starts.

Outputs
  results/tables/e9a_handover.md, results/tables/e9a_handover.csv
  results/figures/e9a_handover.png
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

import matplotlib.pyplot as plt  # noqa: E402

from e4_delay_sweep import MC_SEEDS, x0_hover  # noqa: E402
from rotorfail.certify import invariant_ellipsoid, slice_ellipse  # noqa: E402
from rotorfail.control import DelaySupervisor, FailureLQR, HealthyLQR, SpinUpThenLQR  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import MUTED, REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

DT = 1e-3
T_RUN = 10.0
DECAY = 0.1
F_SPINS = (2.95, 2.45)
TAUS = [round(t, 3) for t in list(np.arange(0.0, 0.0601, 0.005)) + [0.08, 0.10, 0.13]]
NAMES = ["p", "q", "r", "n_x", "n_y", "z", "v_z", "f1", "f2", "f3"]
SUB = [0, 1, 2, 3, 4, 7, 8, 9]          # attitude and motor states (altitude excluded)

# Section 3.2 of the completion plan: (f_spin, tau ms) -> (t_h, w, n, |n - n_bar|, SAFE)
REF32 = {
    (2.95, 0): (0.647, (0.00, -0.97, 9.96), (-0.12, -0.46, 0.88), 0.75, True),
    (2.95, 10): (0.649, (-0.03, -1.59, 9.88), (-0.20, -0.70, 0.68), 1.03, True),
    (2.95, 20): (0.649, (-0.06, -2.11, 9.78), (-0.23, -0.86, 0.46), 1.26, True),
    (2.95, 30): (0.649, (-0.08, -2.54, 9.68), (-0.25, -0.94, 0.25), 1.43, False),
    (2.45, 0): (0.806, (0.07, -0.97, 9.96), (-0.41, -0.24, 0.88), 0.66, True),
    (2.45, 20): (0.803, (0.08, -2.11, 9.78), (-0.78, -0.41, 0.47), 1.15, False),
}


class Probe(SpinUpThenLQR):
    """SpinUpThenLQR that records the state at the hand-over and the spin-up trajectory (logging only)."""
    rec_traj = False

    def __call__(self, t, x):
        was = self.spinning_up
        if was and self.rec_traj:
            self.traj.append((t, x.copy()))
        u = super().__call__(t, x)
        if was and not self.spinning_up:
            self.handover = (t, x.copy())
        return u


def run(args):
    f_spin, tau, seed = args
    eq = relaxed_hover(P)
    probe = Probe(P, FailureLQR(P, eq), f_spin=f_spin)
    probe.handover, probe.traj, probe.rec_traj = None, [], seed is None
    sup = DelaySupervisor(HealthyLQR(P), probe, t_fail=0.0, tau=tau)
    log = simulate(x0_hover(seed), sup, P, T_RUN, dt=DT, ctrl_period=DT, log_every=5)
    o = evaluate(log, eq)
    out = dict(f_spin=f_spin, tau=tau, seed=-1 if seed is None else seed, safe=bool(o.safe),
               captured=bool(o.captured), alt_loss=float(o.alt_loss), min_nz=float(o.min_nz), handed=False)
    if probe.handover is not None:
        th, x = probe.handover
        n = _n(x)
        dev = np.concatenate((x[10:13] - eq.w, n[:2] - eq.n[:2], [x[2], x[5]], x[13:16] - eq.f[:3]))
        out.update(handed=True, t_h=float(th), sample=int(round(th / DT)), dev=dev, n=n, w=x[10:13].copy(),
                   dn=float(np.linalg.norm(n - eq.n)), nz=float(n[2]), f_true=x[13:16].copy(),
                   f_reset=np.array([min(f_spin, P.f_max), 0.0, min(f_spin, P.f_max)]))
    if probe.traj:
        tt = np.array([a for a, _ in probe.traj])
        nn = np.array([_n(x) for _, x in probe.traj])
        ww = np.array([x[10:13] for _, x in probe.traj])
        out["traj"] = (tt, np.linalg.norm(nn - eq.n, axis=1), ww[:, 2] - eq.w[2])
    return out


def _n(x):
    from rotorfail.dynamics import IDX_Q, quat_to_rot
    return quat_to_rot(x[IDX_Q]).T @ np.array([0.0, 0.0, 1.0])


def certificate():
    eq = relaxed_hover(P)
    f = FailureLQR(P, eq)
    fb = eq.f[:3]
    ubar = np.minimum(fb - P.f_min, P.f_max - fb)
    box = [np.inf] * 7 + list(ubar)
    r = invariant_ellipsoid(f.model.A, f.model.B, f.K, ubar, decay=DECAY, box=box)
    assert r["status"] == "optimal", r["status"]
    return r["Q"], r["P"]


def scaling(Q, dev, idx=None):
    """alpha such that alpha*dev is on the boundary; idx = coordinates of a projection."""
    if idx is None:
        v = float(dev @ np.linalg.solve(Q, dev))
    else:
        v = float(dev[idx] @ np.linalg.solve(Q[np.ix_(idx, idx)], dev[idx]))
    return v, (1.0 / np.sqrt(v) if v > 0 else np.inf)


def main():
    apply_style()
    out_t, out_f = ROOT / "results/tables", ROOT / "results/figures"
    Q, Pm = certificate()
    jobs = [(fs, t, s) for fs in F_SPINS for t in TAUS for s in [None] + list(range(MC_SEEDS))]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run, jobs, chunksize=4))
    for r in res:
        if r["handed"]:
            r["v_full"], r["alpha_full"] = scaling(Q, r["dev"])
            r["v_sub"], r["alpha_sub"] = scaling(Q, r["dev"], SUB)
    with open(out_t / "e9a_handover.csv", "w", newline="") as fh:
        cols = ["f_spin", "tau", "seed", "safe", "captured", "handed", "t_h", "sample", "nz", "dn", "alpha_full",
                "alpha_sub"] + [f"d_{n}" for n in NAMES] + ["w_p", "w_q", "w_r", "n_x", "n_y", "f_err1", "f_err2", "f_err3"]
        w = csv.writer(fh)
        w.writerow(cols)
        for r in res:
            if r["handed"]:
                w.writerow([r["f_spin"], r["tau"], r["seed"], r["safe"], r["captured"], True, f"{r['t_h']:.3f}",
                            r["sample"], f"{r['nz']:.4f}", f"{r['dn']:.4f}", f"{r['alpha_full']:.5f}",
                            f"{r['alpha_sub']:.5f}"] + [f"{v:.5f}" for v in r["dev"]]
                           + [f"{v:.4f}" for v in r["w"]] + [f"{v:.4f}" for v in r["n"][:2]]
                           + [f"{v:.4f}" for v in r["f_true"] - r["f_reset"]])
            else:
                w.writerow([r["f_spin"], r["tau"], r["seed"], r["safe"], r["captured"], False] + [""] * (len(cols) - 6))

    ex_rows = {(r["f_spin"], r["tau"]): r for r in res if r["seed"] == -1}
    L = ["# E9a: hand-over state of the published strategy and the E5 certificate", "",
         "Nominal plant; healthy LQR for tau, then spin-up (rotors 1 and 3 at f_spin, rotor 2 stopped) and the "
         "failure LQR once |w| > 10 rad/s. Capture coordinates are deviations from the relaxed hover; "
         "alpha is the scaling that puts the hand-over deviation on the boundary of the E5 ellipsoid "
         f"(decay {DECAY}); alpha >= 1 means inside. 'Sub' uses the 8 attitude and motor states only "
         "(altitude excluded). See the docstring of `experiments/e9a_handover.py`.", ""]
    ce = Q.shape[0]
    L += ["E5 ellipsoid semi-axes (sqrt Q_ii): " + ", ".join(f"{n} {np.sqrt(Q[i, i]):.3g}" for i, n in enumerate(NAMES)) + ".", ""]

    # acceptance
    L += ["## Acceptance: reproduction of section 3.2 (exact hover start)", "",
          "| f_spin (N) | tau (ms) | t_h (s) | w (rad/s) | n | abs(n - n_bar) | SAFE | matches plan to 2 decimals |",
          "|---|---|---|---|---|---|---|---|"]
    all_ok = True
    for (fs, tm), (th, wr, nr, dn, sf) in REF32.items():
        r = ex_rows[(fs, tm / 1000.0)]
        ok = (r["handed"] and abs(r["t_h"] - th) < 0.0051 and np.allclose(r["w"], wr, atol=0.0051)
              and np.allclose(r["n"], nr, atol=0.0051) and abs(r["dn"] - dn) < 0.0051 and r["safe"] == sf)
        all_ok &= bool(ok)
        L.append(f"| {fs} | {tm} | {r['t_h']:.3f} | ({r['w'][0]:.2f}, {r['w'][1]:.2f}, {r['w'][2]:.2f}) | "
                 f"({r['n'][0]:.2f}, {r['n'][1]:.2f}, {r['n'][2]:.2f}) | {r['dn']:.2f} | "
                 f"{'yes' if r['safe'] else 'no'} | {'yes' if ok else 'NO'} |")
    L += ["", f"All six rows reproduced: **{'yes' if all_ok else 'NO'}**.", ""]

    # exact hover, all taus
    for fs in F_SPINS:
        L += [f"## Exact hover start, f_spin = {fs} N", "",
              "| tau (ms) | t_h (s) | sample | Delta r (rad/s) | Delta n_x | Delta n_y | n_z | abs(n - n_bar) | "
              "Delta z (m) | Delta v_z (m/s) | motor est. error f1, f2, f3 (N) | x'Px (all) | alpha (all) | alpha (sub) | SAFE |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for tm in TAUS:
            r = ex_rows[(fs, tm)]
            if not r["handed"]:
                L.append(f"| {tm * 1e3:.0f} | no hand-over | | | | | | | | | | | | | {'yes' if r['safe'] else 'no'} |")
                continue
            d = r["dev"]
            fe = r["f_true"] - r["f_reset"]
            L.append(f"| {tm * 1e3:.0f} | {r['t_h']:.3f} | {r['sample']} | {d[2]:+.2f} | {d[3]:+.3f} | {d[4]:+.3f} | "
                     f"{r['nz']:+.3f} | {r['dn']:.2f} | {d[5]:+.2f} | {d[6]:+.2f} | "
                     f"{fe[0]:+.2f}, {fe[1]:+.2f}, {fe[2]:+.2f} | {r['v_full']:.1f} | {r['alpha_full']:.3f} | "
                     f"{r['alpha_sub']:.3f} | {'yes' if r['safe'] else 'no'} |")
        L.append("")

    # Monte Carlo summary
    L += ["## Monte Carlo starts (the 40 starts of E4)", "",
          "Median [min, max] over the 40 starts that handed over; 'inverted' = n_z < 0 at the hand-over; "
          "'inside' counts hand-over states with alpha >= 1 (all 10 states / attitude and motor states).", "",
          "| f_spin (N) | tau (ms) | SAFE | handed over | t_h (s) | abs(n - n_bar) | Delta r (rad/s) | inverted | "
          "alpha (all) | inside (all / sub) | SAFE but outside (all) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    mc = [r for r in res if r["seed"] >= 0]
    for fs in F_SPINS:
        for tm in TAUS:
            rr = [r for r in mc if r["f_spin"] == fs and r["tau"] == tm]
            hh = [r for r in rr if r["handed"]]
            sf = sum(r["safe"] for r in rr)
            if not hh:
                L.append(f"| {fs} | {tm * 1e3:.0f} | {sf}/{len(rr)} | 0 | | | | | | | |")
                continue
            q = lambda key, f=lambda v: v: (f"{np.median([f(r[key]) for r in hh]):.2f} "  # noqa: E731
                                           f"[{min(f(r[key]) for r in hh):.2f}, {max(f(r[key]) for r in hh):.2f}]")
            dr = [r["dev"][2] for r in hh]
            L.append(f"| {fs} | {tm * 1e3:.0f} | {sf}/{len(rr)} | {len(hh)} | "
                     f"{np.median([r['t_h'] for r in hh]):.3f} | {q('dn')} | "
                     f"{np.median(dr):+.2f} [{min(dr):+.2f}, {max(dr):+.2f}] | {sum(r['nz'] < 0 for r in hh)} | "
                     f"{q('alpha_full')} | {sum(r['alpha_full'] >= 1 for r in hh)} / {sum(r['alpha_sub'] >= 1 for r in hh)} | "
                     f"{sum(r['safe'] and r['alpha_full'] < 1 for r in hh)} |")
    L.append("")

    # overall
    hh = [r for r in res if r["handed"]]
    safe_h = [r for r in hh if r["safe"]]
    L += ["## Summary", "",
          f"- Hand-over states recorded: {len(hh)} of {len(res)} runs; SAFE runs: {len(safe_h)}.",
          f"- Hand-over states inside the E5 ellipsoid (all 10 states): {sum(r['alpha_full'] >= 1 for r in hh)}; "
          f"on the attitude and motor states only: {sum(r['alpha_sub'] >= 1 for r in hh)}.",
          f"- SAFE runs whose hand-over state lies outside the E5 ellipsoid (all 10 states): "
          f"{sum(r['alpha_full'] < 1 for r in safe_h)} of {len(safe_h)}.",
          f"- Largest alpha over all hand-over states: all 10 states {max(r['alpha_full'] for r in hh):.3f}, "
          f"attitude and motor states {max(r['alpha_sub'] for r in hh):.3f}; smallest "
          f"{min(r['alpha_full'] for r in hh):.4f} and {min(r['alpha_sub'] for r in hh):.4f}.",
          f"- Exact hover, tau = 0, f_spin = 2.95 N: alpha = {ex_rows[(2.95, 0.0)]['alpha_full']:.3f} (all), "
          f"{ex_rows[(2.95, 0.0)]['alpha_sub']:.3f} (sub). Decision rule: "
          + ("alpha < 1, so the published hand-over state is NOT inside the E5 certificate." if
             ex_rows[(2.95, 0.0)]["alpha_full"] < 1 else "alpha >= 1, the hand-over state is inside."), ""]
    # inverted
    inv = [(r["f_spin"], r["tau"]) for r in ex_rows.values() if r["handed"] and r["nz"] < 0]
    L.append("- Exact-hover hand-overs with the vehicle inverted (n_z < 0): " +
             (", ".join(f"f_spin {a} N, tau {b * 1e3:.0f} ms" for a, b in sorted(inv)) if inv else "none") + ".")
    L.append("")

    # deviation build-up
    L += ["## Where the deviation builds up (exact hover, tau = 0 and 20 ms)", "",
          "| f_spin (N) | tau (ms) | time since failure (s) | abs(n - n_bar) | r - r_bar (rad/s) |", "|---|---|---|---|---|"]
    for fs in F_SPINS:
        for tm in (0.0, 0.02):
            tt, dn, dr = ex_rows[(fs, tm)]["traj"]
            for tq in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
                k = int(np.argmin(np.abs(tt - tq - tm)))
                if abs(tt[k] - tq - tm) < 1.5e-3:
                    L.append(f"| {fs} | {tm * 1e3:.0f} | {tt[k]:.3f} | {dn[k]:.2f} | {dr[k]:+.2f} |")
    L.append("")
    (out_t / "e9a_handover.md").write_text("\n".join(L))
    print("\n".join(L))

    # figure
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    iR, iNx, iNy = 2, 3, 4
    for ax, (i, j, xl, yl) in zip(axs[:2], [(iR, iNy, "Δr = r − r̄ (rad/s)", "Δn_y"),
                                            (iNx, iNy, "Δn_x", "Δn_y")]):
        E = slice_ellipse(Pm, i, j)
        ax.fill(E[0], E[1], color=SERIES[0], alpha=0.12)
        ax.plot(E[0], E[1], color=SERIES[0], lw=2, label="E5 certificate (slice)")
        for fs, mk in zip(F_SPINS, ("o", "s")):
            for safe, col in ((True, SERIES[2]), (False, SERIES[1])):
                pts = np.array([[r["dev"][i], r["dev"][j]] for r in hh if r["f_spin"] == fs and r["seed"] >= 0
                                and r["safe"] == safe])
                if len(pts):
                    ax.scatter(pts[:, 0], pts[:, 1], s=9, color=col, marker=mk, alpha=0.45, zorder=2)
            pts = np.array([[r["dev"][i], r["dev"][j]] for r in hh if r["f_spin"] == fs and r["seed"] == -1])
            ax.scatter(pts[:, 0], pts[:, 1], s=55, facecolor="none", edgecolor=SERIES[6], marker=mk, lw=1.4, zorder=3)
        ax.axhline(0, color=REF, lw=0.6)
        ax.axvline(0, color=REF, lw=0.6)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
    axs[0].set_title("E9a · hand-over states, (Δr, Δn_y)")
    axs[1].set_title("E9a · hand-over states, (Δn_x, Δn_y)")
    h = [plt.Line2D([], [], color=SERIES[0], lw=2), plt.Line2D([], [], marker="o", ls="", color=SERIES[2]),
         plt.Line2D([], [], marker="o", ls="", color=SERIES[1]),
         plt.Line2D([], [], marker="o", ls="", mfc="none", mec=SERIES[6]),
         plt.Line2D([], [], marker="o", ls="", color=MUTED), plt.Line2D([], [], marker="s", ls="", color=MUTED)]
    axs[0].legend(h, ["E5 certificate (slice)", "Monte Carlo, SAFE", "Monte Carlo, not SAFE", "exact hover start",
                      "f_spin 2.95 N", "f_spin 2.45 N"], fontsize=7.5, loc="lower left")
    for k, tm in enumerate((0.0, 0.02, 0.04, 0.06)):
        for fs, ls in zip(F_SPINS, ("-", "--")):
            tt, dn, dr = ex_rows[(fs, tm)]["traj"]
            axs[2].plot(tt, dn, ls=ls, color=SERIES[k % 4], label=f"τ {tm * 1e3:.0f} ms, {fs} N")
    axs[2].set_xlabel("time since failure (s)")
    axs[2].set_ylabel("‖n − n̄‖ (exact hover start)")
    axs[2].set_title("E9a · build-up of the attitude deviation")
    axs[2].legend(fontsize=7, ncol=2)
    fig.tight_layout()
    save(fig, out_f / "e9a_handover.png")


if __name__ == "__main__":
    main()
