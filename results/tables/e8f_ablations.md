# E8f: Ablations

Settings fixed in the docstring of `experiments/e8f_ablations.py`. Errors are normalised RMSE (mean over the 7 states).

## 1. Dictionary degree (residual EDMDc, ridge 1e-3)

| Degree | dictionary size | cond(Gram) | test | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 13 | 1.7e+01 | A | 0.025 | 0.111 | 0.180 | 0.306 | 0.443 | 0.584 | 0.733 | 1.727 | 4.353 |
| 1 | 13 | 1.7e+01 | B | 0.302 | 1.207 | 2.950 | 5.983 | 11.768 | 16.080 | 16.749 | 24.302 | 23.920 |
| 2 | 91 | 2.3e+03 | A | 0.016 | 0.098 | 0.111 | 0.152 | 0.209 | 0.322 | 0.641 | 2.714 | 6.226 |
| 2 | 91 | 2.3e+03 | B | 0.315 | 1.241 | 2.992 | 5.982 | 12.121 | 17.580 | 19.905 | 23.970 | 30.623 |
| 3 | 455 | 1.6e+06 | A | 0.038 | 0.129 | 0.202 | 0.234 | 0.277 | 0.379 | 0.639 | 1.292 | 1.866 |
| 3 | 455 | 1.6e+06 | B | 0.317 | 1.166 | 2.513 | 4.612 | 8.652 | 6.063 | 6.049 | 5.586 | 5.940 |
| analytical | - | - | A | 0.157 | 0.654 | 1.600 | 3.166 | 5.729 | 4.367 | 7.088 | 7.926 | 13.957 |
| analytical | - | - | B | 0.222 | 0.884 | 2.173 | 4.312 | 7.579 | 5.157 | 7.940 | 6.950 | 10.288 |

## 2. Ridge parameter (chosen on the validation split by the mean error at 100, 200 and 400 ms)

| lambda | validation (mean) | test A: 100 ms / 500 ms / 1 s | test B: 100 ms / 500 ms / 1 s |
|---|---|---|---|
| 1e-06 | 1.657 | 0.322 / 0.641 / 2.714 | 17.580 / 19.905 / 23.970 |
| 0.0001 | 1.657 | 0.322 / 0.641 / 2.714 | 17.580 / 19.905 / 23.970 |
| 0.001 | 1.657 | 0.322 / 0.641 / 2.714 | 17.580 / 19.905 / 23.970 |
| 0.01 | 1.657 | 0.322 / 0.641 / 2.714 | 17.580 / 19.904 / 23.968 |
| 0.1 | 1.657 | 0.322 / 0.641 / 2.714 | 17.575 / 19.896 / 23.955 |

Chosen on validation: lambda = 0.1 (published: 1e-3).

## 3. Sampling period

| TS | test | 20 ms | 100 ms | 500 ms | 1000 ms |
|---|---|---|---|---|---|
| 2 ms | A, analytical | 0.651 | 3.190 | 4.285 | 7.000 |
| 2 ms | A, residual | 0.058 | 0.101 | 0.261 | 0.559 |
| 2 ms | B, analytical | 0.840 | 4.131 | 4.934 | 7.586 |
| 2 ms | B, residual | 1.132 | 5.641 | 14.668 | 15.096 |
| 5 ms | A, analytical | 0.652 | 3.258 | 4.436 | 7.203 |
| 5 ms | A, residual | 0.058 | 0.103 | 0.265 | 0.578 |
| 5 ms | B, analytical | 0.849 | 4.198 | 5.031 | 7.750 |
| 5 ms | B, residual | 1.158 | 5.788 | 17.465 | 19.111 |
| 10 ms | A, analytical | 0.641 | 3.167 | 4.337 | 6.980 |
| 10 ms | A, residual | 0.062 | 0.102 | 0.263 | 0.576 |
| 10 ms | B, analytical | 0.830 | 4.085 | 4.922 | 7.505 |
| 10 ms | B, residual | 1.128 | 5.595 | 19.828 | 21.831 |

Closed loop (steady altitude error, E7 Part 1 protocol, controller period = TS, horizon 0.1 s):

| TS | plant | LQR | MPC analytical | MPC residual |
|---|---|---|---|---|
| 2 ms | A (full) | -0.285 m | -0.285 m | -0.191 m |
| 2 ms | B without thrust loss | +0.112 m | +0.111 m | +0.170 m |
| 5 ms | A (full) | -0.285 m | -0.286 m | -0.193 m |
| 5 ms | B without thrust loss | +0.112 m | +0.111 m | +0.164 m |
| 10 ms | A (full) | -0.285 m | -0.287 m | -0.196 m |
| 10 ms | B without thrust loss | +0.112 m | +0.110 m | +0.162 m |

## 4. Sensor noise

Prediction on noisy test episodes (normalised RMSE):

| Model | test | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| Residual, clean-trained | A noisy | 0.292 | 0.333 | 0.317 | 0.334 | 0.380 | 0.464 | 0.879 | 3.301 | 7.065 |
| Residual, clean-trained | B noisy | 0.436 | 1.283 | 3.012 | 5.987 | 12.118 | 17.589 | 19.924 | 23.928 | 30.624 |
| Residual, noise-trained | A noisy | 0.298 | 0.491 | 0.924 | 2.023 | 5.907 | 15.279 | 35.858 | 94.836 | 175.599 |
| Residual, noise-trained | B noisy | 0.456 | 1.279 | 2.603 | 4.568 | 11.802 | 39.427 | 84.693 | 244.320 | 498.454 |
| Analytical (M&D) | A noisy | 0.320 | 0.718 | 1.608 | 3.182 | 5.750 | 4.382 | 7.083 | 7.918 | 13.932 |
| Analytical (M&D) | B noisy | 0.373 | 0.940 | 2.199 | 4.315 | 7.575 | 5.161 | 7.945 | 6.949 | 10.258 |

Closed loop with noisy controller inputs (steady altitude error, E7 Part 1 protocol):

| Plant | LQR | MPC analytical | MPC residual (clean-trained) | MPC residual (noise-trained) | Offset-free MPC (state d) |
|---|---|---|---|---|---|
| A (full) | -0.286 m | -0.286 m | -0.192 m | +2.813 m | -0.003 m |
| B (full, held out) | -0.030 m | -0.033 m | +0.024 m | +2.710 m | -0.002 m |
| nominal + A's thrust loss only | -0.101 m | -0.101 m | -0.031 m | +2.792 m | -0.002 m |
