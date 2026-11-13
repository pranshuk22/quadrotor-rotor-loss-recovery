# E8b: MPC on the full-state Koopman model (proposal controller 2)

Controllers: analytical MPC, MPC on the full-state Koopman model (`LiftedKoopmanMPC`), residual Koopman MPC, and the LQR as reference. Pre-registered settings are in the docstring of `experiments/e8_full_koopman_mpc.py`.

## Model and terminal-cost checks

- Lifted states: 55 (+1 altitude state in the MPC); eigenvalues outside the unit circle: 4 of 55, largest modulus 1.0070.
- Terminal cost: `dare`. Riccati residual (relative) 2.1e-15, asymmetry 0.0e+00, smallest/largest eigenvalue 2.3e-09, spectral radius of the lifted closed loop 0.9949, condition number 4.4e+08; all checks passed: True.
- Command issued at the exact trim (should be zero; a bias of the learned model): (+0.066, -0.450, +0.124) N from the relaxed-hover thrusts.

## Part 1: steady altitude bias by mismatch effect

Protocol of E7/E8a. A run that diverged is shown with its stop time.

| Plant | LQR | MPC, analytical | MPC, full-state Koopman | MPC, residual Koopman |
|---|---|---|---|---|
| A (full) | -0.285 m | -0.286 m | -0.186 m | -0.193 m |
| A without thrust loss | -0.154 m | -0.154 m | -0.055 m | -0.066 m |
| nominal + A's thrust loss only | -0.100 m | -0.101 m | -0.028 m | -0.033 m |
| B (full, held out) | -0.029 m | -0.033 m | +0.031 m | +0.022 m |
| B without thrust loss | +0.112 m | +0.111 m | +0.178 m | +0.164 m |
| nominal + B's thrust loss only | -0.174 m | -0.177 m | -0.105 m | -0.107 m |

| Plant | Controller | RMS z (m) | max standardised xi | non-optimal QPs | median wall time per step (ms) |
|---|---|---|---|---|---|
| A (full) | MPC, full-state Koopman | 0.337 | 8.8 | 0 | 62.5 |
| A without thrust loss | MPC, full-state Koopman | 0.279 | 8.9 | 0 | 75.9 |
| nominal + A's thrust loss only | MPC, full-state Koopman | 0.270 | 8.0 | 0 | 53.3 |
| B (full, held out) | MPC, full-state Koopman | 0.263 | 9.1 | 0 | 52.7 |
| B without thrust loss | MPC, full-state Koopman | 0.287 | 8.5 | 0 | 53.0 |
| nominal + B's thrust loss only | MPC, full-state Koopman | 0.295 | 8.0 | 0 | 53.5 |

## Part 2: capture after a detection delay (exact hover start)

Hover, rotor 4 fails, healthy LQR for τ, spin-up on rotors 1 and 3 at 2.95 N, then the capture controller. Criterion: `rotorfail/metrics.py`; capture is judged against each controller's own closed-loop steady state on that plant. Cells: altitude loss (m) / minimum n_z / SAFE; 'stopped' = the run hit the divergence rule at the given time.

### Plant: A (full)

| τ (ms) | LQR | MPC, analytical | MPC, full-state Koopman | MPC, residual Koopman |
|---|---|---|---|---|
| 0 | 0.40 / 0.26 / yes | 0.53 / 0.25 / yes | 0.74 / 0.08 / yes | 0.58 / 0.20 / yes |
| 10 | 1.69 / 0.04 / yes | 2.52 / -0.05 / no | 4.96 / -0.26 / no | 2.80 / -0.06 / no |
| 20 | 6.56 / -0.08 / no | 8.53 / -0.29 / no | 100.08 / -0.51 / no (stopped 6.26 s) | 7.94 / -0.25 / no |
| 30 | 12.62 / -0.10 / no | 19.19 / -0.46 / no | 100.03 / -0.67 / no (stopped 4.76 s) | 19.51 / -0.43 / no |
| 40 | 22.81 / -0.16 / no | 38.55 / -0.61 / no | 100.07 / -0.75 / no (stopped 4.34 s) | 38.82 / -0.59 / no |
| 60 | 68.00 / -0.39 / no | 100.07 / -0.80 / no (stopped 4.91 s) | 100.23 / -0.87 / no (stopped 3.95 s) | 100.01 / -0.80 / no (stopped 5.03 s) |

### Plant: nominal

| τ (ms) | LQR | MPC, analytical | MPC, full-state Koopman | MPC, residual Koopman |
|---|---|---|---|---|
| 0 | 0.03 / 0.47 / yes | 0.05 / 0.45 / yes | 0.03 / 0.38 / yes | 0.00 / 0.43 / yes |
| 10 | 0.40 / 0.21 / yes | 0.66 / 0.14 / yes | 0.90 / 0.02 / yes | 0.73 / 0.13 / yes |
| 20 | 1.96 / 0.02 / yes | 2.94 / -0.14 / no | 5.13 / -0.27 / no | 3.31 / -0.12 / no |
| 30 | 5.30 / -0.02 / no | 7.57 / -0.33 / no | 100.11 / -0.46 / no (stopped 7.19 s) | 9.16 / -0.30 / no |
| 40 | 10.00 / -0.08 / no | 16.70 / -0.49 / no | 100.14 / -0.57 / no (stopped 5.17 s) | 21.64 / -0.47 / no |
| 60 | 23.88 / -0.29 / no | 95.13 / -0.70 / no | 100.14 / -0.72 / no (stopped 4.11 s) | 100.07 / -0.69 / no (stopped 6.86 s) |

### Full-state Koopman MPC during capture

| Plant | τ (ms) | max standardised xi | non-optimal QPs | median wall time per step (ms) |
|---|---|---|---|---|
| A (full) | 0 | 37.5 | 0 | 64.9 |
| A (full) | 10 | 44.9 | 0 | 72.9 |
| A (full) | 20 | 192.6 | 0 | 260.7 |
| A (full) | 30 | 283.5 | 0 | 267.4 |
| A (full) | 40 | 314.5 | 0 | 316.1 |
| A (full) | 60 | 350.0 | 0 | 288.9 |
| nominal | 0 | 34.5 | 0 | 92.7 |
| nominal | 10 | 40.9 | 0 | 87.9 |
| nominal | 20 | 47.4 | 0 | 73.5 |
| nominal | 30 | 194.6 | 0 | 190.1 |
| nominal | 40 | 243.7 | 0 | 241.7 |
| nominal | 60 | 336.4 | 0 | 269.4 |

Total run time: 1097 s on 8 processes.
