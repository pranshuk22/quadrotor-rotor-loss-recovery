# Task List (whole project, both research questions)

Legend: ✅ done · 🔜 next · ⬜ later · ★ needed for presentation 1
RQ1 = residual Koopman MPC (proposal PDF). RQ2 = certified detection-delay budget.

## Phase 0: Literature and novelty gate
- [ ] 🔜 T0.1 Read Stephan, Schmitt & Fichter, JGCD 2018 (LPV on yaw rate). Decide whether RQ2-C2 stays (IITK library / AIAA)
- [ ] 🔜 T0.2 Read Lanzon, Freddi & Longhi, JGCD 2014
- [x] ✅ T0.3 Read Mueller & D'Andrea ICRA 2014 in full
- [x] ✅ T0.4 Detector-delay numbers: 30 to 130 ms (Strack van Schijndel et al. 2021); 45 ms (Yang et al., RA-L 2026)
- [x] ✅ T0.5 Verify the flagged PDF references: "Lee et al. 2024" Koopman FT-MPC attribution; RK-MPC "unstable within seconds"
- [ ] ⬜ T0.6 Re-run the novelty searches before the final report (`literature/search-log.md`)

## Phase 1: Shared foundation (presentation 1)
- [x] ✅★ T1.1 Nonlinear 6-DOF simulator: rotor gyroscopics, thrust limits, motor lag, failure injection
- [x] ✅★ T1.2 Relaxed-hover equilibrium + validation vs paper + ρ sweep (E1)
- [x] ✅★ T1.3 Healthy and failed linear models (unit-tested)
- [x] ✅★ T1.4 Controllability, PBH, Gramians; observability for sensor sets (E2)
- [x] ✅★ T1.5 Healthy LQR + failure LQR; poles and delay margins; nonlinear check (E3)
- [x] ✅★ T1.6 Truth-plant families A / B / randomized (thrust loss at high body rate, inertia error, motor lag)
- [x] ✅ T1.7 Test suite: 45 tests, incl. physics invariants and published-number validation (`tests/`)
- [x] ✅ T1.9 Model validation against 3 papers + their flight data (`results/tables/validation_report.md`)
- [ ] ★ T1.8 Build the slides from `progress/presentation-1-plan.md`

## Track RQ1: residual Koopman MPC
- [x] ✅★ K1 Data generation (excited closed-loop episodes, 5 ms) and nominal discrete M&D model
- [x] ✅★ K2 Full-state EDMDc: spectrum + multi-step error (E6, H1)
- [x] ✅★ K3 Residual EDMDc: multi-step error, data efficiency, held-out family, randomized training (E6, H2, H4)
- [x] ✅★ K4 MPC: analytical vs residual Koopman (measured disturbance), regulation under mismatch + capture after delay (E7, H3)
- [ ] 🔜 K5 MPC on the full-state Koopman model (PDF controller 2)
- [ ] 🔜 K6 Offset-free MPC / integral action baseline (reviewers will ask why the bias isn't removed with integral action)
- [ ] 🔜 K7 Online residual adaptation (recursive least squares on W), to answer the generalization failure in E6
- [ ] ⬜ K8 Residual trained on spin-up transients (capture far from the equilibrium)
- [ ] ⬜ K9 Ablations: dictionary, regularization, sampling period, sensor noise
- [ ] ⬜ K10 Longer MPC horizon / tuning study for capture (E7 part 2 showed no gain over LQR)
- [ ] 🔜 K11 Add air-relative thrust (IJRR 2016 eq. 4) and quadratic drag to the truth plant (validated in `rotorfail/validation.py`); retrain and re-test RQ1

## Track RQ2: certified delay budget
- [x] ✅★ D1 Detection-delay supervisor + M&D spin-up baseline; τ sweep + Monte Carlo (E4)
- [x] ✅★ D2 First saturation-aware LMI certificate (LTI) + nonlinear conservatism (E5)
- [ ] 🔜 D3 LPV reduced-attitude model in r: A(r), B(r), trims x̄(r)
- [ ] 🔜 D4 r-robust capture LMIs (common P, then P(r)); moving-trim disturbance term; gate: contains hover onset?
- [ ] ⬜ D5 Gain-scheduled capture controller K(r), certified
- [ ] ⬜ D6 Reachable set of the undetected phase; switch map; containment LMI; τ\* by bisection
- [ ] ⬜ D7 Trade study: τ\* vs healthy tuning, idle thrust f_min, thrust-to-weight, motor lag, sampling, **and yaw drag / thrust model** (our model spins up 30% slower than the ICRA flight, which affects the E4 delay numbers)
- [ ] ⬜ D8 Certificate for the residual-Koopman MPC loop: bound the true plant mismatch over the plant family (d_max is only a training percentile) and handle the MPC constraints (unconstrained-region or terminal-set argument); τ\* per capture controller
- [ ] ⬜ D9 Monte Carlo tightness (certified vs empirical τ\*); LQG / output feedback

## Phase 5: Write-up
- [ ] ⬜ W1 Final report + figures · W2 final presentation · W3 code clean-up

## Suggested schedule after presentation 1 (adjust to the course calendar)

| Block | RQ1 | RQ2 | Deliverable |
|---|---|---|---|
| Weeks 1–2 | K5, K6 | T0.1, T0.2, D3, D4 | Full-state Koopman MPC + offset-free baseline; r-robust capture certificate (gate) |
| Weeks 3–4 | K7 | D5, D6 | Online residual adaptation; first certified τ\* |
| Weeks 5–6 | K8, K9 | D7, D8 | Trade study incl. τ\* per capture controller (presentation 2) |
| Weeks 7–8 | K10 (if time) | D9 | Final report and presentation |
