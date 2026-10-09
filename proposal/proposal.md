# Fault-Tolerant Control Under Complete Rotor Loss via Physics-Informed Residual Koopman MPC, with Certified Fault-Detection-Delay Budgets

**Course:** EE650, Basics of Modern Control Systems  **Scope:** simulation and analysis only  **Version:** v5 (merged), 2026-10-10

This document contains the full revised proposal as submitted (`history/v1-proposal-koopman.pdf`, §1–5 and §8, kept with its wording) and completes it with the two sections the PDF did not include (§6 and §7). Those sections add the control-theoretic certification layer developed afterwards (v4, see `history/CHANGELOG.md`). Text added beyond the PDF is marked **[added]**.

---

## 1. Summary of Revisions

Following your feedback on our earlier proposal, we went back and re-audited the literature in detail. You were right: both "Koopman-based control for quadrotors" and "Koopman-based control for actuator faults" already exist in the 2024–2026 literature, including recent work applying residual Koopman modeling to quadrotors directly. We are grateful for the correction, since it forced us to find a more precise and defensible research question rather than a generic application of a known method.

The revised proposal below identifies a narrower, more specific gap and states our novelty claim carefully, as something we did not find in an extensive search rather than as an absolute claim.

**[added]** A further audit after the proposal (2026-10-09) led to one extension, which keeps everything above unchanged. A data-driven predictor says nothing about *where* recovery is guaranteed, and most recovery methods with guarantees assume the failure is detected *instantly*. We therefore add a second, control-theoretic research question (RQ2, §6): a certified bound on the tolerable fault-detection delay. The residual Koopman MPC of RQ1 is one of the capture controllers this bound evaluates.

---

## 2. The Revised Research Question

> **RQ1.** Can a Koopman/EDMDc residual model, built around the analytically known spinning-equilibrium dynamics of a completely failed quadrotor, provide a better long-horizon predictive model for MPC than either the analytical failure model alone or a generic full-state Koopman model?

> **RQ2 [added].** For a quadrotor that loses one rotor completely, what is the largest fault-detection delay τ\* for which recovery into the spinning equilibrium is *guaranteed*, given the healthy controller, the failure-mode (capture) controller, thrust saturation, motor lag and sampling? How do the capture controllers of RQ1 change τ\*?

**What is genuinely different from existing work, and why we believe it is defensible:**

- Existing Koopman fault-tolerant control (e.g., Lee et al., 2024) addresses **partial loss-of-effectiveness** faults, where all four rotors remain active and the vehicle retains full attitude authority.
- Existing residual Koopman work on quadrotors (Todde et al., 2026) and quadrupeds (Narayanan & Vaidya, 2026) addresses **nominal operation under model/parameter uncertainty**, not actuator loss.
- **Complete rotor loss is structurally different from both**: one column of the actuator-mixing map vanishes entirely, yaw authority is lost, and the vehicle is forced into a qualitatively different regime (a continuous spinning equilibrium) rather than a degraded version of normal hover.

We could not find residual Koopman modeling applied specifically to this complete-loss, spinning-equilibrium regime, across searches spanning direct term combinations, citation trails from the Mueller & D'Andrea paper, and adjacent "reduced attitude" terminology. We state this as the result of our search, not as a claim that it does not exist anywhere.

**[added] For RQ2:** most recovery methods with a guarantee assume the failure-mode controller starts at the instant of failure (Simha et al. 2017; Al Lawati & Akhtar 2026 state "a reliable FDI module and an instantaneous transition"). Başak & Prempain (ECC 2015) prove stability for a switched linear model with a fixed detection delay, without thrust saturation and without computing the largest tolerable delay. Reported tolerances are empirical (180 ms for the heli-quad; recovery with 0.1 to 0.18 s of delay for nonlinear controllers, Chen et al. 2025, Zhou et al. 2025). Fast detectors report 30 to 130 ms (Strack van Schijndel et al. 2021). We did not find a certified *maximum* tolerable delay under thrust saturation. Mueller & D'Andrea list "a fault detection scheme ... and switching strategies for transitioning from four propellers to three" as future work. Details: `novelty-and-claims.md`.

---

## 3. The Architecture

