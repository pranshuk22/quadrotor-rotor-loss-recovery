# 5. Koopman Models and MPC

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

Models trained on family A (40 × 4 s), normalized RMSE:

| Predictor | A, 0.1 s | A, 1 s | A, 3 s | B, 1 s |
|---|---|---|---|---|
| Analytical | 3.17 | 7.09 | 14.0 | 7.94 |
| Full-state EDMDc | 0.17 | 0.91 | 14.1 | 26.2 |
| Residual EDMDc | **0.15** | **0.64** | 6.23 | 19.9 |
| No change | 2.42 | 2.38 | 2.56 | 2.44 |

- On family A the residual model is the most accurate predictor at every horizon from 100 ms on; at 20 and 50 ms the full-state model is slightly better.
- Full-state EDMDc: 4 of 55 eigenvalues outside the unit circle (spectral radius 1.0070); it falls behind "no change" by 2 s. At 2 s the residual model is also behind "no change", so long open-loop horizons need feedback.
- Data efficiency (0.5 s horizon): residual with 10 episodes, 0.42; full-state with 40, 0.48.
- **Generalization fails:** on family B both learned models are worse than the analytical model. Training on randomized plants (one random plant per episode) helps the residual model on B only up to about 100 ms (3.68 vs 4.31 for the analytical model) and makes both models worse on A (residual 15.7 at 1 s; the full-state model diverges, spectral radius 1.028). A static regression cannot infer per-plant parameters (motor lag, thrust loss) from one state sample.

## 5.4 MPC (`FailureMPC`)
- Prediction model: the nominal discrete model (10 states). Horizon N = 20 (100 ms). Stage cost from `failure_weights()`, terminal cost from the discrete Riccati equation. Input bounds [f_min − f̄, f_max − f̄].
- Residual-Koopman MPC: the residual is evaluated at the current state with the previous input, outside the QP, and held constant over the horizon as a measured disturbance (as in Todde et al. 2026). The QP stays convex.
- Solver: OSQP via CVXPY parameters (warm start, eps 1e-5). The controller keeps its own filter f̂ of its commands.

## 5.5 Closed-loop results (E7, `results/tables/e7_mpc_closed_loop.md`)

Steady altitude error near the relaxed hover, broken down by mismatch effect (one start 1 m below the set-point per plant, 8 s, mean over the last 2 s; the steady state does not depend on the start):

| Plant | LQR | MPC, analytical | MPC, residual Koopman | Residual MPC vs LQR |
|---|---|---|---|---|
| A (full) | −0.285 m | −0.286 m | **−0.193 m** | −32% |
| A without thrust loss | −0.154 m | −0.154 m | −0.066 m | −57% |
| nominal + A's thrust loss only | −0.100 m | −0.101 m | −0.033 m | −67% |
| B (full, held out) | −0.029 m | −0.033 m | +0.022 m | −25% |
| B without thrust loss | +0.112 m | +0.111 m | +0.164 m | **+47%** |
| nominal + B's thrust loss only | −0.174 m | −0.177 m | −0.107 m | −39% |

- Timing: median 0.73 ms per step inside OSQP, 4.4 ms wall clock through CVXPY. The sample period is 5 ms, so a real-time version would call the solver directly.
- As capture controllers after a detection delay (truth A; spin-up at 2.95 N, then the controller; capture judged against each controller's own closed-loop steady state on A), LQR is SAFE up to τ = 10 ms and both MPCs only at τ = 0. The likely bottleneck is the validity of the linear prediction model far from the spin, not constraint handling.

## 5.6 Not done yet
- MPC on the full-state Koopman model (proposal controller 2), task K5.
- Offset-free MPC / integral action as the classical baseline for bias removal, task K6.
- Online residual adaptation (recursive least squares on W), task K7.
- Residual trained on spin-up transients; air-relative thrust in the truth plant, tasks K8, K11.
