# Simha, Vadgama & Raha (2017): A Geometric Approach to Rotor Failure Tolerant Trajectory Tracking Control Design for a Quadrotor

**arXiv:** 1704.00327  **Read depth:** full (per v3 session). PDF not stored locally.

## What it does
- Geometric controller on SO(3) with two torques, extended to SE(3) with saturation-based position feedback and bounded thrust.
- **Analytic region of attraction:** initial conditions in the sublevel set Ψ⁻¹[0, 2) with ‖e_Ω(0)‖ < 2α(2 − Ψ(0)).
- Assumes the fault is already detected (T₄ ≡ 0 from t = 0). The positive-thrust constraint is only tested in simulation, and there is no motor lag.

## Use in v4
- Certified regions for failed quadrotors **do exist**, so v4 must **not** claim "first certified region".
- The delay is zero by assumption. v4's contribution is the **delay budget** plus a saturation-aware set for the *linear relaxed-hover* controller.
