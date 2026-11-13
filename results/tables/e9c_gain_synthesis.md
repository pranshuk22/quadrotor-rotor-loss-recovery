# E9c: capture-gain synthesis and later hand-over (redesigned capture)

The published strategy (FailureLQR, hand-over at |w| > 10 rad/s) is the reference in every table; the synthesised gains and the later thresholds are labelled **redesigned capture**. Choices fixed in the docstring of `experiments/e9c_gain_synthesis.py`. 'Certified' is used only for the LPV-model certificates that pass the numerical verification (quasi-LPV model, remainder estimated numerically, nonlinear falsification below).

## Hand-over state versus the threshold w_sw (exact hover, tau = 0, 2.95 N)

| w_sw (rad/s) | t_h (s) | Delta p, q, r (rad/s) | Delta n_x, n_y | Delta z, v_z | Delta f1, f2, f3 (N) | abs(Dn) | beta ceiling: disc / box |
|---|---|---|---|---|---|---|---|
| 18 | 1.367 | +0.35, -4.46, -0.83 | +0.374, -0.062 | +1.14, +1.51 | +0.91, -1.02, +0.91 | 0.38 | 2.052 / 1.078 |
| 16 | 1.161 | +0.97, -5.37, -2.83 | -0.231, -0.572 | +0.85, +1.30 | +0.91, -1.02, +0.91 | 0.62 | 0.982 / 1.078 |
| 14 | 0.975 | +0.66, -6.08, -4.83 | +0.389, -0.128 | +0.62, +1.14 | +0.91, -1.02, +0.91 | 0.41 | 1.806 / 1.078 |
| 12 | 0.804 | +0.23, -6.31, -6.84 | -0.355, -0.164 | +0.44, +0.94 | +0.91, -1.02, +0.91 | 0.39 | 1.825 / 1.078 |
| 10 | 0.647 | +0.00, -6.34, -8.85 | -0.124, -0.737 | +0.30, +0.81 | +0.91, -1.02, +0.91 | 0.75 | 0.796 / 1.078 |
| 8 | 0.501 | -0.01, -6.34, -10.87 | +0.318, -0.580 | +0.19, +0.73 | +0.91, -1.02, +0.91 | 0.66 | 0.931 / 1.078 |
| 6 | 0.365 | +0.17, -6.33, -12.88 | +0.330, -0.254 | +0.10, +0.58 | +0.91, -1.02, +0.91 | 0.42 | 1.612 / 1.078 |
| 4 | 0.236 | +0.50, -6.20, -14.93 | +0.157, -0.134 | +0.04, +0.38 | +0.91, -1.02, +0.91 | 0.21 | 3.217 / 1.078 |
| 3 | 0.174 | +0.69, -6.06, -15.96 | +0.081, -0.145 | +0.02, +0.27 | +0.91, -1.02, +0.91 | 0.17 | 3.710 / 1.078 |

## Certified extent toward the hand-over state (beta >= 1 means contained)

beta_LPV: remainder-free LPV certificate; kappa, g_P: remainder shrink (g_P <= 0.05); beta_final = beta_LPV sqrt(kappa). 'pole' is the largest closed-loop eigenvalue magnitude (rad/s); rho(1 ms), rho(5 ms) the worst spectral radius of the sampled frozen-parameter loop. Status 'infeasible' marks the infeasibility boundary.

