# E6 (RQ1): Koopman predictors in the failed regime

Training: 40 episodes × 4 s on truth family A (32000 samples at 5 ms). Test: 10 held-out episodes of family A and 10 of family B (unseen mismatch magnitudes).

Dictionary: constant + 9 standardized states/filtered inputs + all degree-2 monomials (lifted dimension 55). Ridge regression.

## H1: spectrum of the full-state EDMDc operator

Trained on family A: 4 of 55 eigenvalues have |λ| > 1; spectral radius 1.0054. Trained on randomized families: 3 of 55; spectral radius 1.0193.

## Multi-step open-loop prediction error (normalized RMSE, mean over the 7 states)

### Models trained on family A only

| Model, test set | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D), family A | 0.114 | 0.469 | 1.161 | 2.285 | 4.012 | 3.215 | 5.126 | 7.301 | 13.577 |
| Full-state EDMDc, family A | 0.013 | 0.026 | 0.059 | 0.128 | 0.205 | 0.433 | 0.697 | 1.669 | 4.968 |
| Residual EDMDc (proposed), family A | 0.012 | 0.050 | 0.066 | 0.114 | 0.153 | 0.237 | 0.421 | 1.341 | 3.546 |
| No-change baseline, family A | 0.137 | 0.614 | 1.411 | 1.927 | 1.953 | 1.885 | 2.033 | 2.171 | 2.215 |
| Analytical (M&D), family B (held out) | 0.160 | 0.636 | 1.557 | 3.065 | 5.193 | 3.772 | 5.568 | 6.021 | 9.857 |
| Full-state EDMDc, family B (held out) | 0.230 | 0.910 | 2.180 | 4.370 | 8.485 | 14.940 | 12.254 | 48.050 | 147.841 |
| Residual EDMDc (proposed), family B (held out) | 0.226 | 0.895 | 2.168 | 4.390 | 8.788 | 12.678 | 11.806 | 16.150 | 8.664 |
| No-change baseline, family B (held out) | 0.165 | 0.786 | 1.560 | 1.951 | 2.019 | 1.905 | 1.926 | 1.924 | 2.031 |

### Models trained on domain-randomized families (B outside the ranges)

| Model, test set | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D), family A | 0.114 | 0.469 | 1.161 | 2.285 | 4.012 | 3.215 | 5.126 | 7.301 | 13.577 |
| Full-state EDMDc, family A | 0.076 | 0.317 | 0.842 | 1.837 | 4.394 | 11.922 | 77.521 | 3995.028 | 197927.908 |
| Residual EDMDc (proposed), family A | 0.075 | 0.299 | 0.778 | 1.730 | 4.033 | 7.695 | 7.915 | 9.877 | 12.214 |
| No-change baseline, family A | 0.137 | 0.614 | 1.411 | 1.927 | 1.953 | 1.885 | 2.033 | 2.171 | 2.215 |
| Analytical (M&D), family B (held out) | 0.160 | 0.636 | 1.557 | 3.065 | 5.193 | 3.772 | 5.568 | 6.021 | 9.857 |
| Full-state EDMDc, family B (held out) | 0.128 | 0.548 | 1.351 | 2.840 | 6.642 | 15.449 | 103.072 | 5472.155 | 255839.933 |
| Residual EDMDc (proposed), family B (held out) | 0.126 | 0.537 | 1.333 | 2.823 | 6.401 | 9.439 | 13.436 | 16.161 | 20.385 |
| No-change baseline, family B (held out) | 0.165 | 0.786 | 1.560 | 1.951 | 2.019 | 1.905 | 1.926 | 1.924 | 2.031 |

Normalization: each state divided by its standard deviation in the training data.

## H4: data efficiency (error at 0.5 s horizon, family A test)

| Training episodes | 2 | 5 | 10 | 20 | 40 |
|---|---|---|---|---|---|
| Full-state EDMDc | 1.240 | 0.678 | 0.595 | 0.469 | 0.433 |
| Residual EDMDc (proposed) | 1.411 | 0.639 | 0.323 | 0.287 | 0.237 |
| Analytical (M&D), no data | 3.215 | 3.215 | 3.215 | 3.215 | 3.215 |
