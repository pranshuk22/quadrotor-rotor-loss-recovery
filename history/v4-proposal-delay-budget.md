# How Long Can a Quadrotor Wait? Certified Fault-Detection-Delay Budgets for Recovery from Complete Rotor Loss

**Course:** EE650, Basics of Modern Control Systems  **Scope:** simulation and analysis only  **Version:** v4 (2026-10-09)
**Supersedes:** `history/v3-plan-certified-recoverability.md`. The Koopman idea (v1/v2) is kept as an optional extension (see `work-plan.md` §6).

---

## 1. Problem in one paragraph

When one rotor of a quadrotor fails completely, the vehicle can no longer hover level. Its only steady state is the **relaxed hover** of Mueller & D'Andrea (2014): a constant spin (~20 rad/s) about a tilted body axis, with translation obtained by tilting that axis. Linear controllers (LQR, H∞ loop-shaping, LPV) stabilize this spin in flight tests. But they all assume something that never holds in practice: that the failure-mode controller is switched on **at the instant the rotor fails**. In reality, a fault-detection module needs **τ ≈ 30–130 ms** (reported in recent detectors) before it reports the fault. During that window the *healthy* controller keeps running on a vehicle that has lost a rotor. It chases a yaw error it can no longer correct, may saturate the surviving rotors, and lets the attitude drift. After τ, the failure controller must capture the vehicle from wherever it is.

Today the only answer to *"how large can τ be?"* is empirical: one simulation-sweep number (180 ms) for a different vehicle, and qualitative remarks that linear failure controllers "could fail" after large upsets. **No one has a guaranteed delay budget.**

## 2. Research question

> **For a quadrotor that loses one rotor completely, what is the largest fault-detection delay τ\* for which recovery into the relaxed hover is *guaranteed*, given the healthy controller in use, the failure-mode controller, thrust saturation, motor lag and sampling? How does τ\* depend on these design choices?**

The answer is a number an engineer can use. It is the **specification the fault detector must meet**, derived from the control design rather than guessed.

## 3. Approach: three sets and one containment test

The failure event is a three-phase switched system:

```
 healthy flight ──(rotor fails, t=0)──► Phase A: undetected ──(detected, t=τ)──► Phase B: failure-mode control ──► relaxed hover
   x0 ∈ X0                         healthy LQR on a 3-rotor vehicle            capture controller (LQR / gain-scheduled)
```

| Set | Meaning | How it is computed (all LMI / linear-algebra tools from the course) |
|---|---|---|
| **X0** | Pre-failure states (normal flight disturbances around hover) | Ellipsoid from the healthy closed-loop's steady-state covariance or a chosen envelope |
| **R(τ)** | Everything the vehicle can reach during the undetected window | Phase A is **affine LTI**: ẋ = A_f x + d, where A_f is the healthy closed loop with the failed rotor's input column zeroed and d is the lost trim thrust/torque. So R(τ) = e^{A_f τ} X0 ⊕ {∫₀^τ e^{A_f s} d ds}, an exact shifted ellipsoid. We check analytically, from support functions, that no surviving rotor saturates; if one does, we use a saturation-aware outer bound. |
| **C** | Certified capture set of the failure-mode controller | Largest ellipsoid {ξ : ξᵀPξ ≤ 1} that is **positively invariant and contractive** for the reduced-attitude dynamics under **thrust saturation** (sector / Hu–Lin polytopic conditions) and **robust over the spin-up yaw rate** r ∈ [r_onset, r_eq] (see §4) |

**Certified delay budget:**  τ\* = sup { τ : M·R(τ) ⊆ C },
where M is the (linearized) map from hover coordinates to reduced-attitude coordinates at the switch. Ellipsoid-in-ellipsoid containment is an exact LMI (S-procedure), so τ\* follows by bisection on τ.

## 4. The key technical step: certifying through the spin-up

Version v3 had a fatal gap. A capture set built from the linearization **at** the relaxed hover is local. A hover-onset state has yaw rate r ≈ 0, which is ~20 rad/s away from the equilibrium, so the ellipsoid can never contain it.

