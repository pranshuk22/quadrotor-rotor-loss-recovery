# E8a: Offset-free baselines against the residual Koopman MPC

All controllers are designed on the nominal parameters. Every MPC uses horizon 20 × 5 ms, the same weights, DARE terminal cost and thrust limits. The offset-free MPC adds a constant thrust-offset disturbance model, a steady-state Kalman filter and a target calculation (`rotorfail/offset_free.py`); the pre-registered settings are in the docstring of `experiments/e8_offset_free.py`. 'LQR + integrator' is the failure LQR with an integrator on the altitude error.

## Part 1: steady altitude bias by mismatch effect

Protocol of E7: one start per plant (1 m below the set-point, 8 s); steady error = mean altitude over the last 2 s.

| Plant | LQR | MPC, analytical | MPC, residual Koopman | MPC, offset-free | MPC, offset-free (state d) | MPC, residual + offset-free | MPC, residual + o.-f. (state d) | LQR + integrator |
|---|---|---|---|---|---|---|---|---|
| A (full) | -0.285 m | -0.286 m | -0.193 m | -0.239 m | -0.000 m | +0.001 m | -0.000 m | +0.001 m |
| A without thrust loss | -0.154 m | -0.154 m | -0.066 m | -0.228 m | -0.000 m | +0.009 m | -0.000 m | +0.009 m |
| nominal + A's thrust loss only | -0.100 m | -0.101 m | -0.033 m | -0.007 m | -0.000 m | +0.197 m | -0.000 m | +0.012 m |
| B (full, held out) | -0.029 m | -0.033 m | +0.022 m | +0.165 m | -0.000 m | +0.342 m | -0.000 m | +0.016 m |
| B without thrust loss | +0.112 m | +0.111 m | +0.164 m | +0.173 m | -0.000 m | +0.346 m | -0.000 m | +0.024 m |
| nominal + B's thrust loss only | -0.174 m | -0.177 m | -0.107 m | -0.011 m | -0.000 m | +0.194 m | -0.000 m | +0.007 m |

### Further metrics

