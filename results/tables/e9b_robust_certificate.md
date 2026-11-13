# E9b: r-robust saturation-aware certificate for the published failure LQR (LPV model, nominal plant)

Closed loop e' = A(rho) e + B sat(-K e) + R(e) on the 10-state quasi-LPV model, rho = (r, n_z). Hu-Lin conditions at the 4 vertices x 8 saturation patterns with a common quadratic Lyapunov function, decay 0.1, scaled coordinates. The remainder R is handled a posteriori (shrinking factor kappa). Choices fixed in the docstring of `experiments/e9b_robust_certificate.py`. Certified here means: for the quasi-LPV model, remainder bounded numerically on the box, re-verified with numpy; the nonlinear check is the falsification section.

Hand-over direction d (exact hover, tau = 0, f_spin = 2.95 N): p +0.000, q -6.341, r -8.851, n_x -0.124, n_y -0.737, z +0.305, v_z +0.813, f1 +0.910, f2 -1.020, f3 +0.910.

## Certificate versus the size of the scheduling box (nu)

| nu | r range (rad/s) | n_z range | objective | solver status | kappa (remainder shrink) | final semi-axes p, q, r | n_x, n_y | z, v_z | beta to d (final) | beta ceiling: disc / box |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | [7.81, 29.81] | [0.20, 1] | log det | optimal_inaccurate | not verified | - | - | - | - | 0.948 / 1.000 |
| 1.0 | [7.81, 29.81] | [0.20, 1] | toward d | optimal_inaccurate | not verified | - | - | - | - | 0.948 / 1.000 |
| 0.8 | [10.01, 27.61] | [0.36, 1] | log det | optimal_inaccurate | 0.0002 | 0.02, 0.03, 0.05 | 0.003, 0.003 | 0.01, 0.01 | 0.0022 | 0.885 / 0.800 |
| 0.8 | [10.01, 27.61] | [0.36, 1] | toward d | optimal | none passes | - | - | - | - | 0.885 / 0.800 |
| 0.6 | [12.21, 25.41] | [0.52, 1] | log det | optimal_inaccurate | 0.0005 | 0.02, 0.04, 0.08 | 0.004, 0.004 | 0.02, 0.03 | 0.0029 | 0.780 / 0.600 |
| 0.6 | [12.21, 25.41] | [0.52, 1] | toward d | optimal_inaccurate | none passes | - | - | - | - | 0.780 / 0.600 |
| 0.4 | [14.41, 23.21] | [0.68, 1] | log det | optimal_inaccurate | 0.001 | 0.02, 0.04, 0.08 | 0.005, 0.004 | 0.03, 0.04 | 0.0029 | 0.618 / 0.400 |
| 0.4 | [14.41, 23.21] | [0.68, 1] | toward d | optimal_inaccurate | 0.0001 | 0.01, 0.01, 0.02 | 0.001, 0.001 | 0.00, 0.01 | 0.0012 | 0.618 / 0.400 |
| 0.25 | [16.06, 21.56] | [0.80, 1] | log det | optimal_inaccurate | 0.002 | 0.02, 0.04, 0.08 | 0.005, 0.004 | 0.03, 0.04 | 0.0027 | 0.439 / 0.250 |
| 0.25 | [16.06, 21.56] | [0.80, 1] | toward d | optimal_inaccurate | 0.0001 | 0.00, 0.01, 0.02 | 0.001, 0.001 | 0.00, 0.00 | 0.0008 | 0.439 / 0.250 |
| 0.15 | [17.16, 20.46] | [0.88, 1] | log det | optimal_inaccurate | 0.007 | 0.03, 0.04, 0.09 | 0.006, 0.005 | 0.04, 0.05 | 0.0032 | 0.271 / 0.150 |
| 0.15 | [17.16, 20.46] | [0.88, 1] | toward d | optimal_inaccurate | 0.0002 | 0.00, 0.01, 0.01 | 0.001, 0.001 | 0.00, 0.00 | 0.0007 | 0.271 / 0.150 |

