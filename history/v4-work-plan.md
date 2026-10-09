# Work Plan (v4): Certified Detection-Delay Budget

Companion to `proposal.md`. This file covers how the work gets done: tasks, experiments, milestones, risks and code layout.

## 1. Week 0: literature gate (before any code)

- [ ] Read Stephan, Schmitt & Fichter, JGCD 2018 (LPV, yaw-rate scheduling). Decide whether C2 stays or narrows.
- [ ] Read Lanzon, Freddi & Longhi, JGCD 2014.
- [ ] Re-read Mueller & D'Andrea IJRR §3–5 for the reduced-attitude equations and the published vehicle parameters (for E1).
- [ ] Get the detector-delay numbers (IEEE 11235993) to fix the τ range of interest.

**Gate:** C1 confirmed unpublished. If it is not, fall back to C3 (design study) + C2.

## 2. Technical tasks

### 2.1 Models (`model/`)
- Nonlinear 6-DOF with 4 rotors, thrust f_i ∈ [0, f_max], rotor drag torque κ f_i, first-order motor lag τ_m, optional rotor gyroscopic term, and failure injection at t = 0 (f_1 ≡ 0).
- **Healthy linearization** at hover: x = (position, velocity, Euler angles, body rates[, motor states]).
- **Failed-vehicle reduced-attitude LPV model:** ξ = (n_x − n̄_x(r), n_y − n̄_y(r), p − p̄(r), q − q̄(r)), with A(r), B(r) affine in r, plus the scalar yaw-rate equation. Compute trims as functions of r.
- **Switch map M:** linearized map from hover state (φ, θ, p, q) to ξ at the detection instant.
- Unit tests: equilibrium matches Mueller & D'Andrea; finite-difference Jacobians match the analytic ones.

### 2.2 Structural analysis (`analysis/`)
- Controllability rank/PBH for the healthy model, the failed model at r_eq, and along r ∈ [r_onset, r_eq] (minimum singular value of the controllability Gramian vs r).
- Observability for sensor sets S1 = IMU (gyro + accel), S2 = S1 + position, S3 = S1 + magnetometer/yaw. Report rank, PBH and Gramian conditioning.

### 2.3 Controllers (`control/`)
- Healthy LQR family K_h(α), with α scaling Q from "soft" to "aggressive".
- Failure LQR at r_eq (M&D baseline) and gain-scheduled K(r) (LQR at a grid of r, interpolated).
- Discrete-time versions at T_s ∈ {1, 2, 5, 10} ms. Kalman filter / LQG for the output-feedback runs.
- Report poles and gain/phase/delay margins.

### 2.4 Sets and certificate (`certify/`)
- **X0:** ellipsoid from the healthy closed-loop covariance under nominal disturbance (scaled by a factor β for sweeps).
- **R(τ):** affine reachable ellipsoid (closed form). Saturation check via support functions h_R(±e_i) on each surviving rotor command.
- **C:** maximize log det P⁻¹ (or the extent along chosen directions) subject to:
  - vertex Lyapunov LMIs at r = r_onset and r = r_eq (A(r) is affine, so the vertices suffice for a common P);
  - Hu–Lin saturation conditions (auxiliary gain H, with E(P) ⊂ L(H));
  - bounded-disturbance term for the moving trim (−∂x̄/∂r · ṙ, |ṙ| ≤ ṙ_max).
- **τ\*:** bisection on τ with the containment LMI M·R(τ) ⊆ C (S-procedure).
- Discrete-time and motor-lag versions via state augmentation.

### 2.5 Validation simulator (`sim/`)
- Independent nonlinear RK4 at 1 kHz, with motor lag, sensor noise and a different integrator/step from the design model.
- Success criterion (fixed before running E7): within 3 s, the reduced-attitude error enters and stays in a small ball around the relaxed hover, the vehicle does not flip, and the altitude loss stays below a chosen limit.

## 3. Experiments

