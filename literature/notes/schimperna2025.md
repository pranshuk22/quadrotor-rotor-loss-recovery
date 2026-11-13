# Schimperna, Bold & Worthmann (2025): Offset-free nonlinear MPC with Koopman-based surrogate models

**arXiv:** 2504.10954 (April 2025).  **Read depth:** abstract page only (via a fetch of the arXiv abstract).

## What the abstract says
- Offset-free tracking of the controlled output for nonlinear MPC on EDMD (Koopman) surrogate models, using a disturbance model and an observer; the guarantee holds when the modelling error is asymptotically constant.
- Tested on the van der Pol oscillator and the four-tanks process (numerical simulation).

## Use in this project
- Offset-free action on a learned Koopman model is therefore not new in general; it has not been found for a quadrotor, and not for the complete-rotor-loss regime. Our E8a compares an offset-free MPC and an integrator LQR with the residual Koopman MPC on the failed vehicle; the comparison, not the idea, is the contribution.
- Related searches (see `search-log.md`, 2026-11-13) found no paper that compares offset-free control with learned residual MPC on a quadrotor.
