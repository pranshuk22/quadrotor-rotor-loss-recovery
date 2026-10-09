# Project Plan (v2): Residual Koopman MPC for Recovery from Complete Rotor Loss — Simulation Study

Source: `project-proposal.pdf` (revised proposal). v1 written 2026-10-09; v2 reworks the plan to sharpen novelty and to fit a **simulation-only** scope.

## 1. What changed from v1 and why

The original proposal's question ("is a residual Koopman model a better predictor than the analytical or full-state model?") is a known pattern (residual Koopman MPC) applied to a new regime. On its own it is incremental. v2 makes the headline claim something none of the prior work I found tests:

> **Headline claim.** A Koopman residual built on the Mueller–D'Andrea (M&D) spinning-equilibrium model enlarges the region of the state space where a *linear (QP-solvable) predictor* is valid, so a linear-MPC controller can recover a quadrotor from complete rotor loss over a much wider set of failure-onset conditions than the analytical model alone or a full-state Koopman model.

This also answers the main reviewer question, "why Koopman and not a GP or NN residual?", and it is a pure-simulation experiment (large Monte Carlo), which is where simulation has an advantage over hardware.

## 1a. Why this is novel

Each ingredient exists. The novelty is in the combination and in the question we ask of it:

1. **A new regime for residual Koopman.** Existing residual-Koopman work (quadrupeds, road vehicles, soft arms, and nominal quadrotor flight) corrects *small mismatch around a nominal operating point*. Complete rotor loss is a different equilibrium (a continuous spin, no level hover, lost yaw authority), so a generic hover model cannot serve as the nominal model. Using the M&D spinning-equilibrium model as the physics backbone is what makes a "small residual" plausible here, and we found no prior work doing this.
2. **It fills the gap between two literatures that don't meet.** Koopman fault-tolerant control handles *partial* loss of effectiveness only. Complete-rotor-loss control (M&D, NMPC, INDI, RL) does not use a learned linear predictor for MPC. We found nothing connecting them.
3. **It tests a claim nobody has measured.** Prior residual-Koopman papers show better prediction and tracking. They do not ask how far from the nominal equilibrium the linear predictor stays valid, or whether that translates into a larger recovery region from failure onset. That is the most safety-relevant question for rotor loss, and it is what separates Koopman from a GP/NN residual on the same nominal model.
4. **It explains a known failure instead of avoiding it.** Full-state EDMDc is documented as unstable in related settings. We reproduce this for the failed vehicle (spectral radius > 1) and show that putting the dominant physics in the nominal model is what restores a stable, well-conditioned learned part.
5. **Data scarcity makes it practical.** Failed flights end in crashes, so little data exists. A residual formulation that needs far less data than full-state or GP/NN models is a result that matters for this specific problem.

**Caveat:** this is a "not found in extensive search" claim, not proof of absence, and the closest overlap (Todde et al., ICUAS 2026) is unverified. Phase 0 must resolve it before the claim is stated in any write-up.

## 2. Novelty assessment

### Prior work (do not claim these)

| Area | Prior work found | Implication |
|---|---|---|
| Complete-rotor-loss physics/control | Mueller & D'Andrea 2014; Nan et al. 2022 NMPC FTC (arXiv 2109.12886); NMPC FTC with unknown complete failure (IEEE 9901659); INDI FTC (arXiv 2002.07837) | Strong non-learning baselines. NMPC (Nan) is the upper reference. |
| RL for rotor failure | arXiv 2109.10488, 2002.11564, 2503.02649; meta-RL FTC | Learned *policies*, not learned MPC prediction models. |
| Koopman for quadrotors | SE(3) Koopman-MPC (arXiv 2305.03868); Martini et al. analytical Koopman MPC (ICUAS 2025, arXiv 2409.12374); Deep Koopman MPC (arXiv 2508.13795) | Koopman-MPC for quadrotors is established. |
| Koopman FTC (partial faults) | Bakhtiaridoust et al. 2024 (IET CTA); IEEE 10773232; Koopman FDI (J. Intell. Robot. Syst. 2024) | Loss of effectiveness only, all four rotors still active. |
| Residual Koopman MPC | RK-MPC quadrupeds (arXiv 2604.04221); vehicle dynamics (arXiv 2507.18396); soft arm (Bruder 2025) | Residual-Koopman pattern is not new. |
| Nominal + learned residual quadrotor MPC | GP-MPC (arXiv 2102.05773); Neural-MPC (arXiv 2203.07747); KNODE | Must be included as baselines. |

