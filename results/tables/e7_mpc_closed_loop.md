# E7 (RQ1, first version): closed-loop MPC comparison on the mismatched truth plant

All controllers are designed on the nominal parameters; the plant is truth family A (the family the residual was trained on) or B (held out). MPC: horizon 20 × 5 ms, DARE terminal cost, thrust limits, OSQP. The residual is evaluated outside the QP and held constant over the horizon (measured disturbance), so the QP stays convex.

## Part 1: regulation (8 random starts near the relaxed hover, 1 m below the set-point, 8 s)

| Controller | Truth | Steady altitude error (m), mean ± sd | Altitude RMS (m) | Upright & finite | QP time (ms, median) |
|---|---|---|---|---|---|
| LQR | A | -0.285 ± 0.000 | 0.397 | 8/8 | 0.00 |
| MPC, analytical | A | -0.286 ± 0.000 | 0.398 | 8/8 | 4.77 |
| MPC, residual Koopman | A | -0.194 ± 0.000 | 0.340 | 8/8 | 4.85 |
| LQR | B | -0.029 ± 0.000 | 0.273 | 8/8 | 0.00 |
| MPC, analytical | B | -0.033 ± 0.000 | 0.275 | 8/8 | 5.12 |
| MPC, residual Koopman | B | +0.022 ± 0.000 | 0.265 | 8/8 | 4.28 |

## Part 2: capture controller after a detection delay (truth family A, hover start)

Hover → rotor 4 fails → healthy LQR for τ → M&D two-rotor spin-up → capture controller. 'Settled' = n_z steady (spread < 0.05) and > 0.8 over the last 2 s.

| τ (ms) | LQR: alt. loss (m) / min n_z / settled | MPC, analytical: alt. loss (m) / min n_z / settled | MPC, residual Koopman: alt. loss (m) / min n_z / settled |
|---|---|---|---|
| 0 | 0.84 / 0.46 / yes | 1.36 / 0.28 / yes | 1.24 / 0.32 / yes |
| 10 | 2.28 / 0.48 / yes | 4.49 / 0.06 / yes | 4.15 / 0.12 / yes |
| 20 | 5.75 / 0.23 / yes | 10.71 / -0.16 / yes | 10.49 / -0.09 / yes |
| 30 | 16.25 / -0.01 / yes | 20.55 / -0.34 / yes | 20.64 / -0.28 / yes |
| 40 | 41.03 / -0.21 / yes | 32.87 / -0.45 / no | 32.83 / -0.41 / no |
| 60 | 147.91 / -0.46 / yes | 167.60 / -0.63 / no | 131.51 / -0.60 / no |
