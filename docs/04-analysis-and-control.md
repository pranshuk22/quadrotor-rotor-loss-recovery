# 4. Analysis, Control and Certification Methods

Code: `rotorfail/analysis.py`, `rotorfail/control.py`, `rotorfail/metrics.py` (and, exploratory, `rotorfail/certify.py`).

## 4.1 Structural analysis (`analysis.py`)
- **Controllability matrix** `ctrb(A, B)` = [B, AB, …, Aⁿ⁻¹B]. `scaled_rank` normalizes the columns before the SVD, because the Krylov blocks differ by orders of magnitude.
- **PBH test** `pbh_controllability`: for each eigenvalue λ, the smallest singular value of [λI − A, B̃] (B scaled to ‖A‖). Near zero means an uncontrollable mode. `pbh_observability` is the dual.
- **Finite-horizon Gramian** `finite_gramian(A, B, T)` = ∫₀ᵀ e^{As} B Bᵀ e^{Aᵀs} ds, computed with Van Loan's matrix exponential. It works for unstable or marginal A. The observability Gramian uses (Aᵀ, Cᵀ).
- **Input-delay margin** `delay_margin(A, B, K)`: the largest pure delay h such that ẋ = Ax − BKx(t − h) stays stable. It uses an exact ZOH discretization at 1 ms with an h/dt-step delay line, and bisection on h.

Results (E2, `results/tables/e2_structure.md`): both models are controllable (rank, PBH, Gramian). Observability of the failed model by sensor set:

| Sensors | Rank | Unobservable | λ_min W_o(1 s), noise-normalized |
|---|---|---|---|
| Gyro | 3/7 | n_x, n_y, z, v_z | 0 |
| Gyro + tilt estimate | 5/7 | z, v_z | 0 |
| Gyro + barometer | 7/7 | none | 2.4e-3 |
| Gyro + tilt + barometer | 7/7 | none | 6.6 |

Each output is divided by an assumed sensor noise level (gyro 0.005 rad/s, tilt estimate 0.01, barometer 0.1 m) before the Gramian is computed. Gyro + barometer is observable only because the relaxed hover is tilted (∂v̇_z/∂n_y ≠ 0), and for these noise levels it is ~2,700× weaker than with a tilt measurement. This is a structural remark, not an estimator design.

## 4.2 Controllers (`control.py`)

**HealthyLQR.** 12-state hover model, Bryson weights (0.5 m, 1 m/s, 0.2 rad (ψ: 0.5 rad), 2 rad/s; 0.5 N per rotor); `alpha` scales all state weights (aggressiveness). Feedback uses Euler angles from the quaternion; the yaw error is wrapped. Commands are clipped to [f_min, f_max].

**FailureLQR.** 7-state reduced-attitude/altitude model plus 3 motor states (10 states), with the weights of Mueller & D'Andrea (1 on p, q; 20 on n_x, n_y; 0 on r and the motor states; 1 N⁻² on inputs) plus 4 on z and 1 on v_z. Motor states are not measured. They are reconstructed by an internal first-order filter of the controller's own clipped commands (`f_est`). `reset(f_now)` initializes the filter at a switch.

**SpinUpThenLQR.** The flight strategy of Mueller & D'Andrea: after detection, fly on rotors 1 and 3 (`f_spin` each, rotor 2 stopped) until ‖ω‖ > 10 rad/s, then switch to the LQR. The default `f_spin` = 2.95 N is read from the flight data (ICRA Fig. 4); mg/2 = 2.45 N is used as a sensitivity case.

**DelaySupervisor.** Rotor 4 fails at t_fail. Until t_fail + τ the healthy controller runs (its rotor-4 command is lost); afterwards the failure-mode controller runs. At the switch it is reset with the supervisor's own filter of the healthy commands, not with the true motor thrust, which the controller cannot measure.

Results (E3): failure LQR slowest poles −1.09, −2.01 ± 1.04j, −3.80 ± 19.68j (the last is the least-damped mode, ζ ≈ 0.19); input-delay margin **18 ms** (healthy: 40 ms). Nonlinear settling: altitude 1.8 s, tilt 2.1 s, yaw rate 2.5 s. A design without motor states is still stable with the real 15 ms lag.

## 4.3 Success criterion (`metrics.py`, fixed before the sweeps)
- **Captured:** over the last 1 s, ‖n − n̄‖ < 0.05 and ‖ω − ω̄‖ < 2 rad/s.
- **Safe:** captured, altitude loss < 2 m, and never inverted (n_z > 0 throughout).
- Altitude loss = z(t_fail) − min z(t ≥ t_fail).

## 4.4 Undetected-phase bound
Near hover the body rates are small, so the gyroscopic terms vanish and I^B_xx ṗ = l(f₂ − f₄) = l f₂. A running motor cannot go below f_min, so ṗ ≥ l f_min / I^B_xx = 10.6 rad/s² for any healthy-controller tuning. A pure-acceleration lower bound on the tilt is therefore ½ (l f_min / I_xx) t².

## 4.5 Exploratory: saturation-aware certificates (`certify.py`, not in the submission)
The first certificate (E5) closes the loop of the failure LQR with a thrust saturation and asks for the largest invariant ellipsoid of the linear loop (Hu & Lin 2001: LMIs over the 2^m saturation patterns, solved with CVXPY/Clarabel with an SCS fallback). It covers 22 % of the way from the equilibrium to the state right after a failure; nonlinear simulation recovers without inversion up to 70 %. Later extensions (quasi-LPV over a range of spin rates, gain synthesis, reachable sets, a certificate for the residual-MPC loop) did not give a certified delay budget; see "Exploratory work not in the submission" in the root README. They are not part of the report.
