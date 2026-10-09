# Project Plan (v3): Certified Recoverability of a Quadrotor After Complete Rotor Loss

**Course:** EE650, Basics of Modern Control Systems. **Scope:** simulation only.
**Earlier versions:** the Koopman-based plan is kept as `plan-v2-koopman-backup.md`. It is now an optional extension (§9), not the core.

## 1. Why the plan changed

The Koopman direction is mostly a machine-learning contribution on top of known control. Two things were wrong for this course:
- EE650 is judged on modern (state-space) control: modelling, controllability/observability, state feedback/LQR, observers/LQG, Lyapunov stability, robustness. The Koopman plan used little of that.
- The Koopman novelty was only about 80% / 50–60% certain. The neighbouring paper (Todde et al., ICUAS 2026) has now been read (`research/`): it is **healthy-quadrotor trajectory tracking** under mass, inertia, arm-length and thrust-coefficient mismatch (±30%), with an MLP residual added to an analytical lifted model. It involves **no rotor failure, no spinning equilibrium, and no guarantees** (its future work lists "structured uncertainty bounds ... formal robustness guarantees"). So the Koopman failure-regime idea is *not* pre-empted, which makes it a safe optional extension (§9), but it is still not a controls contribution.

A literature search of the control-theory side found a cleaner gap (§3). This plan makes the **control-theoretic analysis and certification** the contribution.

## 2. Problem

