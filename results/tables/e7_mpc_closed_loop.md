# E7: Closed-loop comparison on mismatched plants

All controllers are designed on the nominal parameters. MPC: horizon 20 × 5 ms, DARE terminal cost, thrust limits, OSQP through CVXPY. The residual (trained on family A, as in E6) is evaluated outside the QP and held constant over the horizon (measured disturbance), so the QP stays convex.

## Part 1: steady altitude bias by mismatch effect

One start per plant (1 m below the set-point, 8 s); the steady error is the mean altitude over the last 2 s. The steady state does not depend on the start.

| Plant | LQR | MPC, analytical | MPC, residual Koopman | Residual MPC vs LQR |
|---|---|---|---|---|
| A (full) | -0.285 m | -0.286 m | -0.193 m | -32% in magnitude |
| A without thrust loss | -0.154 m | -0.154 m | -0.066 m | -57% in magnitude |
| nominal + A's thrust loss only | -0.100 m | -0.101 m | -0.033 m | -67% in magnitude |
| B (full, held out) | -0.029 m | -0.033 m | +0.022 m | -25% in magnitude |
| B without thrust loss | +0.112 m | +0.111 m | +0.164 m | +47% in magnitude |
| nominal + B's thrust loss only | -0.174 m | -0.177 m | -0.107 m | -39% in magnitude |

Median time per MPC step: 4.4 ms wall clock through CVXPY, 0.73 ms inside OSQP. The sample period is 5 ms, so the CVXPY wrapper leaves no real-time margin; the solver itself does.

## Part 2: capture after a detection delay (family A, exact hover start)

Hover, rotor 4 fails, healthy LQR for τ, spin-up on rotors 1 and 3 at 2.95 N, then the capture controller. Criterion: `rotorfail/metrics.py` (captured, altitude loss < 2 m, never inverted). Capture is measured against each controller's own closed-loop steady state on family A, because a controller designed on the nominal model does not settle at the plant's open-loop relaxed hover.

| τ (ms) | LQR: alt. loss (m) / min n_z / SAFE | MPC, analytical: alt. loss (m) / min n_z / SAFE | MPC, residual Koopman: alt. loss (m) / min n_z / SAFE |
|---|---|---|---|
| 0 | 0.40 / 0.26 / yes | 0.53 / 0.25 / yes | 0.58 / 0.20 / yes |
| 10 | 1.69 / 0.04 / yes | 2.52 / -0.05 / no | 2.80 / -0.06 / no |
| 20 | 6.56 / -0.08 / no | 8.53 / -0.29 / no | 7.94 / -0.25 / no |
| 30 | 12.62 / -0.10 / no | 19.19 / -0.46 / no | 19.51 / -0.43 / no |
| 40 | 22.81 / -0.16 / no | 38.55 / -0.61 / no | 38.82 / -0.59 / no |
| 60 | 68.00 / -0.39 / no | 339.10 / -0.80 / no | 308.83 / -0.80 / no |
