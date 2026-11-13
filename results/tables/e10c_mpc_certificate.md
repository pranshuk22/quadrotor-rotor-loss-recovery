# E10c: Certificate for the residual Koopman MPC loop

The unconstrained finite-horizon MPC with DARE terminal cost is a linear law u = -K s + G d in the 10-state measurement s = (x7, f_est) and the (clipped) residual d (`rotorfail/mpc_cert.py`; checked against the QP). Settings fixed in the docstring of `experiments/e10c_mpc_certificate.py`.

Closed-loop spectral radius of A - B K: 0.9946. Learned-term bound d_max (99.5 % percentile, 7 states): 0.1006, 0.0409, 0.0056, 0.0007, 0.0007, 0.0000, 0.0049.

## Unconstrained region and inscribed ellipsoid

Solver status optimal; semi-axes (sqrt Q_ii): p 0.459, q 2.110, r 0.960, n_x 0.049, n_y 0.051, z 0.367, v_z 0.501, f1 1.760, f2 0.820, f3 1.760.

Verification (scaled, numpy): worst eigenvalue of A_cl Q A_cl' - 0.995 Q = -7.42e-06; smallest face margin b^2 - h'Qh = -1.1e-11; min eig Q = 5.34e-03. Cross-check: log det Q Clarabel -3.75160 versus SCS 0.19464.

## Mismatch margin (triangle inequality in the P-norm)

Contraction margin 1 - sqrt(lam) = 0.0025. Learned-term contribution Delta_dhat at d_max = 1.7137. Largest uniform one-step mismatch delta* the ellipsoid tolerates: 0.00e+00 per physical state (0 means the learned term alone already exceeds the margin).

## Empirical mismatch and falsification

1000 runs from physical starts (500 on the boundary, 500 interior; 0 sampled points were not physical and skipped), each on its own plant of `random_family`, 3 s with the actual residual MPC. Mismatch per step while the state is inside the ellipsoid (1907 steps):

| State | p | q | r | n_x | n_y | z | v_z |
|---|---|---|---|---|---|---|---|
| max abs mismatch (empirical bound delta_emp) | 1.23e-01 | 6.94e-02 | 6.00e-03 | 1.70e-04 | 3.00e-04 | 1.14e-05 | 4.52e-03 |
| 99.9th percentile | 1.21e-01 | 6.81e-02 | 5.73e-03 | 1.63e-04 | 2.95e-04 | 1.09e-05 | 4.29e-03 |

Largest tolerated uniform mismatch delta* = 0.00e+00; empirical maximum over components 1.23e-01. With delta_emp the left side of the invariance condition is sqrt(lam) + Delta_dhat + sum w_i delta_i = 4.340 against 1: NOT satisfied, so no certificate; the ellipsoid would have to be about 1335 times larger.

Runs in which V(s) exceeded 1.001 at some step: 1000 of 1000 (500 of 500 boundary starts). Maximum V over all runs: 60.22. Runs that ended inverted or not completed: 0.

## Use as capture set in D6: centre of the hand-over set (published chain, exact hover)

| tau (ms) | alpha_c (centre scaling onto the boundary; < 1 means outside) |
|---|---|
| 0 | 0.0258 |
| 5 | 0.0223 |
| 10 | 0.0200 |
| 15 | 0.0185 |
| 20 | 0.0174 |
| 25 | 0.0166 |
| 30 | 0.0161 |
| 35 | 0.0158 |
| 40 | 0.0156 |
| 45 | 0.0155 |
| 50 | 0.0154 |
| 55 | 0.0154 |
| 60 | 0.0154 |
| 80 | 0.0157 |
| 100 | 0.0162 |
| 130 | 0.0175 |
