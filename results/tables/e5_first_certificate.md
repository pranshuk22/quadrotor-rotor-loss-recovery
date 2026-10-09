# E5 (preliminary): first LMI certificate, LTI model at the relaxed hover

Closed loop x' = A x + B sat(−K x) on the 10-state model (7 states + 3 motor states). Hu–Lin saturation conditions with symmetric levels ū = min(f̄ − f_min, f_max − f̄) = (1.76, 0.82, 1.76) N; motor-state deviations bounded by ū (physical range).

| Required decay rate (1/s) | Status | Semi-axes Δp, Δq, Δr (rad/s) | Δn_x, Δn_y | Δz (m) | β to hover onset |
|---|---|---|---|---|---|
| 0.0 | optimal_inaccurate | 2.23, 3.49, 6.20 | 0.42, 0.36 | 3.17 | 0.223 |
| 0.1 | optimal | 2.17, 3.49, 6.09 | 0.41, 0.35 | 2.99 | 0.221 |
| 0.3 | optimal | 2.07, 3.50, 5.89 | 0.40, 0.34 | 2.61 | 0.218 |
| 0.5 | optimal | 1.96, 3.52, 5.76 | 0.38, 0.32 | 2.17 | 0.215 |

β = largest scaling such that β·(hover-onset deviation) is inside the certified ellipsoid (β ≥ 1 would mean the hover-onset state is certified).

Without the motor-state bound the LMI is ill-conditioned: the open-loop linear model is only marginally stable, so a near-zero contraction margin certifies an almost unbounded and physically meaningless set (|Δn_x| > 1, motor deviations > 100 N). The bound is required.

## Nonlinear check along the hover-onset direction (failure LQR, no detection delay)

| β | captured | never inverted | altitude loss (m) |
|---|---|---|---|
| 0.1 | yes | yes | 0.01 |
| 0.2 | yes | yes | 0.01 |
| 0.3 | yes | yes | 0.02 |
| 0.4 | yes | yes | 0.04 |
| 0.5 | yes | yes | 0.08 |
| 0.6 | yes | yes | 0.18 |
| 0.7 | yes | yes | 0.42 |
| 0.8 | yes | no | 1.34 |
| 0.9 | yes | no | 5.77 |
| 1.0 | no | no | 14.90 |

Empirical: every β ≤ 0.7 recovers without inversion along this direction (certified β at decay 0.1: see table).

## 2-D slice (Δr, Δn_y), others at equilibrium; decay rate 0.1

Grid points recovered without inversion: 376 / 441. Fraction of those inside the certified slice: 7% (the rest is the conservatism gap).