### Claimed contributions (worded as "we did not find prior work that…")

- **C1 (main).** We did not find prior work that evaluates how far from the spin equilibrium a residual-Koopman linear predictor stays valid for a quadrotor with complete rotor loss, or that compares recovery success from failure-onset conditions across analytical, full-state Koopman and residual Koopman MPC.
- **C2.** We did not find prior work that builds the Koopman residual on the M&D spinning equilibrium, or that shows the full-state EDMDc failure mode (spectral radius > 1) in the failed-vehicle regime.
- **C3 (supporting).** Data efficiency of the residual formulation (failed-flight data is scarce in practice) and generalization to mismatch types unseen in training, compared with GP and NN residuals on the same nominal model.
- **C4 (optional, theory).** A multi-step prediction-error bound for the residual and a tube-MPC constraint-satisfaction result built on it.
- **C5 (stretch).** One predictor/controller across failure severity (partial loss → complete loss) with online residual adaptation.

If Phase 0 shows that Todde et al. (ICUAS 2026) already covers C1/C2, narrow the claim to C3 + C4.

### Honest limits of the claim
- NMPC on the full nonlinear model (Nan et al.) will probably still have the largest recovery region. **We do not claim to beat NMPC on region size.** The claim is the region/compute trade-off: how much of the NMPC region a convex-QP controller can recover.
- "Not found in a search" is not "does not exist". Re-run the search before submission.

### Items to fix in the proposal
- **Citations:** I could not find "Todde, Martini, Rizzo & Valavanis (2026), Residual Koopman-Based MPC of Quadrotors, ICUAS 2026". I only found their ICUAS 2025 paper. Verify it exists and read it. "Lee et al. 2024, Koopman FT-MPC" looks mis-attributed. The IET paper is by Bakhtiaridoust et al.; check the IEEE 10773232 authors. Also verify RK-MPC's "unstable within seconds" statement, since I could only partly read the paper.
- **Missing sections:** the PDF jumps from Section 5 to Section 8, so get the missing sections or confirm they were dropped.
- **"Linear and time-invariant"** about the spin equilibrium holds only in suitable (reduced-attitude / rotating-frame) coordinates because the equilibrium is periodic. Fix the coordinates in Phase 1.

## 3. Hypotheses and success criteria

- **H1 (full-state instability):** Full-state EDMDc on the failed vehicle has spectral radius > 1 and underperforms a "no-change" predictor at long horizons.
- **H2 (prediction):** The residual model has lower multi-step open-loop error than the analytical and full-state models at horizons of 0.5–5 s.
- **H3 (region of validity, headline):** The residual predictor's validity region and the closed-loop recovery region are larger than the analytical-only and full-state ones, with statistical support.
- **H4 (data efficiency):** The residual reaches a given prediction error with substantially less data than full-state Koopman, and than GP/NN residuals.
- **H5 (generalization):** Under mismatch families not seen in training, the residual degrades less than the full-state Koopman model and no more than GP/NN residuals.
- **H6 (optional):** The residual error bound holds empirically, and the tube MPC keeps constraints satisfied.

Outcomes are reported even if a hypothesis fails. A clear negative on H3 is still a publishable finding, but it changes the framing.

## 4. Simulation-only protocol (guarding against circularity)

If we write both the truth simulator and the unmodeled effects, the learner may just be recovering our own code. All of the following are required:

1. **Independent truth model.** The nominal model is the analytic M&D model. The truth simulator is a separate implementation with *different structure*: first-order motor lag, blade flapping and induced/rotor drag, nonlinear thrust-vs-speed, rotor gyroscopic effects, wind. Prefer an independent physics engine (e.g., PyBullet/Gazebo-class dynamics with a custom aero layer) over a perturbed copy of the M&D equations. Use a different integrator and time step from the controller's.
2. **Mismatch families with a train/test split.**
   - Family A (training): motor lag + rotor drag + inertia error.
   - Family B (held out): wind/gust, thrust nonlinearity, different inertia error, battery sag.
   - Train on A, test on A and on B. Rotate the families.