| w_sw | gain | solver status | verified | beta_LPV | kappa | g_P | beta_final | pole | rho(1 ms) | rho(5 ms) | accepted |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 18 | published LQR gain | optimal | yes | 0.1270 | - | - | - | 70.6 | 0.9990 | 0.9950 | no |
| 18 | synthesised, g = 2 | optimal_inaccurate | yes | 0.3750 | - | - | - | 5220.0 | 4.0931 | 22.2089 | no |
| 18 | synthesised, g = 4 | optimal_inaccurate | yes | 0.3750 | - | - | - | 11411.1 | 10.1312 | 49.6686 | no |
| 18 | synthesised, g = 8 | optimal_inaccurate | yes | 0.3750 | - | - | - | 23632.2 | 22.0451 | 103.7531 | no |
| 18 | synthesised, g = 16 | optimal_inaccurate | yes | 0.3750 | - | - | - | 47662.7 | 45.4694 | 210.0498 | no |
| 16 | published LQR gain | optimal_inaccurate | yes | 0.3094 | - | - | - | 71.7 | 0.9990 | 0.9950 | no |
| 16 | synthesised, g = 2 | optimal_inaccurate | yes | 0.4617 | - | - | - | 524.2 | 0.9994 | 1.2647 | no |
| 16 | synthesised, g = 4 | optimal | yes | 0.4617 | - | - | - | 582.3 | 0.9994 | 1.5159 | no |
| 16 | synthesised, g = 8 | optimal_inaccurate | yes | 0.4617 | - | - | - | 676.1 | 0.9994 | 1.9208 | no |
| 16 | synthesised, g = 16 | optimal_inaccurate | yes | 0.4617 | - | - | - | 1037.0 | 0.9994 | 3.4759 | no |
| 14 | published LQR gain | optimal | yes | 0.2653 | - | - | - | 72.4 | 0.9990 | 0.9950 | no |
| 14 | synthesised, g = 2 | optimal_inaccurate | yes | 0.3464 | - | - | - | 765.3 | 0.9993 | 2.4794 | no |
| 14 | synthesised, g = 4 | optimal_inaccurate | yes | 0.3464 | - | - | - | 1666.3 | 0.9993 | 6.5574 | no |
| 14 | synthesised, g = 8 | optimal_inaccurate | yes | 0.3464 | - | - | - | 2739.4 | 1.6816 | 11.3856 | no |
| 14 | synthesised, g = 16 | optimal_inaccurate | yes | 0.3464 | - | - | - | 3556.7 | 2.4811 | 15.0649 | no |
| 12 | published LQR gain | optimal_inaccurate | yes | 0.3163 | - | - | - | 72.9 | 0.9990 | 0.9951 | no |
| 12 | synthesised, g = 2 | optimal_inaccurate | yes | 0.4288 | - | - | - | 364.0 | 0.9991 | 0.9954 | no |
| 12 | synthesised, g = 4 | optimal_inaccurate | yes | 0.4288 | - | - | - | 414.5 | 0.9991 | 0.9954 | no |
| 12 | synthesised, g = 8 | optimal_inaccurate | yes | 0.4288 | - | - | - | 464.0 | 0.9991 | 1.1010 | no |
| 12 | synthesised, g = 16 | optimal_inaccurate | yes | 0.4288 | - | - | - | 648.9 | 0.9991 | 1.9277 | no |
| 10 | published LQR gain | optimal | yes | 0.1466 | - | - | - | 73.0 | 0.9990 | 0.9952 | no |
| 10 | synthesised, g = 2 | optimal | yes | 0.1966 | 0.0003 | 0.0492 | 0.0034 | 453.5 | 0.9993 | 0.9964 | no |
| 10 | synthesised, g = 4 | optimal_inaccurate | yes | 0.1966 | 0.0003 | 0.0492 | 0.0034 | 582.1 | 0.9993 | 1.5042 | no |
| 10 | synthesised, g = 8 | optimal | yes | 0.1966 | 0.0003 | 0.0492 | 0.0034 | 632.8 | 0.9993 | 1.7223 | no |
| 10 | synthesised, g = 16 | optimal_inaccurate | yes | 0.1966 | 0.0003 | 0.0492 | 0.0034 | 788.4 | 0.9993 | 2.3900 | no |
| 8 | published LQR gain | optimal | yes | 0.1772 | 0.0001 | 0.0374 | 0.0018 | 73.0 | 0.9991 | 0.9954 | yes |
| 8 | synthesised, g = 2 | optimal_inaccurate | yes | 0.2931 | - | - | - | 216.1 | 0.9996 | 0.9981 | no |
| 8 | synthesised, g = 4 | optimal_inaccurate | yes | 0.2931 | - | - | - | 231.7 | 0.9996 | 0.9981 | no |
| 8 | synthesised, g = 8 | optimal_inaccurate | yes | 0.2931 | - | - | - | 248.2 | 0.9996 | 0.9981 | no |
| 8 | synthesised, g = 16 | optimal_inaccurate | yes | 0.2931 | - | - | - | 303.3 | 0.9996 | 0.9980 | no |
| 6 | published LQR gain | optimal | yes | 0.0986 | 0.0003 | 0.0496 | 0.0017 | 73.0 | 0.9993 | 0.9964 | yes |
| 6 | synthesised, g = 2 | optimal_inaccurate | yes | 0.2490 | - | - | - | 237.5 | 0.9995 | 0.9978 | no |
| 6 | synthesised, g = 4 | optimal | yes | 0.2490 | - | - | - | 298.7 | 0.9995 | 0.9977 | no |
| 6 | synthesised, g = 8 | optimal_inaccurate | yes | 0.2490 | - | - | - | 318.4 | 0.9995 | 0.9977 | no |
| 6 | synthesised, g = 16 | optimal | yes | 0.2490 | - | - | - | 389.3 | 0.9995 | 0.9977 | no |
| 4 | published LQR gain | optimal_inaccurate | NO | 0.1117 | - | - | - | - | - | - | no |
| 4 | synthesised, g = 2 | optimal_inaccurate | yes | 0.2039 | - | - | - | 256.1 | 0.9994 | 0.9970 | no |
| 4 | synthesised, g = 4 | optimal_inaccurate | yes | 0.2039 | - | - | - | 581.8 | 0.9994 | 1.7697 | no |
| 4 | synthesised, g = 8 | optimal_inaccurate | yes | 0.2039 | - | - | - | 1143.7 | 0.9994 | 4.3955 | no |
| 4 | synthesised, g = 16 | optimal_inaccurate | yes | 0.2039 | - | - | - | 1574.1 | 0.9994 | 6.3902 | no |
| 3 | published LQR gain | optimal_inaccurate | NO | 0.0987 | - | - | - | - | - | - | no |
| 3 | synthesised, g = 2 | optimal_inaccurate | yes | 0.1738 | 0.0001 | 0.0477 | 0.0017 | 268.6 | 0.9995 | 0.9973 | no |
| 3 | synthesised, g = 4 | optimal_inaccurate | yes | 0.1738 | 0.0001 | 0.0478 | 0.0017 | 600.4 | 0.9995 | 1.9095 | no |
| 3 | synthesised, g = 8 | optimal | yes | 0.1738 | 0.0001 | 0.0477 | 0.0017 | 1213.2 | 0.9995 | 4.8637 | no |
| 3 | synthesised, g = 16 | optimal_inaccurate | yes | 0.1738 | 0.0001 | 0.0477 | 0.0017 | 2322.0 | 1.3018 | 10.1774 | no |

