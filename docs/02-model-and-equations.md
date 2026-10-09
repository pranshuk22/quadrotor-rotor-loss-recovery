# 2. Model and Equations

Source model: Mueller & D'Andrea, ICRA 2014, eqs. (1)–(15) (`literature/papers/MuellerDAndrea2014_ICRA_PropellerLoss.pdf`). Code: `rotorfail/params.py`, `rotorfail/dynamics.py`, `rotorfail/equilibrium.py`, `rotorfail/models.py`.

## 2.1 Frames and conventions
- Inertial frame: z points **up**; gravity is −g e₃ with g = 9.81 m/s².
- Body frame: z along the thrust direction. Attitude is a unit quaternion (scalar first) mapping body to inertial vectors, R = R(q).
- Rotor positions (arm length l): rotor 1 at +x, 2 at +y, 3 at −x, 4 at −y.
- Propeller spin: rotors 1 and 3 spin with **negative** speed and rotors 2 and 4 with **positive** speed (`prop_sign = (−1, 1, −1, 1)`). The reaction torque is τ_i = (−1)^{i+1} κ_τ f_i: positive yaw torque from rotors 1 and 3.
- Rotor 4 is the failed rotor throughout (as in the paper); the problem is symmetric in the choice.

## 2.2 Equations of motion
State of the simulator (17 entries): position d (3), velocity v (3), quaternion (4), body rates ω = (p, q, r) (3), produced thrusts f (4).

Translation:

    m d̈ = R e₃ Σ f_i · η(ω) − m g e₃

Rotation (paper eq. 4, with the term I^P ω̇ neglected as in the paper):

    I^B ω̇ = τ − ω × ( I^T ω + I^P_zz ω_Σ e₃ ),      ω_Σ = Σ ω_i,   f_i = κ_f ω_i²
    τ = ( l(f₂ − f₄),  l(f₃ − f₁),  κ_τ(f₁ − f₂ + f₃ − f₄) − γ r )   [thrusts scaled by η(ω)]

I^B is the body inertia and I^T = I^B + 4 I^P includes the propellers.

Attitude kinematics: q̇ = ½ q ⊗ (0, ω), renormalized after each step.

Motors (first-order lag on thrust): ḟ_i = (sat(u_i) − f_i)/σ, where
- sat(u) = 0 if u ≤ 0 (motor stopped), otherwise clip(u, f_min, f_max);
- a failed rotor produces f = 0.

Thrust-efficiency (truth plants only): η(ω) = max(0, 1 − k‖ω‖²). The nominal model has k = 0.

Integration: fixed-step RK4 (0.5–1 ms). The controller is sampled every 1–5 ms with a zero-order hold (`rotorfail/sim.py`).

## 2.3 Reduced attitude
n = Rᵀ e₃ is the inertial "up" direction in body axes. It obeys ṅ = −ω × n. After the failure only n is controlled; the yaw angle is given up.

## 2.4 Relaxed hover (equilibrium)
Conditions: ω̇ = 0 (rotation equation), n ∥ ω (so ṅ = 0), and f_Σ n_z = m g (zero mean vertical acceleration). The centre of mass moves on a horizontal circle of radius √(1 − n_z²)/n_z · g/‖ω‖².

With rotor 4 lost and f₁ = f₃, f₂ = ρ f₁, the rate equations have a closed form:

    p = 0,   r = κ_τ (f₁ − f₂ + f₃)/γ,   q = l f₂ / ( (I^T_zz − I^T_xx) r + I^P_zz ω_Σ )

`relaxed_hover(p, rho)` then solves f₁ by a 1-D root search on f_Σ n_z = m g. Other configurations:
- `two_rotor_hover(p)`: rotors 2 and 4 lost, f₁ = f₃ = mg/2, n = e₃.
- `single_rotor_hover(p)`: only rotor 1. Solves f₁ and ω jointly (numerical root find).

Design point (ρ = 0.5): f = (2.040, 1.020, 2.040, 0) N, ω = (0, 5.37, 18.81) rad/s, n = (0, 0.274, 0.962) (tilt 16°), orbit radius 7.3 mm.

## 2.5 Parameters (`QuadParams`)

| Field | Value | Meaning |
|---|---|---|
| m | 0.50 kg | mass |
| l | 0.17 m | arm length |
| Ixx_T, Izz_T | 3.2e-3, 5.5e-3 kg m² | total inertia (body + propellers) |
| Izz_P, Ixx_P | 1.5e-5, 0 kg m² | propeller inertia |
| kappa_f | 6.41e-6 N s²/rad² | thrust coefficient |
| kappa_tau | 1.69e-2 m | reaction torque per thrust |
| gamma | 2.75e-3 N m s/rad | linear yaw drag |
| f_min, f_max | 0.2, 3.8 N | running-motor thrust range |
| sigma_mot | 0.015 s | motor time constant |
| thrust_loss | 0 (nominal) | truth-plant effect k |

Truth plants (`truth_family`, `random_family`):

| Family | thrust_loss k | I_xx × | I_zz × | σ |
|---|---|---|---|---|
| A (training) | 1.5e-4 | 1.08 | 0.95 | 20 ms |
| B (held out) | 2.5e-4 | 0.94 | 1.06 | 12 ms |
| Randomized | U[0, 2e-4] | U[0.96, 1.10] | U[0.93, 1.03] | U[15, 22] ms |

## 2.6 Linear models (`rotorfail/models.py`)
Both are central-difference Jacobians of exact nonlinear equations (tested against finite differences).

**Healthy hover** (12 states, 4 inputs): x = (x, y, z, v_x, v_y, v_z, φ, θ, ψ, p, q, r), ZYX Euler angles; trim f_i = mg/4. Open loop: eleven zero eigenvalues and the yaw-drag mode −0.506.

**Failed vehicle** (7 states, 3 inputs): s = (p, q, r, n_x, n_y, z, v_z), inputs (f₁, f₂, f₃), with n_z = √(1 − n_x² − n_y²) and v̇_z = f_Σ n_z/m − g. These equations are autonomous in body coordinates, so the linearization about the relaxed hover is **time invariant**. Open loop: ±10.10j (gyroscopic coupling ā = A[p,q]), ±19.56j (= ‖ω̄‖), −0.506, and a double integrator.
- ā matches the paper's eq. (28): ā = (I^T_xx − I^T_zz)/I^B_xx · r̄ − I^P_zz/I^B_xx · ω̄_Σ.
- The exact coefficient of n_y in ṅ_x is r̄ + q̄ n̄_y/n̄_z = 20.3. The paper's simplified eq. (27) uses r̄ = 18.8.

`add_motor_lag(model, σ)` appends three produced-thrust states (f_dot = (f_cmd − f)/σ), giving the 10-state model used by the failure LQR, the MPC and the certificate.

## 2.7 Known modelling limitations
- No air-relative thrust (IJRR 2016 eq. 4) and no quadratic drag in the simulator; both are validated in `rotorfail/validation.py` but not yet in the truth plant (task K11).
- The spin-up time depends strongly on the thrust of the two remaining rotors; at the flight thrust it is within about 4% of the ICRA flight (see `03-validation.md`). The papers' models over-predict the steady spin rate by about 20%.
- No translational drag, no blade flapping, no ground effect, no sensor noise (yet).
