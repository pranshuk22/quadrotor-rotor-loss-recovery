# E8g: Truth plants with air-relative thrust and quadratic drag (A+, B+)

Training: 40 episodes of 4 s on A+ (seed 111). Test: 10 episodes of A+ (seed 112) and of B+ (seed 113). Settings fixed in the docstring of `experiments/e8g_realistic_plant.py`.

Full-state EDMDc trained on A+: 4 of 55 eigenvalues outside the unit circle, spectral radius 1.0049.

## Multi-step prediction error on A+ (normalised RMSE)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.203 | 0.826 | 2.073 | 4.212 | 7.818 | 6.304 | 10.899 | 12.190 | 20.990 |
| Full-state EDMDc (A+) | 0.018 | 0.045 | 0.104 | 0.199 | 0.257 | 0.412 | 0.677 | 1.749 | 4.562 |
| Residual EDMDc (A+) | 0.017 | 0.067 | 0.101 | 0.180 | 0.255 | 0.350 | 0.565 | 1.709 | 4.210 |
| Residual EDMDc (trained on A, E6) | 0.048 | 0.191 | 0.446 | 0.911 | 1.902 | 4.537 | 2.067 | 7.064 | 11.314 |

## Multi-step prediction error on B+ (held out) (normalised RMSE)

| Model | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D) | 0.173 | 0.690 | 1.690 | 3.342 | 5.905 | 4.053 | 6.321 | 7.684 | 14.105 |
| Full-state EDMDc (A+) | 0.317 | 1.259 | 3.013 | 5.978 | 11.971 | 24.049 | 14.950 | 53.919 | 156.339 |
| Residual EDMDc (A+) | 0.311 | 1.236 | 2.977 | 5.867 | 11.860 | 18.449 | 15.241 | 21.581 | 8.181 |
| Residual EDMDc (trained on A, E6) | 0.264 | 1.053 | 2.546 | 5.068 | 10.473 | 15.960 | 17.197 | 22.784 | 20.578 |

## Steady altitude bias (E7 Part 1 protocol; mean altitude over the last 2 s; 'diverged' if the run ended inverted or non-finite)

| Plant | LQR | MPC, analytical | MPC, residual (A+) | Offset-free MPC (state d) | LQR + integrator |
|---|---|---|---|---|---|
| A+ (full) | -0.412 m | -0.414 m | -0.273 m | -0.000 m | -0.004 m |
| A+ without thrust loss | -0.281 m | -0.282 m | -0.147 m | -0.000 m | +0.003 m |
| nominal + effects only | -0.117 m | -0.118 m | -0.006 m | -0.000 m | +0.012 m |
| B+ (full, held out) | -0.145 m | -0.150 m | -0.050 m | -0.000 m | +0.009 m |
| B+ without thrust loss | +0.009 m | +0.008 m | +0.102 m | -0.000 m | +0.018 m |
