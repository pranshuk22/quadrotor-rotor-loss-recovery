# 6. Experiments

Each experiment is one script in `experiments/`. It writes a markdown table to `results/tables/` and figures to `results/figures/`. Seeds are fixed. Runtimes are on an 8-core laptop.

| ID | Script | Question | Outputs | Runtime |
|---|---|---|---|---|
| V0 | `v0_validation_report.py` | Does the model match published numbers and flight data? | `validation_report.md` | seconds |
| E1 | `e1_equilibrium.py` | Relaxed-hover equilibrium vs the paper; ρ sweep | `e1_equilibrium.md`, `e1_rho_sweep.png` | seconds |
| E2 | `e2_structure.py` | Eigenvalues, controllability (rank, PBH, Gramian), observability by sensor set | `e2_structure.md` | seconds |
| E3 | `e3_lqr.py` | LQR designs: poles, delay margins, nonlinear check | `e3_lqr.md`, `e3_*_lqr_nonlinear.png` | ~15 s |
| E6 | `e6_koopman_prediction.py` | Analytical vs full-state vs residual EDMDc prediction | `e6_koopman_prediction.md`, `e6_multistep_error.png`, `e6_data_efficiency.png`, `e6_full_edmdc_eigs.png` | ~2.5 min |
| E7 | `e7_mpc_closed_loop.py` | LQR vs analytical MPC vs residual-Koopman MPC in closed loop | `e7_mpc_closed_loop.md`, `e7_altitude.png` | ~3 min |
| E8a | `e8_offset_free.py` | Offset-free MPC (two disturbance models, with and without residual) and LQR with integrator vs residual-Koopman MPC | `e8_offset_free.md`, `e8_altitude.png` | ~9 min |
| E8b | `e8_full_koopman_mpc.py` | MPC on the full-state Koopman model vs analytical and residual-Koopman MPC | `e8_full_koopman_mpc.md`, `e8_full_koopman.png` | ~18 min |
| E8c | `e8c_adaptive_residual.py` | Online RLS adaptation of the residual: prediction, closed loop, with offset-free MPC, capture | `e8c_adaptive_residual.md`, `e8c_adaptive.png` | ~25 min |
| E8d | `e8d_spinup_residual.py` | Residual trained on spin-up/capture transients | `e8d_spinup_residual.md`, `e8d_spinup.png` (run 1: `e8d_run1_discard_rule.md`) | ~15 min |
| E8e | `e8e_mpc_tuning.py` | MPC horizon (10 to 80) and weight study for capture | `e8e_mpc_tuning.md`, `e8e_horizon.png` | ~1 h |
| E8f | `e8f_ablations.py` | Dictionary degree, ridge, sampling period, sensor noise | `e8f_ablations.md`, `e8f_ablations.png` | ~1.5 h |
| E8g | `e8g_realistic_plant.py` | Truth plants with air-relative thrust and quadratic drag (A+, B+) | `e8g_realistic_plant.md`, `e8g_plants.png` | ~12 min |

## E1: Equilibrium
- Set-up: nominal parameters, ρ = 0.5; sensitivity to ±0.05e-3 in the inertias; ρ sweep 0.02–1.6 with continuation.
- Result: f, r, n_z within 0.5% of the paper; q and n_y −6% (paper inconsistency, see `03-validation.md`); Fig. 3 minima within 2–3%.

## E2: Structure
- Set-up: healthy (12-state) and failed (7-state) linear models; sensor sets S1–S4 (healthy) and F1–F4 (failed).
- Result: both controllable; gyro + position leaves ψ unobservable (healthy); gyro + barometer makes the failed model observable, but weakly.

## E3: LQR
- Set-up: healthy LQR (Bryson), failure LQR with and without motor states; delay margin via the delay-line method; nonlinear runs from perturbed starts.
- Result: failure LQR delay margin 18 ms (healthy 40 ms); on the nonlinear model the altitude settles in 1.8 s, the tilt in 2.1 s and the yaw rate in 2.5 s; the least-damped mode is −3.80 ± 19.68j (ζ ≈ 0.19).

## E6: Koopman prediction
- Set-up: 40 × 4 s training episodes on family A (seed 11); tests: 10 episodes of A (seed 12) and B (seed 13); randomized training (seed 21); data-efficiency sweep 2–40 episodes.
- Result: see `05-koopman-and-mpc.md`.

## E7: MPC closed loop
- Set-up: residual trained on the E6 family-A data; part 1: steady altitude error on six plants (A and B, each in full, without its thrust loss, and its thrust loss alone on the nominal plant), one start 1 m below the set-point, 8 s; part 2: capture after delay τ ∈ {0, 10, 20, 30, 40, 60} ms on family A, judged against each controller's own closed-loop steady state.
- Result: residual-Koopman MPC reduces the steady altitude error on 5 of 6 plants (−32% on A) but increases it by 47% on B without thrust loss; as a capture controller, LQR is SAFE up to 10 ms and both MPCs only at 0 ms.

