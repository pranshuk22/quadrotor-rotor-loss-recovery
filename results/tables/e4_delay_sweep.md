# E4: Empirical detection-delay tolerance (nonlinear simulation)

Hover at z = 0, rotor 4 fails at t = 0, healthy LQR runs until t = τ, then the failure strategy. Run length 10 s. Success criterion fixed in advance (`rotorfail/metrics.py`): attitude captured (|n − n̄| < 0.05 and |ω − ω̄| < 2 rad/s over the last 1 s), altitude loss < 2 m, never inverted (n_z > 0).

## Nominal start (exact hover), healthy-LQR aggressiveness α = 1

| τ (ms) | A: captured | A: alt. loss (m) | A: min n_z | B: captured | B: alt. loss (m) | B: min n_z |
|---|---|---|---|---|---|---|
| 0 | yes | 14.90 | -0.79 | yes | 0.41 | 0.58 |
| 10 | yes | 15.52 | -0.81 | yes | 1.25 | 0.52 |
| 20 | yes | 15.99 | -0.82 | yes | 2.99 | 0.36 |
| 30 | yes | 16.25 | -0.82 | yes | 7.13 | 0.12 |
| 40 | yes | 16.28 | -0.82 | yes | 16.32 | -0.07 |
| 50 | yes | 16.09 | -0.82 | no | 30.39 | -0.22 |
| 60 | yes | 15.73 | -0.81 | no | 41.48 | -0.33 |
| 70 | yes | 15.21 | -0.80 | no | 51.51 | -0.41 |
| 80 | yes | 14.63 | -0.79 | no | 61.18 | -0.47 |
| 90 | yes | 14.06 | -0.78 | no | 72.58 | -0.52 |
| 100 | yes | 13.52 | -0.76 | no | 86.81 | -0.57 |
| 110 | yes | 13.01 | -0.75 | no | 105.95 | -0.62 |
| 120 | yes | 12.52 | -0.73 | no | 134.52 | -0.66 |
| 130 | yes | 12.06 | -0.72 | no | 167.11 | -0.70 |
| 140 | yes | 11.64 | -0.70 | no | 198.58 | -0.73 |
| 150 | yes | 11.25 | -0.68 | no | 227.91 | -0.76 |
| 160 | yes | 10.89 | -0.66 | no | 254.94 | -0.79 |
| 170 | yes | 10.58 | -0.65 | no | 278.71 | -0.82 |
| 180 | yes | 10.33 | -0.63 | no | 298.48 | -0.84 |
| 190 | yes | 10.10 | -0.61 | no | 313.55 | -0.86 |
| 200 | yes | 9.90 | -0.59 | no | 323.64 | -0.87 |
| 210 | yes | 9.71 | -0.58 | no | 327.99 | -0.88 |
| 220 | yes | 9.55 | -0.56 | no | 326.35 | -0.89 |
| 230 | yes | 9.42 | -0.54 | no | 318.90 | -0.90 |
| 240 | yes | 9.30 | -0.53 | no | 305.57 | -0.90 |
| 250 | yes | 9.22 | -0.51 | no | 286.99 | -0.91 |
| 260 | yes | 9.16 | -0.50 | no | 263.52 | -0.91 |
| 270 | yes | 9.13 | -0.49 | no | 235.96 | -0.90 |
| 280 | yes | 9.13 | -0.47 | no | 205.31 | -0.90 |
| 290 | yes | 9.16 | -0.47 | no | 172.40 | -0.89 |
| 300 | yes | 9.22 | -0.46 | no | 137.82 | -0.88 |

## Empirical delay tolerance τ*_emp (largest τ with every smaller grid τ SAFE)

| Strategy | α (healthy aggressiveness) | τ*_emp |
|---|---|---|
| LQR at r̄ (direct) | 1.0 | not safe even at τ = 0 |
| Spin-up + LQR (M&D) | 0.3 | 10 ms |
| Spin-up + LQR (M&D) | 1.0 | 10 ms |
| Spin-up + LQR (M&D) | 3.0 | 10 ms |

## Monte Carlo (strategy B, α = 1): 20 random pre-failure states per τ

Pre-failure state: velocity σ = 0.3 m/s, Euler angles σ = 3°, body rates σ = 0.3 rad/s.

| τ (ms) | SAFE | captured | median alt. loss (m) |
|---|---|---|---|
| 0 | 20/20 | 20/20 | 0.38 |
| 10 | 17/20 | 20/20 | 1.11 |
| 20 | 6/20 | 19/20 | 3.20 |
| 30 | 1/20 | 18/20 | 9.12 |
| 50 | 0/20 | 9/20 | 39.09 |
| 80 | 0/20 | 3/20 | 76.54 |
