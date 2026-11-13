# E8a diagnostic: state-model offset-free MPC as capture controller, tau = 0

A single diagnostic run (nominal plant, exact hover start, spin-up 2.95 N, tau = 0 ms, 10 s), with the pre-registered settings of E8a; no parameter was changed. See the docstring of `experiments/e8a_diag_state_capture.py`. Not a statistical result.

- Hand-over to the controller at t = 0.650 s; at the hand-over r - r_bar = -8.81 rad/s, n_z = 0.88.
- First n_z < 0 at t = 0.865 s (0.215 s after the hand-over).
- Share of controller samples before that time with an exact target: 1.000 (0 of 43 inexact).
- Total samples after the hand-over: 1871; exact targets overall: 0.983.

## Disturbance estimate by component

d_hat is an offset per state and step, in the unit of the state. Share = peak |d_hat_i| before the first n_z < 0 divided by the largest one-step change of the measured state i over the same interval.

| Component | unit | peak abs. d_hat (whole run) | peak abs. d_hat (before first n_z < 0) | time of that peak (s) | largest one-step change | share | dominant |
|---|---|---|---|---|---|---|---|
| p | rad/s | 0.4090 | 0.0813 | 0.685 | 0.3071 | 0.26 | no |
| q | rad/s | 0.1879 | 0.1341 | 0.860 | 0.6798 | 0.20 | no |
| r | rad/s | 0.0000 | 0.0000 | 0.675 | 0.0614 | 0.00 | no |
| n_x | - | 0.0498 | 0.0235 | 0.725 | 0.0500 | 0.47 | no |
| n_y | - | 0.0360 | 0.0360 | 0.850 | 0.0491 | 0.73 | yes |
| z | m | 0.0001 | 0.0001 | 0.860 | 0.0041 | 0.02 | no |
| v_z | m/s | 0.0561 | 0.0275 | 0.860 | 0.0466 | 0.59 | yes |

Dominant components before the first n_z < 0: n_y, v_z.

## Time series

u_s is the target input as a deviation from the relaxed-hover thrusts (N); the command column is the controller's output as absolute thrusts of rotors 1 to 3 (N; limits 0.2 and 3.8 N).

| t (s) | n_z | r - r_bar (rad/s) | exact target | d_hat (p, q, r, n_x, n_y, z, v_z) | u_s (N, deviation) | command (N, absolute) |
|---|---|---|---|---|---|---|
| 0.650 | 0.88 | -8.81 | yes | +0.000, +0.000, +0.000, +0.000, +0.000, +0.000, +0.000 | +0.00, +0.00, +0.00 | +0.20, +0.20, +3.80 |
| 0.675 | 0.88 | -8.59 | yes | -0.078, -0.004, -0.000, +0.014, -0.004, -0.000, -0.006 | +0.09, +0.53, -0.03 | +0.26, +1.90, +2.54 |
| 0.700 | 0.86 | -8.56 | yes | -0.073, -0.014, -0.000, +0.021, -0.009, -0.000, -0.009 | +0.21, +0.74, -0.05 | +1.11, +1.23, +1.63 |
| 0.725 | 0.81 | -8.57 | yes | -0.046, -0.033, -0.000, +0.023, -0.015, -0.000, -0.010 | +0.34, +0.78, -0.08 | +1.50, +0.84, +1.38 |
| 0.750 | 0.72 | -8.54 | yes | -0.021, -0.054, +0.000, +0.022, -0.021, -0.000, -0.010 | +0.48, +0.74, -0.11 | +1.76, +0.75, +1.36 |
| 0.775 | 0.59 | -8.50 | yes | -0.002, -0.073, +0.000, +0.017, -0.027, -0.000, -0.011 | +0.65, +0.67, -0.12 | +1.97, +0.74, +1.50 |
| 0.800 | 0.43 | -8.42 | yes | +0.009, -0.090, +0.000, +0.011, -0.032, -0.000, -0.013 | +0.84, +0.62, -0.07 | +2.19, +0.72, +1.81 |
| 0.825 | 0.26 | -8.30 | yes | +0.014, -0.107, +0.000, +0.006, -0.035, -0.000, -0.017 | +1.06, +0.63, +0.09 | +2.45, +0.69, +2.34 |
| 0.850 | 0.09 | -8.13 | yes | +0.020, -0.126, +0.000, +0.001, -0.036, -0.000, -0.024 | +1.34, +0.75, +0.39 | +2.79, +0.70, +3.15 |
| 0.875 | -0.07 | -7.87 | yes | +0.030, -0.147, +0.000, -0.000, -0.035, -0.000, -0.035 | +1.72, +1.06, +0.88 | +3.06, +0.85, +3.80 |
| 0.900 | -0.20 | -7.57 | no | +0.053, -0.168, +0.000, +0.003, -0.033, -0.000, -0.047 | +1.76, +1.52, +1.69 | +1.70, +0.20, +3.80 |
| 0.925 | -0.23 | -7.34 | no | +0.091, -0.169, +0.000, +0.015, -0.028, -0.000, -0.052 | +1.76, +2.47, +1.76 | +0.20, +2.59, +3.80 |
| 0.950 | -0.10 | -7.27 | no | +0.140, -0.153, +0.000, +0.033, -0.021, -0.000, -0.055 | +1.76, +2.59, +1.76 | +0.20, +3.80, +3.80 |
| 0.975 | 0.17 | -7.22 | no | +0.185, -0.143, +0.000, +0.045, -0.012, -0.000, -0.056 | +1.76, +2.53, +1.76 | +2.31, +2.64, +3.80 |
| 1.000 | 0.53 | -7.07 | no | +0.251, -0.152, +0.000, +0.050, -0.003, -0.000, -0.054 | +1.75, +2.15, +1.76 | +3.80, +0.91, +3.80 |
| 1.025 | 0.85 | -6.78 | no | +0.334, -0.177, +0.000, +0.043, +0.004, -0.000, -0.042 | +1.12, +1.50, +1.76 | +3.80, +0.20, +2.31 |
| 1.050 | 0.99 | -6.46 | yes | +0.393, -0.188, +0.000, +0.030, +0.006, -0.000, -0.027 | +0.55, +0.71, +1.55 | +3.80, +0.20, +2.22 |
