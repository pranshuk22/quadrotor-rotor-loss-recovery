# 1. Project Overview

## The problem
A quadrotor that loses one rotor completely cannot hover level, because three rotors cannot produce zero yaw torque while carrying the weight. Mueller & D'Andrea (ICRA 2014, IJRR 2016) showed that it can still fly. It spins at a constant rate about a tilted body-fixed axis (the **relaxed hover**) and translates by tilting that axis. In body coordinates the relaxed hover is a fixed point, so linear time-invariant tools (linearization, LQR, LMIs) apply.

## Research questions

| | Question | Origin |
|---|---|---|
| **RQ1** | Can a Koopman/EDMDc **residual** model, built on the Mueller–D'Andrea spinning-equilibrium model, predict and control (inside MPC) better than the analytical model alone or a full-state Koopman model? | The proposal as presented (`history/v1-proposal-koopman.pdf`) |
| **RQ2** | What is the largest **fault-detection delay** τ\* for which recovery into the relaxed hover is **guaranteed**, given the healthy controller, the capture controller, thrust limits and motor lag? How do the RQ1 controllers change τ\*? | Added after the proposal (v4) |

**How they connect:** every capture controller (LQR, analytical MPC, residual-Koopman MPC) is compared by the delay it tolerates. Certifying the residual-corrected loop needs a bound on the true plant mismatch (the clipping level d_max is a percentile of the training residuals, not such a bound) and an argument that covers the MPC's constraints.

## The failure timeline

```
healthy flight ──(rotor 4 fails, t = 0)──► undetected phase ──(detected, t = τ)──► capture controller ──► relaxed hover
                                           healthy controller still
                                           flying a 3-rotor vehicle
```

## Status (progress review 1)

| Area | Status | Where |
|---|---|---|
| Simulator, equilibria, linear models | Done, validated against 3 papers | `rotorfail/`, `docs/03-validation.md` |
| Controllability / observability, LQR | Done | E2, E3 |
| RQ1: predictors (analytical, full-state EDMDc, residual EDMDc) | Done, first version | E6 |
| RQ1: analytical MPC, residual-Koopman MPC | Done, first version | E7 |
| RQ1: MPC on the full-state Koopman model, offset-free baseline, online adaptation | Not started | task list K5–K7 |
| RQ2: empirical delay sweep, first LTI certificate | Done | E4, E5 |
| RQ2: certificate over the spin-up (LPV), reachable sets, certified τ\* | Not started | task list D3–D6 |

The full task list is in `progress/task-list.md`, and the honest status and caveats are in `progress/status.md`.

## Headline results so far
1. The simulator reproduces the published two-rotor and three-rotor-loss equilibria to every digit, and five hover solutions of the IJRR model within 0.7%. **Known gap:** the real vehicle spun up ~30% faster than the model.
2. **RQ1.** The residual model has the lowest multi-step error on the training plant (1 s: 0.42 vs full-state 0.70 vs analytical 5.1) and needs less data. It does **not** generalize to an unseen plant. The residual-Koopman MPC cuts a steady altitude error by 32%.
3. **RQ2.** The published recovery strategy tolerates **≈ 10 ms** of detection delay (SAFE 20/20 at 0 ms, 6/20 at 20 ms, 0/20 at 50 ms); reported detectors need 30–130 ms. The first LTI certificate covers 22% of the way to the hover-onset state (70% recovers in simulation).

## Where things are

| Folder | Content |
|---|---|
| `proposal/` | The proposal (all PDF content + RQ2), novelty and claims, work plan |
| `progress/` | Status, task list, presentation plan, review reports |
| `docs/` | This documentation, the LaTeX report, the slide deck |
| `rotorfail/` | Python package (simulator, models, controllers, certificates, Koopman, MPC) |
| `experiments/` | One script per experiment (V0, E1–E7) |
| `results/` | Generated tables and figures |
| `tests/` | 45 automated tests |
| `literature/` | Literature review, search log, paper notes, PDFs |
| `history/` | Earlier proposal versions and changelog |