3. **Randomized mismatch per trial** (parameter ranges, not a single setting).
4. **Realism of the loop, not the vehicle:** sensor noise, state-estimator error, control latency, discretization mismatch, and actuator saturation. Measure the MPC solve time on embedded-class hardware or a throttled CPU.
5. **Scoped language:** all claims read "in simulation, under mismatch X, Y, Z". Do not claim real-vehicle fault tolerance.
6. **Reproducibility:** fixed seeds, config files per experiment, and released code/data.

## 5. Technical design

### 5.1 Nominal model (M&D)
Implement the closed-form relaxed-hover equilibrium (spin rate/axis, rotor thrusts, tilt–translation relation). Choose the reduced-attitude/deviation coordinates, linearize and discretize. **Gate:** LQR on the nominal model stabilizes the ideal failed vehicle, matching their reported behaviour.

### 5.2 Truth simulator
Per §4. Single-rotor loss first. Two-opposite-rotor loss is a stretch goal. Include a failure-onset trigger at a chosen time and state.

### 5.3 Failure-onset scenario generator (key for H3)
Sample failure-onset initial conditions over:
- attitude (tilt up to a large angle), angular rate, linear velocity (hover through high-speed forward flight), altitude, and which rotor fails.
- Use Sobol/Latin-hypercube sampling plus targeted sweeps along single axes for interpretable plots.

### 5.4 Data and learning
- Data comes from the failed vehicle near the equilibrium (LQR + randomized excitation) and, for H3, from broader but still limited coverage. Report how coverage affects validity.
- Residual targets: `e_{k+1} = x_{k+1} − f_nominal(x_k, u_k)`. Hold out whole trajectories.
- EDMDc on the residual with dictionaries: identity, polynomial (deg 2–3), RBF, SE(3)-structured. Ridge regularization. Log eigenvalues, spectral radius, condition number.
- Baselines learned on the same data: full-state EDMDc; GP residual; small NN residual (same nominal model).

### 5.5 Controllers (same cost, horizon, constraints, solver)
1. Analytical MPC (M&D only).
2. Full-state Koopman MPC.
3. **Residual Koopman MPC (proposed).**
4. Nan et al. NMPC (upper reference, nonlinear, not a QP).
5. Nominal + GP residual MPC.
6. Nominal + NN residual MPC.
Constraints: non-negative rotor thrust, max thrust, tilt limits. Terminal cost from the LQR solution. Soft constraints for feasibility.

### 5.6 Definitions for H3
- **Prediction-validity radius:** for a chosen error threshold (e.g., 1-s position/attitude error < tolerance), the largest set of initial conditions (measured in a normalized distance from the equilibrium) where the predictor stays within threshold.
- **Recovery success:** within T seconds the vehicle reaches and stays in a neighborhood of the spin equilibrium and tracks the position reference, with no crash, no divergence and altitude loss below a limit.
- **Recovery region:** the set of failure-onset conditions with success rate ≥ 95% over repeated randomized-mismatch trials. Report area/volume along slices and the success-rate heatmaps.

## 6. Experiments

| # | Experiment | Metric | Tests |
|---|---|---|---|
| E1 | Open-loop multi-step prediction, held-out trajectories | RMSE vs horizon; divergence fraction | H2 |
| E2 | Spectral analysis | eigenvalues > 1; spectral radius | H1 |
| E3 | **Prediction-validity radius vs distance from equilibrium** | validity radius per model | **H3** |
| E4 | **Recovery from failure onset: Monte Carlo over §5.3 scenarios** | recovery success map, region size, time-to-recover | **H3** |
| E5 | Trajectory tracking after recovery (circle, step, figure-8) | RMSE, saturation, solve time | closed loop |
| E6 | Data efficiency sweep | error / success vs training samples | H4 |
| E7 | Held-out mismatch families (train A → test B and rotated) | degradation vs. in-family | H5 |
| E8 | Noise / latency / estimator-error sweep | success vs magnitude | robustness |
| E9 | Ablations: dictionary, regularization, nominal-model quality, residual on/off | which part carries the gain | mechanism |
| E10 | Real-time feasibility | solve time vs. rate budget (≥ 100 Hz target) | tractability |
| E11 (optional) | Error bound and tube MPC | bound violation rate; constraint satisfaction | H6 |
| E12 (stretch) | Severity sweep 100% → 0% thrust with online residual update | success vs severity; switching behaviour | C5 |

