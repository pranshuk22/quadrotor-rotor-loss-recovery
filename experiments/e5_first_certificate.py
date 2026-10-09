"""E5 (preliminary): first saturation-aware LMI certificate for the failure-mode LQR,
built on the LTI model at the relaxed hover, and its comparison with nonlinear simulation.

Questions
  1. How large is the certified invariant ellipsoid (Hu-Lin conditions, thrust limits)?
  2. Does it contain the hover-onset state (H1)?  -> beta along the onset direction
  3. How conservative is it? -> nonlinear recovery map on a 2-D slice (Δr, Δn_y)

Outputs
  results/tables/e5_first_certificate.md
  results/figures/e5_certificate_slice.png
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

from rotorfail.certify import invariant_ellipsoid, semi_axes, slice_ellipse  # noqa: E402
from rotorfail.control import FailureLQR  # noqa: E402
from rotorfail.dynamics import IDX_Q, make_state, quat_from_n  # noqa: E402
from rotorfail.equilibrium import relaxed_hover  # noqa: E402
from rotorfail.metrics import evaluate  # noqa: E402
from rotorfail.params import DEFAULT as P  # noqa: E402
from rotorfail.plotting import REF, SERIES, apply_style, save  # noqa: E402
from rotorfail.sim import simulate  # noqa: E402

DECAY = 0.1
T_RUN = 8.0
ALIVE3 = lambda t: np.array([True, True, True, False])  # noqa: E731


def setup():
    eq = relaxed_hover(P)
    f = FailureLQR(P, eq)
    fb = eq.f[:3]
    ubar = np.minimum(fb - P.f_min, P.f_max - fb)
    box = [np.inf] * 7 + list(ubar)   # motor states stay within the physical thrust range
    x_on = np.concatenate((-eq.w, -eq.n[:2], [0.0, 0.0], P.weight / 4 - fb))
    return eq, f, ubar, box, x_on


def state_from_dev(eq, dev):
    """Nonlinear initial state from a deviation in the 10-state LQR coordinates."""
    w = eq.w + dev[0:3]
    nxy = eq.n[:2] + dev[3:5]
    nz2 = 1.0 - nxy @ nxy
    if nz2 <= 0:
        return None
    n = np.array([nxy[0], nxy[1], np.sqrt(nz2)])
    f = np.concatenate((eq.f[:3] + dev[7:10], [0.0]))
    x = make_state(d=(0, 0, dev[5]), v=(0, 0, dev[6]), w=w, f=f)
    x[IDX_Q] = quat_from_n(n)
    return x


def run_dev(dev):
    eq, f, *_ = setup()
    x0 = state_from_dev(eq, dev)
    if x0 is None:
        return None
    f.reset(x0[13:16])
    log = simulate(x0, f, P, T_RUN, dt=1e-3, ctrl_period=1e-3, alive_fn=ALIVE3, log_every=5)
    o = evaluate(log, eq)
    return dict(captured=o.captured, upright=o.min_nz > 0, alt_loss=o.alt_loss, min_nz=o.min_nz)


def main():
    apply_style()
    eq, f, ubar, box, x_on = setup()
    A, B, K = f.model.A, f.model.B, f.K
    names = f.model.states

    L = ["# E5 (preliminary): first LMI certificate, LTI model at the relaxed hover", "",
         "Closed loop x' = A x + B sat(−K x) on the 10-state model (7 states + 3 motor states). "
         "Hu–Lin saturation conditions with symmetric levels ū = min(f̄ − f_min, f_max − f̄) = "
         f"({ubar[0]:.2f}, {ubar[1]:.2f}, {ubar[2]:.2f}) N; motor-state deviations bounded by ū (physical range).", "",
         "| Required decay rate (1/s) | Status | Semi-axes Δp, Δq, Δr (rad/s) | Δn_x, Δn_y | Δz (m) | β to hover onset |",
         "|---|---|---|---|---|---|"]
    results = {}
    for decay in (0.0, 0.1, 0.3, 0.5):
        r = invariant_ellipsoid(A, B, K, ubar, decay=decay, box=box)
        rb = invariant_ellipsoid(A, B, K, ubar, decay=decay, box=box, direction=x_on)
        results[decay] = r
        sa = semi_axes(r["Q"])
        L.append(f"| {decay} | {r['status']} | {sa[0]:.2f}, {sa[1]:.2f}, {sa[2]:.2f} | {sa[3]:.2f}, {sa[4]:.2f} | "
                 f"{sa[5]:.2f} | {rb['beta']:.3f} |")
    L += ["", "β = largest scaling such that β·(hover-onset deviation) is inside the certified ellipsoid "
          "(β ≥ 1 would mean the hover-onset state is certified).", "",
          "Without the motor-state bound the LMI is ill-conditioned: the open-loop linear model is only "
          "marginally stable, so a near-zero contraction margin certifies an almost unbounded and physically "
          "meaningless set (|Δn_x| > 1, motor deviations > 100 N). The bound is required.", ""]

    # nonlinear: along the onset direction
    betas = np.round(np.arange(0.1, 1.01, 0.1), 2)
    with ProcessPoolExecutor(max_workers=8) as ex:
        along = list(ex.map(run_dev, [b * x_on for b in betas]))
    L += ["## Nonlinear check along the hover-onset direction (failure LQR, no detection delay)", "",
          "| β | captured | never inverted | altitude loss (m) |", "|---|---|---|---|"]
    for b, o in zip(betas, along):
        L.append(f"| {b:.1f} | {'yes' if o['captured'] else 'no'} | {'yes' if o['upright'] else 'no'} | {o['alt_loss']:.2f} |")
    ok = [b for b, o in zip(betas, along) if o["captured"] and o["upright"]]
    emp = 0.0
    for b, o in zip(betas, along):
        if o["captured"] and o["upright"]:
            emp = b
        else:
            break

    # 2-D slice (Δr, Δn_y)
    i_r, i_ny = names.index("r"), names.index("n_y")
    P_cert = results[DECAY]["P"]
    dr = np.linspace(-20, 20, 21)
    dny = np.linspace(-0.6, 0.6, 21)
    grid = []
    for a in dr:
        for b in dny:
            d = np.zeros(10)
            d[i_r], d[i_ny] = a, b
            grid.append(d)
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run_dev, grid, chunksize=4))
    ok_pts = np.array([[g[i_r], g[i_ny]] for g, o in zip(grid, res) if o and o["captured"] and o["upright"]])
    bad_pts = np.array([[g[i_r], g[i_ny]] for g, o in zip(grid, res) if o and not (o["captured"] and o["upright"])])
    frac_cert = np.mean([float(g @ P_cert @ g) <= 1 for g, o in zip(grid, res) if o and o["captured"] and o["upright"]])
    L += ["", f"Empirical: every β ≤ {emp:.1f} recovers without inversion along this direction "
          f"(certified β at decay {DECAY}: see table).", "",
          f"## 2-D slice (Δr, Δn_y), others at equilibrium; decay rate {DECAY}", "",
          f"Grid points recovered without inversion: {len(ok_pts)} / {len(ok_pts) + len(bad_pts)}. "
          f"Fraction of those inside the certified slice: {frac_cert:.0%} (the rest is the conservatism gap).", ""]
    (ROOT / "results/tables/e5_first_certificate.md").write_text("\n".join(L))
    print("\n".join(L))

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    if len(ok_pts):
        ax.scatter(ok_pts[:, 0], ok_pts[:, 1], s=16, color=SERIES[2], label="nonlinear sim: recovered", zorder=2)
    if len(bad_pts):
        ax.scatter(bad_pts[:, 0], bad_pts[:, 1], s=16, color=SERIES[1], marker="x",
                   label="nonlinear sim: inverted / not captured", zorder=2)
    E = slice_ellipse(P_cert, i_r, i_ny)
    ax.fill(E[0], E[1], color=SERIES[0], alpha=0.12, zorder=1)
    ax.plot(E[0], E[1], color=SERIES[0], lw=2, label="LMI certificate (LTI at r̄)", zorder=3)
    ax.scatter([x_on[i_r]], [x_on[i_ny]], s=70, color=REF, marker="*", zorder=4,
               label="hover onset (projection)")
    ax.axhline(0, color=REF, lw=0.6)
    ax.axvline(0, color=REF, lw=0.6)
    ax.set_xlabel("Δr = r − r̄  (rad/s)")
    ax.set_ylabel("Δn_y = n_y − n̄_y")
    ax.set_title("E5 · Certified set vs. nonlinear recovery (slice: Δr, Δn_y)")
    ax.legend(loc="upper left", fontsize=8, bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    save(fig, ROOT / "results/figures/e5_certificate_slice.png")


if __name__ == "__main__":
    main()