1. Complete rotor failure
2. Spinning equilibrium (Mueller & D'Andrea)
3. Learn residual with EDMDc
4. MPC

- A generic Koopman-MPC approach asks a data-driven model to learn the entire post-failure dynamics from scratch.
- In our own preliminary testing (Section 5 below), this produced a numerically unstable learned model.
- Instead, we provide the dominant post-failure physics analytically, via Mueller & D'Andrea's spinning-equilibrium model.
- We then ask the learned model to represent only the mismatch:

  e_k = x_k^true − x_k^nominal

We then build three controllers on the same simulator and compare them directly:

1. **MPC on the analytical nominal model alone** (no learning)
2. **MPC on a full-state Koopman model** (our original approach, retained as a baseline precisely because we found it to be unstable, which motivates the residual formulation)
3. **MPC on the residual Koopman model** (proposed approach)

**[added] Where the architecture sits in the failure timeline (RQ2):**

```
 healthy flight ──(rotor fails, t=0)──► undetected phase ──(detected, t=τ)──► capture controller ──► relaxed hover
   x0 ∈ X0                         healthy controller flies a 3-rotor vehicle      LQR / MPC (1–3 above)
```

The three MPCs above, plus LQR and the Mueller & D'Andrea spin-up strategy as reference controllers, are each evaluated by (i) prediction accuracy (RQ1), (ii) closed-loop recovery, and (iii) the detection delay they tolerate (RQ2).

---

## 4. Why Mueller–D'Andrea Specifically, Not an Arbitrary Nominal Model

This is the central technical justification for the approach, not a citation of convenience.

**Complete rotor loss is not "normal flight plus a disturbance."** After a rotor is completely lost, the vehicle permanently loses independent control of yaw, and it can no longer hover still. The only valid steady state remaining is a continuous spin about a fixed body axis, with translational motion achieved by tilting that spin axis. This is a genuinely different equilibrium, not a perturbed version of the previous one.

**An arbitrary nominal model would defeat the purpose of residual learning.** If we instead used a generic nominal model unaware of the failure (e.g., an ordinary hover template), it would keep predicting a vehicle sitting still and level, while the real vehicle is continuously spinning. The "residual" would then have to contain the entire spinning motion: a large, persistent signal, not a small correction. This does not simplify the learning problem; it relabels it. The benefit of residual learning depends entirely on the nominal model already capturing the *dominant* behavior.

**Mueller & D'Andrea's model is dominant-behavior-complete for this specific regime.** It is derived specifically for complete rotor loss and already provides, in closed form, the correct spin axis and spin rate, the correct steady-state thrust levels, and the correct relationship between axis tilt and translation. What remains for a residual to capture is genuinely second-order: blade flapping and induced-drag effects at high spin rate, inertia measurement error, motor lag, and similar effects not captured by their idealized derivation. This is plausibly a small, well-behaved residual, which is the regime EDMDc is best suited to.

**Two further practical advantages.** The model is linear and time-invariant once expressed as deviations from the equilibrium, making it cheap to compute and well understood, unlike attempting to correct around a constantly moving, otherwise-undefined target. **[added, verified]** This holds in body-fixed reduced-attitude coordinates (n = Rᵀe₃, body rates): there the relaxed hover is a fixed point, so no Floquet analysis is needed. It is also not a guess: it is experimentally validated (real quadrotor flight, one- and two-rotor loss) and analytically proven controllable, so the physics half of the architecture is trustworthy before any learning is introduced.

**Why we expect this to help, stated as a hypothesis, not a result.** The same pattern (a physics backbone with a learned correction for the remaining mismatch) has shown benefits in adjacent domains: soft robot arms, ground vehicles, and quadruped locomotion, consistently producing smaller and better-conditioned models than learning the full dynamics from data. There is a physically grounded reason to expect this to transfer to the complete-rotor-loss regime. Testing whether it does is the actual content of the project, not an assumption we are making going in.

---

## 5. Preliminary Evidence Motivating This Direction

Before arriving at this formulation, we built a proof-of-concept fitting a full-state EDMDc model to simulated (undamaged) quadrotor flight data. Diagnostic testing revealed that although the model was accurate one step ahead (comparable training and held-out error), the learned linear operator had 10 of 22 eigenvalues with magnitude greater than 1. This means errors compound exponentially rather than merely accumulate over a rollout, and the model underperformed a trivial "assume nothing changes" baseline beyond roughly half a second of open-loop prediction. This is a documented failure mode of full-state EDMD in the recent literature (e.g., Narayanan & Vaidya, 2026, who report a related SE(3)-Koopman baseline becoming unstable within seconds in simulation, motivating their own residual formulation). This finding is what motivated us to move from a full-state to a residual formulation, rather than treating it as background reading alone.

**[added] Progress since the proposal** (details in `../progress/presentation-1-plan.md`; tables and figures in `../results/`):
- Nonlinear simulator of the Mueller & D'Andrea vehicle; their equilibrium reproduced (thrusts, spin rate and n_z within 0.5%).
- Controllability/observability of the failed vehicle; LQR at the relaxed hover verified on the nonlinear model.
- In our simulation, the published recovery strategy recovers safely with probability above 0.9 only for detection delays up to about **12 ms** (below 0.5 beyond 19 ms; 40 random starts per delay, flight spin-up thrust), against 30–130 ms reported for real detectors (motivation for RQ2).
- First saturation-aware LMI certificate: covers 22% of the way to the hover-onset state, against 70% recovered in nonlinear simulation.
- **The proposal's preliminary finding, repeated in the failed regime (E6):** full-state EDMDc on failed-vehicle data has eigenvalues outside the unit circle (4 of 55) and falls behind the "no-change" predictor by 2 s. From 100 ms on, the residual model gives the lowest multi-step error on the training mismatch family (1 s horizon, normalized RMSE: residual 0.64, full-state 0.91, analytical 7.1, no-change 2.4). It needs less data (10 episodes beat full-state with 40).
- **Limitation found (E6):** neither learned model generalizes to an unseen mismatch family, and training on randomized vehicles helps the residual on the unseen family only up to about 100 ms while making both models worse on the training family. Next: online residual adaptation.
- **Closed loop (E7):** residual-Koopman MPC cuts the steady altitude bias under mismatch by 32% (−0.29 → −0.19 m) and reduces it on 5 of 6 test plants, but increases it by 47% on one held-out variant; the QP solver needs 0.7 ms per step. As a capture controller after a detection delay it does not yet beat LQR.

---

## 6. [added] Certified Fault-Detection-Delay Budget (RQ2)

**Problem.** A fault detector needs τ ≈ 30–130 ms. During that time the healthy controller flies a three-rotor vehicle. It cannot cancel the roll torque of the opposite rotor, because that rotor's thrust cannot go below idle, so roll acceleration is at least l·f_min/I_xx. After τ, the capture controller must recover the vehicle from wherever it is.

**Approach: three sets and one containment test.**

| Set | Meaning | Computation |
|---|---|---|
| X0 | Pre-failure states | Ellipsoid from the healthy closed loop |
| R(τ) | States reachable during the undetected window | Affine LTI: ẋ = A_f x + d, so R(τ) = e^{A_f τ}X0 ⊕ {∫₀^τ e^{A_f s} d ds}, an exact shifted ellipsoid; saturation checked by support functions |
| C | Certified capture set of the capture controller | Largest saturation-aware invariant ellipsoid (Hu–Lin LMIs), **robust over the spin-up yaw rate r** (the reduced-attitude dynamics are affine in r, so vertex LMIs suffice) |

τ\* = sup{τ : M·R(τ) ⊆ C}, found by bisection with an LMI containment test.

**Link to RQ1.** The residual Koopman MPC is a capture controller, so it can be compared with LQR by the delay it tolerates. A certificate for this loop needs two ingredients that the learned model does not supply by itself: a bound on the *true* plant mismatch over the family of plants considered (the clipping level d_max is a percentile of the training residuals, so it is not such a bound), and, because the controller is a constrained MPC, an argument that covers its constraints, such as the region where the MPC equals its unconstrained LQR law or a terminal-set condition. LMI certificates with bounded learned error (as in SafEDMD, Strässer et al. 2024) are the starting point.

**Contributions (RQ2).**
- C1: certified τ\* for complete single-rotor loss.
- C2: saturation-aware capture set robust over the spin-up yaw rate.
- C3: trade study of τ\* (healthy tuning, idle thrust, thrust-to-weight, motor lag, sampling, capture controller).
- C4: tightness against nonlinear Monte Carlo.

---

## 7. [added] Hypotheses, Experiments and Evaluation

### Hypotheses

| ID | Hypothesis | Source |
|---|---|---|
| H1 | Full-state EDMDc on the *failed* vehicle has spectral radius > 1 and loses to the "no-change" predictor at long horizons | PDF §5, now in the failure regime |
| H2 | The residual model has lower multi-step open-loop error than the analytical and full-state models | RQ1 |
| H3 | Residual Koopman MPC removes the steady bias of the analytical MPC under model mismatch (thrust loss at high spin, inertia error, motor lag) and enlarges the recovery region | RQ1 |
| H4 | The residual reaches a given prediction error with less data than full-state EDMDc | RQ1 (data scarcity: failed flights end in crashes) |
| H5 | The LTI capture certificate does not contain hover onset; the r-robust certificate does | RQ2 |
| H6 | τ\* is finite and of the same order as real detector delays | RQ2 |
| H7 | Certified τ\* is within about 2–3× of the empirical τ\* | RQ2 |

### Experiments

| # | Experiment | Status |
|---|---|---|
| E1 | Equilibrium and validation vs Mueller & D'Andrea | done |
| E2 | Controllability / observability | done |
| E3 | LQR designs, margins, nonlinear check | done |
| E4 | Empirical detection-delay sweep + Monte Carlo | done |
| E5 | First saturation-aware LMI certificate + conservatism | done (LTI) |
| E6 | Failed-regime data, full-state vs residual EDMDc, multi-step prediction, data efficiency, held-out family (H1, H2, H4) | done |
| E7 | Analytical MPC vs residual Koopman MPC in closed loop under mismatch (H3) | done (first version) |
| E8 | Full-state Koopman MPC (PDF controller 2); offset-free MPC baseline; online residual adaptation | next |
| E9 | r-robust capture certificate (H5); reachable sets; certified τ\* (H6) | next |
| E10 | τ\* for each capture controller (LQR, analytical MPC, residual Koopman MPC); trade study; Monte Carlo tightness (H7) | later |

### Simulation protocol (avoiding circularity)
The truth simulator is the full nonlinear model **plus effects absent from the nominal model**: thrust loss at high body rate (observed by Mueller & D'Andrea as a 2.4 m height offset), inertia error and a different motor time constant. Mismatch families are split into training and held-out sets. Seeds and thresholds are fixed before runs. All claims are scoped to simulation.

---

## 8. Key References

1. Mueller, M.W. & D'Andrea, R. (2014). *Stability and Control of a Quadrocopter Despite the Complete Loss of One, Two, or Three Propellers.* ICRA 2014.
2. Nan, F., Sun, S., Foehn, P., & Scaramuzza, D. (2022). *Nonlinear MPC for Quadrotor Fault-Tolerant Control.* IEEE RA-L.
3. Lee et al. (2024). *Koopman Fault-Tolerant Model Predictive Control for Multirotor with Actuator Fault.* (verified: J. D. Lee, H. Kim, Y. Kim, H. Bang, ICCAS 2024, doi:10.23919/ICCAS63016.2024.10773232)
4. Lee et al. (2024). *Data-Driven Fault Detection and Isolation for Multirotor System Using Koopman Operator.* J. Intelligent & Robotic Systems.
5. Narayanan & Vaidya (2026). *RK-MPC: Residual Koopman Model Predictive Control for Quadruped Locomotion in Offroad Environments.* arXiv:2604.04221. (verified in the full text: the SE(3)-KMPC baseline fails within about 5 s)
6. Todde, Martini, Rizzo, & Valavanis (2026). *Residual Koopman-Based Model Predictive Control of Quadrotors.* ICUAS 2026. (Read in full: `literature/notes/todde2026.md`.)
7. Bruder, D., Bombara, D., & Wood, R.J. (2025). *A Koopman-based residual modeling approach for the control of a soft robot arm.* IJRR.
8. Fu et al. (2025). *Residual Koopman Model Predictive Control for Enhanced Vehicle Dynamics with Small On-Track Data Input.*

**[added] References for RQ2 and the extended analysis**

9. Mueller, M.W. & D'Andrea, R. (2016). *Relaxed hover solutions for multicopters.* IJRR.
10. Stephan, J., Schmitt, L., & Fichter, W. (2018). *Linear parameter-varying control for quadrotors in case of complete actuator loss.* JGCD 41(10). **(to read: novelty gate for C2)**
11. Lanzon, A., Freddi, A., & Longhi, S. (2014). *Flight control of a quadrotor vehicle subsequent to a rotor failure.* JGCD 37(2).
12. Sun, S., Baert, M., Strack van Schijndel, B., & de Visser, C. (2020). *Upset recovery control for quadrotors subjected to a complete rotor failure from large initial disturbances.* arXiv:2002.09425.
13. Sun, S., Wang, X., Chu, Q., & de Visser, C. (2020). *Incremental nonlinear fault-tolerant control of a quadrotor with complete loss of two opposing rotors.* T-RO.
14. Kulkarni, E., Sundararajan, N., & Sundaram, S. *Heli-quad design for full-attitude fault-tolerant control under complete failure of an actuator.* arXiv:2011.07529.
15. Al Lawati, M. & Akhtar, A. (2026). *Quasi-static fault-tolerant feedback control of a quadrotor under rotor failure with provable safety guarantees.* arXiv:2609.23918.
16. Simha, P., Vadgama, A., & Raha, R. (2017). *A geometric approach to rotor failure tolerant trajectory tracking control design for a quadrotor.* arXiv:1704.00327.
17. Stoican, F. & Olaru, S. (2013). *Set-Theoretic Fault-Tolerant Control in Multisensor Systems.* Wiley-ISTE.
18. Hu, T. & Lin, Z. (2001). *Control Systems with Actuator Saturation: Analysis and Design.* Birkhäuser.
19. Boyd, S., El Ghaoui, L., Feron, E., & Balakrishnan, V. (1994). *Linear Matrix Inequalities in System and Control Theory.* SIAM.
20. Williams, M.O., Kevrekidis, I.G., & Rowley, C.W. (2015). *A data-driven approximation of the Koopman operator: extending dynamic mode decomposition.* J. Nonlinear Sci. (EDMD); Korda, M. & Mezić, I. (2018). *Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control.* Automatica (EDMDc for MPC).
