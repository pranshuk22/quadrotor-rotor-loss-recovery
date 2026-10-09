# Work Plan (v5): both research questions

Companion to `proposal.md`. Status and schedule are tracked in `../progress/task-list.md`. The v4-only plan is in `../history/v4-work-plan.md`.

## Shared foundation (done)
- Nonlinear 6-DOF simulator of the Mueller & D'Andrea vehicle: rotor gyroscopics, thrust limits, motor lag, failure injection, detection-delay supervisor (`rotorfail/`).
- Relaxed-hover equilibrium validated (E1). Healthy and failed linear models, controllability/observability (E2). LQR designs (E3).
- **Truth plants** for learning: family A (training) and family B (held out), plus randomized families. All of them add effects the nominal model lacks: thrust loss at high body rate, inertia error, different motor time constant (`rotorfail/params.py`).

## Track 1: RQ1, residual Koopman MPC (from the proposal PDF)

| Step | Content | Status |
|---|---|---|
| 1.1 | Data: closed-loop failure-LQR episodes with random command excitation, 5 ms sampling | done (`rotorfail/koopman.py`) |
| 1.2 | Nominal predictor: ZOH-discretized M&D LTI model + motor states | done |
| 1.3 | Full-state EDMDc (degree-2 dictionary, 55 lifted states): spectrum, multi-step error | done (E6) |
| 1.4 | Residual EDMDc: one-step residual regression on the same dictionary, clipped at d_max | done (E6) |
| 1.5 | Multi-step comparison vs the no-change baseline; data efficiency; held-out family | done (E6) |
| 1.6 | MPC (QP, OSQP): analytical, and residual-corrected as a measured disturbance | done (E7, first version) |
| 1.7 | MPC on the full-state Koopman model (PDF controller 2) | next (E8) |
| 1.8 | Offset-free MPC / integral action as the classical baseline for bias removal | next (E8) |
| 1.9 | Online residual adaptation (recursive least squares on W), motivated by the generalization result | next (E8) |
| 1.10 | Residual trained on spin-up transients (to help capture far from the equilibrium) | later |
| 1.11 | Dictionary/regularization ablations; sensor noise | later |

## Track 2: RQ2, certified detection-delay budget

| Step | Content | Status |
|---|---|---|
| 2.1 | Empirical τ sweep + Monte Carlo with the published strategy | done (E4) |
| 2.2 | First saturation-aware LMI certificate (LTI) + nonlinear conservatism | done (E5) |
| 2.3 | LPV model in r; r-robust capture certificate (common P, then P(r)) | next |
| 2.4 | Reachable set of the undetected phase; switch map; containment LMI; τ\* by bisection | next |
| 2.5 | τ\* trade study: healthy tuning, idle thrust, thrust-to-weight, motor lag, sampling | later |
| 2.6 | τ\* per capture controller: LQR, analytical MPC, residual-Koopman MPC (certificate with a bound on the true mismatch and an MPC terminal-set argument) | later |
| 2.7 | Monte Carlo tightness; LQG / output feedback | later |

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| Residual does not generalize across vehicles (seen in E6) | Online RLS adaptation; report the limitation and the per-vehicle use case |
| Full-state Koopman MPC unusable (unstable predictor) | Report it as the expected failure mode (PDF §5); use a stabilized fit only as a sensitivity check |
| Common-P LMI over r infeasible | Parameter-dependent P(r), or a staged funnel of nested ellipsoids |
| Certificates too conservative | Report the ratio; parameter-dependent Lyapunov functions; SOS on a polynomial model (stretch) |
| Stephan 2018 overlaps C2 | Keep C1, C3 and the RQ1–RQ2 link as the headline |

## Code layout
See `../README.md`.
