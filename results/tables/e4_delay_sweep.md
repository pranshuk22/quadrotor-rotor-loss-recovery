# E4: Recovery versus fault-detection delay (nonlinear simulation, nominal plant)

Hover at z = 0; rotor 4 fails at t = 0; healthy LQR until t = τ; then the failure strategy. Runs of 10 s. Success criterion fixed in advance (`rotorfail/metrics.py`): attitude captured (|n − n̄| < 0.05 and |ω − ω̄| < 2 rad/s over the last 1 s of a completed run), altitude loss < 2 m, never inverted (n_z > 0).

Spin-up thrust: **2.95 N** per rotor is read from the flight data in Mueller & D'Andrea (2014) Fig. 4; **2.45 N** (m g / 2) is a sensitivity case.

## Monte Carlo: 40 random pre-failure states per delay

Pre-failure state: velocity σ = 0.3 m/s, Euler angles σ = 3°, body rates σ = 0.3 rad/s. P(SAFE) with 95% Wilson interval.

| τ (ms) | Spin-up 2.95 N (flight) + LQR: P(SAFE) [95% CI] / captured / median alt. loss (m) | Spin-up 2.45 N (m g/2) + LQR: P(SAFE) [95% CI] / captured / median alt. loss (m) |
|---|---|---|
| 0 | 1.00 [0.91, 1.00] / 40/40 / 0.04 | 1.00 [0.91, 1.00] / 40/40 / 0.43 |
| 5 | 1.00 [0.91, 1.00] / 40/40 / 0.14 | 0.95 [0.83, 0.99] / 40/40 / 0.72 |
| 10 | 0.97 [0.87, 1.00] / 40/40 / 0.38 | 0.82 [0.68, 0.91] / 40/40 / 1.27 |
| 15 | 0.80 [0.65, 0.90] / 40/40 / 0.97 | 0.45 [0.31, 0.60] / 40/40 / 2.16 |
| 20 | 0.42 [0.29, 0.58] / 40/40 / 2.21 | 0.28 [0.16, 0.43] / 39/40 / 3.51 |
| 25 | 0.33 [0.20, 0.48] / 39/40 / 4.11 | 0.10 [0.04, 0.23] / 39/40 / 5.46 |
| 30 | 0.17 [0.09, 0.32] / 39/40 / 6.68 | 0.07 [0.03, 0.20] / 35/40 / 9.11 |
| 35 | 0.10 [0.04, 0.23] / 38/40 / 9.72 | 0.07 [0.03, 0.20] / 31/40 / 14.97 |
| 40 | 0.07 [0.03, 0.20] / 33/40 / 12.55 | 0.07 [0.03, 0.20] / 20/40 / 22.19 |
| 45 | 0.07 [0.03, 0.20] / 29/40 / 16.14 | 0.05 [0.01, 0.17] / 15/40 / 30.64 |
| 50 | 0.07 [0.03, 0.20] / 23/40 / 20.78 | 0.03 [0.00, 0.13] / 14/40 / 37.79 |
| 55 | 0.07 [0.03, 0.20] / 17/40 / 24.96 | 0.03 [0.00, 0.13] / 12/40 / 44.24 |
| 60 | 0.07 [0.03, 0.20] / 16/40 / 30.60 | 0.03 [0.00, 0.13] / 10/40 / 51.35 |

| Spin-up thrust | τ₉₀ (P(SAFE) falls below 0.9) | τ₅₀ (P(SAFE) falls below 0.5) | τ₅₀ for capture only |
|---|---|---|---|
| Spin-up 2.95 N (flight) + LQR | 12 ms | 19 ms | 52 ms |
| Spin-up 2.45 N (m g/2) + LQR | 7 ms | 14 ms | 40 ms |

## Nominal start (exact hover), healthy-LQR aggressiveness α = 1