Use at least 30 seeds per cell for closed-loop results; report means, confidence intervals and failure counts. Pre-register the thresholds (validity tolerance, success criteria) before running E3/E4 to avoid tuning them post hoc.

## 7. Milestones and gates

| Phase | Deliverable | Gate |
|---|---|---|
| 0. Lit audit (≈ 1 wk) | Read Todde 2026, Martini 2025, RK-MPC, Nan 2022; fix references; recover missing proposal sections | Claims C1/C2 confirmed or narrowed |
| 1. Simulators + nominal model (≈ 2–3 wk) | Independent truth sim with mismatch families; M&D model; LQR stabilization; coordinates fixed | LQR stabilizes ideal failed quadrotor |
| 2. Data + full-state Koopman (≈ 1–2 wk) | Data generator; full-state EDMDc; H1 evidence | H1 shown or revised |
| 3. Residual Koopman (≈ 2 wk) | Residual EDMDc; E1–E3 | **Stop/re-scope if the residual is not better than nominal (H2) or the validity radius does not grow (H3 prediction part)** |
| 4. MPC + baselines (≈ 3 wk) | Controllers 1–6; E4, E5 | Closed-loop recovery map produced |
| 5. Data efficiency + generalization + robustness (≈ 2 wk) | E6–E10 | Results for H4/H5 |
| 6. Optional theory / stretch (≈ 2–4 wk) | E11 and/or E12 | Only if Phases 1–5 are on schedule |
| 7. Write-up (≈ 2–3 wk) | Report/paper, figures, released code | Claims match evidence |

## 8. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Residual gain is an artifact of our own simulator | High | §4 protocol: independent truth model, held-out mismatch families, randomization |
| Region of validity does not grow (H3 fails) | Medium | Report as a negative result; fall back to C3 + C4; the Phase 3 gate catches this before the MPC build |
| NMPC dominates everywhere, leaving no story | Medium | Frame the claim as region-vs-compute for convex-QP controllers; report solve times |
| Koopman residual not better than GP/NN residual | Medium | Position on convexity, interpretability, linear-in-lifted-space prediction, and data efficiency |
| Todde 2026 overlaps C1/C2 | Unknown | Resolve in Phase 0 |
| Coordinates make the nominal model not truly LTI | Medium | Fix the reduced-attitude formulation in Phase 1 |
| Scope creep (partial-failure continuum, multi-rotor loss, theory) | High | Stretch items start only after the Phase 5 gate |
| Simulation-only limits venue options | Certain | Scoped claims; lean on the region-of-validity study and the error-bound theory |

## 9. Repository layout

```
rotor-failure-project/
├── project-proposal.pdf
├── plan.md
├── README.md
├── sim/
│   ├── truth/        # independent high-fidelity simulator + mismatch families A/B
│   └── scenarios/    # failure-onset scenario generator (Sobol/LHS, axis sweeps)
├── models/           # nominal M&D model, EDMDc, dictionaries, GP/NN residuals
├── control/          # LQR, MPC variants, NMPC reference
├── experiments/      # E1–E12 scripts, configs, seeds, preregistered thresholds
├── results/          # figures, tables, logs
└── tests/            # equilibrium check, linearization check, EDMDc sanity, simulator-independence check
```
Stack: Python, NumPy/SciPy, CVXPY + OSQP (QP-MPC), CasADi/acados (NMPC reference), PyTorch/GPyTorch (baselines), Matplotlib.

## 10. Immediate next steps
1. Phase 0: verify the Todde 2026 and Koopman-FTC references; read Nan et al. and RK-MPC fully; recover the proposal's missing sections.
2. Fix state coordinates for the spinning equilibrium.
3. Decide the truth-simulator route (custom independent aero layer vs. PyBullet/Gazebo) and write the mismatch-family spec before any learning code.
4. Draft and pre-register the validity tolerance and recovery-success criteria.
