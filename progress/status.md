# Project Status (2026-10-10)

## Is everything done?

**No.** The work planned for **progress presentation 1 is done**, except the slides themselves. The main contributions of both research questions are still ahead (`task-list.md`).

| Item | Status |
|---|---|
| Proposal: all PDF content kept + RQ2 added (`proposal/`) | ✅ |
| Simulator, equilibria, linear models, LQR | ✅ validated |
| RQ1: data, full-state EDMDc, residual EDMDc, analytical + residual-Koopman MPC | ✅ first version |
| RQ1: MPC on the full-state Koopman model (PDF controller 2) | ❌ not started (K5) |
| RQ1: offset-free MPC baseline, online residual adaptation | ❌ not started (K6, K7) |
| RQ2: empirical delay sweep, first LTI LMI certificate | ✅ |
| RQ2: r-robust (LPV) certificate, reachable sets, **certified τ\*** (the main contribution) | ❌ not started (D3–D6) |
| Novelty gate: read Stephan et al. 2018 and Lanzon et al. 2014 | ❌ needs library access (T0.1, T0.2) |
| Slides for presentation 1 | ❌ outline ready (`presentation-1-plan.md`) |

## Setup

- **Language/stack:** Python 3.12 in `.venv/` (NumPy, SciPy, CVXPY with Clarabel/SCS/OSQP, python-control, Matplotlib, pytest; versions pinned in `requirements.txt`).
- **Simulator** (`rotorfail/dynamics.py`): 6-DOF rigid body with quaternion attitude; rotor gyroscopic terms; per-rotor thrust limits [0.2, 3.8] N (a command ≤ 0 stops a motor); first-order motor lag (15 ms); rotor failure masks; RK4 at 0.5–1 ms; zero-order-hold controller at 1–5 ms (`sim.py`).
- **Vehicle:** the Mueller & D'Andrea Hummingbird (ICRA 2014 Sec. V-A), with every parameter from the paper (`params.py`).
- **Truth plants for learning:** nominal model + thrust loss at high body rate, inertia error and a different motor time constant; families A (train), B (held out) and randomized.
- **Controllers:** healthy LQR, failure-mode LQR (paper's weights), the paper's spin-up strategy, detection-delay supervisor, linear MPC (OSQP), and residual-Koopman MPC.
- **Analysis:** numerical Jacobians, controllability/observability (rank, PBH, Gramians), delay margins, Hu–Lin saturation LMIs (CVXPY).
- **Reproducibility:** every figure and table is produced by a script in `experiments/` with fixed seeds. Success criteria are fixed in code before the runs (`metrics.py`).

## Validation: what has been checked, and how

**45 automated tests pass** (`.venv/bin/python -m pytest -q`, ~20 s):

| File | Tests | What it checks |
|---|---|---|
| `tests/test_physics.py` | 13 | Simulator against **hand-derived solutions and conservation laws**: free fall; thrust direction from a hand-built rotation matrix; torque-free precession (closed form); conservation of inertial angular momentum and kinetic energy (1e-8); reduced-attitude kinematics vs the matrix exponential; first-order yaw spin-up (closed form); motor-lag step response; RK4 convergence order (≈ 16× per halving); saturation rules; agreement with an independent transcription of the paper's eqs. (12)–(14); agreement with an independent implementation of the IJRR general model; relaxed-hover centre-of-mass acceleration = g·tan(tilt) |
| `tests/test_paper_validation.py` | 19 | **Published numbers** from 3 papers (next table) |
| `tests/test_core.py` | 9 | Equilibrium fixed points, Jacobians vs finite differences, LQR stability, nonlinear recovery, LMI certificate invariance (500 boundary samples) |
| `tests/test_koopman_mpc.py` | 4 | Nominal discrete model accuracy, residual reduces one-step error, EDMDc rollout, MPC feasibility |

**Against papers** (full tables: `results/tables/validation_report.md`, produced by `experiments/v0_validation_report.py`):

| Source | What was compared | Result |
|---|---|---|
| Mueller & D'Andrea, ICRA 2014 | Two-rotor-loss equilibrium (eqs. 57–59) | ✅ every published digit (≤ 0.14%) |
| | Three-rotor-loss equilibrium (eqs. 62–64), exercises gyroscopic terms with p ≠ 0 | ✅ every published digit (≤ 0.8%) |
| | One-rotor-loss equilibrium (eqs. 50–53) | f, r, n_z ✅ ≤ 0.5%; q̄, n̄_y −6%: the paper's own values leave a residual in its eq. (12), so that one published case is inconsistent |
| | Fig. 3 minima of the ρ sweep | ✅ within 2–3% |
| | Coupling constant ā (eq. 28) = our Jacobian entry; controllability loss when ā = 0 (eqs. 37–39) | ✅ exact; rank 7 → 6, roll rate p uncontrollable |
| Mueller & D'Andrea, IJRR 2016 (independent implementation of their more detailed model) | Hover solutions for 5 failure cases (no failure, 1 rotor, 2 opposing, 2 adjacent, 3 rotors) | ✅ 0–4% with published parameters; all ≤ 0.7% with one inertia value inside the published rounding |
| Sun et al., T-RO 2020 (Parrot Bebop 2, a second airframe) | Two-rotor equilibrium, eq. (60) | ✅ equals the paper's formula; the paper's quoted numbers are 1.5% off its own formula |
| Flight data (ICRA Fig. 4, IJRR Sec. 5.3) | Spin-up time; spin rate | ⚠️ the model spins up **30% slower** than in flight (0.80 vs 0.62 s), and the papers' models over-predict the spin rate ~20%. A known model limitation; see below |

## Caveats you should know before presenting

1. **Model vs flight gap.** The ideal model (the same one the paper uses) spins up more slowly than the real vehicle. The empirical delay tolerance (E4, ≈ 10 ms) depends on this, so present it as "for the published model" and plan the sensitivity study (D7).
2. **RQ1 generalization.** The residual model helps only on the mismatch family it was trained on. This is a real limitation, not a bug.
3. **Certificates are linear-model certificates.** E5 certifies the linearized saturated loop; the nonlinear gap is measured by simulation, not proven.
4. **Novelty of RQ2-C2** depends on two papers not yet read (Stephan 2018, Lanzon 2014).
5. **E4 used the nominal plant; E7 part 2 used truth family A.** Their absolute numbers are not directly comparable.