E5 (LTI at the relaxed hover, same decay): semi-axes p, q, r = 2.17, 3.49, 6.09; n_x, n_y = 0.413, 0.353; z, v_z = 2.99, 3.88; beta to d = 0.2321. The E5 ellipsoid used the saturation level (not the physical range) as motor-state box and no box on z, v_z.

## Verification (section 1.4 of the plan), scaled units

Worst (largest) eigenvalue of any dynamics block over the 4 vertices x 8 saturation patterns and the 15 x 15 grid x 8 patterns (must be below -1e-6), the smallest eigenvalue of the linear-region blocks (PSD, accepted down to -1e-8) and of Q, and the remainder measure g_P of the final kappa (guaranteed decay 2 (0.1 - g_P) when g_P < 0.1).

| nu | objective | solver used | worst eig of dynamics blocks | linear-region min eig | min eig Q | passes | g_P at final kappa |
|---|---|---|---|---|---|---|---|
| 1.0 | log det | Clarabel | 1.16e-02 | 5.4e-06 | 3.4e-03 | NO | - |
| 1.0 | toward d | Clarabel | 3.85e-02 | 7.9e-05 | 5.2e-03 | NO | - |
| 0.8 | log det | Clarabel | -1.00e-05 | 1.2e-09 | 1.5e-02 | yes | 0.0433 |
| 0.8 | toward d | Clarabel | -1.00e-05 | -4.5e-11 | 3.4e-03 | yes | - |
| 0.6 | log det | Clarabel | -1.00e-05 | 3.6e-03 | 1.9e-02 | yes | 0.0493 |
| 0.6 | toward d | Clarabel | -9.99e-06 | 3.3e-04 | 2.1e-03 | yes | - |
| 0.4 | log det | Clarabel | -1.00e-05 | 2.0e-02 | 2.0e-02 | yes | 0.0460 |
| 0.4 | toward d | Clarabel | -9.97e-06 | 1.0e-03 | 1.8e-03 | yes | 0.0489 |
| 0.25 | log det | Clarabel | -1.00e-05 | 2.1e-02 | 2.1e-02 | yes | 0.0414 |
| 0.25 | toward d | Clarabel | -9.92e-06 | 1.9e-04 | 7.5e-04 | yes | 0.0372 |
| 0.15 | log det | Clarabel | -1.00e-05 | 2.1e-02 | 2.1e-02 | yes | 0.0475 |
| 0.15 | toward d | Clarabel | -9.96e-06 | 8.5e-05 | 5.7e-04 | yes | 0.0416 |

## Second-solver cross-check (objective: extent toward d, nu = 0.6, before shrinking)

Clarabel: beta = 0.162143 (optimal_inaccurate); SCS: beta = 0.162329 (optimal_inaccurate); relative difference 1.14e-03.

## Falsification in the nonlinear nominal plant (log det certificate after shrinking)

Samples on the boundary (V = 0.999999) and in the interior; initial state in capture coordinates; FailureLQR, 8 s. A failure is: not captured, V above 1.001 at some time, or n_z <= 0.

| nu | kappa | set | samples | not captured | left the set (V > 1.001) | inverted | max V |
|---|---|---|---|---|---|---|---|
| 0.15 | 0.007 | boundary | 500 | 0 | 0 | 0 | 1.000 |
| 0.15 | 0.007 | interior | 500 | 0 | 0 | 0 | 1.000 |
| 0.6 | 0.0005 | boundary | 500 | 0 | 0 | 0 | 1.000 |
| 0.6 | 0.0005 | interior | 500 | 0 | 0 | 0 | 1.000 |

## Hand-over states of E9a against the largest-volume robust certificate

Largest log-volume certificate: nu = 0.15. Hand-over states: 1312; inside (alpha >= 1): 0; largest alpha 0.0048; median alpha 0.0019. E5 for comparison: largest alpha 0.353.
