# E8d: Residual trained on spin-up and capture transients

Training: 40 near-trim episodes (E6 data) and 40 capture-transient episodes (0 discarded; 32000 samples at 5 ms, recorded from the hand-over on). Test: 10 near-trim episodes (seed 12) and 10 transient episodes (seed 32, 0 discarded), all on family A. Settings fixed in the docstring of `experiments/e8d_spinup_residual.py`.

Hand-over states of the transient data (median over episodes): |n_xy deviation| = 1.11, |rate deviation| = 11.5 rad/s.

## Multi-step prediction error on held-out near-trim episodes (normalised RMSE)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms |
|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.159 | 0.648 | 1.609 | 3.220 | 5.831 | 4.417 | 7.158 | 8.159 |
| Near-trim only (E6) | 0.012 | 0.070 | 0.082 | 0.116 | 0.164 | 0.271 | 0.570 | 2.547 |
| Transients only | 0.026 | 0.080 | 0.195 | 0.326 | 0.397 | 0.422 | 0.525 | 0.868 |
| Near-trim + transients | 0.018 | 0.049 | 0.123 | 0.214 | 0.258 | 0.302 | 0.411 | 0.713 |
| Near-trim + transients, row-normalised | 0.025 | 0.059 | 0.117 | 0.200 | 0.253 | 0.375 | 0.733 | 2.845 |

## Multi-step prediction error on held-out transient episodes (normalised RMSE)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms |
|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.574 | 2.311 | 5.561 | 10.040 | 16.171 | 20.572 | 22.760 | 30.103 |
| Near-trim only (E6) | 0.487 | 1.951 | 4.649 | 8.196 | 13.175 | 19.874 | 22.717 | 32.345 |
| Transients only | 0.039 | 0.163 | 0.348 | 0.571 | 0.817 | 1.088 | 1.639 | 2.866 |
| Near-trim + transients | 0.058 | 0.249 | 0.447 | 0.671 | 0.975 | 1.301 | 1.902 | 3.111 |
| Near-trim + transients, row-normalised | 0.075 | 0.279 | 0.518 | 0.780 | 1.146 | 1.523 | 2.308 | 4.615 |

## Capture after a detection delay (family A, exact hover, spin-up 2.95 N): alt. loss (m) / min n_z / SAFE

| tau (ms) | LQR | MPC, analytical | MPC, Near-trim only (E6) | MPC, Near-trim + transients | MPC, Near-trim + transients, row-normalised |
|---|---|---|---|---|---|
| 0 | 0.40 / 0.26 / yes | 0.53 / 0.25 / yes | 0.58 / 0.20 / yes | 1.97 / -0.27 / no | 1.61 / -0.21 / no |
| 10 | 1.69 / 0.04 / yes | 2.52 / -0.05 / no | 2.80 / -0.06 / no | 12.09 / -0.67 / no | 8.65 / -0.57 / no |
| 20 | 6.56 / -0.08 / no | 8.53 / -0.29 / no | 7.94 / -0.25 / no | 34.98 / -0.86 / no | 25.94 / -0.78 / no |
| 30 | 12.62 / -0.10 / no | 19.19 / -0.46 / no | 19.51 / -0.43 / no | 195.64 / -0.93 / no | 80.46 / -0.87 / no |
| 40 | 22.81 / -0.16 / no | 38.55 / -0.61 / no | 38.82 / -0.59 / no | 417.04 / -0.98 / no | 295.26 / -0.94 / no |
| 60 | 68.00 / -0.39 / no | 339.10 / -0.80 / no | 308.83 / -0.80 / no | 713.74 / -1.00 / no | 614.14 / -0.99 / no |