## Verification (section 1.4), scaled units

| w_sw | gain | worst eig of dynamics blocks | linear-region min eig | gain-bound min eig | min eig Q |
|---|---|---|---|---|---|
| 18 | LQR | -9.99e-06 | 8.2e-05 | - | 1.5e-03 |
| 18 | 2 | -9.99e-06 | -2.7e-11 | 7.4e-06 | 1.8e-04 |
| 18 | 4 | -9.99e-06 | -1.0e-10 | 1.0e-05 | 1.8e-04 |
| 18 | 8 | -9.98e-06 | -1.1e-10 | 9.6e-06 | 1.8e-04 |
| 18 | 16 | -9.99e-06 | 2.3e-11 | 1.0e-05 | 1.8e-04 |
| 16 | LQR | -1.00e-05 | 6.0e-10 | - | 5.8e-03 |
| 16 | 2 | -1.00e-05 | 7.0e-11 | 9.7e-04 | 3.2e-03 |
| 16 | 4 | -1.00e-05 | 1.4e-11 | 2.7e-03 | 3.2e-03 |
| 16 | 8 | -1.00e-05 | 2.4e-10 | 3.1e-03 | 3.2e-03 |
| 16 | 16 | -1.00e-05 | 7.1e-11 | 3.1e-03 | 3.2e-03 |
| 14 | LQR | -1.00e-05 | 8.1e-10 | - | 5.0e-03 |
| 14 | 2 | -1.00e-05 | 5.1e-12 | 1.5e-04 | 5.0e-03 |
| 14 | 4 | -1.00e-05 | -5.8e-11 | 2.9e-04 | 5.0e-03 |
| 14 | 8 | -1.00e-05 | -5.0e-11 | 2.1e-03 | 5.0e-03 |
| 14 | 16 | -1.00e-05 | 3.3e-11 | 3.9e-03 | 5.0e-03 |
| 12 | LQR | -1.00e-05 | 2.1e-10 | - | 9.7e-03 |
| 12 | 2 | -1.00e-05 | -2.9e-10 | 1.6e-03 | 6.2e-03 |
| 12 | 4 | -1.00e-05 | -7.9e-11 | 5.0e-03 | 6.2e-03 |
| 12 | 8 | -1.00e-05 | -1.7e-10 | 5.9e-03 | 6.2e-03 |
| 12 | 16 | -1.00e-05 | 1.6e-10 | 6.1e-03 | 6.2e-03 |
| 10 | LQR | -1.00e-05 | 2.9e-10 | - | 9.5e-03 |
| 10 | 2 | -1.00e-05 | -5.6e-11 | 2.1e-03 | 9.8e-03 |
| 10 | 4 | -1.00e-05 | -1.7e-10 | 7.2e-03 | 9.8e-03 |
| 10 | 8 | -1.00e-05 | -8.7e-11 | 9.1e-03 | 9.8e-03 |
| 10 | 16 | -1.00e-05 | -1.2e-10 | 9.6e-03 | 9.8e-03 |
| 8 | LQR | -1.00e-05 | -4.1e-11 | - | 3.0e-02 |
| 8 | 2 | -9.97e-06 | -1.3e-09 | 4.5e-03 | 2.1e-02 |
| 8 | 4 | -9.98e-06 | -7.4e-10 | 1.7e-02 | 2.1e-02 |
| 8 | 8 | -9.99e-06 | -2.9e-10 | 2.0e-02 | 2.1e-02 |
| 8 | 16 | -9.99e-06 | -3.0e-10 | 2.1e-02 | 2.1e-02 |
| 6 | LQR | -9.70e-06 | -1.5e-10 | - | 1.1e-02 |
| 6 | 2 | -9.99e-06 | -7.9e-10 | 1.5e-03 | 1.5e-02 |
| 6 | 4 | -1.00e-05 | -7.7e-11 | 1.1e-02 | 1.5e-02 |
| 6 | 8 | -9.98e-06 | -1.1e-09 | 1.4e-02 | 1.5e-02 |
| 6 | 16 | -1.00e-05 | -3.1e-11 | 1.5e-02 | 1.5e-02 |
| 4 | LQR | 8.35e-02 | 7.4e-05 | - | 1.7e-02 |
| 4 | 2 | -9.99e-06 | -4.8e-10 | 3.5e-04 | 1.2e-02 |
| 4 | 4 | -9.99e-06 | -4.5e-10 | 7.8e-04 | 1.2e-02 |
| 4 | 8 | -9.99e-06 | -4.0e-10 | 2.2e-03 | 1.2e-02 |
| 4 | 16 | -9.99e-06 | -5.1e-10 | 7.7e-03 | 1.2e-02 |
| 3 | LQR | 8.64e-02 | 5.4e-05 | - | 1.2e-02 |
| 3 | 2 | -9.99e-06 | -5.3e-10 | 2.7e-04 | 8.9e-03 |
| 3 | 4 | -9.98e-06 | -1.5e-09 | 4.7e-04 | 8.9e-03 |
| 3 | 8 | -1.00e-05 | -2.1e-10 | 6.9e-04 | 8.9e-03 |
| 3 | 16 | -9.99e-06 | -5.8e-10 | 1.6e-03 | 8.9e-03 |

