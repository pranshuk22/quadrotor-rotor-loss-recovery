# 6. Experiments

Each experiment is one script in `experiments/`. It writes a markdown table to `results/tables/` and figures to `results/figures/`. Seeds are fixed. Runtimes are on an 8-core laptop.

| ID | Script | Question | Outputs | Runtime |
|---|---|---|---|---|
| V0 | `v0_validation_report.py` | Does the model match published numbers and flight data? | `validation_report.md` | seconds |
| E1 | `e1_equilibrium.py` | Relaxed-hover equilibrium vs the paper; ρ sweep | `e1_equilibrium.md`, `e1_rho_sweep.png` | seconds |
| E2 | `e2_structure.py` | Eigenvalues, controllability (rank, PBH, Gramian), observability by sensor set | `e2_structure.md` | seconds |
| E3 | `e3_lqr.py` | LQR designs: poles, delay margins, nonlinear check | `e3_lqr.md`, `e3_*_lqr_nonlinear.png` | ~15 s |
| E4 | `e4_delay_sweep.py` | Effect of detection delay τ on recovery (empirical) | `e4_delay_sweep.md/.csv`, `e4_p_safe.png`, `e4_delay_sweep.png`, `e4_time_histories.png`, `e4_undetected_phase.png` | several minutes (`--plot-only` redraws from the CSV) |
| E5 | `e5_first_certificate.py` | First saturation-aware LMI certificate; conservatism vs simulation | `e5_first_certificate.md`, `e5_certificate_slice.png` | ~8 min |
| E6 | `e6_koopman_prediction.py` | Analytical vs full-state vs residual EDMDc prediction | `e6_koopman_prediction.md`, `e6_multistep_error.png`, `e6_data_efficiency.png`, `e6_full_edmdc_eigs.png` | ~2.5 min |
| E7 | `e7_mpc_closed_loop.py` | LQR vs analytical MPC vs residual-Koopman MPC in closed loop | `e7_mpc_closed_loop.md`, `e7_altitude.png` | ~3 min |

## E1: Equilibrium
- Set-up: nominal parameters, ρ = 0.5; sensitivity to ±0.05e-3 in the inertias; ρ sweep 0.02–1.6 with continuation.
- Result: f, r, n_z within 0.5% of the paper; q and n_y −6% (paper inconsistency, see `03-validation.md`); Fig. 3 minima within 2–3%.

## E2: Structure
- Set-up: healthy (12-state) and failed (7-state) linear models; sensor sets S1–S4 (healthy) and F1–F4 (failed).
- Result: both controllable; gyro + position leaves ψ unobservable (healthy); gyro + barometer makes the failed model observable, but weakly.

## E3: LQR
- Set-up: healthy LQR (Bryson), failure LQR with and without motor states; delay margin via the delay-line method; nonlinear runs from perturbed starts.
- Result: failure LQR delay margin 18 ms (healthy 40 ms); on the nonlinear model the altitude settles in 1.8 s, the tilt in 2.1 s and the yaw rate in 2.5 s; the least-damped mode is −3.80 ± 19.68j (ζ ≈ 0.19).

## E4: Detection delay (empirical)
- Set-up: nominal plant; hover at z = 0; rotor 4 fails at t = 0; healthy LQR until τ; then the LQR directly, or spin-up on rotors 1 and 3 until ‖ω‖ > 10 rad/s followed by the LQR. Spin-up thrust 2.95 N per rotor (flight value, ICRA Fig. 4) and 2.45 N = mg/2 (sensitivity case). Nominal-start sweep τ = 0–300 ms in 10 ms steps; healthy aggressiveness α ∈ {0.3, 1, 3}. Monte Carlo: 40 random pre-failure states (σ_v = 0.3 m/s, σ_angle = 3°, σ_ω = 0.3 rad/s) at τ = 0–60 ms in 5 ms steps, P(SAFE) with 95% Wilson intervals. Runs are 10 s; SAFE is defined in `rotorfail/metrics.py`.
- Result: with the flight thrust, P(SAFE) falls below 0.9 at 12 ms and below 0.5 at 19 ms (7 and 14 ms at mg/2); for attitude capture alone, the 50% point is 52 ms (40 ms at mg/2). From the exact hover start, every τ ≤ 20 ms is SAFE for all three α. With no delay the vehicle climbs 0.40 m and drops 0.03 m below its start. The LQR directly captures the attitude but always inverts (9–16 m altitude loss).

## E5: First certificate
- Set-up: 10-state failure LQR; Hu–Lin LMIs with decay rates 0–0.5 s⁻¹ and motor-state box; β along the hover-onset direction; nonlinear runs at β = 0.1–1.0; 21 × 21 grid on (Δr, Δn_y).
- Result: β = 0.22 certified vs 0.7 recovered without inversion; 376/441 grid points recover, of which 7% are certified. All failures lie at spin rates r ≤ 4.8 rad/s; none at r ≥ 6.8 rad/s.

## E6: Koopman prediction
- Set-up: 40 × 4 s training episodes on family A (seed 11); tests: 10 episodes of A (seed 12) and B (seed 13); randomized training (seed 21); data-efficiency sweep 2–40 episodes.
- Result: see `05-koopman-and-mpc.md`.

## E7: MPC closed loop
- Set-up: residual trained on the E6 family-A data; part 1: steady altitude error on six plants (A and B, each in full, without its thrust loss, and its thrust loss alone on the nominal plant), one start 1 m below the set-point, 8 s; part 2: capture after delay τ ∈ {0, 10, 20, 30, 40, 60} ms on family A, judged against each controller's own closed-loop steady state.
- Result: residual-Koopman MPC reduces the steady altitude error on 5 of 6 plants (−32% on A) but increases it by 47% on B without thrust loss; as a capture controller, LQR is SAFE up to 10 ms and both MPCs only at 0 ms.

## Known comparability issues
- E4 uses the nominal plant; E7 part 2 uses truth family A. Absolute delay numbers differ between them.
- E4 delay results depend on the spin-up thrust, so both the flight value and mg/2 are reported (`03-validation.md`).
