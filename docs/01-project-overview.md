# 1. Project Overview

## The problem
A quadrotor that loses one rotor completely cannot hover level, because three rotors cannot produce zero yaw torque while carrying the weight. Mueller & D'Andrea (ICRA 2014, IJRR 2016) showed that it can still fly. It spins at a constant rate about a tilted body-fixed axis (the **relaxed hover**) and translates by tilting that axis. In body coordinates the relaxed hover is a fixed point, so linear time-invariant tools (linearization, LQR, LMIs) apply.

## Research questions

| | Question | Origin |
|---|---|---|
| **RQ1** | Can a Koopman/EDMDc **residual** model, built on the Mueller–D'Andrea spinning-equilibrium model, predict and control (inside MPC) better than the analytical model alone or a full-state Koopman model? | The proposal as presented (`history/v1-proposal-koopman.pdf`) |
| **RQ2** | What is the largest **fault-detection delay** τ\* for which recovery into the relaxed hover is **guaranteed**, given the healthy controller, the capture controller, thrust limits and motor lag? How do the RQ1 controllers change τ\*? | Added after the proposal (v4) |

The report and slides present the two as one merged story; the labels are kept here only for cross-referencing with the proposal and the task list.

**How they connect:** every capture controller (LQR, analytical MPC, residual-Koopman MPC) is compared by the delay it tolerates. Certifying the residual-corrected loop needs a bound on the true plant mismatch (the clipping level d_max is a percentile of the training residuals, not such a bound) and an argument that covers the MPC's constraints.

## The failure timeline

```
healthy flight ──(rotor 4 fails, t = 0)──► undetected phase ──(detected, t = τ)──► capture controller ──► relaxed hover
                                           healthy controller still
                                           flying a 3-rotor vehicle
```

## Status (10 October 2026)

| Area | Status | Where |
|---|---|---|
| Simulator, equilibria, linear models | Done, validated against 3 papers and flight data | `rotorfail/`, `docs/03-validation.md` |
| Controllability / observability, LQR | Done | E2, E3 |
| RQ1: predictors (analytical, full-state EDMDc, residual EDMDc) | Done, first version | E6 |
| RQ1: analytical MPC, residual-Koopman MPC | Done, first version | E7 |
| RQ1: MPC on the full-state Koopman model, offset-free baseline, online adaptation | Not started | task list K5–K7 |
| RQ2: P(safe) versus delay (Monte Carlo), first LTI certificate | Done | E4, E5 |
| RQ2: certificate over the spin-up (LPV), reachable sets, certified τ\* | Not started | task list D3–D6 |

Course milestones: final progress presentation on **31 October 2026**, journal-style final report due **13 November 2026**. The full task list is in `progress/task-list.md`, and the status and caveats are in `progress/status.md`.

## Headline results so far
1. The simulator reproduces the published two-rotor and three-rotor-loss equilibria to every digit, five hover solutions of the IJRR model within 4% (body-rate vector), and, at the thrust used in flight, the flight spin-up time within about 4% (0.65 s vs 0.62 s).
2. **RQ1.** From 100 ms on, the residual model has the lowest multi-step error on the training plant (1 s: 0.64 vs full-state 0.91 vs analytical 7.1) and needs less data (10 episodes: 0.42 vs full-state with 40: 0.48, at 0.5 s). It does **not** generalize to an unseen plant. The residual-Koopman MPC cuts a steady altitude error by 32% on the training plant, but increases it by 47% on one held-out variant.
3. **RQ2.** With the flight spin-up thrust, the published recovery strategy is safe with probability above 0.9 up to about **12 ms** of detection delay and below 0.5 beyond **19 ms** (7 and 14 ms at mg/2); fast detectors need 30–130 ms. The first LTI certificate covers 22% of the way to the hover-onset state (up to 70% recovers in simulation); the LQR fails only at spin rates ≤ 4.8 rad/s.

## Where things are

| Folder | Content |
|---|---|
| `proposal/` | The proposal (all content of the presented proposal + RQ2), novelty and claims, work plan |
| `progress/` | Status, task list, presentation plan, review reports |
| `docs/` | This documentation, the LaTeX report, the slide deck |
| `rotorfail/` | Python package (simulator, models, controllers, certificates, Koopman, MPC) |
| `experiments/` | One script per experiment (V0, E1–E7) |
| `results/` | Generated tables and figures |
| `tests/` | 46 automated tests (plus 1 expected failure documenting a published inconsistency) |
| `literature/` | Literature review, search log, paper notes, links to the papers |
| `history/` | Earlier proposal versions and changelog |
