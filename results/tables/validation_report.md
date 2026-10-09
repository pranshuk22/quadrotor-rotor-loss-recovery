# Model validation report

Simulator: `rotorfail/` (Mueller & D'Andrea ICRA 2014 model). Independent implementation of the IJRR 2016 general model: `rotorfail/validation.py`. Pass/fail tests: `tests/test_physics.py` (analytic solutions, conservation laws) and `tests/test_paper_validation.py` (published numbers).

## 1. Mueller & D'Andrea, ICRA 2014 (same vehicle and model as our simulator)

| Quantity | Ours | Published | Difference | Unit |
|---|---|---|---|---|
| **One rotor lost, ρ = 0.5** (eqs. 50–53) | | | | |
| f1 = f3 | 2.040 | 2.050 | -0.47% | N |
| f2 | 1.020 | 1.020 | +0.01% | N |
| p | 0.000 | 0.000 | +0.000 (abs) | rad/s |
| q | 5.366 | 5.690 | -5.69% | rad/s |
| r | 18.808 | 18.890 | -0.43% | rad/s |
| n_y | 0.274 | 0.289 | -5.06% |  |
| n_z | 0.962 | 0.958 | +0.38% |  |
| orbit radius | 7.317 | 8.000 | -8.54% | mm |
| **Two opposing rotors lost** (eqs. 57–59) | | | | |
| f1 = f3 | 2.453 | 2.450 | +0.10% | N |
| propeller speed ω1 | -618.551 | -619.000 | +0.07% | rad/s |
| r | 30.143 | 30.100 | +0.14% | rad/s |
| **Three rotors lost** (eqs. 62–64) | | | | |
| f1 | 5.369 | 5.370 | -0.02% | N |
| propeller speed ω1 | -915.188 | -915.000 | -0.02% | rad/s |
| p | 14.684 | 14.700 | -0.11% | rad/s |
| q | 0.000 | 0.000 | +0.000 (abs) | rad/s |
| r | 32.994 | 33.000 | -0.02% | rad/s |
| n_x | 0.407 | 0.410 | -0.83% |  |
| n_z | 0.914 | 0.910 | +0.40% |  |
| **Fig. 3 minima** | | | | |
| min |ω| | 18.618 | 19.000 | -2.01% | rad/s |
| ρ at min |ω| | 0.675 | 0.655 | +3.05% |  |
| min f1 | 2.029 | 2.040 | -0.53% | N |
| ρ at min f1 | 0.580 | 0.563 | +3.02% |  |

**Reading.** The two-rotor and single-rotor equilibria are reproduced to every published digit, including the single-rotor case, which exercises the gyroscopic and propeller-momentum terms with p ≠ 0. In the one-rotor case, f, r and n_z match, but q and n_y are 6% lower. Substituting the paper's own published values into its eq. (12) leaves a roll-torque residual of -0.0113 N·m (7% of the rotor-2 torque), so that published case is not an exact equilibrium of the paper's own model with the stated parameters. We treat it as an inconsistency in that single published case, not a model error.

Also checked analytically (tests): eq. (21) for r̄; eq. (28) for the coupling constant ā equals our Jacobian entry; eqs. (37)–(39): our controllability rank drops from 7 to 6, with the roll rate p uncontrollable, exactly when ā = 0.

## 2. Mueller & D'Andrea, IJRR 2016 (same vehicle, more detailed aerodynamics)

The IJRR model differs from ICRA 2014 in two ways: propeller thrust uses the speed relative to the **air** (Ω + r), and the drag torque is **quadratic** in ω on all axes. Our independent implementation (`rotorfail/validation.py`) solves the rotational equilibrium for the published propeller speeds.

| Failure case | Published Ω (rad/s) | Published ω | Ours, published parameters | Ours, I_xx = 2.75e-3 | Vertical force ratio |
|---|---|---|---|---|---|
| no failure | (438, 438, 438, 438) | (0.00, 0.00, 0.00) | (0.00, 0.00, 0.00) | (0.00, 0.00, 0.00) | 1.003 |
| rotor 4 failed | (585, 362, 585, 0) | (0.20, 4.30, 19.50) | (0.15, 4.19, 19.47) | (0.16, 4.30, 19.46) | 1.002 |
| rotors 2, 4 failed (opposing) | (643, 0, 643, 0) | (0.00, 0.00, 24.50) | (-0.00, 0.00, 24.50) | (-0.00, 0.00, 24.50) | 1.001 |
| rotors 3, 4 failed (adjacent) | (1067, 218, 0, 0) | (26.00, 0.00, 23.30) | (24.94, 0.06, 23.57) | (26.15, -0.03, 23.17) | 0.995 |
| rotors 2, 3, 4 failed | (1103, 0, 0, 0) | (28.00, -1.60, 24.50) | (26.73, -1.45, 24.93) | (28.25, -1.65, 24.42) | 0.994 |

**Reading.** With the published parameters, the hover solutions are within 0–4%. The two high-rate cases are the most sensitive to the drag and inertia values, which are published to 1–2 significant figures. One value inside the rounding of the published I_xx = 2.7e-3 (2.75e-3) brings all five cases within 0.7% in ω and 0.6% in force balance. The two-rotor speed 643 rad/s is explained only by air-relative thrust: κ_f(643 − 24.5)² = mg/2, while κ_f·643² is 8% too high.

**Consequence for our simulator.** The ICRA model we simulate omits air-relative thrust. At the one-rotor equilibrium (r ≈ 19 rad/s; propeller speeds −565, +399, −565 rad/s) it changes the thrust of rotors 1 and 3 by about −7% and of rotor 2 by about +10%. That is comparable in size to the uniform thrust loss in our truth families (`params.truth_family`), but different in structure, because it acts per rotor. Adding air-relative thrust to the truth plant is a cheap and valuable next step (task K11).

## 3. Sun, Wang, Chu & de Visser, T-RO 2020: a second airframe (Parrot Bebop 2)

| Quantity | Ours | Eq. (60) with Table III | Published text | Unit |
|---|---|---|---|---|
| r̄ (two opposing rotors lost) | 26.81 | 26.81 | 26.4 | rad/s |
| propeller speed ω̄ | 1029 | 1029 | 1015 | rad/s |

**Reading.** Our solver equals the paper's own closed form exactly. The paper's quoted numbers are about 1.5% below its own formula evaluated with its Table III, which is internal to the paper.

## 4. Against flight data (where the model is known to be imperfect)

| Quantity | Our model | The paper's model | Flight | Source |
|---|---|---|---|---|
| Time to |ω| > 10 rad/s on two rotors after propeller 4 is disabled | 0.81 s (closed form 0.80 s) | not reported | 0.62 s | ICRA 2014, Fig. 4 |
| Spin rate about n, one rotor lost | 19.6 rad/s (ρ = 0.5) | 19.9 rad/s (min-power solution) | 15.8 rad/s | IJRR 2016, Sec. 5.3 |
| Height offset, two rotors, from thrust loss while spinning | not in the nominal model | not in the model | ≈ 2.4 m | ICRA 2014, Sec. V-E |

**Reading.** The nominal model spins up about 30% slower than the flight and over-predicts the spin rate by about 20% (both papers attribute the gaps to unmodelled aerodynamics). These are the reasons the project (i) keeps a model-mismatch truth plant for RQ1 and (ii) must report the RQ2 delay results with a sensitivity study on the yaw-drag and thrust parameters (task D7). The empirical delay tolerance in E4 depends on spin-up speed.