| # | Experiment | Output | Tests |
|---|---|---|---|
| E1 | Equilibrium + linear models | Match to the published equilibrium; A(r), B(r) | — |
| E2 | Controllability / observability tables | Ranks, PBH, Gramian values per sensor set | course core |
| E3 | Healthy and failure controller designs | Poles, margins, time responses | course core |
| E4 | **Capture set: LTI-at-r_eq vs r-robust** | Does C contain hover onset? Volume, axis extents | **H1, C2** |
| E5 | Phase-A reachable sets | R(τ) over time; time to first saturation | C1 |
| E6 | **τ\* maps** vs X0 size, healthy aggressiveness α, thrust-to-weight, motor lag, T_s, failure controller | Curves and heatmaps | **H2–H4, C1, C3** |
| E7 | Nonlinear Monte Carlo | Empirical τ\*; conservatism ratio | **H5, C4** |
| E8 | LQG vs state feedback | τ\* reduction from estimation error | H6 |
| E9 | (stretch) Failure-aware healthy tuning | Pareto: nominal performance vs τ\* | C5 |

At least 30 seeds per Monte Carlo cell. Report confidence intervals and failure counts.

## 4. Milestones (≈ 8 weeks)

| Week | Deliverable | Gate |
|---|---|---|
| 0 | Literature gate (§1) | C1 confirmed |
| 1 | Models, equilibrium, linearizations (E1) | Equilibrium matches the published one |
| 2 | Structural analysis + controllers (E2, E3) | Closed loops stable in the nonlinear sim |
| 3 | **Capture set C (E4)** | **Critical gate:** C is non-trivial and contains hover onset. If not → §5 fallback |
| 4 | Reachable sets + τ\* pipeline (E5) | τ\* computed for the nominal case |
| 5 | τ\* trade study (E6) | H2–H4 answered |
| 6 | Monte Carlo + LQG (E7, E8) | H5, H6 answered |
| 7 | Stretch (E9) or buffer | — |
| 8 | Report, figures, presentation | Claims match evidence |

## 5. Risks and fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| Common-P LMI infeasible over the whole r interval | Medium | Parameter-dependent P(r) = P0 + r P1 (multi-convexity conditions); or split the interval into stages with nested ellipsoids (a "funnel" chain) |
| Positive-thrust limits make C tiny near r ≈ 0 | Medium | Use the gain-scheduled K(r); report the smallest r_onset at which capture is certifiable as a finding in its own right |
| Phase A leaves the hover-linearization validity region before τ\* | Low–medium | Bound the nonlinear terms as norm-bounded uncertainty, or report validity limits honestly |
| Certificates are very conservative (H5 fails badly) | Medium | Report the ratio; tighten with generalized sector conditions or SOS on a polynomial reduced model (stretch) |
| Stephan 2018 overlaps C2 | Unknown (week 0) | Keep C1 + C3 as the headline |
| "Collection of known tools" criticism | Medium | Lead with the question and the design insight (C3), not the tools |

## 6. Optional extensions (only after week 6)

1. **Koopman residual** (from v1/v2): learn the nonlinear-sim vs LPV-model mismatch with EDMDc and test whether it narrows the certified/empirical τ\* gap. Details: `../history/v2-plan-koopman.md`. Borrow from Todde et al. 2026: evaluate the residual outside the optimization and clip it to d_max.
2. Two opposite rotors lost.
3. Linear MPC capture controller vs LQR capture set.

## 7. Code layout (to create once week 0 passes)

```
model/       nonlinear model, trims, healthy + LPV linearizations, switch map
analysis/    controllability, observability, margins
control/     healthy LQR family, failure LQR, gain-scheduled K(r), LQG
certify/     X0, R(τ), capture-set LMIs, τ* bisection
sim/         independent nonlinear simulator, Monte Carlo
experiments/ E1–E9 scripts + configs + seeds
results/     figures and tables
tests/       equilibrium, Jacobian, LMI sanity checks
```
Stack: Python (NumPy, SciPy, python-control), CVXPY + SCS/MOSEK, Matplotlib. MATLAB + YALMIP is an equivalent alternative.
