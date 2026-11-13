# 1. Project Overview

## The problem
A quadrotor that loses one rotor completely cannot hover level, because three rotors cannot produce zero yaw torque while carrying the weight. Mueller & D'Andrea (ICRA 2014, IJRR 2016) showed that it can still fly. It spins at a constant rate about a tilted body-fixed axis (the **relaxed hover**) and translates by tilting that axis. In body coordinates the relaxed hover is a fixed point, so linear time-invariant tools (linearization, LQR, LMIs) apply.

## Research question

Can a Koopman/EDMDc **residual** model, built on the Mueller-D'Andrea spinning-equilibrium model, predict and control (inside MPC) the failed vehicle better than the analytical model alone or a full-state Koopman model? "Better" means a smaller multi-step prediction error on new data and a smaller steady error in closed loop. Every controller is also judged by how well it catches the drone after a detection delay. The question comes from the proposal as presented (`history/v1-proposal-koopman.pdf`).

Work on how long fault detection may take before recovery is no longer possible (a certified delay budget) was explored and is **not part of the submission**; see "Exploratory work not in the submission" in the root README.

## The failure timeline

```
healthy flight ──(rotor 4 fails, t = 0)──► undetected phase ──(detected, t = tau)──► capture controller ──► relaxed hover
                                           healthy controller still
                                           flying a 3-rotor vehicle
```

The capture experiments use delays from 0 to 60 ms (see report Section 8, "How the capture is judged").

## Status (14 November 2026)

| Area | Status | Where |
|---|---|---|
| Simulator, equilibria, linear models | Done, validated against 3 papers and flight data | `rotorfail/`, `docs/03-validation.md` |
| Controllability / observability, LQR | Done | E2, E3 |
| Predictors (analytical, full-state EDMDc, residual EDMDc) | Done | E6 |
| Analytical MPC, residual-Koopman MPC | Done | E7 |
| Offset-free MPC and integral-action baselines, MPC on the full-state Koopman model | Done | E8a, E8b |
| Online adaptation, transient training, MPC tuning, ablations, realistic truth plant | Done | E8c to E8g |
| Delay-budget certificates | Explored, not in the submission | root README |

The report is `docs/report/report.pdf`, the short paper `docs/paper/paper.pdf`, the slides `docs/deck/final-presentation.pdf`. The task list is in `progress/task-list.md`, the status and caveats in `progress/status.md`.

## Headline results
1. The simulator reproduces the published two-rotor and three-rotor-loss equilibria to every digit, five hover solutions of the IJRR model within 4% (body-rate vector), and, at the thrust used in flight, the flight spin-up time within about 4% (0.65 s vs 0.62 s).
2. From 100 ms on, the residual model has the lowest multi-step error on the training plant (1 s: 0.64 vs full-state 0.91 vs analytical 7.1) and needs less data (10 episodes: 0.42 vs full-state with 40: 0.48, at 0.5 s). It does **not** generalize to an unseen plant; online adaptation halves the error there but is no better on the training plant.
3. The residual-Koopman MPC cuts a steady altitude error by 32% on the training plant but increases it by 47% on one held-out variant. An LQR with an integrator reduces the error to at most 0.024 m and keeps the capture of the LQR, so it is the better remedy; an offset-free MPC removes the error but fails the capture; the MPC on the full-state Koopman model fails the capture earlier.
4. Training on capture transients, other MPC horizons or weights, other dictionaries, regularization or sampling periods did not improve the capture; training on noisy measurements is harmful; the conclusions hold on plants with air-relative thrust and quadratic drag.

## Where things are

| Folder | Content |
|---|---|
| `proposal/` | The proposal (all content of the presented proposal; delay-budget additions marked as explored, not submitted), novelty and claims, work plan |
| `progress/` | Status, task list, presentation plan, review reports |
| `docs/` | This documentation, the LaTeX report, the slide deck |
| `rotorfail/` | Python package (simulator, models, controllers, Koopman, MPC; see its README) |
| `experiments/` | One script per experiment (V0, E1 to E3, E6, E7, E8a to E8g; exploratory E4, E5, E9, E10; see its README) |
| `results/` | Generated tables and figures |
| `tests/` | 123 automated tests (122 pass; 1 expected failure documenting a published inconsistency; see its README) |
| `literature/` | Literature review, search log, paper notes, links to the papers |
| `history/` | Earlier proposal versions and changelog |