| τ (ms) | LQR directly: alt. loss (m) / min n_z / SAFE | Spin-up 2.95 N (flight) + LQR: alt. loss (m) / min n_z / SAFE | Spin-up 2.45 N (m g/2) + LQR: alt. loss (m) / min n_z / SAFE |
|---|---|---|---|
| 0 | 14.92 / -0.79 / no | 0.03 / 0.47 / yes | 0.41 / 0.58 / yes |
| 10 | 15.54 / -0.81 / no | 0.37 / 0.23 / yes | 1.24 / 0.52 / yes |
| 20 | 16.01 / -0.82 / no | 1.73 / 0.03 / yes | 2.99 / 0.36 / no |
| 30 | 16.27 / -0.82 / no | 4.74 / 0.00 / no | 7.13 / 0.12 / no |
| 40 | 16.30 / -0.82 / no | 8.98 / -0.06 / no | 16.30 / -0.07 / no |
| 50 | 16.11 / -0.82 / no | 14.74 / -0.14 / no | 30.40 / -0.22 / no |
| 60 | 15.74 / -0.81 / no | 21.44 / -0.25 / no | 41.48 / -0.33 / no |
| 70 | 15.23 / -0.80 / no | 29.00 / -0.35 / no | 51.51 / -0.41 / no |
| 80 | 14.64 / -0.79 / no | 37.96 / -0.43 / no | 61.18 / -0.47 / no |
| 90 | 14.07 / -0.78 / no | 44.91 / -0.48 / no | 72.65 / -0.52 / no |
| 100 | 13.53 / -0.76 / no | 52.93 / -0.52 / no | 86.78 / -0.57 / no |
| 110 | 13.02 / -0.75 / no | 62.30 / -0.56 / no | 105.88 / -0.62 / no |
| 120 | 12.53 / -0.73 / no | 73.50 / -0.60 / no | 134.62 / -0.66 / no |
| 130 | 12.07 / -0.72 / no | 87.62 / -0.63 / no | 167.21 / -0.70 / no |
| 140 | 11.64 / -0.70 / no | 106.59 / -0.66 / no | 198.41 / -0.73 / no |
| 150 | 11.25 / -0.68 / no | 136.24 / -0.69 / no | 227.73 / -0.76 / no |
| 160 | 10.90 / -0.66 / no | 169.76 / -0.72 / no | 254.76 / -0.79 / no |
| 170 | 10.59 / -0.65 / no | 202.08 / -0.75 / no | 278.53 / -0.82 / no |
| 180 | 10.34 / -0.63 / no | 231.96 / -0.78 / no | 298.31 / -0.84 / no |
| 190 | 10.11 / -0.61 / no | 257.77 / -0.80 / no | 313.40 / -0.86 / no |
| 200 | 9.90 / -0.59 / no | 279.60 / -0.83 / no | 323.50 / -0.87 / no |
| 210 | 9.72 / -0.58 / no | 296.89 / -0.85 / no | 327.87 / -0.88 / no |
| 220 | 9.56 / -0.56 / no | 308.86 / -0.86 / no | 326.49 / -0.89 / no |
| 230 | 9.42 / -0.54 / no | 314.93 / -0.87 / no | 318.82 / -0.90 / no |
| 240 | 9.31 / -0.53 / no | 314.66 / -0.88 / no | 305.50 / -0.90 / no |
| 250 | 9.22 / -0.51 / no | 307.96 / -0.89 / no | 286.94 / -0.91 / no |
| 260 | 9.16 / -0.50 / no | 294.97 / -0.89 / no | 263.50 / -0.91 / no |
| 270 | 9.13 / -0.49 / no | 276.06 / -0.90 / no | 235.95 / -0.90 / no |
| 280 | 9.13 / -0.48 / no | 251.93 / -0.89 / no | 205.46 / -0.90 / no |
| 290 | 9.16 / -0.47 / no | 223.45 / -0.89 / no | 172.43 / -0.89 / no |
| 300 | 9.22 / -0.46 / no | 191.57 / -0.89 / no | 137.88 / -0.88 / no |

## Healthy-LQR aggressiveness (spin-up at the flight thrust, nominal start)

| α | Largest grid τ with every smaller τ SAFE |
|---|---|
| 0.3 | 20 ms |
| 1.0 | 20 ms |
| 3.0 | 20 ms |

At τ = 0 with the flight thrust the vehicle first climbs 0.40 m and loses 0.03 m below its starting height (transient), qualitatively like Fig. 4 of the paper, where it climbs about 0.9 m. The steady height offset seen in flight comes from thrust loss while spinning, which the nominal model does not contain.
