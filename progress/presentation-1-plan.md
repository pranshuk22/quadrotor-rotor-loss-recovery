# Progress Presentation 1: Plan and Slide Outline

**Status:** the deck is built (`docs/deck/`, 19 slides). The outline below is the original plan, with the numbers updated to the current results. The deck itself presents the two questions as one merged story, without RQ labels.

**Context:** first review after the proposal (the residual-Koopman PDF) was presented and finalised. About 3–4 calendar weeks have passed, roughly 2–3 weeks of effective work (mid-semester exams in between).
**Structure:** shared foundation, then **RQ1** (the proposal as presented: residual Koopman MPC), then **RQ2** (the certification extension).
**Target length:** 12–14 min, about 15 slides.

## What the evaluators will expect, and what we have

| Expectation | Status | Evidence |
|---|---|---|
| Recap of the finalised proposal and any scope change, stated openly | ✅ | `proposal/proposal.md` (all PDF sections kept; RQ2 added in §6–7) |
| Working mathematical model + simulator | ✅ | `rotorfail/`, slides 3–4 |
| Equilibrium validated against the reference paper | ✅ | E1 |
| Course tools used properly (linearization, controllability/observability, LQR, Lyapunov/LMI) | ✅ | E2, E3, E5 |
| **Progress on the proposed method itself (EDMDc, residual, MPC)** | ✅ first version | E6, E7 |
| Preliminary results that test the hypotheses, including negatives | ✅ | E4–E7 |
| Realistic plan for the remaining weeks | ✅ | `progress/task-list.md` |

## Slide outline