| Plant | Controller | RMS z (m) | settling to ±5 cm (s) | steady attitude error | max rate error (rad/s) | upright |
|---|---|---|---|---|---|---|
| A (full) | LQR | 0.391 | not settled | 0.0301 | 2.37 | yes |
| A (full) | MPC, analytical | 0.392 | not settled | 0.0311 | 2.37 | yes |
| A (full) | MPC, residual Koopman | 0.335 | not settled | 0.0263 | 2.41 | yes |
| A (full) | MPC, offset-free | 0.366 | not settled | 0.0287 | 2.45 | yes |
| A (full) | MPC, offset-free (state d) | 0.263 | 1.82 | 0.0001 | 2.13 | yes |
| A (full) | MPC, residual + offset-free | 0.265 | 1.84 | 0.0003 | 2.13 | yes |
| A (full) | MPC, residual + o.-f. (state d) | 0.262 | 1.82 | 0.0001 | 2.13 | yes |
| A (full) | LQR + integrator | 0.254 | 1.46 | 0.0302 | 2.37 | yes |
| A without thrust loss | LQR | 0.313 | not settled | 0.0327 | 2.28 | yes |
| A without thrust loss | MPC, analytical | 0.313 | not settled | 0.0343 | 2.28 | yes |
| A without thrust loss | MPC, residual Koopman | 0.277 | not settled | 0.0249 | 2.30 | yes |
| A without thrust loss | MPC, offset-free | 0.358 | not settled | 0.0276 | 2.34 | yes |
| A without thrust loss | MPC, offset-free (state d) | 0.261 | 1.81 | 0.0001 | 2.13 | yes |
| A without thrust loss | MPC, residual + offset-free | 0.262 | 1.79 | 0.0013 | 2.13 | yes |
| A without thrust loss | MPC, residual + o.-f. (state d) | 0.259 | 1.81 | 0.0001 | 2.13 | yes |
| A without thrust loss | LQR + integrator | 0.247 | 3.83 | 0.0328 | 2.28 | yes |
| nominal + A's thrust loss only | LQR | 0.288 | not settled | 0.0052 | 2.13 | yes |
| nominal + A's thrust loss only | MPC, analytical | 0.290 | not settled | 0.0057 | 2.13 | yes |
| nominal + A's thrust loss only | MPC, residual Koopman | 0.267 | 2.10 | 0.0250 | 2.13 | yes |
| nominal + A's thrust loss only | MPC, offset-free | 0.262 | 1.85 | 0.0008 | 2.13 | yes |
| nominal + A's thrust loss only | MPC, offset-free (state d) | 0.259 | 1.79 | 0.0001 | 2.13 | yes |
| nominal + A's thrust loss only | MPC, residual + offset-free | 0.295 | not settled | 0.0272 | 2.13 | yes |
| nominal + A's thrust loss only | MPC, residual + o.-f. (state d) | 0.258 | 1.79 | 0.0001 | 2.13 | yes |
| nominal + A's thrust loss only | LQR + integrator | 0.248 | 4.26 | 0.0052 | 2.13 | yes |
| B (full, held out) | LQR | 0.267 | 1.99 | 0.0333 | 2.13 | yes |
| B (full, held out) | MPC, analytical | 0.269 | 2.03 | 0.0353 | 2.13 | yes |
| B (full, held out) | MPC, residual Koopman | 0.260 | 1.67 | 0.0462 | 2.13 | yes |
| B (full, held out) | MPC, offset-free | 0.281 | not settled | 0.0252 | 2.23 | yes |
| B (full, held out) | MPC, offset-free (state d) | 0.258 | 1.78 | 0.0000 | 2.13 | yes |
| B (full, held out) | MPC, residual + offset-free | 0.378 | not settled | 0.0472 | 2.57 | yes |
| B (full, held out) | MPC, residual + o.-f. (state d) | 0.257 | 1.78 | 0.0000 | 2.13 | yes |
| B (full, held out) | LQR + integrator | 0.250 | 4.67 | 0.0333 | 2.18 | yes |
| B without thrust loss | LQR | 0.264 | not settled | 0.0280 | 2.13 | yes |
| B without thrust loss | MPC, analytical | 0.264 | not settled | 0.0291 | 2.13 | yes |
| B without thrust loss | MPC, residual Koopman | 0.279 | not settled | 0.0406 | 2.13 | yes |
| B without thrust loss | MPC, offset-free | 0.282 | not settled | 0.0264 | 2.29 | yes |
| B without thrust loss | MPC, offset-free (state d) | 0.256 | 1.78 | 0.0000 | 2.13 | yes |
| B without thrust loss | MPC, residual + offset-free | 0.378 | not settled | 0.0477 | 2.63 | yes |
| B without thrust loss | MPC, residual + o.-f. (state d) | 0.254 | 1.77 | 0.0000 | 2.13 | yes |
| B without thrust loss | LQR + integrator | 0.252 | 5.45 | 0.0279 | 2.34 | yes |
| nominal + B's thrust loss only | LQR | 0.325 | not settled | 0.0090 | 2.13 | yes |
| nominal + B's thrust loss only | MPC, analytical | 0.327 | not settled | 0.0098 | 2.13 | yes |
| nominal + B's thrust loss only | MPC, residual Koopman | 0.292 | not settled | 0.0279 | 2.13 | yes |
| nominal + B's thrust loss only | MPC, offset-free | 0.264 | 1.89 | 0.0015 | 2.13 | yes |
| nominal + B's thrust loss only | MPC, offset-free (state d) | 0.261 | 1.79 | 0.0001 | 2.13 | yes |
| nominal + B's thrust loss only | MPC, residual + offset-free | 0.296 | not settled | 0.0267 | 2.13 | yes |
| nominal + B's thrust loss only | MPC, residual + o.-f. (state d) | 0.259 | 1.79 | 0.0001 | 2.13 | yes |
| nominal + B's thrust loss only | LQR + integrator | 0.251 | 3.71 | 0.0090 | 2.13 | yes |