## Second-solver cross-check (w_sw = 4, g = 8, beta_LPV)

Clarabel 0.203908 (optimal_inaccurate); SCS 0.209967 (optimal_inaccurate); relative difference 2.97e-02.

## Selected designs

| w_sw | selected gain bound | beta_final | published-gain beta_final (same box) |
|---|---|---|---|
| 18 | none accepted | - | - |
| 16 | none accepted | - | - |
| 14 | none accepted | - | - |
| 12 | none accepted | - | - |
| 10 | none accepted | - | - |
| 8 | none accepted | - | 0.0018 |
| 6 | none accepted | - | 0.0017 |
| 4 | none accepted | - | - |
| 3 | none accepted | - | - |

## Empirical protocol (E4 Monte Carlo, new seeds 1000 to 1039, nominal plant)

P(SAFE) over the 40 starts; exact-hover start in the last block. tau_90 and tau_50 as in E4 (linear interpolation on the grid 0 to 60 ms).

| chain | tau_90 | tau_50 | 0 ms | 5 ms | 10 ms | 15 ms | 20 ms | 25 ms | 30 ms | 35 ms | 40 ms | 45 ms | 50 ms | 55 ms | 60 ms | 80 ms | 100 ms | 130 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| published (LQR, w_sw 10) | 9 ms | 23 ms | 1.00 | 0.97 | 0.88 | 0.72 | 0.65 | 0.40 | 0.25 | 0.25 | 0.20 | 0.17 | 0.12 | 0.10 | 0.10 | 0.05 | 0.00 | 0.00 |
| LQR, w_sw 18 | 9 ms | 20 ms | 1.00 | 0.97 | 0.88 | 0.70 | 0.50 | 0.35 | 0.28 | 0.23 | 0.20 | 0.12 | 0.12 | 0.12 | 0.03 | 0.00 | 0.00 | 0.00 |
| LQR, w_sw 16 | 9 ms | 23 ms | 1.00 | 0.97 | 0.88 | 0.75 | 0.62 | 0.40 | 0.30 | 0.23 | 0.20 | 0.15 | 0.12 | 0.12 | 0.10 | 0.03 | 0.00 | 0.00 |
| LQR, w_sw 14 | 12 ms | 28 ms | 1.00 | 1.00 | 0.95 | 0.85 | 0.72 | 0.62 | 0.42 | 0.28 | 0.25 | 0.23 | 0.20 | 0.20 | 0.12 | 0.05 | 0.03 | 0.00 |
| LQR, w_sw 12 | 15 ms | 33 ms | 1.00 | 1.00 | 1.00 | 0.90 | 0.80 | 0.75 | 0.62 | 0.42 | 0.30 | 0.25 | 0.23 | 0.23 | 0.20 | 0.12 | 0.05 | 0.00 |
| LQR, w_sw 8 | 15 ms | 42 ms | 1.00 | 1.00 | 1.00 | 0.90 | 0.88 | 0.72 | 0.72 | 0.60 | 0.53 | 0.47 | 0.42 | 0.30 | 0.30 | 0.20 | 0.12 | 0.03 |
| LQR, w_sw 6 | >60 ms | >60 ms | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.97 | 0.88 |
| LQR, w_sw 4 | 17 ms | 33 ms | 0.93 | 0.95 | 0.97 | 0.95 | 0.85 | 0.80 | 0.57 | 0.45 | 0.45 | 0.42 | 0.38 | 0.33 | 0.33 | 0.28 | 0.25 | 0.17 |
| LQR, w_sw 3 | 0 ms | 0 ms | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Exact hover start, SAFE by tau (1 = SAFE):

| chain | 0 | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 55 | 60 | 80 | 100 | 130 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| published (LQR, w_sw 10) | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 18 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 16 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 14 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 12 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 8 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 6 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| LQR, w_sw 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LQR, w_sw 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