**Fix used here.** In Mueller & D'Andrea's reduced-attitude coordinates, the yaw rate r enters the remaining dynamics **bilinearly**. The reduced attitude n (inertial vertical in body axes) obeys ṅ = −ω × n, and the roll/pitch rates carry gyroscopic terms (I_zz − I_yy) q r. So with r treated as a time-varying parameter, the (n_x, n_y, p, q) subsystem is a **linear parameter-varying (LPV) system, affine in r**. In addition:
- r itself obeys a scalar, damped first-order equation (net rotor drag torque − yaw damping), so it rises monotonically from ~0 into a known interval [r_onset, r_eq + δ] with a bounded ṙ;
- because A(r) is affine in r, a **common quadratic Lyapunov function** checked at the two interval endpoints (vertex LMIs) certifies the whole interval;
- the r-dependent trim enters as a bounded disturbance −(∂x̄/∂r)·ṙ, which is handled with the standard invariant-ellipsoid-under-bounded-disturbance LMI (Boyd et al. 1994, ch. 6).

This turns the capture certificate into a **robust, saturation-aware invariant set valid from hover onset to the relaxed hover**. It is the piece that makes the delay budget meaningful for the main scenario (failure during hover or cruise).

*Credit:* scheduling on yaw rate is not new as a **synthesis** idea (Stephan, Schmitt & Fichter, JGCD 2018). We use it for **analysis and certification under saturation and detection delay**, which that line of work does not report, as far as the accessible literature shows (see `novelty-and-claims.md`).

## 5. Contributions

| ID | Contribution | Status |
|---|---|---|
| **C1** (main) | **Certified fault-detection-delay budget τ\*** for complete single-rotor loss, from the reachable set of the undetected phase and the capture set of the failure controller | Not found in the literature |
| **C2** | **Saturation-aware capture set that is robust over the spin-up yaw rate**, so it contains hover-onset states (resolves the v3 locality problem) | Not found as an analysis result; LPV synthesis exists (Stephan 2018) |
| **C3** | **Design trade-study of τ\***: how it moves with healthy-controller aggressiveness, thrust-to-weight ratio, motor lag, sampling period and the failure controller (fixed LQR vs gain-scheduled) | Follows from C1; the healthy-controller dependence has not been studied |
| **C4** | **Tightness check**: certified τ\* vs empirical τ\* from a nonlinear Monte Carlo (conservatism ratio) | Validation |
| C5 (stretch) | **Failure-aware tuning of the healthy controller**: pick healthy LQR weights that maximize τ\* while keeping nominal performance | Not found |

