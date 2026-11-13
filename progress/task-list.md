# Task List (whole project, both research questions)

Legend: ✅ done · 🔜 next · ⬜ later · ★ needed for presentation 1
RQ1 = residual Koopman MPC (the presented proposal). RQ2 = certified detection-delay budget.

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
- [x] ✅ T1.7 Test suite: 59 tests plus 1 expected failure, incl. physics invariants and published-number validation (`tests/`)
- [x] ✅ T1.9 Model validation against 3 papers + their flight data (`results/tables/validation_report.md`)
- [x] ✅★ T1.8 Progress report and slides (`docs/report/`, `docs/deck/`)

## Track RQ1: residual Koopman MPC
- [x] ✅★ K1 Data generation (excited closed-loop episodes, 5 ms) and nominal discrete M&D model
- [x] ✅★ K2 Full-state EDMDc: spectrum + multi-step error (E6, H1)
- [x] ✅★ K3 Residual EDMDc: multi-step error, data efficiency, held-out family, randomized training (E6, H2, H4)
- [x] ✅★ K4 MPC: analytical vs residual Koopman (measured disturbance), regulation under mismatch + capture after delay (E7, H3)
- [x] ✅ K5 MPC on the full-state Koopman model (PDF controller 2) (E8b)
- [x] ✅ K6 Offset-free MPC / integral action baseline (E8a)
- [x] ✅ K7 Online residual adaptation (recursive least squares on W), to answer the generalization failure in E6
- [x] ✅ K8 Residual trained on spin-up transients (capture far from the equilibrium)
- [x] ✅ K9 Ablations: dictionary, regularization, sampling period, sensor noise
- [x] ✅ K10 Longer MPC horizon / tuning study for capture (E7 part 2 showed no gain over LQR)
- [x] ✅ K11 Add air-relative thrust (IJRR 2016 eq. 4) and quadratic drag to the truth plant (validated in `rotorfail/validation.py`); retrain and re-test RQ1

## Track RQ2: certified delay budget
- [x] ✅★ D1 Detection-delay supervisor + M&D spin-up baseline; τ sweep + Monte Carlo P(safe) with Wilson intervals at two spin-up thrusts (E4)
- [x] ✅★ D2 First saturation-aware LMI certificate (LTI) + nonlinear conservatism (E5)
- [x] ✅ D3 LPV reduced-attitude model in r: A(r), B(r), trims x̄(r)
- [x] ✅ D4 r-robust capture LMIs (common P, then P(r)); moving-trim disturbance term; gate: contains hover onset?
- [x] ✅ D5 Capture-gain synthesis (result: infeasible for a certified hand-over; the gain-scheduled variant was not attempted)
- [ ] ⬜ D6 Reachable set of the undetected phase; switch map; containment LMI; τ\* by bisection
- [ ] ⬜ D7 Trade study: τ\* vs healthy tuning, idle thrust f_min, thrust-to-weight, motor lag, sampling, **spin-up thrust** (E4 shows a strong effect: τ₉₀ = 12 ms at 2.95 N vs 7 ms at mg/2)
- [x] ✅ D8 Certificate for the residual-Koopman MPC loop (result: not certifiable): bound the true plant mismatch over the plant family (d_max is only a training percentile) and handle the MPC constraints (unconstrained-region or terminal-set argument); τ\* per capture controller
- [ ] ⬜ D9 Monte Carlo tightness (certified vs empirical τ\*); LQG / output feedback

## Phase 5: Write-up
- [ ] ⬜ W1 Journal-style final report (due 13 Nov) · W2 final progress presentation (31 Oct) · W3 code clean-up

## Stages of the remaining work

The journal-style final report is due on **13 November 2026**. Work proceeds stage by stage; each stage is reviewed before the next starts.

- **A. Clean baseline:** R0 (report text reflects the present).
- **B. RQ1 proposal deliverables:** K6 (offset-free MPC baseline), K5 (MPC on the full-state Koopman model).
- **C. RQ2 foundations:** X1 (hand-over diagnostic), D3 (quasi-LPV attitude model), D4 (r-robust capture certificate), D5 (capture-gain synthesis).
- **D. RQ2 main result:** D6 (reachable sets, beta(tau), certified tau\*), D9 (tightness), D7 (trade study).
- **E. RQ1 generalization and depth:** K7 (online adaptation), K8 (spin-up training data), K10 (MPC tuning study), K9 (ablations), K11 (air-relative thrust and drag in the truth plant).
- **F. Learned-controller certificate:** D8 (certificate for the residual Koopman MPC loop).
- **G. Literature and write-up:** L1 (literature closure), R3 (journal-style paper), R5 (deck), W3 (reproducibility and clean-up).
