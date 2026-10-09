# E6 (RQ1): Koopman predictors in the failed regime

Training: 40 episodes × 4 s on truth family A (32000 samples at 5 ms). Test: 10 held-out episodes of family A and 10 of family B (unseen mismatch magnitudes).

Dictionary: constant + 9 standardized states/filtered inputs + all degree-2 monomials (lifted dimension 55). Ridge regression.

## H1: spectrum of the full-state EDMDc operator

Trained on family A: 4 of 55 eigenvalues have |λ| > 1; spectral radius 1.0070. Trained on randomized families: 3 of 55; spectral radius 1.0276.

## Multi-step open-loop prediction error (normalized RMSE, mean over the 7 states)

### Models trained on family A only

| Model, test set | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D), family A | 0.157 | 0.654 | 1.600 | 3.166 | 5.729 | 4.367 | 7.088 | 7.926 | 13.957 |
| Full-state EDMDc, family A | 0.014 | 0.040 | 0.080 | 0.171 | 0.246 | 0.477 | 0.912 | 3.454 | 14.113 |
| Residual EDMDc (proposed), family A | 0.016 | 0.098 | 0.111 | 0.152 | 0.209 | 0.322 | 0.641 | 2.714 | 6.226 |
| No-change baseline, family A | 0.164 | 0.813 | 1.875 | 2.415 | 2.438 | 2.268 | 2.379 | 2.509 | 2.555 |
| Analytical (M&D), family B (held out) | 0.222 | 0.884 | 2.173 | 4.312 | 7.579 | 5.157 | 7.940 | 6.950 | 10.288 |
| Full-state EDMDc, family B (held out) | 0.322 | 1.278 | 3.050 | 6.094 | 12.181 | 24.024 | 26.244 | 130.521 | 540.555 |
| Residual EDMDc (proposed), family B (held out) | 0.315 | 1.241 | 2.992 | 5.982 | 12.121 | 17.580 | 19.905 | 23.970 | 30.623 |
| No-change baseline, family B (held out) | 0.218 | 1.109 | 2.113 | 2.505 | 2.576 | 2.423 | 2.436 | 2.406 | 2.491 |

### Models trained on domain-randomized families (B outside the ranges)

| Model, test set | 5 ms | 20 ms | 50 ms | 100 ms | 200 ms | 500 ms | 1000 ms | 2000 ms | 3000 ms |
|---|---|---|---|---|---|---|---|---|---|
| Analytical (M&D), family A | 0.157 | 0.654 | 1.600 | 3.166 | 5.729 | 4.367 | 7.088 | 7.926 | 13.957 |
| Full-state EDMDc, family A | 0.111 | 0.483 | 1.310 | 2.938 | 8.193 | 48.006 | 748.837 | 129257.588 | 798147.509 |
| Residual EDMDc (proposed), family A | 0.101 | 0.403 | 1.038 | 2.355 | 6.028 | 11.239 | 15.651 | 22.397 | 27.331 |
| No-change baseline, family A | 0.164 | 0.813 | 1.875 | 2.415 | 2.438 | 2.268 | 2.379 | 2.509 | 2.555 |
| Analytical (M&D), family B (held out) | 0.222 | 0.884 | 2.173 | 4.312 | 7.579 | 5.157 | 7.940 | 6.950 | 10.288 |
| Full-state EDMDc, family B (held out) | 0.176 | 0.782 | 1.938 | 4.175 | 11.664 | 61.777 | 1101.970 | 151002.173 | 836062.996 |
| Residual EDMDc (proposed), family B (held out) | 0.174 | 0.739 | 1.767 | 3.684 | 8.462 | 14.805 | 18.296 | 28.242 | 37.398 |
| No-change baseline, family B (held out) | 0.218 | 1.109 | 2.113 | 2.505 | 2.576 | 2.423 | 2.436 | 2.406 | 2.491 |

Normalization: each state divided by its standard deviation in the training data.

## H4: data efficiency (error at 0.5 s horizon, family A test)

| Training episodes | 2 | 5 | 10 | 20 | 40 |
|---|---|---|---|---|---|
| Full-state EDMDc | 2.279 | 0.929 | 0.757 | 0.589 | 0.477 |
| Residual EDMDc (proposed) | 1.974 | 1.018 | 0.421 | 0.412 | 0.322 |
| Analytical (M&D), no data | 4.367 | 4.367 | 4.367 | 4.367 | 4.367 |
