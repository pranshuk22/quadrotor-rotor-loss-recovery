# Project Status (2026-11-14)

## Summary

The submission studies one question: can a Koopman (EDMDc) model of only the error of the physics model of the spinning drone, used inside MPC, predict and control the failed drone better than the physics model alone or a Koopman model of the full dynamics? The experiments (E6 to E8g) are finished and written up in the report (`docs/report/`), the short paper (`docs/paper/`) and the slide deck (`docs/deck/`). Work on certified fault-detection-delay budgets was explored and is not part of the submission (see "Exploratory work not in the submission" in the root README).

| Item | Status |
|---|---|
| Proposal: all content of the presented proposal kept (`proposal/`); delay-budget additions marked "explored; not part of the final submission" | done |
| Simulator, equilibria, linear models, LQR | done, validated |
| Data, full-state EDMDc, residual EDMDc, analytical and residual-Koopman MPC | done (E6, E7) |
| MPC on the full-state Koopman model (proposal controller 2) | done (E8b); stable near the hover, fails the capture earlier |
| Offset-free MPC and integral-action baselines | done (E8a); the state-disturbance MPC removes the bias but fails the capture; the integrator LQR reduces it to at most 0.024 m with unchanged capture |
| Online adaptation, transient training, MPC tuning, ablations, realistic truth plant | done (E8c to E8g) |
| Delay-budget certificates (E4, E5, E9a to E9d, E10c) | explored; no certified budget exists; not in the submission |
| E9e, E10a, E10b and the corrected E9d coverage re-run | pre-registered, not run |
| Primary texts of Stephan 2018 and Lanzon 2014 | not obtained; the report relies on abstracts |

## Validation: what has been checked, and how

**122 automated tests pass, plus 1 expected failure** (`.venv/bin/python -m pytest -q`, ~60 s):

| File | Tests | What it checks |
|---|---|---|
| `tests/test_physics.py` | 13 | Simulator against **hand-derived solutions and conservation laws**: free fall; thrust direction from a hand-built rotation matrix; torque-free precession (closed form); conservation of inertial angular momentum and kinetic energy (1e-8); reduced-attitude kinematics vs the matrix exponential; first-order yaw spin-up (closed form); motor-lag step response; RK4 convergence order (≈ 16× per halving); saturation rules; agreement with an independent transcription of the paper's eqs. (12)–(14); agreement with an independent implementation of the IJRR general model; relaxed-hover centre-of-mass acceleration = g·tan(tilt) |
| `tests/test_paper_validation.py` | 20 | **Published numbers** from 3 papers (next table); the published one-rotor q̄ is an expected failure (`xfail`) because it is inconsistent with the paper's own eq. (12) |
| `tests/test_core.py` | 10 | Equilibrium fixed points, Jacobians vs finite differences, LQR stability, nonlinear recovery, LMI certificate invariance (500 boundary samples), one controller call per period, supervisor switch from filtered commands |
| `tests/test_koopman_mpc.py` | 7 | Nominal discrete model accuracy, residual reduces the one-step error on a held-out episode, EDMDc rollout, MPC status and first move vs discrete LQR, MPC options default to the published behaviour |
| other test files | 80 | Offset-free MPC, online adaptation, truth-plant effects (bit-identical defaults), and the exploratory certificate code; see `tests/README.md` |

**Against papers** (full tables: `results/tables/validation_report.md`, produced by `experiments/v0_validation_report.py`):

| Source | What was compared | Result |
|---|---|---|
| Mueller & D'Andrea, ICRA 2014 | Two-rotor-loss equilibrium (eqs. 57–59) | ✅ every published digit (≤ 0.14%) |
| | Three-rotor-loss equilibrium (eqs. 62–64), exercises gyroscopic terms with p ≠ 0 | ✅ every published digit (≤ 0.8%) |
| | One-rotor-loss equilibrium (eqs. 50–53) | f, r, n_z ✅ ≤ 0.5%; q̄, n̄_y −6%: the paper's own values leave a residual in its eq. (12), so that one published case is inconsistent |
| | Fig. 3 minima of the ρ sweep | ✅ values within 2%, locations within 3% |
| | Coupling constant ā (eq. 28) = our Jacobian entry; controllability loss when ā = 0 (eqs. 37–39) | ✅ exact; rank 7 → 6, roll rate p uncontrollable |
| Mueller & D'Andrea, IJRR 2016 (independent implementation of their more detailed model) | Hover solutions for 5 failure cases (no failure, 1 rotor, 2 opposing, 2 adjacent, 3 rotors) | ✅ body-rate vector within 4% with published parameters (sensitivity check: ≤ 0.7% with one inertia value inside the published rounding, fitted to the same cases) |
| Sun et al., T-RO 2020 (Parrot Bebop 2, a second airframe) | Two-rotor equilibrium, eq. (60) | ✅ equals the paper's formula; the paper's quoted numbers are 1.5% off its own formula |
| Flight data (ICRA Fig. 4, IJRR Sec. 5.3) | Spin-up time; spin rate | ✅ spin-up 0.65 s vs 0.62 s at the flight thrust (2.95 N); 0.81 s at mg/2. The papers' models over-predict the steady spin rate by about 20% |

## Main results

- **Prediction (E6).** From 100 ms on, the residual model is the most accurate predictor on family A (1 s: 0.64 vs 0.91 full-state vs 7.1 analytical). Data efficiency at 0.5 s: residual with 10 episodes 0.42, full-state with 40 0.48. No generalization to family B.
- **MPC (E7).** Residual-Koopman MPC reduces the steady altitude error on 5 of 6 plants (-32% on A), but increases it by 47% on B without thrust loss. Solver 0.73 ms per step, 4.4 ms wall clock through CVXPY. As a capture controller after a delay, LQR is SAFE up to 10 ms, both MPCs only at 0 ms.
- **Baselines (E8a, E8b).** The integrator LQR reduces the bias to at most 0.024 m and keeps the capture; the state-model offset-free MPC removes it but fails the capture; the full-state Koopman MPC fails the capture earlier.
- **Depth (E8c to E8g).** Adaptation halves the error on the unseen plant but not on the training plant; transient training improves the prediction of transients but not the capture; horizon and weights change nothing much; cubic features help long horizons; noisy training data are harmful; conclusions hold with air-relative thrust and drag.

## Caveats

1. **Spin-up thrust.** The capture experiments use the flight value 2.95 N, read from a plot.
2. **Generalization.** The residual model helps only on the mismatch family it was trained on. This is a real limitation, not a bug.
3. **Simulation only,** with exact state measurement and one vehicle.
4. **Novelty statements** depend on a literature search; two key papers (Stephan 2018, Lanzon 2014) were available only as abstracts.
