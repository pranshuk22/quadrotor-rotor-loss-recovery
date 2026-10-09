# 4. Analysis, Control and Certification Methods

Code: `rotorfail/analysis.py`, `rotorfail/control.py`, `rotorfail/certify.py`, `rotorfail/metrics.py`.

## 4.1 Structural analysis (`analysis.py`)
- **Controllability matrix** `ctrb(A, B)` = [B, AB, …, Aⁿ⁻¹B]. `scaled_rank` normalizes the columns before the SVD, because the Krylov blocks differ by orders of magnitude.
- **PBH test** `pbh_controllability`: for each eigenvalue λ, the smallest singular value of [λI − A, B̃] (B scaled to ‖A‖). Near zero means an uncontrollable mode. `pbh_observability` is the dual.
- **Finite-horizon Gramian** `finite_gramian(A, B, T)` = ∫₀ᵀ e^{As} B Bᵀ e^{Aᵀs} ds, computed with Van Loan's matrix exponential. It works for unstable or marginal A. The observability Gramian uses (Aᵀ, Cᵀ).
- **Input-delay margin** `delay_margin(A, B, K)`: the largest pure delay h such that ẋ = Ax − BKx(t − h) stays stable. It uses an exact ZOH discretization at 1 ms with an h/dt-step delay line, and bisection on h.

Results (E2, `results/tables/e2_structure.md`): both models are controllable (rank, PBH, Gramian). Observability of the failed model by sensor set:

| Sensors | Rank | Unobservable | λ_min W_o(1 s) |
|---|---|---|---|
| Gyro | 3/7 | n_x, n_y, z, v_z | 0 |
| Gyro + tilt estimate | 5/7 | z, v_z | 0 |
| Gyro + barometer | 7/7 | none | 2.4e-5 |
| Gyro + tilt + barometer | 7/7 | none | 6.6e-2 |

Gyro + barometer is observable only because the relaxed hover is tilted (∂v̇_z/∂n_y ≠ 0), and it is ~2,700× weaker than with a tilt measurement.

## 4.2 Controllers (`control.py`)

**HealthyLQR.** 12-state hover model, Bryson weights (0.5 m, 1 m/s, 0.2 rad (ψ: 0.5 rad), 2 rad/s; 0.5 N per rotor); `alpha` scales all state weights (aggressiveness). Feedback uses Euler angles from the quaternion; the yaw error is wrapped. Commands are clipped to [f_min, f_max].

**FailureLQR.** 7-state reduced-attitude/altitude model plus 3 motor states (10 states), with the weights of Mueller & D'Andrea (1 on p, q; 20 on n_x, n_y; 0 on r and the motor states; 1 N⁻² on inputs) plus 4 on z and 1 on v_z. Motor states are not measured. They are reconstructed by an internal first-order filter of the controller's own clipped commands (`f_est`). `reset(f_now)` initializes the filter at a switch.

**SpinUpThenLQR.** The flight strategy of Mueller & D'Andrea: after detection, fly on rotors 1 and 3 (f = mg/2 each, rotor 2 stopped) until ‖ω‖ > 10 rad/s, then switch to the LQR.

**DelaySupervisor.** Rotor 4 fails at t_fail. Until t_fail + τ the healthy controller runs (its rotor-4 command is lost); afterwards the failure-mode controller runs (`reset` at the switch).

Results (E3): failure LQR slowest poles −1.09, −2.01 ± 1.04j, −3.80 ± 19.68j; input-delay margin **18 ms** (healthy: 40 ms). A design without motor states is still stable with the real 15 ms lag.

## 4.3 Success criterion (`metrics.py`, fixed before the sweeps)
- **Captured:** over the last 1 s, ‖n − n̄‖ < 0.05 and ‖ω − ω̄‖ < 2 rad/s.
- **Safe:** captured, altitude loss < 2 m, and never inverted (n_z > 0 throughout).
- Altitude loss = z(t_fail) − min z(t ≥ t_fail).

## 4.4 Undetected-phase bound
Near hover the body rates are small, so the gyroscopic terms vanish and I^B_xx ṗ = l(f₂ − f₄) = l f₂. A running motor cannot go below f_min, so ṗ ≥ l f_min / I^B_xx = 10.6 rad/s² for any healthy-controller tuning. A pure-acceleration lower bound on the tilt is therefore ½ (l f_min / I_xx) t².

## 4.5 Saturation-aware certificate (`certify.py`)
Closed loop ẋ = Ax + B sat(Fx), F = −K, symmetric levels ū_i = min(f̄_i − f_min, f_max − f̄_i). The ellipsoid E = {x : xᵀQ⁻¹x ≤ 1} is contractively invariant if there is Y = HQ with (Hu & Lin 2001):

    AQ + QAᵀ + B(DFQ + D⁻Y) + (DFQ + D⁻Y)ᵀBᵀ + 2αQ ⪯ −εI   for every diagonal 0/1 matrix D (2^m vertices), D⁻ = I − D
    [ ū_i²  Y_i ; Y_iᵀ  Q ] ⪰ 0                               for each input i  (E inside the linear region of H)
    Q_ii ≤ b_i²                                              optional box (used: motor states within ū)

Objectives: maximize log det Q, or maximize β such that β·d ∈ E for a direction d (via [[t, dᵀ],[d, Q]] ⪰ 0, β = 1/√t). Solver: CVXPY with Clarabel, falling back to SCS.

Notes:
- Without the motor-state box the LMI is ill-conditioned. The open-loop linear model is only marginally stable, so a near-zero contraction margin certifies an almost unbounded, physically meaningless set.
- The certificate is for the **linear** saturated loop. The gap to the nonlinear system is measured by simulation (E5), not proven.

Results (E5): certified |Δr| ≤ 6.1 rad/s, |Δn_x| ≤ 0.41; β to hover onset = 0.22 (decay 0.1 s⁻¹); nonlinear simulation recovers without inversion up to β = 0.7.

## 4.6 Planned methods (not implemented yet)
- **LPV in r:** treat the yaw rate as a parameter in [r_onset, r̄ + δ]. A(r) is affine in r, so a common P checked at the vertices certifies the interval. The moving trim enters as a bounded disturbance.
- **Reachable set of the undetected phase:** affine LTI ẋ = A_f x + d from an ellipsoid X₀, giving R(τ) = e^{A_f τ}X₀ ⊕ {∫₀^τ e^{A_f s} d ds}.
- **Certified delay budget:** τ\* = sup{τ : M R(τ) ⊆ C}, with ellipsoid containment as an LMI (S-procedure) and bisection on τ.
