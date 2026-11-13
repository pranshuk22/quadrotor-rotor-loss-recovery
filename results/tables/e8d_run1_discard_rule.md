> Run 1 of `experiments/e8d_spinup_residual.py` (commit 3408475). Kept for the record: the pre-registered discard rule (tilt deviation above 0.9) removed 32 of 40 training and 7 of 10 test transient episodes, because genuine hand-over states already have a median tilt deviation of 0.87; the rule was replaced by a divergence rule (non-finite, or body rate above 60 rad/s) in a later commit and the experiment re-run.

# E8d: Residual trained on spin-up and capture transients

Training: 40 near-trim episodes (E6 data) and 8 capture-transient episodes (32 discarded; 6400 samples at 5 ms, recorded from the hand-over on). Test: 10 near-trim episodes (seed 12) and 3 transient episodes (seed 32, 7 discarded), all on family A. Settings fixed in the docstring of `experiments/e8d_spinup_residual.py`.

Hand-over states of the transient data (median over episodes): |n_xy deviation| = 0.87, |rate deviation| = 11.0 rad/s.

## Multi-step prediction error on held-out near-trim episodes (normalised RMSE)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms |
|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.159 | 0.648 | 1.609 | 3.220 | 5.831 | 4.417 | 7.158 | 8.159 |
| Near-trim only (E6) | 0.012 | 0.070 | 0.082 | 0.116 | 0.164 | 0.271 | 0.570 | 2.547 |
| Transients only | 0.024 | 0.097 | 0.213 | 0.320 | 0.380 | 0.585 | 0.868 | 2.153 |
| Near-trim + transients | 0.013 | 0.033 | 0.091 | 0.173 | 0.204 | 0.290 | 0.545 | 2.045 |
| Near-trim + transients, row-normalised | 0.026 | 0.049 | 0.119 | 0.220 | 0.278 | 0.375 | 0.642 | 2.224 |

## Multi-step prediction error on held-out transient episodes (normalised RMSE)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms |
|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.426 | 1.712 | 4.053 | 7.372 | 12.267 | 13.549 | 15.843 | 15.213 |
| Near-trim only (E6) | 0.340 | 1.343 | 3.080 | 5.338 | 8.970 | 12.038 | 11.031 | 15.808 |
| Transients only | 0.036 | 0.139 | 0.186 | 0.277 | 0.377 | 0.607 | 0.876 | 1.481 |
| Near-trim + transients | 0.140 | 0.544 | 1.016 | 1.540 | 2.166 | 2.278 | 2.181 | 7.236 |
| Near-trim + transients, row-normalised | 0.168 | 0.570 | 1.118 | 1.686 | 2.292 | 4.016 | 4.116 | 11.161 |

## Capture after a detection delay (family A, exact hover, spin-up 2.95 N): alt. loss (m) / min n_z / SAFE

| tau (ms) | LQR | MPC, analytical | MPC, Near-trim only (E6) | MPC, Near-trim + transients | MPC, Near-trim + transients, row-normalised |
|---|---|---|---|---|---|
| 0 | 0.40 / 0.26 / yes | 0.53 / 0.25 / yes | 0.58 / 0.20 / yes | 1.24 / -0.11 / no | 1.07 / -0.04 / no |
| 10 | 1.69 / 0.04 / yes | 2.52 / -0.05 / no | 2.80 / -0.06 / no | 5.24 / -0.34 / no | 4.57 / -0.31 / no |
| 20 | 6.56 / -0.08 / no | 8.53 / -0.29 / no | 7.94 / -0.25 / no | 14.42 / -0.48 / no | 11.46 / -0.48 / no |
| 30 | 12.62 / -0.10 / no | 19.19 / -0.46 / no | 19.51 / -0.43 / no | 32.10 / -0.65 / no | 26.67 / -0.65 / no |
| 40 | 22.81 / -0.16 / no | 38.55 / -0.61 / no | 38.82 / -0.59 / no | 102.94 / -0.77 / no | 46.92 / -0.75 / no |
| 60 | 68.00 / -0.39 / no | 339.10 / -0.80 / no | 308.83 / -0.80 / no | 442.95 / -0.90 / no | 275.96 / -0.89 / no |
