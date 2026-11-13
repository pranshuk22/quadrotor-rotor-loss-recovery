"""E9d: reachable hand-over sets, containment, beta(tau) and the certified delay budget tau* (task D6).

Question. For a pre-failure set X0 and a detection delay tau, is the hand-over set S(tau) of the chain
(healthy LQR for tau, open-loop spin-up, hand-over at |w| > w_sw) contained in a certified invariant set C of
the capture controller? beta(tau) is the largest scaling with c + beta L-ball inside C (plan section 4,
beta >= 1 certified); tau* = first grid tau with beta < 1. If the centre c is outside C, beta is undefined
and the scaling alpha_c with alpha_c c on the boundary of C is reported.

Fixed before running (do not tune afterwards)
  - X0: the 99 % chi-square ellipsoid (9 dof, radius sqrt(21.67) = 4.655 sigma) of the E4 pre-failure
    distribution (v ~ 0.3 m/s, Euler angles ~ 3 deg, w ~ 0.3 rad/s, per axis), centred at the hover; the family
    gamma X0, gamma in {0 (exact hover), 0.1, 0.25, 0.5, 1}.
  - Nominal plant; healthy LQR alpha = 1; controller period 1 ms; switch at the first sample with t >= tau.
  - tau in {0, 5, ..., 60, 80, 100, 130} ms; f_spin in {2.95, 2.45} N; w_sw in {10 (published), 12, 14, 16, 18} rad/s.
  - Hand-over set: variational method along the nonlinear nominal trajectory (the chain Jacobian of
    `rotorfail.reach.chain_jacobian`, central differences, step 1e-3 sigma, hand-over state interpolated to
    the exact crossing of |w| = w_sw). This single nonlinear-trajectory method covers plan steps 2(b), 4 and 5
    (the coordinate change from the healthy Euler state to the capture coordinates is part of the simulated
    map and is validated through the coverage check; no separate Jacobian-versus-exact comparison is made).
  - Undetected phase, method (a) of the proposal (affine LTI model, exact ellipsoid propagation), compared with
    1000 nonlinear samples at tau in {10, 30, 60} ms for gamma = 1 (seed 7000): fraction of samples inside the
    propagated ellipsoid and worst normalised excess. Saturation classification of the three working rotors
    with support functions for every tau and gamma (unsat / sat / ambiguous). Configurations with a saturated or
    ambiguous rotor are marked: the variational set is then a local linearisation around the nominal modes.
  - Coverage of the hand-over sets: 1000 nonlinear samples (seed 7100) for gamma = 1, f_spin = 2.95, tau in
    {0, 20, 60} ms and w_sw in {10, 18}; 100 samples (seed 7200) for gamma = 1, f_spin = 2.95, every other
    (tau, w_sw). Reported: fraction inside the linearised set, worst normalised excess (min t with the sample
    inside c + t L-ball), worst orthogonal residual (the set is rank 9 in 10 dimensions), hand-over time window
    in samples, and the largest gap between the first-sample state and the interpolated state ("jitter").
    A configuration is called "linearised set verified" only if every sample is inside after the set is
    inflated by max(1, worst excess) and a margin column of the size of the worst orthogonal residual is added;
    inflated results are labelled "sampling-based".
  - Certificates C (read from results/certificates/e9c_designs.npz, produced by E9c, nominal plant):
      published LQR gain on the box designed for the same w_sw ("LQR"),
      the accepted synthesised gain of E9c for that w_sw with the largest beta_final ("redesigned"),
    each in two tiers: "rigorous" = kappa Q (remainder-inclusive, g_P <= 0.05) and "LPV" = Q (remainder-free
    LPV certificate). Only the tier named "rigorous" is called certified; "LPV" is certified for the quasi-LPV
    model only.
  - Containment: the S-procedure LMI (`max_beta`), cross-checked against the trust-region evaluation
    (`max_beta_exact`); the largest disagreement is reported.
  - tau* = first grid tau with beta < 1 (or with the centre outside), reported as "does not exist" if
    beta(0) < 1. The full grid is always computed; no bisection is done across a non-monotone region.
  - Altitude (SAFE needs a loss of less than 2 m) is not bounded by the attitude certificate in this experiment;
    the altitude loss is reported only as observed in the E4 Monte Carlo of E9c (not certified).

Outputs
  results/tables/e9d_certified_delay.md, results/tables/e9d_certified_delay.csv, results/figures/e9d_certified_delay.png
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
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt  # noqa: E402

from rotorfail.control import DelaySupervisor, HealthyLQR  # noqa: E402
from rotorfail.dynamics import make_state, rk4_step  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import MUTED, REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.reach import (X0_RADIUS, X0_SIGMA, ChainSpec, UndetectedLTI, centre_scaling,  # noqa: E402
                             chain_jacobian, command_ranges, coverage, hand_over_set, max_beta, max_beta_exact,
                             run_chain, sample_x0, x0_state)

TAUS = [round(t, 3) for t in list(np.arange(0.0, 0.0601, 0.005)) + [0.08, 0.10, 0.13]]
F_SPINS = (2.95, 2.45)
W_SWS = (10, 12, 14, 16, 18)
GAMMAS = (0.0, 0.1, 0.25, 0.5, 1.0)
GAIN_BOUNDS = (2, 4, 8, 16)
DES = np.load(ROOT / "results/certificates/e9c_designs.npz")


def design_keys(w):
    """Keys of the LQR design and of the accepted synthesised design with the largest beta_final for threshold w."""
    out = {"LQR": f"w{w}_glqr"}
    best, bk = -1.0, None
    for g in GAIN_BOUNDS:
        k = f"w{w}_g{g}"
        if k + "_Q" not in DES.files or DES[k + "_ok"][0] < 0.5:
            continue
        Q, kap, d = DES[k + "_Q"], DES[k + "_kappa"][0], DES[k + "_d"]
        beta = np.sqrt(kap) / np.sqrt(d @ np.linalg.solve(Q, d))
        if beta > best:
            best, bk = beta, k
    if bk is not None:
        out["redesigned"] = bk
    return out


def certificates(w):
    """{(controller, tier): Q2} for threshold w (only accepted designs; tier 'rigorous' needs a kappa)."""
    out = {}
    for ctrl, k in design_keys(w).items():
        if k + "_Q" not in DES.files:
            continue
        Q, kap = DES[k + "_Q"], DES[k + "_kappa"][0]
        out[(ctrl, "LPV")] = Q
        if not np.isnan(kap) and DES[k + "_ok"][0] > 0.5:
            out[(ctrl, "rigorous")] = kap * Q
    return out


def hand_over_job(args):
    f, w, tau = args
    spec = ChainSpec(P, tau=tau, w_sw=float(w), f_spin=f)
    c, J, info = chain_jacobian(spec)
    return (f, w, tau), (c, J, info)


def coverage_job(args):
    f, w, tau, n, seed = args
    spec = ChainSpec(P, tau=tau, w_sw=float(w), f_spin=f)
    us = sample_x0(1.0, n, seed)
    dev, devi, th = [], [], []
    for u in us:
        r = run_chain(spec, u)
        if r["handed"]:
            dev.append(r["dev"])
            devi.append(r["dev_interp"])
            th.append(r["sample"])
        else:
            dev.append(None)
    return (f, w, tau), dict(dev=dev, devi=devi, samples=th, n=n, us=us)


def undetected_coverage(args):
    tau, n, seed = args
    lti = UndetectedLTI(P)
    steps = int(round(tau / lti.T))
    cs, Ps = lti.propagate(steps)
    L0 = np.zeros((15, 9))
    for i in range(3):
        L0[3 + i, i] = X0_SIGMA[i]
        L0[6 + i, 3 + i] = X0_SIGMA[3 + i]
        L0[9 + i, 6 + i] = X0_SIGMA[6 + i]
    L0 *= X0_RADIUS
    Lk = Ps[-1] @ L0
    us = sample_x0(1.0, n, seed)
    out = []
    ctrl = HealthyLQR(P)
    for u in us:
        sup = DelaySupervisor(ctrl, lambda t, x: np.zeros(4), t_fail=0.0, tau=1e9)
        x = x0_state(u, P)
        alive = np.array([True, True, True, False])
        for k in range(steps):
            cmd = sup(k * 1e-3, x)
            x = rk4_step(x, cmd, 1e-3, P, alive, True)
        z12 = ctrl.state12(x)
        z = np.concatenate((z12, x[13:16] - P.weight / 4.0))
        out.append(z)
    ex = coverage(cs[-1], Lk, out)
    return tau, float(np.mean(ex[:, 0] <= 1.0 + 1e-9)), float(ex[:, 0].max()), float(ex[:, 1].max())


def main():
    apply_style()
    out_t, out_f = ROOT / "results/tables", ROOT / "results/figures"
    L = ["# E9d: reachable hand-over sets, containment and the certified delay budget", "",
         "X0 = 99 % ellipsoid of the E4 pre-failure distribution, scaled by gamma; nominal plant. Choices fixed in the docstring of "
         "`experiments/e9d_certified_delay.py`. 'rigorous' certificates (remainder-inclusive) are certified; 'LPV' certificates are "
         "certified for the quasi-LPV model only (see E9b and E9c). beta >= 1 means the whole hand-over set is inside; "
         "'out (alpha_c)' means the centre of the hand-over set is outside C and alpha_c is the scaling of the centre onto the boundary.", ""]

    # --- undetected phase
    with ProcessPoolExecutor(max_workers=8) as ex:
        und = list(ex.map(undetected_coverage, [(0.01, 1000, 7000), (0.03, 1000, 7000), (0.06, 1000, 7000)]))
    L += ["## Undetected phase: affine LTI ellipsoid (proposal method) against 1000 nonlinear samples (gamma = 1)", "",
          "| tau (ms) | fraction of samples inside the LTI ellipsoid | worst normalised excess | worst orthogonal residual |", "|---|---|---|---|"]
    for t, fr, e, o in und:
        L.append(f"| {t * 1e3:.0f} | {fr:.3f} | {e:.3f} | {o:.2e} |")
    lti = UndetectedLTI(P)
    L0 = np.zeros((15, 9))
    for i in range(3):
        L0[3 + i, i], L0[6 + i, 3 + i], L0[9 + i, 6 + i] = X0_SIGMA[i], X0_SIGMA[3 + i], X0_SIGMA[6 + i]
    L += ["", "Saturation classification of rotors 1 to 3 over the propagated set (support function; 'clear' = all rotors unsaturated at all "
          "controller samples):", "", "| tau (ms) | " + " | ".join(f"gamma {g}" for g in GAMMAS) + " |", "|---|" + "---|" * len(GAMMAS)]
    sat_flag = {}
    for tau in TAUS:
        row = []
        for g in GAMMAS:
            cls = command_ranges(lti, int(round(tau / lti.T)), (g * X0_RADIUS * L0) @ (g * X0_RADIUS * L0).T)
            flat = [c for r in cls for c in r]
            lab = "clear" if all(c == "unsat" for c in flat) else ("ambiguous" if "ambiguous" in flat else "saturated")
            sat_flag[(tau, g)] = lab
            row.append(lab)
        L.append(f"| {tau * 1e3:.0f} | " + " | ".join(row) + " |")
    L.append("")

    # --- hand-over sets (Jacobians)
    jobs = [(f, w, t) for f in F_SPINS for w in W_SWS for t in TAUS]
    with ProcessPoolExecutor(max_workers=8) as ex:
        HO = dict(ex.map(hand_over_job, jobs, chunksize=2))

    # --- coverage
    cj = [(2.95, w, t, 1000, 7100) for w in (10, 18) for t in (0.0, 0.02, 0.06)]
    cj += [(2.95, w, t, 100, 7200) for w in W_SWS for t in TAUS if not (w in (10, 18) and t in (0.0, 0.02, 0.06))]
    with ProcessPoolExecutor(max_workers=8) as ex:
        CV = dict(ex.map(coverage_job, cj, chunksize=1))
    infl = {}
    L += ["## Coverage of the hand-over sets by 1000 or 100 nonlinear samples (gamma = 1, f_spin = 2.95 N)", "",
          "| w_sw | tau (ms) | samples | handed over | inside the linearised set | worst excess | worst orth. residual | hand-over sample window | jitter (max abs, first sample vs interpolated) | verdict |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for (f, w, t), v in sorted(CV.items(), key=lambda kv: (kv[0][1], kv[0][2])):
        c, J, info = HO[(f, w, t)]
        if c is None:
            L.append(f"| {w} | {t * 1e3:.0f} | {v['n']} | 0 | - | - | - | - | - | no hand-over |")
            continue
        _, Lm = hand_over_set(c, J, 1.0)
        devi = [d for d, o in zip(v["devi"], v["dev"]) if o is not None]
        dev = [d for d in v["dev"] if d is not None]
        ex_ = coverage(c, Lm, devi)
        jit = max(float(np.max(np.abs(a - b))) for a, b in zip(dev, devi))
        frac = float(np.mean(ex_[:, 0] <= 1 + 1e-9))
        worst, orth = float(ex_[:, 0].max()), float(ex_[:, 1].max())
        infl[(w, t)] = (max(1.0, worst), orth, jit)
        verdict = "linearised set verified" if frac == 1.0 and orth < 1e-6 else "linearised set misses samples (sampling-based after inflation)"
        s = v["samples"]
        L.append(f"| {w} | {t * 1e3:.0f} | {v['n']} | {len(devi)} | {frac:.3f} | {worst:.3f} | {orth:.2e} | {min(s)} to {max(s)} | {jit:.3f} | {verdict} |")
    L.append("")

    # --- containment
    rows = []
    worst_gap = 0.0
    for (f, w, t), (c, J, info) in HO.items():
        certs = certificates(w)
        for g in GAMMAS:
            for (ctrl, tier), Q2 in certs.items():
                if c is None:
                    rows.append(dict(f=f, w=w, tau=t, gamma=g, ctrl=ctrl, tier=tier, status="no hand-over", beta=np.nan, alpha_c=np.nan))
                    continue
                P2 = np.linalg.inv(Q2)
                ac = centre_scaling(P2, c)
                if ac < 1.0:
                    rows.append(dict(f=f, w=w, tau=t, gamma=g, ctrl=ctrl, tier=tier, status="out", beta=np.nan, alpha_c=ac))
                    continue
                _, Lm = hand_over_set(c, J, g)
                if g == 0.0:
                    b = np.inf
                else:
                    b = max_beta(c, Lm, Q2)
                    b2 = max_beta_exact(c, Lm, Q2)
                    if b is not None and b2 is not None:
                        worst_gap = max(worst_gap, abs(b - b2) / max(b2, 1e-9))
                rows.append(dict(f=f, w=w, tau=t, gamma=g, ctrl=ctrl, tier=tier, status="in", beta=b if b is not None else np.nan, alpha_c=ac))
    with open(out_t / "e9d_certified_delay.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    def tau_star(f, w, g, ctrl, tier):
        rr = sorted([r for r in rows if r["f"] == f and r["w"] == w and r["gamma"] == g and r["ctrl"] == ctrl and r["tier"] == tier],
                    key=lambda r: r["tau"])
        if not rr:
            return None, None
        first = rr[0]
        b0 = "centre outside, alpha_c = %.4f" % first["alpha_c"] if first["status"] == "out" else (
            "beta(0) = infinity (exact hover, centre inside)" if first["beta"] == np.inf else "beta(0) = %.4f" % first["beta"])
        ts = None
        for r in rr:
            if r["status"] != "in" or (np.isfinite(r["beta"]) and r["beta"] < 1.0):
                ts = r["tau"]
                break
        return b0, ts

    L += ["## Certified delay budget", "",
          f"Largest relative disagreement between the LMI and the trust-region evaluation of beta over all cases: {worst_gap:.2e}.", ""]
    for tier in ("rigorous", "LPV"):
        for ctrl in ("LQR", "redesigned"):
            L += [f"### Capture controller: {ctrl}; certificate tier: {tier}", "",
                  "| f_spin (N) | w_sw (rad/s) | gamma | state at tau = 0 | tau* |", "|---|---|---|---|---|"]
            for f in F_SPINS:
                for w in W_SWS:
                    for g in GAMMAS:
                        b0, ts = tau_star(f, w, g, ctrl, tier)
                        if b0 is None:
                            continue
                        L.append(f"| {f} | {w} | {g} | {b0} | {'does not exist' if ts == 0.0 else ('> 130 ms (never fails on the grid)' if ts is None else f'{ts * 1e3:.0f} ms')} |")
            L.append("")
    (out_t / "e9d_certified_delay.md").write_text("\n".join(L))
    print("\n".join(L))

    # figure: alpha_c / beta against tau for LQR and redesigned, LPV tier, gamma 0, f_spin 2.95
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, ctrl in zip(axs, ("LQR", "redesigned")):
        for k, w in enumerate(W_SWS):
            rr = sorted([r for r in rows if r["f"] == 2.95 and r["w"] == w and r["gamma"] == 0.0 and r["ctrl"] == ctrl and r["tier"] == "LPV"],
                        key=lambda r: r["tau"])
            if not rr:
                continue
            y = [r["alpha_c"] if r["status"] == "out" else np.nan for r in rr]
            ax.plot([r["tau"] * 1e3 for r in rr], y, marker="o", ms=3, color=SERIES[k], label=f"w_sw {w}")
        ax.axhline(1.0, color=REF, lw=0.8)
        ax.set_yscale("log")
        ax.set_xlabel("detection delay τ (ms)")
        ax.set_ylabel("α_c (centre of S(τ) onto the boundary of C)")
        ax.set_title(f"E9d · exact hover, {ctrl} capture, LPV tier")
        ax.legend(fontsize=7)
    fig.tight_layout()
    save(fig, out_f / "e9d_certified_delay.png")


if __name__ == "__main__":
    main()