### Solver and estimator statistics (Part 1)

| Controller | median wall time per step (ms) | median time inside OSQP (ms) | inexact targets | d_hat at its bound | non-optimal QPs | largest abs. d_hat |
|---|---|---|---|---|---|---|
| MPC, analytical | 4.1 | 0.70 | n/a | n/a | 0 | n/a |
| MPC, residual Koopman | 4.2 | 0.72 | n/a | n/a | 0 | n/a |
| MPC, offset-free | 4.2 | 0.69 | 0.000 (max) | 0.000 (max) | 0 | 0.463 |
| MPC, offset-free (state d) | 4.6 | 0.94 | 0.000 (max) | 0.000 (max) | 0 | 0.109 |
| MPC, residual + offset-free | 4.4 | 0.74 | 0.000 (max) | 0.000 (max) | 0 | 0.672 |
| MPC, residual + o.-f. (state d) | 4.6 | 0.88 | 0.000 (max) | 0.000 (max) | 0 | 0.145 |

d_hat is in N for the thrust model and in state units per step for the state model, so the two are not comparable.

## Part 2: capture after a detection delay (exact hover start)

Hover, rotor 4 fails, healthy LQR for τ, spin-up on rotors 1 and 3 at 2.95 N, then the capture controller. Criterion: `rotorfail/metrics.py`. Capture is measured against each controller's own closed-loop steady state on that plant (12 s run from the trim).

### Plant: A (full)

| τ (ms) | LQR | MPC, analytical | MPC, residual Koopman | MPC, offset-free | MPC, offset-free (state d) | MPC, residual + offset-free | MPC, residual + o.-f. (state d) | LQR + integrator |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.40 / 0.26 / yes | 0.53 / 0.25 / yes | 0.58 / 0.20 / yes | 0.89 / 0.03 / yes | 14.33 / -0.54 / no | 0.83 / 0.01 / yes | 10.65 / -0.55 / no | 0.36 / 0.26 / yes |
| 10 | 1.69 / 0.04 / yes | 2.52 / -0.05 / no | 2.80 / -0.06 / no | 3.13 / -0.19 / no | 181.01 / -0.88 / no | 3.89 / -0.27 / no | 209.11 / -0.88 / no | 1.83 / 0.04 / yes |
| 20 | 6.56 / -0.08 / no | 8.53 / -0.29 / no | 7.94 / -0.25 / no | 8.18 / -0.33 / no | 274.04 / -1.00 / no | 9.66 / -0.44 / no | 246.88 / -1.00 / no | 6.30 / -0.05 / no |
| 30 | 12.62 / -0.10 / no | 19.19 / -0.46 / no | 19.51 / -0.43 / no | 21.26 / -0.52 / no | 616.24 / -1.00 / no | 25.04 / -0.64 / no | 568.10 / -1.00 / no | 12.36 / -0.05 / no |
| 40 | 22.81 / -0.16 / no | 38.55 / -0.61 / no | 38.82 / -0.59 / no | 47.00 / -0.67 / no | 756.67 / -1.00 / no | 68.92 / -0.79 / no | 654.43 / -1.00 / no | 23.84 / -0.14 / no |
| 60 | 68.00 / -0.39 / no | 339.10 / -0.80 / no | 308.83 / -0.80 / no | 434.52 / -0.88 / no | 754.42 / -1.00 / no | 467.39 / -0.95 / no | 673.81 / -1.00 / no | 107.25 / -0.45 / no |

### Plant: nominal

