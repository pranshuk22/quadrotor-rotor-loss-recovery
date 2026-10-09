# E1: Relaxed-hover equilibrium (rotor 4 lost, rho = f2/f1 = 0.5)

Vehicle: Mueller & D'Andrea ICRA 2014, Sec. V-A parameters.

| Quantity | Ours | Paper | Rel. diff |
|---|---|---|---|
| f1 = f3 (N) | 2.040 | 2.050 | -0.5% |
| f2 (N) | 1.020 | 1.020 | +0.0% |
| p (rad/s) | 0.000 | 0.000 | n/a |
| q (rad/s) | 5.366 | 5.690 | -5.7% |
| r (rad/s) | 18.808 | 18.890 | -0.4% |
| n_y | 0.274 | 0.289 | -5.1% |
| n_z | 0.962 | 0.958 | +0.4% |
| orbit radius (mm) | 7.317 | 8.000 | -8.5% |

**Inertia-rounding sensitivity.** The paper gives I_xx^T = 3.2e-3 and I_zz^T = 5.5e-3 (2 significant figures). Perturbing each by ±0.05e-3 moves q from 5.07 to 5.69 rad/s and n_y from 0.261 to 0.289; the published q = 5.69, n_y = 0.289 are reached only at the edge of this band. However, the paper's two-rotor and single-rotor equilibria are reproduced to every published digit with the stated parameters (see results/tables/validation_report.md), and the published one-rotor values leave a residual in the paper's own eq. (12). The more likely explanation is an inconsistency in that one published case, not a model error. f, r and n_z do not depend on it.

**Rho sweep vs. paper Fig. 3 text.**
- Minimum |w|: ours 18.62 rad/s at rho = 0.675; paper 19.0 rad/s at rho = 0.655.
- Minimum f1: ours 2.029 N at rho = 0.579; paper 2.04 N at rho = 0.563.
Values agree within 2%; the minimizer locations differ by about 3% (both minima are shallow).