Supporting course content, *not* claimed as novel: controllability (already shown by Mueller & D'Andrea), observability for different sensor sets, LQG and the reduction in τ\* under output feedback.

## 6. Hypotheses (each one can fail; failures get reported)

- **H1:** The capture set from the linearization at r_eq alone does **not** contain hover-onset states. The r-robust set (C2) **does**, for realistic thrust-to-weight ratios (≥ ~1.8).
- **H2:** τ\* is finite and of the same order as real detector delays (tens to ~200 ms), so the budget actually constrains detector design.
- **H3:** A more aggressive healthy controller **reduces** τ\*, because it drives the surviving rotors into saturation while chasing the uncorrectable yaw error. (The opposite result, that aggressive control helps by holding attitude, is equally informative.)
- **H4:** τ\* falls monotonically with motor lag and sampling period.
- **H5:** The certified τ\* is within a factor of ~2–3 of the empirical τ\* from nonlinear Monte Carlo.
- **H6:** Moving from state feedback to LQG lowers τ\* by a measurable, reportable amount.

## 7. Method summary (details in `work-plan.md`)

1. **Model.** 6-DOF nonlinear quadrotor with rotor drag torque, first-order motor lag and thrust limits [0, f_max]. Healthy hover linearization (12 states + motor states). Mueller & D'Andrea reduced-attitude model (n_x, n_y, p, q; r as a parameter) for the failed vehicle. Reproduce their published equilibrium.
2. **Structural analysis.** Controllability (rank/PBH) is a reproduction. Observability for IMU-only, IMU + position and IMU + magnetometer sensor sets.
3. **Controllers.** Healthy LQR (with a Q/R family from soft to aggressive). Failure LQR at r_eq (Mueller & D'Andrea baseline). Gain-scheduled LQR K(r) (Stephan-style). Discrete-time versions at several T_s.
4. **Sets.** X0, R(τ), C via CVXPY (SCS/MOSEK) LMIs; τ\* by bisection.
5. **Validation.** An independent nonlinear RK4 simulator with noise and motor lag. A Monte Carlo over onset states × τ gives the empirical τ\*, which is compared with the certified value.

## 8. EE650 topics this project exercises

State-space modelling and linearization · controllability/observability (rank, PBH, Gramians) · state feedback, pole placement, LQR · observers, Kalman filter, LQG, separation principle · Lyapunov stability, quadratic Lyapunov functions, invariant sets · LMIs/convex optimization · LPV/gain scheduling · actuator saturation · sampled-data control, discretization · time delay and switching.

## 9. Scope and honest limits

- The capture certificate covers the **attitude (reduced-attitude) recovery**. Altitude loss and position recovery are measured in simulation and bounded only roughly; they are not certified.
- All certificates are for **linear/LPV models** with explicit saturation. The nonlinear Monte Carlo measures how much this costs (H5).
- Phase A uses the hover linearization. It is valid only while the vehicle stays near hover, which holds for the short windows of interest (τ ≲ 0.3 s). This validity is checked in simulation and reported.
- Novelty statements mean "not found in the searches logged in `literature/search-log.md`", not proof of absence. Two key related papers (Stephan 2018, Lanzon 2014) are paywalled and **must be read before submission** (see `work-plan.md` §1).

## 10. Key references

1. M. W. Mueller, R. D'Andrea. Stability and control of a quadrocopter despite the complete loss of one, two, or three propellers. ICRA 2014; Relaxed hover solutions for multicopters. IJRR 2016.
2. J. Stephan, L. Schmitt, W. Fichter. Linear parameter-varying control for quadrotors in case of complete actuator loss. JGCD 41(10), 2018. doi:10.2514/1.G003441
3. A. Lanzon, A. Freddi, S. Longhi. Flight control of a quadrotor vehicle subsequent to a rotor failure. JGCD 37(2), 2014.
4. S. Sun, M. Baert, B. Strack van Schijndel, C. de Visser. Upset recovery control for quadrotors subjected to a complete rotor failure from large initial disturbances. ICRA 2020. arXiv:2002.09425
5. F. Nan, S. Sun, P. Foehn, D. Scaramuzza. Nonlinear MPC for quadrotor fault-tolerant control. RA-L 2022. arXiv:2109.12886
6. S. Sun, X. Wang, Q. Chu, C. de Visser. Incremental nonlinear fault-tolerant control of a quadrotor with complete loss of two opposing rotors. T-RO 2020. arXiv:2002.07837
7. E. Kulkarni, N. Sundararajan, S. Sundaram. Heli-quad design for full-attitude fault-tolerant control under complete failure of an actuator. arXiv:2011.07529
8. M. Al Lawati, A. Akhtar. Quasi-static fault-tolerant feedback control of a quadrotor under rotor failure with provable safety guarantees. arXiv:2609.23918 (2026)
9. P. Simha, A. Vadgama, R. Raha (2017). A geometric approach to rotor failure tolerant trajectory tracking control design for a quadrotor. arXiv:1704.00327
10. Failure detection and recovery for quadrotors in the presence of severe rotor failures with multiple-model L1 adaptive controller. IEEE (2025), doc. 11235993 (detection delays 30–130 ms)
11. F. Stoican, S. Olaru. Set-Theoretic Fault-Tolerant Control in Multisensor Systems. Wiley-ISTE, 2013 (general set-based FTC methodology)
12. T. Hu, Z. Lin. Control Systems with Actuator Saturation: Analysis and Design. Birkhäuser, 2001
13. S. Boyd, L. El Ghaoui, E. Feron, V. Balakrishnan. Linear Matrix Inequalities in System and Control Theory. SIAM, 1994
14. E. Todde, S. Martini, A. Rizzo, K. Valavanis. Residual Koopman-based MPC of quadrotors. ICUAS 2026 (healthy flight only; relevant to the optional Koopman extension)
