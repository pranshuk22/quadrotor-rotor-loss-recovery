# 6. Experiments

Each experiment is one script in `experiments/`. It writes a markdown table to `results/tables/` and figures to `results/figures/`. Seeds are fixed. Runtimes are on an 8-core laptop.

| ID | Script | Question | Outputs | Runtime |
|---|---|---|---|---|
| V0 | `v0_validation_report.py` | Does the model match published numbers and flight data? | `validation_report.md` | seconds |
| E1 | `e1_equilibrium.py` | Relaxed-hover equilibrium vs the paper; ρ sweep | `e1_equilibrium.md`, `e1_rho_sweep.png` | seconds |
| E2 | `e2_structure.py` | Eigenvalues, controllability (rank, PBH, Gramian), observability by sensor set | `e2_structure.md` | seconds |
| E3 | `e3_lqr.py` | LQR designs: poles, delay margins, nonlinear check | `e3_lqr.md`, `e3_*_lqr_nonlinear.png` | ~15 s |
| E4 | `e4_delay_sweep.py` | Effect of detection delay τ on recovery (RQ2, empirical) | `e4_delay_sweep.md/.csv`, `e4_delay_sweep.png`, `e4_time_histories.png`, `e4_undetected_phase.png` | ~5 min (`--plot-only` redraws from the CSV) |
| E5 | `e5_first_certificate.py` | First saturation-aware LMI certificate; conservatism vs simulation | `e5_first_certificate.md`, `e5_certificate_slice.png` | ~8 min |
| E6 | `e6_koopman_prediction.py` | Analytical vs full-state vs residual EDMDc prediction (RQ1) | `e6_koopman_prediction.md`, `e6_multistep_error.png`, `e6_data_efficiency.png`, `e6_full_edmdc_eigs.png` | ~2.5 min |
| E7 | `e7_mpc_closed_loop.py` | LQR vs analytical MPC vs residual-Koopman MPC in closed loop (RQ1) | `e7_mpc_closed_loop.md`, `e7_altitude.png` | ~3 min |

## E1: Equilibrium
- Set-up: nominal parameters, ρ = 0.5; sensitivity to ±0.05e-3 in the inertias; ρ sweep 0.02–1.6 with continuation.
- Result: f, r, n_z within 0.5% of the paper; q and n_y −6% (paper inconsistency, see `03-validation.md`); Fig. 3 minima within 2–3%.

## E2: Structure
- Set-up: healthy (12-state) and failed (7-state) linear models; sensor sets S1–S4 (healthy) and F1–F4 (failed).
- Result: both controllable; gyro + position leaves ψ unobservable (healthy); gyro + barometer makes the failed model observable, but weakly.

## E3: LQR
- Set-up: healthy LQR (Bryson), failure LQR with and without motor states; delay margin via the delay-line method; nonlinear runs from perturbed starts.
- Result: failure LQR delay margin 18 ms (healthy 40 ms); nonlinear convergence verified.

## E4: Detection delay (RQ2, empirical)
- Set-up: nominal plant; hover at z = 0; rotor 4 fails at t = 0; healthy LQR until τ; then strategy A (LQR directly) or B (spin-up on rotors 1, 3 until ‖ω‖ > 10 rad/s, then LQR). τ = 0–300 ms in 10 ms steps; healthy aggressiveness α ∈ {0.3, 1, 3}; Monte Carlo of 20 random pre-failure states (σ_v = 0.3 m/s, σ_angle = 3°, σ_ω = 0.3 rad/s) at τ ∈ {0, 10, 20, 30, 50, 80} ms. Runs are 10 s.
- Result: B is SAFE 20/20 at 0 ms, 17/20 at 10, 6/20 at 20, 1/20 at 30, 0/20 at 50 ms (τ\*_emp ≈ 10 ms for all α). A captures the attitude but always inverts (10–16 m altitude loss).

## E5: First certificate
- Set-up: 10-state failure LQR; Hu–Lin LMIs with decay rates 0–0.5 s⁻¹ and motor-state box; β along the hover-onset direction; nonlinear runs at β = 0.1–1.0; 21 × 21 grid on (Δr, Δn_y).
- Result: β = 0.22 certified vs 0.7 recovered without inversion; 376/441 grid points recover, of which 7% are certified.

## E6: Koopman prediction (RQ1)
- Set-up: 40 × 4 s training episodes on family A (seed 11); tests: 10 episodes of A (seed 12) and B (seed 13); randomized training (seed 21); data-efficiency sweep 2–40 episodes.
- Result: see `05-koopman-and-mpc.md`.

## E7: MPC closed loop (RQ1)
- Set-up: residual trained on the E6 family-A data; part 1: 8 random starts 1 m below the set-point, 8 s, families A and B; part 2: capture after delay τ ∈ {0, 10, 20, 30, 40, 60} ms on family A.
- Result: residual-Koopman MPC −32% steady altitude error on A; no gain as a capture controller.

## Known comparability issues
- E4 uses the nominal plant; E7 part 2 uses truth family A. Absolute delay numbers differ between them.
- E4 delay results depend on spin-up speed, which the model under-predicts relative to flight (`03-validation.md`).
