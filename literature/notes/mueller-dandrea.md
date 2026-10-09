# Mueller & D'Andrea: ICRA 2014 / IJRR 2016 (Relaxed hover)

**Read depth:** ICRA 2014 **full** (2026-10-10); IJRR §1–5 (earlier session).
**Local PDFs:** `../papers/MuellerDAndrea2014_ICRA_PropellerLoss.pdf`, `../papers/MuellerDAndrea2016_IJRR_RelaxedHover.pdf`

## What it does
- **Relaxed hover**: after losing 1–3 propellers the vehicle spins at a constant rate about a body-fixed axis n̄ ∥ ω̄; translation comes from tilting the axis; f_Σ n̄_z = mg.
- Model (eqs. 1–14): rotor gyroscopics I^P_zz·ω_Σ kept, I^P ω̇ neglected; yaw drag τ_d = (0, 0, −γr); τ_i = (−1)^{i+1} κ_τ f_i; rotors 1 (+x), 2 (+y), 3 (−x), 4 (−y).
- **Parameters (Sec. V-A):** m = 0.50 kg, l = 0.17 m, I^T_xx = 3.2e-3, I^T_zz = 5.5e-3 kg m², I^P_zz = 1.5e-5 kg m², κ_f = 6.41e-6 N s²/rad², κ_τ = 1.69e-2 m, γ = 2.75e-3 N m s/rad, f ∈ [0.2, 3.8] N, σ_mot = 15 ms.
- **One-rotor-loss equilibrium, ρ = 0.5:** f̄ = (2.05, 1.02, 2.05, 0) N, ω̄ = (0, 5.69, 18.89) rad/s, n̄ = (0, 0.289, 0.958), orbit radius 8 mm.
- Reduced-attitude LTI model s = (p, q, n_x, n_y); r is treated as constant. Controllable if l ≠ 0 and n̄_z ≠ 0. Motor lag added as states (eqs. 47–49).
- LQR: 1 on rates, 20 on n, 0 on motor states, 1 N⁻² on inputs; position loop ω_n = 1 rad/s; attitude loop at 1 kHz.
- **Flight (Fig. 4):** propeller 4 disabled at t = 0 *with the failure known*; the vehicle first spins up on two opposing propellers and the LQR is enabled at |ω| > 10 rad/s (0.62 s).
- Outlook: "implement the presented results with a **fault detection scheme**, and investigate different **switching strategies** for transitioning from four propellers to three". This is exactly our topic.

## Our reproduction (E1)
- f, r, n_z within 0.5%. q̄ and n̄_y are 6% lower. The paper's two-rotor (eqs. 57–59) and single-rotor (eqs. 62–64) equilibria ARE reproduced to every published digit with the same parameters, and the published one-rotor values leave a −0.011 N·m residual in the paper's own eq. (12). So this is most likely an inconsistency in that one published case.
- IJRR 2016 hover solutions (5 failure cases) reproduced with an independent implementation of its model (air-relative thrust, quadratic drag): body-rate vector within 4% with the published parameters; as a sensitivity check (fitted to the same cases), within 0.7% with I_xx = 2.75e-3 (inside rounding). See `results/tables/validation_report.md`.
- Flight vs model: spin-up to 10 rad/s at the flight thrust (≈ 2.95 N per rotor, read from Fig. 4) 0.65 s (model) vs 0.62 s (flight); 0.81 s at mg/2. IJRR reports flight spin 15.8 vs simulated 19.9 rad/s.
- The paper's eq. (27) (verified on the PDF page) uses r̄ in the ṅ rows; the exact coefficient (with q̄ ≠ 0) is r̄ + q̄ n̄_y / n̄_z (20.3 vs 18.8). We use exact Jacobians.
- With the paper's strategy, the flight thrust and instantaneous detection, our simulator climbs 0.40 m and drops 0.03 m below the start, qualitatively like their flight. P(safe) falls below 0.5 at about 19 ms of detection delay (E4).

## Use in v4
- Source of the vehicle, the model and the baseline controller/strategy.
- **Do not claim** controllability or equilibrium selection.
