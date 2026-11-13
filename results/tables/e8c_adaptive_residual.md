# E8c: Online residual adaptation by recursive least squares

RLS on the 91 x 7 weights of the offline residual (trained on family A as in E6), shared covariance, P0 = I, forgetting 0.995 (main) or 0.999, covariance rescaled when trace(P) > 10 trace(P0). Settings fixed in the docstring of `experiments/e8c_adaptive_residual.py`.

## (a) Multi-step prediction error (normalised RMSE, mean over the 7 states), adaptation running along each episode

### Test episodes of family A (training family)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.158 | 0.655 | 1.606 | 3.181 | 5.755 | 4.365 | 7.080 | 8.000 | 14.009 |
| Offline residual | 0.015 | 0.090 | 0.103 | 0.142 | 0.196 | 0.302 | 0.604 | 2.615 | 6.250 |
| Adaptive (0.995) | 0.014 | 0.089 | 0.121 | 0.243 | 0.501 | 1.299 | 3.657 | 7.232 | 11.614 |
| Adaptive (0.999) | 0.014 | 0.089 | 0.120 | 0.239 | 0.494 | 1.250 | 3.123 | 6.468 | 11.182 |
| Adaptive (0.995, clip x2) | 0.015 | 0.044 | 0.102 | 0.263 | 0.527 | 1.759 | 4.888 | 11.573 | 19.652 |

### Test episodes of family B (held out)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.220 | 0.876 | 2.160 | 4.286 | 7.542 | 5.128 | 7.884 | 6.892 | 10.239 |
| Offline residual | 0.309 | 1.221 | 2.964 | 5.934 | 12.073 | 17.566 | 19.729 | 24.110 | 30.379 |
| Adaptive (0.995) | 0.168 | 0.658 | 1.461 | 2.775 | 5.572 | 8.423 | 9.334 | 12.797 | 16.960 |
| Adaptive (0.999) | 0.168 | 0.658 | 1.461 | 2.777 | 5.576 | 8.382 | 9.361 | 12.922 | 16.838 |
| Adaptive (0.995, clip x2) | 0.173 | 0.685 | 1.485 | 2.790 | 5.787 | 13.561 | 13.954 | 25.313 | 29.108 |

## (b) Closed loop, steady altitude bias (E7 Part 1 protocol, mean altitude over the last 2 s)

| Plant | LQR | MPC, analytical | MPC, offline residual | MPC, adaptive (0.995) | MPC, adaptive (0.999) | MPC, adaptive (0.995, clip x2) |
|---|---|---|---|---|---|---|
| A (full) | -0.285 m | -0.286 m | -0.193 m | -0.194 m | -0.194 m | -0.194 m |
| A without thrust loss | -0.154 m | -0.154 m | -0.066 m | -0.112 m | -0.112 m | -0.112 m |
| nominal + A's thrust loss only | -0.100 m | -0.101 m | -0.033 m | -0.061 m | -0.061 m | -0.061 m |
| B (full, held out) | -0.029 m | -0.033 m | +0.022 m | +0.000 m | +0.000 m | +0.000 m |
| B without thrust loss | +0.112 m | +0.111 m | +0.164 m | +0.084 m | +0.084 m | +0.084 m |
| nominal + B's thrust loss only | -0.174 m | -0.177 m | -0.107 m | -0.112 m | -0.112 m | -0.107 m |

Adaptation statistics (run on plant A full / B without thrust loss): fraction of calls with an active clip, maximum trace(P), rescalings, positive-definiteness violations.

| Controller | plant | clip active | max trace(P) | rescalings | PD violations | median CVXPY ms |
|---|---|---|---|---|---|---|
| MPC, adaptive (0.995) | A (full) | 0.019 | 910.0 | 1073 | 0 | 5.2 |
| MPC, adaptive (0.995) | B without thrust loss | 0.007 | 910.0 | 1085 | 0 | 6.7 |
| MPC, adaptive (0.999) | A (full) | 0.019 | 320.4 | 0 | 0 | 5.2 |
| MPC, adaptive (0.999) | B without thrust loss | 0.007 | 339.0 | 0 | 0 | 6.8 |
| MPC, adaptive (0.995, clip x2) | A (full) | 0.000 | 910.0 | 1072 | 0 | 5.8 |
| MPC, adaptive (0.995, clip x2) | B without thrust loss | 0.001 | 910.0 | 1086 | 0 | 6.2 |

## (c) Adaptive residual combined with offset-free MPC (state disturbance model)

| Plant | Offset-free (state d) | Offset-free + offline residual | Offset-free + adaptive (0.995) |
|---|---|---|---|
| A (full) | -0.000 m | -0.000 m | -0.000 m |
| A without thrust loss | -0.000 m | -0.000 m | -0.000 m |
| nominal + A's thrust loss only | -0.000 m | -0.000 m | -0.000 m |
| B (full, held out) | -0.000 m | -0.000 m | -0.000 m |
| B without thrust loss | -0.000 m | -0.000 m | -0.000 m |
| nominal + B's thrust loss only | -0.000 m | -0.000 m | -0.000 m |

## (d) Capture after a detection delay (exact hover start, spin-up 2.95 N)

Alt. loss (m) / min n_z / SAFE; each controller judged against its own steady state on the plant.

### Plant: A (full)

| tau (ms) | LQR | MPC, offline residual | MPC, adaptive (0.995) |
|---|---|---|---|
| 0 | 0.40 / 0.26 / yes | 0.58 / 0.20 / yes | 0.48 / 0.24 / yes |
| 10 | 1.69 / 0.04 / yes | 2.80 / -0.06 / no | 1.97 / 0.01 / yes |
| 20 | 6.56 / -0.08 / no | 7.94 / -0.25 / no | 6.36 / -0.20 / no |
| 30 | 12.62 / -0.10 / no | 19.51 / -0.43 / no | 15.32 / -0.38 / no |
| 40 | 22.81 / -0.16 / no | 38.82 / -0.59 / no | 28.64 / -0.53 / no |
| 60 | 68.00 / -0.39 / no | 308.83 / -0.80 / no | 208.52 / -0.74 / no |

### Plant: nominal

| tau (ms) | LQR | MPC, offline residual | MPC, adaptive (0.995) |
|---|---|---|---|
| 0 | 0.03 / 0.47 / yes | 0.00 / 0.43 / yes | 0.02 / 0.48 / yes |
| 10 | 0.40 / 0.21 / yes | 0.73 / 0.13 / yes | 0.52 / 0.19 / yes |
| 20 | 1.96 / 0.02 / yes | 3.31 / -0.12 / no | 2.51 / -0.09 / no |
| 30 | 5.30 / -0.02 / no | 9.16 / -0.30 / no | 6.81 / -0.28 / no |
| 40 | 10.00 / -0.08 / no | 21.64 / -0.47 / no | 14.98 / -0.44 / no |
| 60 | 23.88 / -0.29 / no | 141.58 / -0.69 / no | 70.79 / -0.66 / no |
