# 5. Koopman Models and MPC (RQ1)

Code: `rotorfail/koopman.py`, `rotorfail/mpc.py`. Experiments: E6 (prediction), E7 (closed loop).

## 5.1 Data generation (`generate`)
- Truth plant: family A, B or randomized (`params.truth_family`, `params.random_family`). Rotor 4 failed.
- Controller: failure LQR designed on the **nominal** parameters, plus piecewise-constant random excitation on the commands (uniform ±0.35 N, held for 50 ms), clipped to the thrust limits (`ExcitedLQR`).
- Start: relaxed hover plus uniform perturbations (Δω ±2 rad/s, Δn ±0.15, z and v_z ±0.5).
- Sampling Ts = 5 ms (simulation at 1 ms). Episodes that diverge (|Δn| > 0.6) are discarded.
- Stored per episode: x (measured deviations, 7), u (command deviations, 3), and f̂ (the nominal first-order filter of the commands, which the controller knows; 3).

## 5.2 Predictors
**Nominal (analytical).** ZOH discretization of the M&D linear model with nominal motor states: s_{k+1} = A_d s_k + B_d u_k, with s = (x, f̂).

**Full-state EDMDc** (Korda & Mezić 2018). ξ = (p, q, r, n_x, n_y, v_z, f̂) (z excluded: it only integrates v_z). Dictionary ψ(ξ) = [1, ξ̃, all degree-2 monomials of ξ̃] on standardized ξ̃ (55 functions). Fit Z₁ ≈ Z₀Aᵀ + U₀Bᵀ by ridge regression (λ = 1e-6). Prediction lifts once, then iterates z ← Az + Bu, reads ξ from the linear coordinates, and integrates z from v_z.

**Residual EDMDc (proposed).** The one-step residual e_{k+1} = x_{k+1} − [A_d s_k + B_d u_k]_{1:7} is regressed on ψ(ξ_k, u_k) with ridge regression (λ = 1e-3). The prediction is the nominal step plus clip(Wψ, ±d_max), with d_max the 99.5th percentile of the absolute training residuals.

**Evaluation.** Open-loop rollouts with the recorded inputs, starting every 40 samples. Normalized RMSE: each state divided by its training standard deviation, averaged over the 7 states. Horizons from 5 ms to 3 s. The "no change" baseline holds the initial state.

## 5.3 Prediction results (E6, `results/tables/e6_koopman_prediction.md`)

Models trained on family A (40 × 4 s):

| Predictor | A, 0.1 s | A, 1 s | A, 3 s | B, 1 s |
|---|---|---|---|---|
| Analytical | 2.29 | 5.13 | 13.6 | 5.57 |
| Full-state EDMDc | 0.13 | 0.70 | 4.97 | 12.3 |
| Residual EDMDc | **0.11** | **0.42** | 3.55 | 11.8 |
| No change | 1.93 | 2.03 | 2.22 | 1.93 |

- Full-state EDMDc: 4 of 55 eigenvalues outside the unit circle (spectral radius 1.0054); it falls behind "no change" between 2 and 3 s.
- Data efficiency (0.5 s horizon): residual with 10 episodes, 0.32; full-state with 40, 0.43.
- **Generalization fails:** on family B both learned models are worse than the analytical model. Training on randomized plants makes both worse on A too (residual 7.9 at 1 s; the full-state model diverges, ρ = 1.019). A static regression cannot infer per-plant parameters (motor lag, thrust loss) from one state sample.

## 5.4 MPC (`FailureMPC`)
- Prediction model: the nominal discrete model (10 states). Horizon N = 20 (100 ms). Stage cost from `failure_weights()`, terminal cost from the discrete Riccati equation. Input bounds [f_min − f̄, f_max − f̄].
- Residual-Koopman MPC: the residual is evaluated at the current state with the previous input, outside the QP, and held constant over the horizon as a measured disturbance (as in Todde et al. 2026). The QP stays convex.
- Solver: OSQP via CVXPY parameters (warm start, eps 1e-5). The controller keeps its own filter f̂ of its commands.

## 5.5 Closed-loop results (E7, `results/tables/e7_mpc_closed_loop.md`)

Regulation, 8 starts 1 m below the set-point, 8 s:

| Controller | Plant A: steady altitude error | Plant B | QP time |
|---|---|---|---|
| LQR | −0.285 m | −0.029 m | n/a |
| MPC, analytical | −0.286 m | −0.033 m | 4.8 ms |
| MPC, residual Koopman | **−0.194 m** (−32%) | +0.022 m | 4.9 ms |

As capture controllers after a detection delay (truth A; spin-up, then the controller), neither MPC beats LQR, and both stop settling at τ ≥ 40 ms. The bottleneck is the validity of the linear prediction model far from the spin, not constraint handling.

## 5.6 Not done yet
- MPC on the full-state Koopman model (proposal controller 2), task K5.
- Offset-free MPC / integral action as the classical baseline for bias removal, task K6.
- Online residual adaptation (recursive least squares on W), task K7.
- Residual trained on spin-up transients; air-relative thrust in the truth plant, tasks K8, K11.
