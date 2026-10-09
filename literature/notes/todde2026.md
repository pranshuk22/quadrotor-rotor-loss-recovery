# Todde, Martini, Rizzo & Valavanis (ICUAS 2026): Residual Koopman-Based Model Predictive Control of Quadrotors

**DOI:** 10.1109/ICUAS69441.2026.11598621  **Local PDF:** `../papers/Todde2026_ResidualKoopmanMPC_ICUAS.pdf`  **Read depth:** full

## What it does
- Builds on the analytical Koopman lifted model of Martini et al. Reduced lifted state Υ ∈ R⁴ (one coordinate per input), giving the quasi-linear form Υ̇ ≈ G(κ)u, i.e. a set of integrators in the virtual input u\* = G(κ)u.
- Linear MPC in the lifted coordinates (N_p = 20, N_c = 2, T_s = 10 ms), which is a convex QP.
- **Residual:** an MLP (8 → 64 → 32 → 4, tanh, 2,788 parameters) predicts the one-step lifted mismatch d_k = Υ_{k+1}^true − BU_k. It is evaluated **outside** the QP, injected as a measured disturbance, and clipped by d_max (empirical percentiles).
- Training data: 20 runs × 80 s, with mass, inertia, arm length and motor time constant randomized ±20%. **The same reference trajectory is used for training and test.**
- Test: mass/inertia/arm +30%, thrust/torque coefficients −10%; 200 ms position delay, 10 ms attitude delay, noise, 6.75 N saturation, 5 ms motor lag.
- Results (position RMSE under mismatch): KLQI 0.417 m, KMPC 0.146 m, RKMPC 0.095 m. Slightly worse than KMPC under nominal conditions (a robustness–optimality trade-off).
- Future work: online adaptation; "structured uncertainty bounds to provide formal robustness guaranties".

## Use in v4
- **No rotor failure, no spinning equilibrium, no guarantees**, so no overlap with v4.
- Relevant only to the optional Koopman extension. Borrow: residual outside the QP, clipping, randomized-parameter data.