## E8a: offset-free baselines
- Set-up: settings fixed in the script docstring before the runs. Disturbance models: "thrust" (3 states, offset on the produced thrust of rotors 1 to 3) and "state" (7 states, one per physical state); steady-state Kalman filter; target calculation; E7 protocols (steady error on six plants, capture after delay on family A and the nominal plant).
- Result: the state-model offset-free MPC removes the steady altitude error (0.000 m) and the LQR with integrator reduces it to at most 0.024 m; the thrust model does not (-0.239 m on A, +0.165 m on B) because three disturbance states cannot absorb the mismatch of seven physical states. The state model fails capture after delay at every tested delay (including 0 ms); the others behave like the LQR or the other MPCs.

## E8b: MPC on the full-state Koopman model
- Set-up: `LiftedKoopmanMPC` (55 lifted states plus altitude, re-lifted at every step, DARE terminal cost without the constant coordinate); E7 protocols; divergence rule |w| > 100 rad/s or |z| > 100 m.
- Result: stable near the hover with steady errors close to the residual MPC's; capture fails earlier than the other MPCs (runs stopped from 20 ms on family A); the lifting leaves the training range during capture (up to 350 standard deviations); 55 to 319 ms per step.

## E8c to E8g: depth of the study
- E8c: RLS adaptation (lambda 0.995 and 0.999) of the 91 x 7 residual weights. Held-out family B prediction error halves, on A there is no gain; steady bias on the worst plant +0.164 to +0.084 m; the covariance guard is saturated.
- E8d: transient-trained residual predicts transients ~14 times better (100 ms: 0.57 against 8.2) but is a worse capture controller (not SAFE at 0 ms). Run 1 is kept: the tilt-based discard rule removed most episodes.
- E8e: horizon 10 to 80 does not change the number of SAFE delays; a heavier attitude weight adds one; MPC settings equal but do not exceed the LQR.
- E8f: cubic features help long horizons on B; ridge and sampling period do not matter; noise-trained residual is harmful (+2.8 m closed-loop bias).
- E8g: conclusions of E6 to E8a survive air-relative thrust and quadratic drag.

## Exploratory experiments (not in the submission)

These scripts studied how long fault detection may take before recovery is no longer possible. They are in the repository but not in the report, deck or paper. The honest outcome: no certified delay budget exists for any configuration tested, and the state at which the published strategy hands over from its open-loop spin-up to the failure controller cannot be contained in any ellipsoid centred at the relaxed hover.

| ID | Script | Question | Outputs | Status |
|---|---|---|---|---|
| E4 | `e4_delay_sweep.py` | Effect of detection delay τ on recovery (empirical) | `e4_delay_sweep.md/.csv`, `e4_p_safe.png`, `e4_delay_sweep.png`, `e4_time_histories.png`, `e4_undetected_phase.png` | run |
| E5 | `e5_first_certificate.py` | First saturation-aware LMI certificate; conservatism vs simulation | `e5_first_certificate.md`, `e5_certificate_slice.png` | run |
| E9a | `e9a_handover.py` | Where is the hand-over state of the published strategy; is it inside the E5 certificate? | `e9a_handover.md/.csv`, `e9a_handover.png` | run |
| E9b | `e9b_robust_certificate.py` | r-robust saturation-aware certificate (quasi-LPV) for the published LQR | `e9b_robust_certificate.md`, `e9b_robust_certificate.png` (runs 1 and 2: `e9b_run1_*`, `e9b_run2_*`) | run |
| E9c | `e9c_gain_synthesis.py` | Capture-gain synthesis and hand-over threshold study ("redesigned capture") | `e9c_gain_synthesis.md`, `results/certificates/e9c_designs.npz` | run |
| E9d | `e9d_certified_delay.py` | Reachable hand-over sets, containment, beta(tau), certified tau* | `e9d_run1_coverage_pinv.md/.csv` | run 1 only (its coverage statistics are invalid; the corrected re-run was not done) |
| E9e | `e9e_early_handover.py` | Confirmation of the earlier hand-over threshold on new seeds and other plants | `e9e_early_handover.md`, `e9e_early_handover.png` | pre-registered, not run |
| E10a | `e10a_tightness.py` | Certified versus empirical delay budget, soundness | `e10a_tightness.md` | pre-registered, not run |
| E10b | `e10b_trade_study.py` | Trade study over vehicle and design parameters | `e10b_trade_study.md`, `e10b_trade_study.png` | pre-registered, not run |
| E10c | `e10c_mpc_certificate.py` | Certificate for the residual-MPC loop | `e10c_mpc_certificate.md`, `e10c_mpc_certificate.png` | run |

Results in one line each: E4 safe-recovery probability below 0.9 from 12 ms of delay and below 0.5 from 19 ms; E5 first certificate covers 22 % of the way to the state after a failure; E9a hand-over state far from the equilibrium (none of 1312 inside the E5 ellipsoid); E9b robust certificates verified but tiny once the nonlinear remainder is bounded; E9c every synthesised gain rejected (closed-loop poles 216 to 47,700 rad/s); E9d the centre of the hand-over set is outside every certificate; E10c the residual-MPC loop is not certifiable.

## Known comparability issues
- E7 part 2 uses truth family A; the later capture tests use the nominal plant or family A as stated in each table.
- Capture results depend on the spin-up thrust; all capture experiments use the flight value of 2.95 N (`03-validation.md`).
