# 3. Validation

Two layers: **automated tests** (pass/fail, 45 tests, ~20 s) and a **validation report** comparing with published numbers (`results/tables/validation_report.md`, produced by `experiments/v0_validation_report.py`).

## 3.1 Physics tests (`tests/test_physics.py`, 13 tests)
Each test compares the simulator with a hand-derived result, never with another run of the same code.

| Test | Reference solution |
|---|---|
| Free fall | z(t) = z₀ + v_z0 t − g t²/2, horizontal motion uniform (to 1e-9) |
| Thrust direction | d̈ = R e₃ f_Σ/m − g e₃ with R built by hand from Euler angles |
| Hover balance | all derivatives zero at f_i = mg/4 |
| Torque-free precession | r constant; (p, q) rotate at λ = (I^T_zz − I^T_xx) r / I^B_xx (closed form, 1e-8) |
| Angular momentum and energy | R I ω and ½ωᵀIω conserved for a torque-free rigid body (rel. 1e-8) |
| Reduced-attitude kinematics | n(t) = expm(−[ω]× t) n(0) for constant ω |
| Yaw spin-up | rotors 1, 3 only: r(t) = r_ss (1 − e^{−γt/I_zz}), p = q = 0 |
| RK4 order | error ratio 12–20 when dt is halved (theory: 16) |
| Motor lag | f(t) = f_c + (f₀ − f_c) e^{−t/σ} |
| Saturation rules | command ≤ 0 → 0; clip to [f_min, f_max]; failed rotor → 0 |
| Paper eqs. (12)–(14) | independent transcription with signed propeller speeds = simulator (50 random states) |
| IJRR model reduces to simulator | independent general-model code with its extra effects off = simulator (50 random states) |
| Relaxed-hover CoM acceleration | vertical 0; horizontal g·√(1 − n_z²)/n_z |

## 3.2 Published-number tests (`tests/test_paper_validation.py`, 19 tests)

| Source | Check | Our value | Published | Status |
|---|---|---|---|---|
| ICRA 2014 eqs. (57)–(59) | Two rotors lost: f₁, ω₁, r | 2.453 N, −618.6, 30.14 | 2.45, −619, 30.1 | ✅ ≤ 0.14% |
| ICRA 2014 eqs. (62)–(64) | Three rotors lost: f₁, ω₁, ω, n | 5.369, −915.2, (14.68, 0, 32.99), (0.407, 0, 0.914) | 5.37, −915, (14.7, 0, 33.0), (0.41, 0, 0.91) | ✅ ≤ 0.8% |
| ICRA 2014 eqs. (50)–(53) | One rotor lost, ρ = 0.5: f, r, n_z | 2.040/1.020, 18.81, 0.962 | 2.05/1.02, 18.89, 0.958 | ✅ ≤ 0.5% |
| | q, n_y | 5.37, 0.274 | 5.69, 0.289 | ⚠️ −6%: see 3.3 |
| ICRA 2014 Fig. 3 | min ‖ω‖, min f₁ over ρ | 18.6 rad/s, 2.029 N | 19.0, 2.04 | ✅ ≤ 2% |
| ICRA 2014 eq. (21) | r̄ formula | exact | — | ✅ |
| ICRA 2014 eq. (28) | ā = Jacobian entry A[p, q] | exact | — | ✅ |
| ICRA 2014 eqs. (37)–(39) | Controllability rank 7 → 6 (p uncontrollable) exactly when ā = 0 | yes | — | ✅ |
| IJRR 2016 (31)–(50) | 5 hover solutions, published parameters | 0–4% | — | ✅ |
| | same, I_xx = 2.75e-3 (inside rounding of 2.7e-3) | ≤ 0.7% in ω, ≤ 0.6% in force | — | ✅ |
| | Two-rotor speed 643 rad/s explained by air-relative thrust | κ_f (643 − 24.5)² = mg/2 | — | ✅ |
| Sun et al. T-RO 2020, eq. (60) | Bebop 2, two rotors lost: r̄, ω̄ | 26.81, 1029 (= the formula) | text: 26.4, 1015 | ✅ (the paper's text is 1.5% below its own formula) |

## 3.3 Discussion of the gaps
- **ICRA one-rotor q̄.** Substituting the paper's published one-rotor values into its own eq. (12) leaves a roll-torque residual of −0.011 N·m (7% of the rotor-2 torque). The paper's other two equilibria match exactly with the same parameters, so we treat this as an inconsistency in that one published case.
- **IJRR high-rate cases (adjacent pair, three rotors).** With published parameters they are 4% off. The drag and inertia are published to 1–2 significant figures, and one inertia value inside the rounding brings all five cases within 0.7%.

## 3.4 Against flight data (a real limitation)

| Quantity | Our model | Paper's model | Flight |
|---|---|---|---|
| Time to ‖ω‖ > 10 rad/s on two rotors (ICRA Fig. 4) | 0.81 s (closed form 0.80 s) | not reported | 0.62 s |
| Spin rate about n, one rotor lost (IJRR Sec. 5.3) | 19.6 rad/s (ρ = 0.5) | 19.9 rad/s | 15.8 rad/s |
| Height offset from thrust loss, two rotors (ICRA Sec. V-E) | not in nominal model | not in model | ≈ 2.4 m |

The nominal model spins up about 30% more slowly than the real vehicle. The E4 delay tolerance depends on spin-up speed, so it is reported "for the published model", and a sensitivity study is planned (task D7).

## 3.5 Other tests
- `tests/test_core.py` (9): equilibrium fixed points, Jacobians vs finite differences, LQR closed-loop stability, nonlinear recovery, and LMI certificate invariance (V decreases at 500 points on the ellipsoid boundary with true saturation).
- `tests/test_koopman_mpc.py` (4): nominal discrete model accuracy, residual reduces one-step error, EDMDc rollout shape and first step, MPC returns feasible thrusts.

Run everything: `.venv/bin/python -m pytest -q`.