| τ (ms) | LQR | MPC, analytical | MPC, residual Koopman | MPC, offset-free | MPC, offset-free (state d) | MPC, residual + offset-free | MPC, residual + o.-f. (state d) | LQR + integrator |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.03 / 0.47 / yes | 0.05 / 0.45 / yes | 0.00 / 0.43 / yes | 0.04 / 0.39 / yes | 0.63 / -0.24 / no | 0.00 / 0.38 / yes | 0.49 / -0.25 / no | 0.05 / 0.47 / yes |
| 10 | 0.40 / 0.21 / yes | 0.66 / 0.14 / yes | 0.73 / 0.13 / yes | 0.57 / 0.12 / yes | 15.76 / -0.65 / no | 0.54 / 0.12 / yes | 18.37 / -0.66 / no | 0.37 / 0.21 / yes |
| 20 | 1.96 / 0.02 / yes | 2.94 / -0.14 / no | 3.31 / -0.12 / no | 2.37 / -0.08 / no | 26.55 / -0.90 / no | 2.18 / -0.06 / no | 126.33 / -0.90 / no | 1.98 / 0.04 / yes |
| 30 | 5.30 / -0.02 / no | 7.57 / -0.33 / no | 9.16 / -0.30 / no | 6.69 / -0.26 / no | 272.06 / -0.99 / no | 6.65 / -0.27 / no | 244.86 / -0.99 / no | 5.16 / 0.02 / no |
| 40 | 10.00 / -0.08 / no | 16.70 / -0.49 / no | 21.64 / -0.47 / no | 15.38 / -0.43 / no | 574.71 / -1.00 / no | 16.02 / -0.45 / no | 463.28 / -0.99 / no | 10.07 / -0.05 / no |
| 60 | 23.88 / -0.29 / no | 95.13 / -0.70 / no | 141.58 / -0.69 / no | 124.38 / -0.67 / no | 862.64 / -1.00 / no | 152.38 / -0.71 / no | 764.28 / -1.00 / no | 28.51 / -0.36 / no |

Cells: altitude loss (m) / minimum n_z / SAFE.

### Estimator behaviour during capture (offset-free controllers)