| # | Slide | Content | Asset |
|---|---|---|---|
| 1 | Title | Title, team, date | n/a |
| 2 | Recap and scope | RQ1 (as proposed): can a residual EDMDc model built on the M&D spinning-equilibrium model beat the analytical and full-state Koopman models for MPC? **Added RQ2:** every recovery method assumes instant fault detection; how long can detection take with *guaranteed* recovery? One sentence on the link: the MPCs are capture controllers, τ\* is the common yardstick | proposal §2–3 |
| 3 | Model and simulator | 6-DOF rigid body + rotor gyroscopics; f ∈ [0.2, 3.8] N; 15 ms motor lag; M&D vehicle parameters; reduced attitude n = Rᵀe₃. **Truth plants:** thrust loss at high body rate (M&D observed it), inertia error, slower/faster motors; families A (train) and B (held out) | `rotorfail/params.py` |
| 4 | **Model validation** | **3 papers (2 airframes, 2 aerodynamic models) + flight data.** ICRA 2014: two-rotor and single-rotor equilibria reproduced to every published digit; one-rotor f, r, n_z within 0.5% (q̄ −6%: the published case leaves a residual in the paper's own eq. 12). ā formula and controllability-loss condition (eq. 39) confirmed. IJRR 2016 (independent implementation, air-relative thrust): all 5 failure cases within 4% (body-rate vector). Bebop 2 (Sun T-RO 2020): equals eq. 60. **Flight:** spin-up 0.65 s vs 0.62 s at the flight thrust (2.95 N); spin rate over-predicted ~20% by the papers' models. 46 tests incl. conservation laws and analytic solutions | `results/tables/validation_report.md`, E1 figure |
| 5 | Linear model, controllability, observability | Failed model is LTI in body coordinates; modes ±10.1j, ±19.6j, −0.51, double integrator; controllable (rank/PBH/Gramian). **Finding:** gyro + barometer makes the tilt observable after the failure (tilted equilibrium) but ≈ 2,700× weaker than a tilt sensor (noise-normalized Gramian) | E2 tables |
| 6 | LQR baseline | Healthy + failure LQR (M&D weights + motor states); delay margins 40 ms vs **18 ms**; nonlinear verification | E3, `e3_failed_lqr_nonlinear.png` |
| **RQ1** | | | |
| 7 | Koopman set-up | Data: 40 × 4 s excited closed-loop episodes at 5 ms on truth A. Full-state EDMDc: degree-2 dictionary, 55 lifted states. Residual: e = x_true − x_nom regressed on the same dictionary, clipped at d_max (as in Todde 2026) | `rotorfail/koopman.py` |
| 8 | **Prediction results** | At 1 s, normalized RMSE: analytical **7.1**, full-state **0.91**, residual **0.64**, no-change 2.4; the residual model is best from 100 ms on. Full-state EDMDc: 4/55 eigenvalues outside the unit circle; falls behind the no-change baseline by 2 s (**proposal claim confirmed in the failed regime**). At 2 s the residual model also exceeds no-change (2.7 vs 2.5): the nominal model's undamped modes drift, so long open-loop horizons need feedback (MPC re-plans every 5 ms). Data efficiency: residual with 10 episodes beats full-state with 40 | `e6_multistep_error.png`, `e6_data_efficiency.png`, `e6_full_edmdc_eigs.png` |
| 9 | **Honest negative** | On the held-out family B, both learned models are worse than the analytical model; training on randomized vehicles helps the residual on B only up to ~100 ms and hurts on A. Reason: unknown per-vehicle parameters are not identifiable from one state sample. → online residual adaptation (RLS) is next | E6 tables |
| 10 | **MPC in closed loop** | Residual-Koopman MPC cuts the steady altitude bias by 32% on family A (−0.29 → −0.19 m) and on 5 of 6 plants, but +47% on B without thrust loss; solver 0.7 ms per step. As a capture controller after a detection delay, LQR is SAFE up to 10 ms, both MPCs only at 0 ms | `e7_altitude.png`, E7 tables |
| **RQ2** | | | |
| 11 | Why detection delay matters | Healthy controller cannot cancel l·f₂ (idle thrust) → roll accel ≥ 10.6 rad/s²; tilt ≈ 13° at 100 ms | `e4_undetected_phase.png` |
| 12 | **Key result: P(safe) vs delay** | Published strategy, 40 random starts per delay: P(SAFE) < 0.9 from **12 ms**, < 0.5 from **19 ms** at the flight spin-up thrust (7 and 14 ms at mg/2). **Detectors need 30–130 ms** | `e4_p_safe.png`, `e4_undetected_phase.png` |
| 13 | First certificate | Saturation-aware LMI on the LTI model: covers 22% of the way to hover onset (empirical 70%); the LQR fails only at near-zero spin → r-robust (LPV) certificate next | `e5_certificate_slice.png` |
| 14 | Plan | Two-track schedule (task list); the link: bounded residual (d_max) → capture certificate for the residual-Koopman loop → τ\* per controller | `progress/task-list.md` |
| 15 | Summary | 3 bullets: foundation validated; RQ1 hypotheses H1/H2/H4 supported on the training family, generalization is the open problem; RQ2 gap quantified (about 12 ms vs 30–130 ms) | n/a |

Backup: E2 full tables; E3 healthy figure; success-criterion definition; randomized-training table; E7 part-2 table.

## Talking points to get right

- **Scope change, stated openly.** Nothing from the proposal was dropped: all three PDF controllers are in the plan, and two are already running. RQ2 was added because a predictor gives no guarantee and every recovery paper assumes instant detection. It uses the EE650 toolset (Lyapunov/LMI).
- **What's reproduced vs new.** Equilibrium, controllability and LQR reproduce M&D (that's the validation). New: the failed-regime Koopman comparison, the generalization result, the detection-delay sweep, the idle-thrust bound, the barometer observability remark, and the first certificate with its conservatism measured.
- **Success criterion fixed in advance** (`rotorfail/metrics.py`). With the looser "attitude captured" criterion the 50% point is 52 ms instead of 19 ms. Say so if asked.
- **Simulation-only:** validated against the published equilibrium; at τ = 0 with the flight thrust the vehicle climbs 0.40 m and drops 0.03 m below its start, qualitatively like the flight (which climbs about 0.9 m).

## Likely questions and short answers

| Question | Answer |
|---|---|
| Why not integral action / offset-free MPC for the altitude bias? | That is the right classical baseline. It is next (task K6), and the residual must beat it, or add something beyond it (prediction during transients), to be worth it. |
| The residual fails on family B. Is the idea dead? | No. A fixed residual is per-vehicle by construction (as in Todde 2026). The generalization failure is a measured result. Online adaptation (RLS, linear in the parameters) is the fix we test next. |
| Full-state EDMDc beats the analytical model. Isn't that against the proposal? | The analytical model has no learning and suffers the full mismatch. The proposal's claim is residual vs full-state: residual wins at every horizon ≥ 100 ms on the training family and needs less data. Full-state also has unstable eigenvalues and falls behind no-change by 2 s, as the proposal predicted. |
| Why not use NMPC (Nan et al.)? | NMPC gives no certificate and no delay budget. RQ2 applies to whichever capture controller is certified. |
| Is f_min = 0.2 N realistic? | Yes: ESC idle thrust (the paper's measured range). Sensitivity study planned (D7). |
| How is RQ2 different from Stephan et al. 2018 (LPV)? | They synthesize an LPV controller; we certify capture under saturation and derive a delay budget. Being read now (T0.1). |