After one rotor fails completely, a quadrotor cannot hover level. It settles into a **relaxed hover**: a constant spin about a body axis, with translation obtained by tilting that axis (Mueller & D'Andrea 2014). They stabilize it with LQR about the equilibrium and fly it in hardware.

What the literature does **not** give is a *quantified, certified* answer to the engineering question that matters: **from which failure-onset states, and under which real-world imperfections, is recovery guaranteed?** The imperfections are:
- non-negative, bounded rotor thrust (saturation),
- motor lag,
- the delay before the failure is detected,
- finite sampling rate,
- output feedback from imperfect sensors (no full state).

## 3. Novelty (control-theoretic) and certainty

### What exists (do not claim)
| Topic | Prior work found | Gap left |
|---|---|---|
| Relaxed hover + LQR | Mueller & D'Andrea 2014, 2015 (also optimizes the equilibrium for power, spin rate or actuator margin) | Equilibrium choice is **not** a gap. |
| Large-disturbance recovery | Upset recovery with QP allocation, Monte Carlo + flight tests ([arXiv 2002.09425](https://arxiv.org/abs/2002.09425)); NMPC with Monte Carlo ([arXiv 2109.12886](https://arxiv.org/pdf/2109.12886)) | Empirical (Monte Carlo) only, no certified sets for the linear controller. |
| Detection-delay tolerance | Only an empirical figure (~180 ms) for a *different* vehicle (heli-quad, [arXiv 2011.07529](https://arxiv.org/html/2011.07529)) | No systematic delay-vs-state analysis for the plain quadrotor. |
| ROA of linear controllers | Lyapunov-based ROA for VTOL attitude loops ([IEEE 9143612](https://ieeexplore.ieee.org/document/9143612/)); SOS/LMI methods in general | None found for relaxed-hover under thrust saturation. |
| Failure continuum | Passive FTC for one-to-three rotor failures ([arXiv 2211.12972](https://arxiv.org/abs/2211.12972), withdrawn then republished); LPV/polytopic LMI for partial faults | Not a gap. Do not claim. |
| Observability / output feedback | General quadrotor estimation; vision-based flight with rotor failure ([arXiv 2102.13406](https://arxiv.org/abs/2102.13406)); magnetometer noise during spin | No systematic observability analysis of relaxed hover across sensor sets. |
| Sampling / lag margins | General quadrotor sampling studies; Mueller notes motor dynamics matter | No margin analysis specific to relaxed hover. |

### Verified against primary sources (read in full, 2026-10-09)
| Paper | What it actually does | Consequence for us |
|---|---|---|
| Mueller & D'Andrea, ICRA 2014 and IJRR (2015/16, read through §5; later sections on centre-of-mass offset and novel vehicles not read) | Linearization is **LTI in a body-fixed control frame** (5-state reduced attitude); controllability conditions derived analytically; motor lag (15 ms) included in the extended model and simulation; LQR + cascaded position loop; hardware validated. Simulations start *at the hover attitude with a 1 m offset*, **no noise, no disturbances, no failure transition**. Authors state the transition from stationary to the equilibrium is "non-trivial", and list sensing/estimation for rapidly rotating vehicles and robust mode transitions as **future research**. | Controllability is **not** novel. The time-periodic worry is resolved (LTI in these coordinates). Estimation, transitions and detection are explicitly open. |
| Sun et al. 2020 (arXiv 2002.09425) | Recovery from arbitrary attitude/rates via QP allocation; the *attainable moment set* with non-negative thrust defines an "unrecoverable" angular-velocity component ω̃; 200-flight Monte Carlo (all recovered, 95% with <10 m drop); 71% (46/65) indoor throws. EKF with camera + IMU. | Partial, non-certified characterization of what thrust positivity does. No detection-delay analysis, no certified set, no observability analysis. Must be cited and differentiated. |
| Simha, Vadgama & Raha 2017 (arXiv 1704.00327) | Geometric controller with an **analytic region of attraction** (initial conditions in the sublevel set Ψ⁻¹[0,2) with ‖e_Ω(0)‖ < 2α(2−Ψ(0))); assumes the fault is already detected (T₄ ≡ 0); positive-thrust constraint is **only tested in simulation**, with no motor lag. | Certified regions for failed quadrotors **do exist** for a geometric controller. Our C1 must be framed as the LQR/LQG relaxed-hover controller *with* saturation, lag, delay, sampling and sensing, not as "first certified region". |
| Al Lawati & Akhtar 2026 (arXiv 2609.23918) | Path-invariance guarantee via quasi-static feedback linearization; local exponential convergence. States it **assumes a reliable FDI and an instantaneous transition** to the three-rotor mode. No saturation or lag in the theory; simulated in Drake. | Supports C2: guarantee-bearing work assumes zero detection delay. |
| Heli-quad (arXiv 2011.07529) | ~180 ms maximum tolerable FDI delay found **empirically by simulation sweeps** (different vehicle, ~600 g). | Detection-delay tolerance is only known empirically, for another vehicle. |

**A technical issue this reading exposed.** The linear certificate is local. The most common failure-onset state, near-hover, is *far* from the spinning equilibrium (yaw rate 0 → ~20 rad/s). In M&D's 2014 hardware run, the vehicle first uses two propellers to spin up to 10 rad/s before the LQR is enabled. So the ellipsoid will **not** contain a hover-onset state, and a purely linear certificate would miss the main scenario. The design must be two-phase (transition controller + certified capture region). Whether the transition lands inside the certified set can be checked by nonlinear simulation or reachability/SOS, which is a validation, not a proof. This weakens the "certified recoverable set from failure onset" headline unless handled, so the first deliverable after the model is to measure how large the certified region is relative to the onset states of interest.

### Claimed contributions
- **C1 (main): certified recoverable set.** For the relaxed-hover controller, compute an invariant, certified region of failure-onset states (Lyapunov level set via LMI, with thrust saturation modelled by sector/polytopic conditions), and show how it shrinks with motor lag, detection delay and sampling period.
- **C2: critical detection delay.** A map from failure-onset state to the maximum tolerable detection delay τ\*(x₀), checked against the certified set.
- **C3: observability and output-feedback analysis.** (Controllability is already covered analytically by Mueller & D'Andrea, so only *observability* is claimed.) Observability of the linearized relaxed hover for several sensor sets (IMU only, IMU + position, IMU + magnetometer/yaw), the minimum sensor set needed, and the certified-set loss when moving from LQR to LQG.
- **C4: tightness check.** Compare certified sets against a nonlinear Monte Carlo (the conservatism gap), including the nominal controller from Mueller & D'Andrea as the baseline.

### Certainty (my judgment from the searches, not a measurement)
| Claim | Estimated chance it is unpublished | Main risk |
|---|---|---|
| C1 certified set for relaxed-hover LQR/LQG with saturation, lag, delay, sampling | ~60–65% | A certified region exists for a geometric controller (Simha 2017); individual LMI/ROA methods are standard; the linear region may be too small to matter (see technical issue above) |
| C2 detection-delay map | ~70–75% | Guarantee-bearing papers assume zero delay; only empirical delay figures elsewhere; may exist in paywalled papers I could not read |
| C3 observability across sensor sets | ~60% | Possibly covered inside estimation-focused or paywalled papers |
| Combination of C1–C4 as one study | ~60–65% | Each part partially exists; a reviewer could call it a collection of known tools |

The Todde et al. 2026 paper does not affect C1–C4 (healthy flight, no certification). I could not read the original Mueller & D'Andrea papers (2014, 2015) in full. **Before committing, read them** to check whether they already analyse motor lag, saturation margins, or the time-periodic structure of the linearization. If they do, narrow C1 accordingly.

For a course project, the bar is "a defensible, well-analysed contribution", and this plan meets it. Do not present the certainty numbers as proof of absence.

## 4. Course topics used (EE650 mapping)

| Course topic | Where it appears |
|---|---|
| State-space modelling, linearization | 6-DOF model, relaxed-hover equilibrium, (A, B) at the equilibrium |
| Controllability and observability, PBH test, rank/Gramian conditioning | §6.2, C3 |
| State feedback, pole placement, LQR | §6.3 |
| Observers, Kalman filter, LQG, separation principle (and where it fails) | §6.4, C3 |
| Lyapunov stability, quadratic Lyapunov functions, invariant sets | C1, §6.5 |
| LMIs and convex optimization | ROA/certificate synthesis (CVXPY/MOSEK or SCS) |
| Discretization and sampled-data control | Sampling-period sweep |
| Time delay and robustness margins | Delay augmentation, gain/phase/delay margins |
| Saturation and anti-windup (optional) | Anti-windup comparison |
| Time-periodic systems / rotating-frame transformation | §6.1 (if the linearization is periodic) |

## 5. Hypotheses

- **H1:** The relaxed-hover linearization is controllable from three rotors (with the spin phase as a non-controlled mode) and the LQR closed loop is stable with usable margins.
- **H2:** The certified region shrinks monotonically with detection delay, motor lag and sampling period, and a critical delay τ\* exists that depends strongly on failure-onset attitude and rate.
- **H3:** An IMU-only sensor set is insufficient for the output-feedback controller (position or yaw becomes unobservable). Adding position, or position + yaw, restores observability.
- **H4:** The certified set is a conservative but useful inner estimate of the nonlinear Monte Carlo recovery set (target: certified set covers at least ~30–50% of the empirical set by volume; the real number will be reported).

A clear negative on any hypothesis is still a valid result. Report it.

## 6. Technical design

### 6.1 Model
- 6-DOF rigid body, rotor 1 failed (thrust and torque zero). Inputs are the three working rotor thrusts, constrained to [0, f_max]. Include a first-order motor lag as an optional state.
- States for analysis: position, velocity, reduced attitude (thrust-axis direction), body rates, and motor states. Use Mueller & D'Andrea's formulation: a body-fixed control frame in which the relaxed hover is a constant solution, giving an LTI 5-state reduced-attitude system (ξ = (η₁, η₂, α₁, α₂, α₃) − equilibrium) with N_p − 1 inputs, plus motor-lag states. No Floquet analysis is needed in these coordinates (verified in the IJRR paper). The harder modelling question is the **spin-up transition** from the failure-onset state into this regime (§3).
- Compute the relaxed-hover equilibrium (spin rate, axis, rotor thrusts), and validate it against the published numbers from Mueller & D'Andrea.

### 6.2 Structural analysis (course core)
- Controllability matrix rank and PBH test of (A, B). Identify uncontrollable or marginal modes (yaw angle / spin phase) and show that they do not affect the regulated outputs.
- Observability for each sensor set C (IMU, IMU + position, IMU + mag). Report rank, PBH, singular values of the observability Gramian, and which states become unobservable.

### 6.3 State feedback
- LQR (Q, R sweep), pole placement for comparison, and integral action for position hold. Report poles, margins (gain/phase/delay margin) and closed-loop time responses.
- Discrete-time design at several sampling periods.

### 6.4 Output feedback
- Kalman filter and LQG built on the same model. Check the separation principle numerically, and show how saturation breaks it.
- Metric: certified-set shrinkage and degraded performance relative to full-state LQR.

### 6.5 Certified recoverable set (headline)
- Closed-loop with saturation: x⁺ = A x + B sat(K x). Use a **polytopic/sector representation of the saturation** (Hu–Lin / Tarbouriech-style) and solve an LMI problem for the largest ellipsoid {x : xᵀPx ≤ 1} that is positively invariant and contractive. Maximize volume or the extent along chosen axes.
- Extend with state augmentation for: motor lag (extra states), detection delay (delay buffer as extra states or a pre-switch open-loop phase), and sampling (discretization at different T_s).
- For detection delay: simulate the vehicle from failure onset x₀ with the healthy-mode controller still applied for τ seconds, then check whether the state at switch time lies inside the certified ellipsoid. Sweep τ and x₀ to build the map τ\*(x₀).
- The certificate is for the linearized model, so it is local. Quantify the gap with the nonlinear Monte Carlo (§6.6).
- Stretch: nonlinear certificate for a polynomial reduced model by SOS, if time permits (the ROA literature supports this approach).

### 6.6 Validation simulator
- Independent nonlinear simulator (RK4, rotor drag, motor lag, noise), different from the model used to design the controller.
- Monte Carlo over failure-onset states (attitude, rates, velocity) with ≥ 30 seeds per cell and a fixed pre-registered success criterion (reaches and holds a neighbourhood of the equilibrium, no crash, bounded altitude loss).
- Compare empirical recovery set vs certified set, and vs the Mueller & D'Andrea controller as the baseline.

## 7. Experiments

| # | Experiment | Output |
|---|---|---|
| E1 | Equilibrium and linear model validation | Match to published equilibrium; poles; (A, B) |
| E2 | Controllability / observability tables | Ranks, PBH, Gramian values per sensor set (C3) |
| E3 | LQR design + margins | Poles, gain/phase/delay margins vs Q, R |
| E4 | Certified ellipsoid (full-state, no lag) | Volume, extent along each axis |
| E5 | Effect of motor lag, sampling period, saturation | Certified volume vs parameter curves (C1) |
| E6 | Detection-delay map | τ\*(x₀) heatmaps and curves (C2) |
| E7 | LQG vs LQR | Certified-set loss, estimation error |
| E8 | Monte Carlo on nonlinear sim | Empirical recovery set; conservatism ratio (C4) |
| E9 | Ablation: anti-windup, Q/R choices, sensor sets | What most affects the certified set |

## 8. Milestones (assuming ≈ 8 weeks; scale as needed)

| Week | Deliverable | Gate |
|---|---|---|
| 0 (before start) | Read Mueller & D'Andrea 2014/2015 and the Upset Recovery paper in full | Claims C1–C3 confirmed or narrowed |
| 1 | Model, equilibrium, linearization; decide LTI vs periodic | Equilibrium matches the published one |
| 2 | Controllability/observability analysis; LQR design | H1 shown or revised |
| 3 | Discrete-time design; margins; simulator | Closed-loop stable in nonlinear sim |
| 4–5 | Certified ellipsoid via LMI; motor lag, sampling, saturation | Certified set exists and is non-trivial |
| 5–6 | Detection-delay map; LQG | H2, H3 results |
| 6–7 | Monte Carlo and tightness comparison | H4 result |
| 8 | Report, figures, code, presentation | Claims match evidence |

If the certified set is trivially small (LMI infeasible or near zero volume), stop and change the certificate (e.g., use a better Lyapunov function, a smaller saturation-aware design, or SOS) before building the other experiments.

## 9. Optional extensions (only after the core is done)
1. **Koopman residual (from the original proposal):** learn the mismatch between the linear model and the nonlinear sim with EDMDc, and test whether the certified set (or recovery set) grows. This keeps the proposal's idea as an add-on. Details are in `plan-v2-koopman-backup.md`. After reading Todde et al. 2026: it covers only healthy flight with parametric mismatch and an MLP residual, so it does not overlap with failure-regime use. I now put the Koopman-residual-under-rotor-loss idea at roughly 85–90% unpublished (up from ~80%), still limited by what search can see. Borrow from Todde: the residual is evaluated outside the QP and injected as a measured disturbance (keeps the QP convex), clipped to a bound d_max, with training data from randomized mass/inertia/motor-lag runs. Their stated future work (structured uncertainty bounds, formal guarantees) is what the §6.5 certificate could supply for the failed vehicle.
2. **Gain-scheduled / LPV controller across failure severity.** The continuum is already covered by existing passive-FTC work, so treat it as a comparison, not a contribution.
3. **MPC comparison:** linear MPC with the same model vs the LQR certified set.
4. **Two-opposite-rotor loss** as a second case.

## 10. Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Linear certificate does not cover the hover-onset states (transition needs a nonlinear spin-up phase) | **High** | Two-phase design; measure the certified region against onset states first; use SOS/reachability or nonlinear-sim landing checks for the transition; reframe headline if the region is small |
| ~~Linearization is time-periodic~~ | Resolved | M&D's linearization is LTI in a body-fixed control frame (5-state reduced attitude) |
| Certified set is very conservative | High | Report the conservatism honestly (H4); use better Lyapunov functions, local tightening, or SOS |
| LMI problem too large with delay augmentation | Medium | Keep delays in a small number of samples; use lifted/small-gain alternatives |
| Result already exists in the original M&D papers | Unknown | Read them in week 0 and narrow claims |
| "Collection of known tools" criticism | Medium | Emphasize the unified question, the delay/lag/sampling parameter study, and the tightness check |
| Scope creep into learning or MPC | High | Extensions only after the core gate |

## 11. Repository layout

```
rotor-failure-project/
├── project-proposal.pdf
├── plan.md                       # this file (v3)
├── plan-v2-koopman-backup.md     # previous Koopman plan
├── model/       # nonlinear model, equilibrium, linearization, discretization
├── analysis/    # controllability, observability, margins, Floquet (if needed)
├── control/     # LQR, pole placement, LQG, anti-windup
├── certify/     # LMI invariant-set / ROA synthesis, delay and lag augmentation
├── sim/         # independent nonlinear simulator, Monte Carlo scenarios
├── experiments/ # E1–E9 scripts, configs, seeds
├── results/     # figures, tables
└── tests/       # equilibrium and linearization checks
```
Stack: Python (NumPy/SciPy/python-control), CVXPY + SCS/MOSEK for LMIs, Matplotlib. MATLAB is a reasonable alternative for the course (Control System Toolbox + YALMIP).

## 12. Immediate next steps
1. Read Mueller & D'Andrea 2014 and 2015 in full, and the Upset Recovery paper; note what they already analyse.
2. Derive the model and decide the coordinates (LTI vs periodic).
3. Reproduce the relaxed-hover equilibrium and the LQR stabilization (E1, E3).
4. Run the controllability/observability analysis (E2) as the first deliverable.