| Plant | Controller | τ (ms) | largest abs. d_hat | share of inexact targets | share of d_hat at its bound | non-optimal QPs |
|---|---|---|---|---|---|---|
| A (full) | MPC, offset-free | 0 | 1.000 | 0.019 | 0.012 | 0 |
| A (full) | MPC, offset-free | 10 | 1.000 | 0.019 | 0.010 | 0 |
| A (full) | MPC, offset-free | 20 | 1.000 | 0.019 | 0.008 | 0 |
| A (full) | MPC, offset-free | 30 | 1.000 | 0.046 | 0.043 | 0 |
| A (full) | MPC, offset-free | 40 | 1.000 | 0.056 | 0.081 | 0 |
| A (full) | MPC, offset-free | 60 | 1.000 | 0.427 | 0.581 | 0 |
| A (full) | MPC, offset-free (state d) | 0 | 0.500 | 0.101 | 0.004 | 0 |
| A (full) | MPC, offset-free (state d) | 10 | 0.500 | 0.831 | 0.001 | 0 |
| A (full) | MPC, offset-free (state d) | 20 | 0.500 | 0.917 | 0.002 | 0 |
| A (full) | MPC, offset-free (state d) | 30 | 0.483 | 0.993 | 0.000 | 0 |
| A (full) | MPC, offset-free (state d) | 40 | 0.428 | 0.994 | 0.000 | 0 |
| A (full) | MPC, offset-free (state d) | 60 | 0.339 | 0.995 | 0.000 | 0 |
| A (full) | MPC, residual + offset-free | 0 | 0.737 | 0.007 | 0.000 | 0 |
| A (full) | MPC, residual + offset-free | 10 | 0.836 | 0.009 | 0.000 | 0 |
| A (full) | MPC, residual + offset-free | 20 | 0.965 | 0.013 | 0.000 | 0 |
| A (full) | MPC, residual + offset-free | 30 | 1.000 | 0.018 | 0.039 | 0 |
| A (full) | MPC, residual + offset-free | 40 | 1.000 | 0.084 | 0.596 | 0 |
| A (full) | MPC, residual + offset-free | 60 | 1.000 | 0.453 | 0.763 | 0 |
| A (full) | MPC, residual + o.-f. (state d) | 0 | 0.467 | 0.071 | 0.000 | 0 |
| A (full) | MPC, residual + o.-f. (state d) | 10 | 0.413 | 0.875 | 0.000 | 0 |
| A (full) | MPC, residual + o.-f. (state d) | 20 | 0.455 | 0.880 | 0.000 | 0 |
| A (full) | MPC, residual + o.-f. (state d) | 30 | 0.464 | 0.993 | 0.000 | 0 |
| A (full) | MPC, residual + o.-f. (state d) | 40 | 0.400 | 0.994 | 0.000 | 0 |
| A (full) | MPC, residual + o.-f. (state d) | 60 | 0.309 | 0.995 | 0.000 | 0 |
| nominal | MPC, offset-free | 0 | 0.771 | 0.000 | 0.000 | 0 |
| nominal | MPC, offset-free | 10 | 0.906 | 0.000 | 0.000 | 0 |
| nominal | MPC, offset-free | 20 | 1.000 | 0.000 | 0.001 | 0 |
| nominal | MPC, offset-free | 30 | 1.000 | 0.000 | 0.006 | 0 |
| nominal | MPC, offset-free | 40 | 1.000 | 0.000 | 0.034 | 0 |
| nominal | MPC, offset-free | 60 | 1.000 | 0.000 | 0.265 | 0 |
| nominal | MPC, offset-free (state d) | 0 | 0.409 | 0.017 | 0.000 | 0 |
| nominal | MPC, offset-free (state d) | 10 | 0.286 | 0.119 | 0.000 | 0 |
| nominal | MPC, offset-free (state d) | 20 | 0.291 | 0.152 | 0.000 | 0 |
| nominal | MPC, offset-free (state d) | 30 | 0.284 | 0.856 | 0.000 | 0 |
| nominal | MPC, offset-free (state d) | 40 | 0.252 | 0.994 | 0.000 | 0 |
| nominal | MPC, offset-free (state d) | 60 | 0.245 | 0.995 | 0.000 | 0 |
| nominal | MPC, residual + offset-free | 0 | 0.479 | 0.000 | 0.000 | 0 |
| nominal | MPC, residual + offset-free | 10 | 0.532 | 0.000 | 0.000 | 0 |
| nominal | MPC, residual + offset-free | 20 | 0.684 | 0.000 | 0.000 | 0 |
| nominal | MPC, residual + offset-free | 30 | 0.882 | 0.000 | 0.000 | 0 |
| nominal | MPC, residual + offset-free | 40 | 1.000 | 0.000 | 0.011 | 0 |
| nominal | MPC, residual + offset-free | 60 | 1.000 | 0.000 | 0.567 | 0 |
| nominal | MPC, residual + o.-f. (state d) | 0 | 0.314 | 0.016 | 0.000 | 0 |
| nominal | MPC, residual + o.-f. (state d) | 10 | 0.215 | 0.135 | 0.000 | 0 |
| nominal | MPC, residual + o.-f. (state d) | 20 | 0.244 | 0.653 | 0.000 | 0 |
| nominal | MPC, residual + o.-f. (state d) | 30 | 0.248 | 0.805 | 0.000 | 0 |
| nominal | MPC, residual + o.-f. (state d) | 40 | 0.245 | 0.994 | 0.000 | 0 |
| nominal | MPC, residual + o.-f. (state d) | 60 | 0.245 | 0.995 | 0.000 | 0 |

Total run time: 539 s on 8 processes.
